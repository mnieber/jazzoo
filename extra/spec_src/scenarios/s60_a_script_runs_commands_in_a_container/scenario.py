import sunya
from sunya import C as c
from sunya import R as r
from sunya import goal, it, the

scenario = sunya.add_scenario("s60_a_script_runs_commands_in_a_container")


def run_scenario():
    r.script = c.External.Actors.Script
    r.docker = c.External.Actors.Docker
    r.run_docker_action = c.Commands.Actions.RunDocker
    r.run_action = c.Commands.Actions.Run
    r.needs_tty_rule = c.Commands.Rules.NeedsTty
    r.command_result = c.Commands.Models.CommandResult

    with goal().decorate(r.run_action).for_a(r.container):
        with the(r.script).calls(r.run_docker_action).with_the(r.container):
            it().returns_a(r.decorator)
        the(r.script).applies_the(r.decorator).to(r.run_action)

    with goal().run_a(r.command).in_the(r.container):
        with the(r.script).calls_the(r.decorated_run).with_the(r.command):
            it().turns_a(r.string_command).into_a(r.shell_command)
            it().calls(r.needs_tty_rule)
            it().turns_the(r.cwd).and_the(r.env).into(r.docker_exec_options)
            with it().calls(r.run_action).with_the(r.docker_exec_command):
                it().runs(r.docker).in_the(r.foreground)
            it().returns_the(r.command_result)


markdown_node = sunya.add_markdown_node(
    scenario, "A script runs commands in a container"
)

markdown_node.markdown = """
A script decorates `run` with `run_docker`, so that its commands run in a Docker
container that is already running, with `docker exec`. The undecorated `run` still
runs commands on the host.

```python
from jazzoo import get_config as get, run, run_docker

run_be = run_docker(get("/blogs_be/container"), workdir="/app")(run)

run_be("python manage.py migrate")
run_be(["pytest", "-x"], cwd="/app/src")
run("docker compose ps")
```

The decorated function only rewrites the command, and passes it to the function that
it decorates. Echo, confirmation, `capture`, `check` and the `CommandResult` are
therefore those of `run`, and they all show the full `docker exec` command.

### Steps

#### It decorates run

The script calls `run_docker` with the container, and optionally the `user`,
`workdir`, `env` and `shell` that hold for every command.</br>
`run_docker` returns a decorator, which the script applies to `run` (or to any
function with the signature of `run`).</br>

#### It runs a command in the container

The script calls the decorated function as it would call `run`.</br>
A string command becomes a list that runs it in the shell of the container (`bash -c`
by default).</br>
`needs_tty` decides whether to pass `--tty`: only when the output is not captured and
the script runs in a terminal.</br>
The `cwd` of the call is a directory in the container, and replaces the `workdir`; the
`env` of the call is merged over that of `run_docker`. Both become options of
`docker exec`.</br>
It calls `run` with the `docker exec` command, so the command runs in the foreground
in the container, and `run` returns the `CommandResult`.</br>

### Diagram

```mermaid
sequenceDiagram
    participant Script
    participant RunDocker as RunDocker (action)
    participant Run as Run (action)
    participant Docker

    Note over Script,RunDocker: Decorate run
    Script->>RunDocker: run_docker("blogs_be", workdir="/app")
    RunDocker-->>Script: decorator
    Script->>Script: run_be = decorator(run)

    Note over Script,Docker: Run a command in the container
    Script->>RunDocker: run_be(["pytest", "-x"], cwd="/app/src")
    RunDocker->>RunDocker: needs_tty(), build the docker exec command
    RunDocker->>Run: run(["docker", "exec", ..., "blogs_be", "pytest", "-x"])
    Run->>Docker: docker exec --interactive --tty --workdir /app/src blogs_be pytest -x
    Docker-->>Run: exit code
    Run-->>Script: CommandResult
```
"""
