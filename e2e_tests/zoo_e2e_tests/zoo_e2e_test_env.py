import base64
import glob
import hashlib
import json
import os
import typing as T
import zipfile

from zoo_tests.zoo_test_env import Context, TestEnv as ZooTestEnv

__all__ = ["Context", "TestEnv", "SRC_DIR", "COPY_DIR", "VENV", "WHEELS_DIR"]

# The source tree with the copy of jazzoo that the venv links (see
# copy_jazzoo_package). A wrong RECORD can only delete files of this copy, never
# files of the checkout that runs the tests.
SRC_DIR = "checkout/src"
COPY_DIR = f"{SRC_DIR}/jazzoo"

VENV = "projects/shop/.venv"

# The directory of the wheels that pip installs, with --no-index --find-links
WHEELS_DIR = "wheels"

# The console scripts of the link
SCRIPTS = ["zoo", "jaz", "jazzoo", "jaz-run"]


class TestEnv(ZooTestEnv):
    def __post_init__(self):
        super().__post_init__()
        self.remembered_copy: T.Optional[T.Dict[str, str]] = None

        # pip must not read the config of the developer, or ask questions
        self.set_env("PIP_CONFIG_FILE", os.devnull)
        self.set_env("PIP_DISABLE_PIP_VERSION_CHECK", "1")
        self.set_env("PIP_NO_INPUT", "1")

    def create_linked_venv(self, project: str = "shop"):
        """Copies jazzoo to SRC_DIR, and runs the zoo of the copy in projects/<project>:
        `zoo env --init --create-venv`, which creates a venv with pip."""
        self.copy_jazzoo_package(SRC_DIR)
        self.write_project(project)
        self.run_zoo_from_copy(
            SRC_DIR, "env", "--init", "--create-venv", cwd=f"projects/{project}"
        )

    def build_jazzoo_wheel(self, version: str):
        """Writes the wheel of jazzoo <version> to WHEELS_DIR. Its package only has
        MARKER = "wheel <version>"."""
        dist_info = f"jazzoo-{version}.dist-info"
        files = {
            "jazzoo/__init__.py": f'MARKER = "wheel {version}"\n',
            f"{dist_info}/METADATA": (
                f"Metadata-Version: 2.1\nName: jazzoo\nVersion: {version}\n"
            ),
            f"{dist_info}/WHEEL": (
                "Wheel-Version: 1.0\nGenerator: zoo-e2e-tests\n"
                "Root-Is-Purelib: true\nTag: py3-none-any\n"
            ),
        }
        record = "".join(
            f"{name},{_record_hash(text)},{len(text.encode())}\n"
            for name, text in files.items()
        )
        files[f"{dist_info}/RECORD"] = record + f"{dist_info}/RECORD,,\n"

        os.makedirs(self.path(WHEELS_DIR), exist_ok=True)
        wheel = self.path(f"{WHEELS_DIR}/jazzoo-{version}-py3-none-any.whl")
        with zipfile.ZipFile(wheel, "w") as f:
            for name, text in files.items():
                f.writestr(name, text)

    def run_pip(self, venv: str, *args: str):
        """Runs the pip of the venv, and stores the result in completed."""
        self.run_program(self.path(f"{venv}/bin/python"), "-m", "pip", *args)

    def remember_copy(self):
        self.remembered_copy = self.copy_snapshot()

    def _installer(self, dist_info: str) -> T.Optional[str]:
        path = os.path.join(dist_info, "INSTALLER")
        return self.read_file(path).strip() if os.path.exists(path) else None

    # Queries

    def copy_snapshot(self) -> T.Dict[str, str]:
        """The hash of every file in COPY_DIR. Python writes __pycache__ when it
        imports the copy, so these are left out."""
        snapshot = {}
        for root, dirs, files in os.walk(self.path(COPY_DIR)):
            dirs[:] = [name for name in dirs if name != "__pycache__"]
            for name in files:
                path = os.path.join(root, name)
                with open(path, "rb") as f:
                    snapshot[path] = hashlib.sha256(f.read()).hexdigest()
        return snapshot

    def listed_package(self, name: str) -> T.Dict[str, T.Any]:
        """The entry of a package in the output of `pip list --format=json`."""
        (package,) = [p for p in json.loads(self.completed.stdout) if p["name"] == name]
        return package

    def link_files(self, venv: str) -> T.List[str]:
        """The files of the link that exist in the venv: the _jazzoo_link files (also
        the compiled one), the dist-info that zoo installed, and the console
        scripts."""
        site_packages = self.site_packages(venv)
        paths = glob.glob(os.path.join(site_packages, "_jazzoo_link*"))
        paths += glob.glob(os.path.join(site_packages, "__pycache__", "_jazzoo_link*"))
        paths += [
            path
            for path in glob.glob(os.path.join(site_packages, "jazzoo-*.dist-info"))
            if self._installer(path) == "zoo"
        ]
        paths += [
            self.path(f"{venv}/bin/{name}")
            for name in SCRIPTS
            if self.exists(self.path(f"{venv}/bin/{name}"))
        ]
        return sorted(paths)


def _record_hash(text: str) -> str:
    digest = hashlib.sha256(text.encode()).digest()
    return "sha256=" + base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
