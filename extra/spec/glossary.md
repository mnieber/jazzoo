# Glossary

### Config

The merged contents of the YAML config files that a jazzoo file names with `⚙️.load_config`. A later file overrides
an earlier one. A script reads a value from it with `get_config`, and a jazzoo file with `⚙️.get_config`. Values may
reference other config values (`${/a/b}`) and environment variables (`${NAME}`).

### Config layer

A config file that another config file includes with `/jazzoo/includes`. A layer is logically part of the file
that includes it: the layers are applied in their order of appearance, followed by the file itself, so that a file
wins over its layers.

### Linked install

The way `zoo env --init` installs jazzoo into a venv without copying it, as `pip install -e` does. An import hook in the site-packages of the venv finds the package in the linked directory, but a real install of jazzoo in the venv takes precedence.

### Project directory

The root project directory that is associated with a zoo environment.

### Root jazzoo file

The jazzoo file in the root of a project directory.

### Run function

The `run` function of jazzoo, which a script uses to run a command. A string command runs in bash, and a list
command runs directly. It returns a `CommandResult`, or raises `CommandFailedError` when the command fails. With
`jaz --confirm`, it asks the developer before each command.

### Venv

A shorthand for the Python virtual environment.

### Zoo environment

A project directory together with a venv, registered under a name in `~/.config/jazzoo/envs/<name>`. When the venv
is active, `zoo` runs `jaz` in the project directory, using the root jazzoo file.

### Zoo link

The link `~/.local/bin/zoo-<name>` to the `zoo` script of the venv of a zoo environment. It runs `jaz` in the
project directory of that zoo environment, regardless of which venv is active.

### zz

A shell function that runs `zoo env` with its arguments, and sources the line that it prints, so that it activates
a zoo environment in the current shell. `zoo env --install-fish` installs it for fish.
