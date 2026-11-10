[comment]: <> (This file is auto-generated. Do not edit directly.)

# s10_a_developer_registers_a_project

## A developer registers a project

The developer registers a project directory with a root jazzoo file as a zoo
environment, with a new venv or an existing one. When the venv is activated, then `zoo` will always
run `jaz` relative to the project directory. Moreover, `zoo-<name>` will run jaz from the
`<name>` project directory regardless of which venv is active.

### Steps

#### It registers the project

In the project directory, the developer runs `zoo env --init --create-venv --venv-path=/path/to/venv`.</br>
This command makes a linked install of jazzoo in the indicated venv.
The command prints which jazzoo it linked into the venv, because a developer
may not expect it.</br>

#### It runs a target from any directory

`zoo` takes the options of `jaz`, except `--file`: it always runs the root jazzoo
file of the env.</br>

#### It replaces the linked install with pip

The developer runs `pip install jazzoo==0.2.0`.</br>
pip uninstalls the linked install as an editable install, without touching the linked directory, and installs the
release into the venv.</br>

### Diagram

```mermaid
sequenceDiagram
    actor Developer
    participant Zoo as zoo (entrypoint)
    participant Init as InitZooEnv (action)
    participant Jaz as jaz (entrypoint)
    participant Pip as pip

    Note over Developer,Init: Register the project
    Developer->>Zoo: zoo env --init --create-venv --venv-path=...
    Zoo->>Init: init_zoo_env(name, root_dir, venv_dir)
    Init->>Init: create the venv, link jazzoo into it
    Init-->>Developer: print which jazzoo was linked
    Init->>Init: write env dir, link zoo-<name>

    Note over Developer,Jaz: Run a target from any directory
    Developer->>Zoo: zoo build
    Zoo->>Jaz: jaz build (in the project directory)

    Note over Developer,Pip: Replace the linked install with pip
    Developer->>Pip: pip install jazzoo==0.2.0
    Pip->>Pip: uninstall the linked install, install the release
```

