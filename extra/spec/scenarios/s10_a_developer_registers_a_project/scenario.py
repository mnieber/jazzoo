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
    r.link_jazzoo_action = c.Zoo.Actions.LinkJazzoo
    r.get_jazzoo_version_rule = c.Zoo.Rules.GetJazzooVersion
    r.activate_zoo_env_action = c.Zoo.Actions.ActivateZooEnv
    r.run_in_zoo_env_action = c.Zoo.Actions.RunInZooEnv
    r.find_zoo_env_of_venv_rule = c.Zoo.Rules.FindZooEnvOfVenv

    with goal().register_the(r.project_dir).as_a(r.zoo_env).with_a(r.venv):
        with the(r.developer).runs(r.zoo_entrypoint).with_the(r.init_options):
            with it().calls(r.init_zoo_env_action):
                it().checks_the(r.name).and_the(r.root_jazzoo_file)
                with it().calls(r.create_venv_action):
                    it().creates_the(r.venv).at_the(r.venv_path)
                    it().calls(r.link_jazzoo_action)
                with (
                    it().calls(r.link_jazzoo_action).if_the(r.venv).has_no(r.zoo_script)
                ):
                    it().checks_the(r.python_version).of_the(r.venv)
                    with it().makes_a(r.linked_install).of_the(r.jazzoo_package):
                        it().writes_the(r.import_hook).into_the(r.venv)
                        it().calls(r.get_jazzoo_version_rule)
                        it().writes_the(r.package_metadata).into_the(r.venv)
                    it().writes_the(r.console_scripts).into_the(r.venv)
                it().prints_that_it_linked(r.jazzoo_package).into_the(r.venv)
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
    participant Zoo as zoo (entrypoint)
    participant Init as InitZooEnv (action)
    participant Jaz as jaz (entrypoint)

    Note over Developer,Init: Register the project
    Developer->>Zoo: zoo env --init --create-venv --venv-path=...
    Zoo->>Init: init_zoo_env(name, root_dir, venv_dir)
    Init->>Init: create the venv, link jazzoo into it
    Init-->>Developer: print which jazzoo was linked
    Init->>Init: write env dir, link zoo-<name>

    Note over Developer,Jaz: Run a target from any directory
    Developer->>Zoo: zoo build
    Zoo->>Jaz: jaz build (in the project directory)
```
"""
