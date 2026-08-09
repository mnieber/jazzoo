from pathlib import Path

from setuptools import setup


def create_placeholder():
    this_directory = Path(__file__).parent
    pkg_directory = this_directory / "src" / "jazzoo"

    if not pkg_directory.exists():
        pkg_directory.mkdir(parents=True)
        with open(pkg_directory / "__init__.py", "w") as f:
            f.write("# Placeholder for package")


if __name__ == "__main__":
    create_placeholder()
    setup()
