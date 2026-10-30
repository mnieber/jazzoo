import glob
import json
import os
import shutil
import stat
import subprocess
import sys
import textwrap
import typing as T
from pathlib import Path

import pytest
from jazzoo_test_env import Context, TestEnv as JazzooTestEnv

import jazzoo
from jazzoo.runtime.entrypoints.zoo import main, run as run_zoo

__all__ = [
    "Context",
    "TestEnv",
    "SHOP_JAZZOO",
    "FISH_FILES",
    "FISH_MANAGED_LINE",
    "LINKED_DIR",
    "ZOO_MAIN",
]

# The files that `zoo env --install-fish` writes, relative to the fish config dir
FISH_FILES = [
    "functions/zz.fish",
    "completions/zz.fish",
    "completions/jaz.fish",
    "completions/jazzoo.fish",
    "completions/zoo.fish",
    "conf.d/zoo.fish",
]

# The first line of each of these files
FISH_MANAGED_LINE = "# managed by zoo env --install-fish"

# The PATH of a fish that a test runs: the zoo-<name> links, and the system
# directories, but never a zoo or venv of the developer.
FISH_PATH_DIRS = ["/usr/local/bin", "/usr/bin", "/bin"]

# Runs the zoo of the jazzoo package that python finds
ZOO_MAIN = (
    "import sys; from jazzoo.runtime.entrypoints.zoo import main; sys.exit(main())"
)

# The directory of the jazzoo package that runs the tests
LINKED_DIR = os.path.dirname(jazzoo.__file__)

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

    def make_runnable_fake_venv(self, path: str):
        """Writes a fake venv whose bin/zoo, bin/jaz and bin/jazzoo run the jazzoo of
        the test run, and whose activate.fish sets VIRTUAL_ENV and puts bin on the
        PATH, as a real venv does. A fish in a subprocess can use it."""
        venv = self.path(path)
        self.make_fake_venv(path, with_zoo=False)
        self.write_file(
            f"{path}/bin/activate.fish",
            f"set -gx VIRTUAL_ENV {venv}\nset -gx PATH {venv}/bin $PATH\n",
        )
        self.write_executable(
            f"{path}/bin/zoo",
            f"#!{sys.executable}\n"
            "import sys\n"
            "from jazzoo.runtime.entrypoints.zoo import main\n"
            "sys.exit(main())\n",
        )
        for name in ["jaz", "jazzoo"]:
            self.write_executable(
                f"{path}/bin/{name}",
                f"#!{sys.executable}\n"
                "import sys\n"
                "from jazzoo.runtime.entrypoints.jazzoo import main\n"
                "sys.exit(main())\n",
            )

    def add_project(
        self, name: str, jazzoo_text: str = SHOP_JAZZOO, runnable_zoo: bool = False
    ):
        """Writes projects/<name> with a jazzoo file and a fake venv in .venv. With
        runnable_zoo, the zoo of the venv runs (see make_runnable_fake_venv)."""
        self.write_project(name, jazzoo_text)
        if runnable_zoo:
            self.make_runnable_fake_venv(f"projects/{name}/.venv")
        else:
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

    def complete_zoo(self, *words: str):
        """Runs `zoo --complete -- <words>` as fish does: through the console
        script, so that an error would be printed, not raised. The last word is the
        one that is being completed."""
        self.run_zoo_cli("--complete", "--", *words)

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

    def run_fish(self, script: str, interactive: bool = False):
        """Runs script in a new fish, in a subprocess, and stores the result in
        completed. Fish reads its config below tmp_path (HOME is set there), and gets
        a PATH without any zoo of the developer. Skips the test when fish is not
        installed."""
        fish = shutil.which("fish")
        if fish is None:
            pytest.skip("fish is not installed")
        environ = dict(os.environ)
        environ["PATH"] = os.pathsep.join(
            [self.path("home/.local/bin"), os.path.dirname(fish), *FISH_PATH_DIRS]
        )
        options = ["-i"] if interactive else []
        self.completed = subprocess.run(
            [fish, *options, "-c", script],
            cwd=self.path(""),
            env=environ,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def run_python_in_venv(self, venv: str, code: str):
        """Runs code with the python of the venv, in a subprocess, and stores the
        result in completed. PYTHONPATH is unset, so that only the venv decides what
        python imports."""
        environ = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        self.completed = subprocess.run(
            [self.path(f"{venv}/bin/python"), "-c", textwrap.dedent(code)],
            cwd=self.path(""),
            env=environ,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def copy_jazzoo_package(self, src_dir: str):
        """Copies the jazzoo package that runs the tests to <src_dir>/jazzoo: a
        source tree without package metadata."""
        shutil.copytree(
            LINKED_DIR,
            self.path(f"{src_dir}/jazzoo"),
            ignore=shutil.ignore_patterns("__pycache__"),
        )

    def run_zoo_from_copy(self, src_dir: str, *args: str, cwd: str = ""):
        """Runs the zoo of the jazzoo package in <src_dir> (see copy_jazzoo_package)
        in a subprocess, and stores the result in completed. The package metadata
        of the jazzoo that runs the tests is visible there too."""
        environ = dict(os.environ, PYTHONPATH=self.path(src_dir))
        self.completed = subprocess.run(
            [sys.executable, "-c", ZOO_MAIN, *args],
            cwd=self.path(cwd),
            env=environ,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=180,
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

    def fish_dir(self) -> str:
        return self.path("home/.config/fish")

    def fish_file(self, name: str) -> str:
        return os.path.join(self.fish_dir(), name)

    def candidates(self) -> T.List[str]:
        """The candidates that zoo --complete printed, without their descriptions,
        in the printed order."""
        return [line.split("\t")[0] for line in (self.output or "").splitlines()]

    def fish_lines(self) -> T.List[str]:
        """The lines of the stdout of the last fish run."""
        return self.completed.stdout.splitlines()

    def site_packages(self, venv: str) -> str:
        (path,) = glob.glob(self.path(f"{venv}/lib/python*/site-packages"))
        return path

    def dist_info_names(self, venv: str) -> T.List[str]:
        """The names of the dist-info directories of jazzoo in the venv."""
        return sorted(
            os.path.basename(path)
            for path in glob.glob(
                os.path.join(self.site_packages(venv), "jazzoo-*.dist-info")
            )
        )

    def dist_info_file(self, venv: str, name: str) -> str:
        """The path of a file in the (only) dist-info directory of jazzoo."""
        (dist_info,) = self.dist_info_names(venv)
        return os.path.join(self.site_packages(venv), dist_info, name)

    def read_direct_url(self, venv: str) -> T.Dict[str, T.Any]:
        return json.loads(self.read_file(self.dist_info_file(venv, "direct_url.json")))

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
