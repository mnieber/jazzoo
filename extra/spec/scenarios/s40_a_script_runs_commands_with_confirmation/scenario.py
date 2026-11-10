import sunya
from sunya import C as c
from sunya import R as r
from sunya import goal, it, the

scenario = sunya.add_scenario("s40_a_script_runs_commands_with_confirmation")


def run_scenario():
    r.developer = c.External.Actors.Developer
    r.script = c.External.Actors.Script
    r.jaz_entrypoint = c.Runtime.Entrypoints.Jazzoo
    r.has_terminal_rule = c.Commands.Rules.HasTerminal
    r.run_action = c.Commands.Actions.Run
    r.find_executable_rule = c.Commands.Rules.FindExecutable
    r.is_confirm_on_rule = c.Commands.Rules.IsConfirmOn
    r.confirm_command_action = c.Commands.Actions.ConfirmCommand
    r.command_result = c.Commands.Models.CommandResult
    r.command_failed_error = c.Commands.Errors.CommandFailedError
    r.command_aborted_error = c.Commands.Errors.CommandAbortedError
    r.shell_script = c.External.Actors.ShellScript
    r.jaz_run_entrypoint = c.Commands.Entrypoints.JazRun
    r.usage_error = c.Commands.Errors.UsageError

    with goal().switch_on(r.confirmation).for_a(r.target):
        with the(r.developer).runs(r.jaz_entrypoint).with_the(r.confirm_option):
            it().calls(r.has_terminal_rule)
            it().sets(r.jazzoo_confirm).to(r.one)
            it().runs_the(r.script).of_the(r.target)

    with goal().run_a(r.command).from_the(r.script):
        with the(r.script).calls(r.run_action).with_the(r.command):
            it().checks_the(r.command).and_the(r.cwd)
            it().calls(r.find_executable_rule).for_a(r.list_command)
            with it().calls(r.is_confirm_on_rule):
                with it().calls(r.confirm_command_action):
                    it().prompts_the(r.developer).on_the(r.terminal)
                    it().raises(r.command_aborted_error).if_the(r.developer).aborts()
                it().returns_a(r.skipped_result).if_the(r.developer).skips()
            it().runs_the(r.command).in_the(r.foreground)
            it().raises(r.command_failed_error).if_the(r.command).fails()
            it().returns_the(r.command_result)

    with goal().run_a(r.command).from_a(r.shell_script):
        with the(r.shell_script).runs(r.jaz_run_entrypoint).with_the(r.command):
            it().parses_its_own(r.options).up_to_the(r.command)
            it().raises(r.usage_error).if_the(r.arguments).are_invalid()
            it().turns_the(r.arguments).into_a(r.list_command).or_a(r.string_command)
            it().calls(r.run_action).with_the(r.command)
            it().translates_the(r.outcome).into_an(r.exit_code)


markdown_node = sunya.add_markdown_node(
    scenario, "A script runs commands with confirmation"
)

markdown_node.markdown = """
A script (that is triggered by jazzoo) can use the run function to run commands. With
`jaz --confirm`, the developer is asked before each of these commands, and can run it,
skip it or abort. The shell lines and shebang blocks of the jazzoo file itself are never
confirmed.

### Steps

#### It switches on confirmation

The developer runs `jaz --confirm <target>`.</br>
`jaz` calls `has_terminal`, and fails when there is no terminal to ask on. It sets
`JAZZOO_CONFIRM=1` in its environment, which every script of the run (and of a
nested `jaz`) inherits, and runs the target.</br>

#### It runs a command

The script calls `run` with a command.</br>
When `is_confirm_on` finds `JAZZOO_CONFIRM=1`, `confirm_command` shows the command
with its directory on the terminal, and reads the answer. On `y`, `run` runs the
command; on `n`, it skips the command and returns a `CommandResult` with `skipped=True`;
on `q`, `confirm_command` raises `CommandAbortedError`, so `jaz` stops the run.</br>

#### It runs a command from a shell script

A shell script, or a shell line of a jazzoo file, runs `jaz-run <executable> [<argument> ...]`,
or `jaz-run -c "<command>"` for a command that runs in bash.</br>
`jaz-run` calls `run` with the command, so the command is confirmed in the same way, and exits
with the exit code of the command (`0` when the developer skipped it, `130` when they
aborted).</br>

### Diagram

```mermaid
sequenceDiagram
    actor Developer
    participant Jaz as jaz (entrypoint)
    participant Script
    participant Run as Run (action)
    participant Confirm as ConfirmCommand (action)
    participant JazRun as jaz-run (entrypoint)

    Note over Developer,Script: Switch on confirmation
    Developer->>Jaz: jaz --confirm deploy
    Jaz->>Jaz: has_terminal(), set JAZZOO_CONFIRM=1
    Jaz->>Script: run the block of deploy

    Note over Developer,Confirm: Run a command
    Script->>Run: run("docker compose build")
    Run->>Run: check the command and cwd, find the executable
    Run->>Confirm: confirm_command(command, cwd)
    Confirm->>Developer: (/home/jane/blogs) docker compose build<br/>confirm? [Y/n/q]
    Developer-->>Confirm: y
    Confirm-->>Run: True
    Run->>Run: run the command in the foreground
    Run-->>Script: CommandResult

    Note over Script,JazRun: Run a command from a shell script
    Script->>JazRun: jaz-run -c "docker compose logs | grep error"
    JazRun->>Run: run(command)
    Run-->>JazRun: CommandResult
    JazRun-->>Script: exit code
```
"""
