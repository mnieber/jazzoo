import typing as T

from ..models.command_result import CommandResult
from ..rules.needs_tty import needs_tty

Command = T.Union[str, T.List[str]]
RunFunction = T.Callable[..., CommandResult]


def run_docker(
    container: str,
    user: T.Optional[str] = None,
    workdir: T.Optional[str] = None,
    env: T.Optional[T.Dict[str, str]] = None,
    shell: str = "bash",
) -> T.Callable[[RunFunction], RunFunction]:
    if not container or not container.strip():
        raise ValueError("the container is empty")

    container_env = dict(env or {})

    def decorator(run: RunFunction) -> RunFunction:
        def run_in_container(
            command: Command,
            cwd: T.Optional[str] = None,
            env: T.Optional[T.Dict[str, str]] = None,
            capture: bool = False,
            check: bool = True,
            echo: bool = False,
        ) -> CommandResult:
            # Check the command before the docker command hides it
            if isinstance(command, str):
                if not command.strip():
                    raise ValueError("the command is empty")
                command_args = [shell, "-c", command]
            elif not command:
                raise ValueError("the command is empty")
            else:
                command_args = list(command)

            # The options come in a fixed order
            docker_command = ["docker", "exec", "--interactive"]
            if needs_tty(capture):
                docker_command.append("--tty")
            if user:
                docker_command += ["--user", user]
            # A cwd only replaces the workdir for this call
            call_workdir = cwd or workdir
            if call_workdir:
                docker_command += ["--workdir", call_workdir]
            for name, value in {**container_env, **(env or {})}.items():
                docker_command += ["--env", f"{name}={value}"]
            docker_command += [container, *command_args]

            # The cwd and env belong to the container, not to the docker client
            return run(
                docker_command,
                cwd=None,
                env=None,
                capture=capture,
                check=check,
                echo=echo,
            )

        return run_in_container

    return decorator
