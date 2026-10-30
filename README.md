# jazzoo 🐐🐭🐆

**A beast of a task-runner.**

Jazzoo starts out as simple as `just` or `make`: a file of named tasks whose bodies are
shell lines. But where those tools stop, Jazzoo keeps going. Your tasks are real
functions, your task file can be split into modules with a public and a private side,
and your Python scripts are first-class citizens.

```
🐐.log-level = "info"

build(target, mode="release"):
    cargo build --target=🐆.target --profile=🐆.mode --log-level=🐐.log-level
```

```
$ jaz build target=x86_64 mode=dev
$ jaz build x86_64                   # the first argument may skip its name
```

---

## Why jazzoo

### Tasks are functions, not macros

Every argument in a `.jaz` file is named, so `🐭.build(target="dev")` still reads
right six months later, and adding a parameter never shifts the meaning of a call.
Defaults are expressions, a task returns a value, and you can pre-fill arguments or
chain tasks in a pipe:

```
# currying
🐭.build-dev = 🐭.build[mode="dev"]
# return values, JSON
🐆.version   = 🐭.read-version() | ⚙️.parse
🐆.path      = "input.json" | 🐭.make-full-path[path] | ⚙️.abs
```

The three sigils are the scopes: 🐐 global, 🐭 (module) this file, 🐆 (local) this call. You can tell
at a glance where a value comes from, and a reference needs no quoting or braces in
a shell line.

### One file grows into a tree, without becoming a mess

Split tasks over as many `.jaz` files as you like. An **import** is private to the file
that makes it; an **export** turns functions into targets. Helpers stay helpers, and
`jaz --list` shows only what you meant to publish.

```
from ./docker.jaz import (up, down) as docker     # 🐭.docker.up(), for this file only
from ./frontend.jaz export (build, test) as fe    # jaz fe.build, jaz fe.test
from ./backend.jaz export (build, test) as be     # jaz be.build, jaz be.test
```

**Export layers** give each part of the project its own corner of the command line
(`jaz fe.react.build`), and they nest, rename and merge. A function always runs in the
module that defines it, so an imported task brings its own private helpers along.

### Python is a first-class citizen

A body can switch to any interpreter with a shebang, and Jazzoo variables are
substituted into it. When a task needs real logic, write it in Python, and use the
batteries that come with jazzoo:

```
⚙️.load_config(path=⚙️.module.dirname / "config/base.yaml")

deploy(stage="staging"):
    #!/usr/bin/env python3
    from jazzoo import get_config as get, run

    # Jazzoo substitutes 🐆.stage before Python runs: get("/staging/services")
    for service in get("/🐆.stage/services"):
        run(f"docker compose up -d {service}")
```

`get_config` reads layered YAML config (files include their own layers, later files
override earlier ones, `${...}` expands env vars and other config values). `run` runs
commands with proper errors, and `run_docker` sends them into a running container.

### Look before you leap

`jaz --confirm deploy` asks before every command that the deploy runs, and lets you run,
skip or abort each one. Use it to step through a risky script, or to see what it would
do, without adding a dry-run mode to it. `jaz-run` gives shell scripts the same powers.

### Every project, from any directory

`zoo` registers your projects, each with its own venv. `zz blog` switches to a project,
`zz -` switches back, and `zoo build` runs a target of the active project from wherever
you are.

---

## Features at a glance

**Language**

- Three scopes, written as sigils: 🐐 global, 🐭 module, 🐆 local; ⚙️ for built-ins.
- Bare references in shell lines: `docker compose up --log-level=🐐.log-level`.
- `{{ ... }}` for inline expressions: conditionals, `and`/`or`/`not`, `==`, pipes.
- JSON values: objects and arrays, with dotted access (`🐆.config.hosts.0`).
- Path joins with `/`, and pipes for paths: `⚙️.abs`, `⚙️.basename`, `⚙️.dirname`, `⚙️.ext`, `⚙️.stem`.
- `⚙️.parse` and `⚙️.json` to move between text and JSON.
- `⚙️.sh-quote` to pass untrusted values to the shell safely.
- `?` for optional references, `:-` for defaults, also for env vars: `⚙️.env.CI?:-false`.
- Truthiness that understands env-style flags (`CI=false`, `DEBUG=0`).
- Parse errors are reported when the file loads, before anything runs.

**Functions**

- Named arguments only, with defaults that are expressions.
- Dependencies that run before the body: `build(): clean() codegen()`.
- Return values: the output of the last block, or `🐆.retval`.
- Currying with `f[mode="dev"]`, and function pipes with `|`.
- Functions as values, including `(🐭.fast or 🐭.slow)(input="x")`.
- Local functions inside a function body.
- `[private]` for helpers that are not targets.
- `[interactive]` for prompts, editors, shells and live progress output.
- Calls whose value is used are quiet, like `$(...)` in a shell.
- `@` hides the echo of a shell line.

**Bodies**

- Each shell line runs in bash, and stops the run when it fails.
- Shebang blocks run several lines in any interpreter: bash, Python, node, ...
- Jazzoo assignments inside a shebang block are swept out before it runs.
- `⚙️.stdout` and `⚙️.output` hold what the last block printed.
- `⚙️.load_env` loads a dotenv file; variables that are already set win.

**Modules**

- Explicit relative or absolute import paths; no search path.
- `import ... as ns` for private use, `export` for public targets.
- Export layers for dotted targets (`jaz fe.react.build`), which nest and merge.
- The same function reached along several paths is one function.
- Circular imports work, with live bindings.

**Command line**

- `jaz` lists the targets; `jaz --list fe.build` shows a signature.
- `jaz --list-all` lists every target at every depth.
- `key=value` arguments; the first one may skip its name.
- Options go anywhere: `jaz build myapp --confirm`.
- `--confirm` asks before every command that `run` or `jaz-run` starts.
- `--trace` adds the stack trace to an error.
- Personal aliases in `~/.config/jazzoo/config`, with preset arguments: `fb = fe.build mode=debug`.
- The command can also be spelled `jazzoo`, or 🐐🐭🐆.

**Python and shell scripts**

- `run(...)`: a string runs in bash, a list runs directly; `capture`, `check`, `cwd`, `env`, `echo`.
- `run_docker(container)(run)` runs the same commands with `docker exec`.
- `jaz-run` is `run` for shell scripts, with the same confirmation.
- `get_config("/path/to/key")` reads the merged YAML config.
- `⚙️.python` is the Python that runs `jaz`, to run scripts that import jazzoo.
- Config files include their own layers via `/jazzoo/includes`.
- `${ENV_VAR:-default}` and `${/other/key}` expansion, evaluated lazily.
- Config errors name the file, and the layer, that caused them.

**Projects (`zoo`)**

- `zoo env --init --create-venv` registers a project with its own venv.
- `zoo <target>` runs a target of the active project from any directory.
- `zoo env <name>` and `zoo env -` switch projects, like `cd -`.
- New terminals start in the last active project.
- `zz` shell function, and completions of `jaz` and `zoo` for fish: `zoo env --install-fish`.

---

## Install

```
pip install git+https://github.com/mnieber/jazzoo.git
```

Jazzoo needs Python 3 and has no dependencies.

The sigils are emoji. Bind them to keys in your editor, as
[Editor setup](extra/spec_src/reference/jazzoo-editor-setup.md) describes, and they
are as quick to type as `$`.

## Documentation

- [The Jazzoo language](extra/spec_src/reference/jazzoo-language.md)
- [Running commands: `run`, `jaz-run` and `--confirm`](extra/spec_src/reference/jazzoo-commands.md)
- [Config files](extra/spec_src/reference/jazzoo-config.md)
- [Editor setup: typing the sigils](extra/spec_src/reference/jazzoo-editor-setup.md)
