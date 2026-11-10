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
This command will link the existing jazzoo package into the indicated venv.
The command prints which jazzoo it linked into the venv, because a developer
may not expect it.</br>

#### It runs a target from any directory

`zoo` takes the options of `jaz`, except `--file`: it always runs the root jazzoo
file of the env.</br>

### Diagram

```mermaid
sequenceDiagram
    actor Developer
    participant Shell
    participant Zoo as zoo (entrypoint)
    participant Init as InitZooEnv (action)
    participant CV as CreateVenv (action)
    participant Link as LinkJazzoo (action)
    participant Act as ActivateZooEnv (action)
    participant Run as RunInZooEnv (action)
    participant Jaz as jaz (entrypoint)

    Note over Developer,Act: Register the project
    Developer->>Zoo: zoo env --init --create-venv
    Zoo->>Init: init_zoo_env(name, root_dir, venv_dir)
    Init->>Init: check name and root jazzoo file
    alt --create-venv
        Init->>CV: create_venv(venv_dir)
        CV->>CV: python -m venv
        CV->>Link: link_jazzoo(venv_dir)
    else existing venv without bin/zoo
        Init->>Link: link_jazzoo(venv_dir)
    end
    Link->>Link: check python version, write linked install and scripts
    Init->>Init: write env dir, link zoo-<name>
    Zoo->>Act: activate_zoo_env(name)
    Act->>Act: record latest env
    Act-->>Zoo: source line
    Zoo-->>Shell: source .../envs/<name>/activate.<shell>
    Shell->>Shell: activate the venv

    Note over Developer,Jaz: Run a target from any directory
    Developer->>Zoo: zoo build
    Zoo->>Run: run_in_zoo_env(["build"])
    Run->>Run: find the env of sys.prefix
    Run->>Run: record invocation dir, cd to root dir
    Run->>Jaz: run(["build"], invocation_dir)
```

