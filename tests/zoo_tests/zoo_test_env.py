import json
import os
import shutil
import stat
import subprocess
import sys
import typing as T
from pathlib import Path

from jazzoo_test_env import Context, TestEnv as JazzooTestEnv

from jazzoo.runtime.entrypoints.zoo import main, run as run_zoo

__all__ = ["Context", "TestEnv", "SHOP_JAZZOO"]

# The jazzoo file of most projects. `where` shows the directories of the run, and is
# silent about its commands, so that the output only has the values.
SHOP_JAZZOO = """
where():
    @echo "cwd=$(pwd)"
    @echo "invocation_dir=⚙️.invocation_dir"

greet(name="you"):
    @echo "hello 🐆.name"
"""


class TestEnv(JazzooTestEnv):
    def __post_init__(self):
        self.printed_err: T.Optional[str] = None
        self.completed: T.Optional[subprocess.CompletedProcess] = None
        self.system_exit: T.Optional[SystemExit] = None

        # The registry and the zoo-<name> links go below tmp_path, never into the
        # home directory of the developer.
        os.makedirs(self.path("home/.local/bin"), exist_ok=True)
        self.set_env("HOME", self.path("home"))
        self.unset_env("XDG_CONFIG_HOME")
        self.set_env("SHELL", "/bin/bash")
        self.unset_env("JAZZOO_ENV")
        self.unset_env("VIRTUAL_ENV")
        self.set_env(
            "PATH", self.path("home/.local/bin") + os.pathsep + os.environ["PATH"]
        )

    def write_project(self, name: str, jazzoo_text: str = SHOP_JAZZOO):
        """Writes the project directory projects/<name> with a jazzoo file."""
        self.write_file(f"projects/{name}/jazzoo", jazzoo_text)

    def make_fake_venv(self, path: str, with_zoo: bool = True):
        """Writes a directory that looks like a venv to zoo: a pyvenv.cfg, the
        activate scripts and (optionally) a bin/zoo. Nothing in it can run Python."""
        self.write_file(f"{path}/pyvenv.cfg", "home = /usr/bin\n")
        self.write_file(f"{path}/bin/activate", "export VIRTUAL_ENV=fake\n")
        self.write_file(f"{path}/bin/activate.fish", "set -gx VIRTUAL_ENV fake\n")
        if with_zoo:
            self.write_executable(f"{path}/bin/zoo", "#!/bin/sh\nexit 0\n")

    def add_project(self, name: str, jazzoo_text: str = SHOP_JAZZOO):
        """Writes projects/<name> with a jazzoo file and a fake venv in .venv."""
        self.write_project(name, jazzoo_text)
        self.make_fake_venv(f"projects/{name}/.venv")

    def init_env(
        self,
        name: T.Optional[str],
        project: T.Optional[str] = None,
        venv: T.Optional[str] = None,
    ):
        """Changes to the project directory, and registers it with
        `zoo env --init <name> --use-venv <venv>`."""
        project = project or f"projects/{name}"
        venv = venv or f"{project}/.venv"
        self.change_dir(project)
        name_args = [name] if name else []
        self.run_zoo("env", "--init", *name_args, "--use-venv", self.path(venv))

    def use_zoo_of(self, venv: str):
        """Makes the in-process zoo run in the given venv, as if it were the zoo of
        <venv>/bin."""
        self.context.monkeypatch.setattr(sys, "prefix", self.path(venv))

    def run_zoo(self, *args: str):
        """Runs zoo in-process, and stores the exit code and what was printed."""
        self.context.capsys.readouterr()
        try:
            self.exit_code = run_zoo(list(args))
        finally:
            self.output, self.printed_err = self.context.capsys.readouterr()

    def run_zoo_and_catch_error(self, *args: str):
        self.error = None
        try:
            self.run_zoo(*args)
        except Exception as error:
            self.error = error

    def run_zoo_and_catch_exit(self, *args: str):
        self.system_exit = None
        try:
            self.run_zoo(*args)
        except SystemExit as system_exit:
            self.system_exit = system_exit

    def run_zoo_cli(self, *args: str):
        """Runs zoo as the console script does: errors are printed, not raised."""
        self.context.capsys.readouterr()
        self.exit_code = main(list(args))
        self.output, self.printed_err = self.context.capsys.readouterr()

    def run_program(self, program: str, *args: str, cwd: str = ""):
        """Runs a program (e.g. a script in a real venv) in a subprocess, in the
        directory cwd below tmp_path."""
        self.completed = subprocess.run(
            [program, *args],
            cwd=self.path(cwd),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def write_executable(self, name: str, text: str):
        self.write_file(name, text)
        path = self.path(name)
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)

    def make_dir(self, name: str):
        os.makedirs(self.path(name), exist_ok=True)

    def remove_dir(self, name: str):
        shutil.rmtree(self.path(name))

    # Queries

    def config_dir(self) -> str:
        return self.path("home/.config/jazzoo")

    def env_dir(self, name: str) -> str:
        return os.path.join(self.config_dir(), "envs", name)

    def zoo_link(self, name: str) -> str:
        return self.path(f"home/.local/bin/zoo-{name}")

    def source_line(self, name: str, shell: str = "bash") -> str:
        return f"source {self.env_dir(name)}/activate.{shell}\n"

    def read_link(self, path: str) -> str:
        return os.readlink(path)

    def is_link(self, path: str) -> bool:
        return os.path.islink(path)

    def is_dir(self, path: str) -> bool:
        return os.path.isdir(path)

    def exists(self, path: str) -> bool:
        return os.path.lexists(path)

    def read_file(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")

    def read_lines(self, path: str) -> T.List[str]:
        return [line.strip() for line in self.read_file(path).splitlines()]

    def read_recent(self) -> T.Optional[T.Dict[str, T.Any]]:
        path = os.path.join(self.config_dir(), "recent.json")
        if not os.path.exists(path):
            return None
        return json.loads(self.read_file(path))
