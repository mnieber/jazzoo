import json
import os
import sys
import typing as T
from pathlib import Path

from commands_tests.commands_test_env import (
    CTRL_C,
    CTRL_D,
    Context,
    TestEnv as CommandsTestEnv,
)

from jazzoo.commands import CommandResult, run, run_docker

__all__ = ["CTRL_C", "CTRL_D", "Context", "TestEnv"]

# A stand-in for the docker client. It records its arguments, and the values that the
# variables of the --env options have in its own environment. It then runs the
# command after the container name on the host, in the --workdir directory and with
# the --env variables. The container "stopped" is not running.
FAKE_DOCKER = """\
#!{python}
import json
import os
import subprocess
import sys

args = sys.argv[1:]
assert args[0] == "exec", args

workdir = None
env = {{}}
index = 1
while args[index].startswith("--"):
    option = args[index]
    if option in ("--interactive", "--tty"):
        index += 1
    elif option in ("--user", "--workdir", "--env"):
        value = args[index + 1]
        if option == "--workdir":
            workdir = value
        elif option == "--env":
            name, _, env_value = value.partition("=")
            env[name] = env_value
        index += 2
    else:
        sys.exit(f"fake docker: unknown option {{option}}")
container, command = args[index], args[index + 1 :]

with open({calls_file!r}, "a", encoding="utf-8") as calls:
    client_env = {{name: os.environ.get(name) for name in env}}
    calls.write(json.dumps({{"args": args, "client_env": client_env}}) + "\\n")

if container == "stopped":
    print(
        "Error response from daemon: container stopped is not running",
        file=sys.stderr,
    )
    sys.exit(1)

completed = subprocess.run(command, cwd=workdir, env={{**os.environ, **env}})
sys.exit(completed.returncode)
"""

DOCKER_CALLS_FILE = "docker_calls.jsonl"


class TestEnv(CommandsTestEnv):
    def __post_init__(self):
        super().__post_init__()
        self.decorated: T.Optional[T.Callable[..., CommandResult]] = None
        self.recorded_calls: T.List[T.Dict[str, T.Any]] = []
        self.recorder_results: T.List[CommandResult] = []
        self.logged_commands: T.List[T.Any] = []
        # The PATH of the test run, on which the fake docker finds bash
        self.host_path = os.environ["PATH"]

    def make_dir(self, name: str):
        Path(self.path(name)).mkdir(parents=True, exist_ok=True)

    def install_fake_docker(self):
        """Puts a fake docker executable first on the PATH (see FAKE_DOCKER)."""
        self.write_executable(
            "bin/docker",
            FAKE_DOCKER.format(
                python=sys.executable, calls_file=self.path(DOCKER_CALLS_FILE)
            ),
        )
        self.set_env("PATH", self.path("bin") + os.pathsep + self.host_path)

    def remove_docker_from_path(self):
        """Sets a PATH on which no docker exists."""
        self.make_dir("empty_bin")
        self.set_env("PATH", self.path("empty_bin"))

    def forget_docker_calls(self):
        if self.file_exists(DOCKER_CALLS_FILE):
            os.remove(self.path(DOCKER_CALLS_FILE))

    def decorate_run(self, *args: T.Any, **kwargs: T.Any):
        """Decorates run with run_docker(*args, **kwargs)."""
        self.decorated = run_docker(*args, **kwargs)(run)

    def decorate_recorder(self, *args: T.Any, **kwargs: T.Any):
        """Decorates a function with the signature of run, which records its calls
        instead of running them, with run_docker(*args, **kwargs)."""
        self.decorated = run_docker(*args, **kwargs)(self._record)

    def decorate_recorder_and_catch_error(self, *args: T.Any, **kwargs: T.Any):
        self.error = None
        try:
            self.decorate_recorder(*args, **kwargs)
        except Exception as error:
            self.error = error

    def call_decorated(self, command: T.Any, store_as: str = "result", **kwargs: T.Any):
        setattr(self, store_as, self.decorated(command, **kwargs))

    def call_decorated_and_catch_error(self, command: T.Any, **kwargs: T.Any):
        self.error = None
        try:
            self.decorated(command, **kwargs)
        except Exception as error:
            self.error = error

    def _record(
        self,
        command: T.Any,
        cwd: T.Optional[str] = None,
        env: T.Optional[T.Dict[str, str]] = None,
        capture: bool = False,
        check: bool = True,
        echo: bool = False,
    ) -> CommandResult:
        self.recorded_calls.append(
            dict(
                command=command,
                cwd=cwd,
                env=env,
                capture=capture,
                check=check,
                echo=echo,
            )
        )
        result = CommandResult(command=command, returncode=0)
        self.recorder_results.append(result)
        return result

    def _docker_call_records(self) -> T.List[T.Dict[str, T.Any]]:
        if not self.file_exists(DOCKER_CALLS_FILE):
            return []
        lines = self.read_file(DOCKER_CALLS_FILE).splitlines()
        return [json.loads(line) for line in lines]

    # Queries

    def docker_calls(self) -> T.List[T.List[str]]:
        """The arguments of the calls of the fake docker, without "docker"."""
        return [record["args"] for record in self._docker_call_records()]

    def docker_client_envs(self) -> T.List[T.Dict[str, T.Optional[str]]]:
        """Per call of the fake docker, the values that the variables of its --env
        options had in the environment of the docker client."""
        return [record["client_env"] for record in self._docker_call_records()]

    def last_recorded_command(self) -> T.Any:
        return self.recorded_calls[-1]["command"]
