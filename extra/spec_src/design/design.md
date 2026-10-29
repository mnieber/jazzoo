# Running commands in a container

`run_docker` turns `run` into a function that runs its commands in a Docker container
that is already running, with `docker exec`:

```python
from jazzoo import get_config as get, run, run_docker

run_be = run_docker(get("/blogs_be/container"))(run)

run_be("python manage.py migrate")
run_be(["pytest", "-x"], cwd="/app/src")
version = run_be("python --version", capture=True).stdout
run("docker compose ps")  # the undecorated run still runs on the host
```

A script whose commands all run in the same container may replace `run` itself:
`run = run_docker("blogs_be")(run)`.

```python
run_docker(container, user=None, workdir=None, env=None, shell="bash") -> decorator
```

**The decorator.** `run_docker(...)` returns a decorator. It takes a function with the
signature of `run` and returns a function with the same signature. The returned
function turns its command into a `docker exec` command and passes that to the
decorated function, with the other arguments. So echo, confirmation,
`capture`, `check`, ctrl-c and the `CommandResult` are those of the decorated `run`, and
decorators can be stacked (e.g. a later decorator that logs every command).

**Its arguments** are the settings of `docker exec` that hold for every command:

- `container` is the name or id of the container, as `docker exec` takes it; for a
  Docker Compose stack, the `container_name` of the service. `run_docker` does not read
  the config itself; the script passes the name, typically from `get_config`.
- `user` becomes `--user <user>`.
- `workdir` is the default working directory in the container (`--workdir`); without
  it, the command runs in the `WORKDIR` of the image.
- `env` is a dict of variables that every command gets in the container.
- `shell` is the shell that runs a string command in the container. The default is
  `bash`, as for `run`; an image without bash (e.g. Alpine) needs `shell="sh"`.

**How a call is translated.** The decorated function always receives a list command,
so nothing runs in a shell on the host:

| Call                                  | Command that the decorated `run` receives                 |
| ------------------------------------- | --------------------------------------------------------- |
| `run_be("a \| grep b")`               | `docker exec <options> blogs_be bash -c "a \| grep b"`    |
| `run_be(["pytest", "-x"])`            | `docker exec <options> blogs_be pytest -x`                |
| `run_be(..., cwd="/app/src")`         | `docker exec --workdir /app/src ... blogs_be ...`         |
| `run_be(..., env={"DEBUG": "1"})`     | `docker exec --env DEBUG=1 ... blogs_be ...`              |

- `cwd` is a directory in the container. It replaces `workdir` for this call, and is
  not checked on the host: the decorated function is called with `cwd=None`. The
  command never inherits the host's current directory.
- `env` is merged over the `env` of `run_docker` (the call wins) and passed with
  `--env`; it does not change the environment of the `docker` client. The variables
  that the container already has (e.g. from the `env_file` of its service) are kept.
- `capture`, `check` and `echo` are passed on unchanged.
- The options always come in the same order, so that the echo and the prompt are
  predictable: `docker exec --interactive [--tty] [--user <user>] [--workdir <dir>]
  [--env <name>=<value> ...] <container> <command>`. The `--env` options follow the
  order of the merged dict: the variables of `run_docker` first, then the new ones of
  the call.
- An empty command is a `ValueError`, raised before the `docker exec` command is built,
  as for `run`. An empty or blank `container` is a `ValueError`, raised by
  `run_docker(...)` itself, before anything is decorated.

**Terminal.** `--interactive` is always passed, so the command reads the script's stdin,
as with `run`. `--tty` is passed only when `capture` is false and both stdin and stdout
of the script are terminals. So `run_be("fish")` opens an interactive shell in the
container, while captured output stays clean (a tty would merge stderr into stdout and
end lines with `\r\n`), and a script without a terminal (CI) does not fail with docker's
`the input device is not a TTY`.

**What the user sees.** The echo, the confirmation prompt, `CommandResult.command` and
the message of `CommandFailedError` show the full `docker exec` command, because that is
what runs:

```
(/home/jane/blogs) docker exec --interactive --tty --workdir /app/src blogs_be pytest -x
confirm? [Y/n/q]
```

Values passed with `env` are therefore visible in the echo and the prompt; secrets
belong in the env file of the container instead.

**Errors.**

- A missing `docker` executable on the host is a `CommandNotFoundError`, raised by the
  decorated `run`.
- A container that does not exist or is not running, and an executable that does not
  exist in the container, are reported by `docker exec` itself (on stderr, with a
  non-zero exit code), so with `check=True` they raise `CommandFailedError`.
  `run_docker` does not check the container beforehand, which would cost an extra
  `docker` call per command.

**Ctrl-c.** With `--tty`, a ctrl-c reaches the command in the container through the
tty. Without a tty, the ctrl-c only reaches the `docker` client (`docker exec` does not
forward signals), and the command in the container may keep running.

**Not included.** Starting a new container from an image (`docker run`), addressing a
container by its Docker Compose service name (`docker compose exec`), and mapping paths
between the host and the container. `jaz-run` has no option for containers: a shell line
writes `docker exec` itself, e.g. `jaz-run docker exec blogs_be python manage.py migrate`.
