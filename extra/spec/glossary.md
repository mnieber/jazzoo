# Glossary

### Linked install

The way `zoo env --init` installs jazzoo into a venv without copying it, as `pip install -e` does. An import hook in the site-packages of the venv finds the package in the linked directory, but a real install of jazzoo in the venv takes precedence.

### Project directory

The root project directory that is associated with a zoo environment.

### Root jazzoo file

The jazzoo file in the root of a project directory.

### Venv

A shorthand for the Python virtual environment.

### Zoo environment

A project directory together with a venv, registered under a name in `~/.config/jazzoo/envs/<name>`. When the venv
is active, `zoo` runs `jaz` in the project directory, using the root jazzoo file.

### Zoo link

The link `~/.local/bin/zoo-<name>` to the `zoo` script of the venv of a zoo environment. It runs `jaz` in the
project directory of that zoo environment, regardless of which venv is active.
