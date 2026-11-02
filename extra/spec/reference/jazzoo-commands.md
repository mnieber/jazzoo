# Jazzoo Commands

This document describes how the scripts that a Jazzoo file runs, and its shell lines,
run commands with `run` and `jaz-run`, and how the user confirms them.

---

## 1. Overview

A script that a Jazzoo file runs — a Python shebang block, or any `python foo.py`
shell line — runs commands with `run`:

```python
from jazzoo import run

run("my-app --config=simple doit")                      # runs in the foreground
run("docker compose logs | grep error")                 # a string runs in bash
run(["tmux", "send-keys", "-t", pane, command, "C-m"])  # a list runs directly
head = run("git rev-parse HEAD", capture=True).stdout
if run("tmux has-session -t blogs", check=False).returncode != 0:
    run("tmux new-session -d -s blogs")
```

Jazzoo files themselves do not need `run`: a shell line already runs a command.

## 2. `run`

```python
run(command, cwd=None, env=None, capture=False, check=True, echo=False) -> CommandResult
```

**The command** is a string or a list:

- A string runs in bash (`bash -c "<command>"`), so pipes, `&&`, `;`, redirection,
  `$HOME`, `~`, globs and quoting work as in a shell line of a Jazzoo file.
- A list runs directly, without a shell: the first term is the executable, and the
  others are passed as they are. Its executable is looked up on the `PATH` of the
  command's environment before anything runs; a term that contains a `/` is used as a
  path. An executable that is not found is a `CommandNotFoundError`. For a string,
  bash reports an unknown command itself (exit code 127).
- An empty command is a `ValueError`.

A value that is pasted into a string becomes shell syntax, as in
`jazzoo-language.md`, section 5.5. Use the list form for values from variables, or
quote them with `shlex.quote`.

**Where and how it runs:**

- `cwd` is the working directory of the command; a directory that does not exist is a
  `ValueError`, raised before anything runs.
- `env` is a dict of variables that is laid over `os.environ`; the script's own
  environment is not changed.
- By default the command runs in the foreground: it inherits the script's stdin,
  stdout and stderr, and `run` waits until it ends. Whether it reaches the terminal
  depends on where the script's stdout goes; under `jaz`, that is the terminal in an
  interactive function (`jazzoo-language.md`, section 9.7).
- With `capture=True`, stdout and stderr are captured as text instead of being shown.
  Stdin is still inherited.
- With `echo=True`, the command is printed before it runs. A string is shown as given,
  a list with `shlex.join`; with `cwd`, the directory comes first:
  `(/app/src) python manage.py migrate`. When commands are confirmed (section 3),
  the prompt replaces the echo.

**Ctrl-c.** While a command runs, `run` ignores SIGINT in the script (in the main
thread), so a ctrl-c reaches the command only. Afterwards the old handler is restored.
If the command was ended by SIGINT, `run` raises `KeyboardInterrupt`.

**The result** is a `CommandResult` with `command` (as given), `returncode`, `stdout`
and `stderr` (`None` unless captured), and `skipped` (`True` when the user skipped the
command at a confirmation prompt, section 3). With `check=True` (the default), a
non-zero exit code raises `CommandFailedError`, which holds the result and names the
command and the exit code (and includes the captured stderr). With `check=False`,
`run` returns the result whatever the exit code, for commands that answer a question
through their exit code (`grep -q`, `tmux has-session`).

## 3. Confirming commands

`jaz --confirm <target>` makes `run` ask the user before every command that it
executes. The user can run the command, skip it, or abort:

```
$ jaz --confirm deploy
(/home/jane/blogs) docker compose build
confirm? [Y/n/q] y
...
(/home/jane/blogs) docker compose up -d
confirm? [Y/n/q] n
(/home/jane/blogs) python scripts/migrate.py
confirm? [Y/n/q] q
```

**What is confirmed.** Only the commands of `run` (and of `jaz-run`, section 4).
`jaz` itself never asks: the shell lines and shebang blocks of a Jazzoo file run as
usual. A command that should be confirmed is started with `run` from a Python script,
or with `jaz-run` from a shell script or a shell line:

```
deploy():
    jaz-run docker compose down -v --project=🐆.name
    jaz-run -c "docker compose logs | grep error"
```

Whatever a script does without `run` (writing files, calling `subprocess` directly) is
not confirmed. Every `run` call is confirmed, also with `capture=True` or
`check=False`, but only after `run` has checked its arguments: an empty command, a
missing `cwd` or an unknown executable is still an error, without a prompt.

**Switching it on.** `jaz --confirm` sets the environment variable
`JAZZOO_CONFIRM=1` before it loads the root module (overwriting a value that was
already set); it does not change how `jaz` runs blocks. Every block inherits the
variable, so `run` confirms in every script that the run starts, including the
scripts of a nested `jaz`; everything below a `jaz --confirm` is confirmed. `run`
confirms whenever `JAZZOO_CONFIRM` is exactly `1`, also outside `jaz` (e.g. when a
developer exports the variable and runs a script directly). `--confirm` only matters
when a target runs: `jaz --confirm --list` and `jaz --confirm --help` ignore it.

**The prompt** shows the command as `(<cwd>) <command>` (a string as given, a list
with `shlex.join`), followed by `confirm? [Y/n/q] `. Unlike the echo, it always shows
the directory: without `cwd`, the current directory. With `echo=True`, the prompt
replaces the echo.

The prompt is written to, and the answer read from, the controlling terminal
(`/dev/tty`), not stdout and stdin. So it reaches the person at the terminal from a
captured block, from a quiet call, from `$(jaz-run ...)`, and when the output of `jaz`
is redirected (`jaz --confirm build > build.log`); the prompt is not part of the
output.

**Answers.** The answer is stripped and case-insensitive:

- `y` or Enter runs the command;
- `n` skips it: the command does not run, and the script continues. `run` returns a
  `CommandResult` with `skipped=True` and `returncode=0`; with `capture=True`,
  `stdout` and `stderr` are `""`. Later steps may depend on what a skipped command
  would have done; that is the user's responsibility;
- `q`, or the end of input (ctrl-d), aborts: `run` raises `CommandAbortedError`. A
  script that does not catch it exits non-zero, so its block fails and `jaz` stops
  the run;
- any other answer (also `yes`) asks again.

A ctrl-c at the prompt raises `KeyboardInterrupt`, as anywhere else in the script.

**Without a terminal** (CI, cron), `jaz --confirm <target>` fails before it loads the
root module, with `--confirm needs a terminal`. `run` with `JAZZOO_CONFIRM=1` and no
terminal raises `CommandError` with the same message, and the command does not run.

## 4. `jaz-run`

`jaz-run` is the command-line front-end of `run`, for shell scripts and the shell
lines of Jazzoo files. It runs the command with the same confirmation, echo and
prompt:

```
jaz-run [--echo] [--] <executable> [<argument> ...]   # a list command
jaz-run [--echo] -c "<command>"                       # a string command, run in bash
```

- The options of `jaz-run` come first. The first argument that is not an option of
  `jaz-run` starts the command, and everything after it belongs to the command (as
  with `env` and `sudo`): `jaz-run ls --echo` passes `--echo` to `ls`. `--` ends the
  options explicitly.
- Without `-c`, the arguments are a list command:
  `run([<executable>, <argument>, ...])`. With `-c`, the single argument after it is a
  string command, which runs in bash: `run("<command>")`.
- `--echo` is `run`'s `echo=True`. `--help` prints the usage.
- There are no options for `cwd`, `env`, `capture` and `check`: the command already
  runs in the current directory and environment of the shell, its output is captured
  with `$(jaz-run ...)` (the prompt still reaches the terminal), and its exit code is
  available as usual. A failing command prints no extra message, because its own
  stderr is visible.

Exit codes:

| Code               | When                                                                               |
| ------------------ | ---------------------------------------------------------------------------------- |
| the command's code | the command ran                                                                    |
| `0`                | the user skipped the command, or `--help`                                          |
| `130`              | the user aborted (`jaz-run: aborted by the user` on stderr), or pressed ctrl-c     |
| `127`              | the executable of a list command is not found (the `CommandNotFoundError` message) |
| `2`                | a usage error, or an error of `run` itself (an empty command, no terminal)         |

Every message of `jaz-run` on stderr starts with `jaz-run: `. In a shell line of a
Jazzoo file, a non-zero exit code stops the run; a shell script stops only when it
uses `set -e`.

`jaz-run` is installed as a console script next to `jaz` and `jazzoo`, so it is on the
`PATH` wherever `jaz` is. Its entrypoint lives in `jazzoo.commands`, which also has a
`__main__.py`, so a vendored copy of the sub-package works without installing jazzoo:
`python3 -m myproject.jazzoo_commands -c "..."`.

## 5. The `jazzoo.commands` sub-package

`run`, `CommandResult` and the command errors live in the sub-package
`jazzoo.commands`, and are re-exported by `jazzoo`, so `from jazzoo import run` works.
Like `jazzoo.config` (`jazzoo-config.md`, section 7), the sub-package is
self-contained: it imports only the standard library and its own modules, and its
internal imports are relative, so a project can copy it into its own source tree
under any name.

The name `JAZZOO_CONFIRM` and the prompt are defined in `jazzoo.commands` (like the
name of `JAZZOO_CONFIG_FILES` in `jazzoo.config`), so that a vendored copy reads the
same variable that `jaz` sets. The rest of jazzoo uses `jazzoo.commands` only for the
name of the variable and to check for a terminal.

## 6. Command errors

| Class                  | Meaning                                               |
| ---------------------- | ----------------------------------------------------- |
| `CommandNotFoundError` | the executable of a list command is not on the `PATH` |
| `CommandFailedError`   | a command exited non-zero while `check=True`          |
| `CommandAbortedError`  | the user aborted at a confirmation prompt (section 3) |

All subclass `CommandError(Exception)`, defined in `jazzoo.commands`. Like the config
errors, they are not `JazzooError`s. Invalid arguments (an empty command, a missing
`cwd`) are `ValueError`s. A `run` that must confirm without a terminal raises a plain
`CommandError` (section 3).

```python
class CommandError(Exception): ...
class CommandNotFoundError(CommandError): ...  # the executable of a list command is not found
class CommandFailedError(CommandError): ...    # a command exited non-zero; holds the CommandResult
class CommandAbortedError(CommandError): ...   # the user aborted at a confirmation prompt
class UsageError(CommandError): ...            # a usage error of jaz-run
```
