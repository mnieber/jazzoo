import sunya
from sunya import C as c
from sunya import R as r
from sunya import goal, it, the

scenario = sunya.add_scenario("s10_a_developer_registers_a_project")


def run_scenario():
    r.developer = c.External.Actors.Developer
    r.shell = c.External.Actors.Shell
    r.zoo_entrypoint = c.Runtime.Entrypoints.Zoo
    r.jaz_entrypoint = c.Runtime.Entrypoints.Jazzoo
    r.init_zoo_env_action = c.Zoo.Actions.InitZooEnv
    r.create_venv_action = c.Zoo.Actions.CreateVenv
    r.activate_zoo_env_action = c.Zoo.Actions.ActivateZooEnv
    r.run_in_zoo_env_action = c.Zoo.Actions.RunInZooEnv
    r.find_zoo_env_of_venv_rule = c.Zoo.Rules.FindZooEnvOfVenv

    with goal().register_the(r.project_dir).as_a(r.zoo_env).with_a(r.venv):
        with the(r.developer).runs(r.zoo_entrypoint).with_the(r.init_options):
            with it().calls(r.init_zoo_env_action):
                it().checks_the(r.name).and_the(r.root_jazzoo_file)
                with it().calls(r.create_venv_action):
                    it().creates_the(r.venv).in_the(r.project_dir)
                    it().links_the(r.jazzoo_package).into_the(r.venv)
                    it().writes_the(r.console_scripts).into_the(r.venv)
                it().writes_the(r.env_dir).to_the(r.registry)
                it().links(r.zoo_link).to_the(r.zoo_script).of_the(r.venv)
            with it().calls(r.activate_zoo_env_action):
                it().records_the(r.zoo_env).as_the(r.latest_env)
                it().returns_the(r.source_line)
            it().prints_the(r.source_line)
        the(r.shell).sources_the(r.activate_script).of_the(r.zoo_env)

    with goal().run_a(r.target).of_the(r.zoo_env).from_any_directory():
        with the(r.developer).runs(r.zoo_script).with_the(r.jaz_arguments):
            with it().calls(r.run_in_zoo_env_action):
                it().calls(r.find_zoo_env_of_venv_rule).for_its_own(r.venv)
                it().records_the(r.invocation_dir)
                it().changes_to_the(r.root_dir).of_the(r.zoo_env)
                it().calls(r.jaz_entrypoint).with_the(r.jaz_arguments)


markdown_node = sunya.add_markdown_node(scenario, "A developer registers a project")

markdown_node.markdown = """
The developer registers a project directory with a root jazzoo file as a zoo
environment, with a new venv. From then on, the `zoo` of that venv runs the targets
of the project from any directory, and so does the link `zoo-<name>` in
`~/.local/bin`, whether or not the env is active.

### Steps

#### It registers the project

In the project directory, the developer runs
`eval "$(zoo env --init --create-venv)"`.</br>
`init_zoo_env` checks the name (by default the name of the directory) and that the
directory has a root jazzoo file.</br>
`create_venv` creates `.venv` in the project directory, links the jazzoo package
that runs `zoo` into its site-packages, and writes the `zoo`, `jaz`, `jazzoo` and
`jaz-run` scripts into its `bin` directory.</br>
`init_zoo_env` writes the env directory in `~/.config/jazzoo/envs/<name>`: links to the
root directory and the venv, and an activate script per shell. It also links
`~/.local/bin/zoo-<name>` to the `zoo` of the venv.</br>
`activate_zoo_env` records the env as the latest one, and returns the line that sources
its activate script. `zoo` prints this line, and the shell sources it, which activates
the venv.</br>

#### It runs a target from any directory

The developer runs `zoo <target>` in any directory. With the venv active, this is the
`zoo` of the venv.</br>
`run_in_zoo_env` finds the env whose venv is the venv that `zoo` runs in
(`sys.prefix`).</br>
It records the current directory as `⚙️.invocation_dir`, changes to the root
directory of the env, and runs `jaz` in-process with the same arguments.</br>

### Diagram

```mermaid
sequenceDiagram
    actor Developer
    participant Shell
    participant Zoo as zoo (entrypoint)
    participant Init as InitZooEnv (action)
    participant CV as CreateVenv (action)
    participant Act as ActivateZooEnv (action)
    participant Run as RunInZooEnv (action)
    participant Jaz as jaz (entrypoint)

    Note over Developer,Act: Register the project
    Developer->>Zoo: zoo env --init --create-venv
    Zoo->>Init: init_zoo_env(name, root_dir, venv_dir)
    Init->>Init: check name and root jazzoo file
    Init->>CV: create_venv(venv_dir)
    CV->>CV: python -m venv, link jazzoo, write scripts
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
"""
