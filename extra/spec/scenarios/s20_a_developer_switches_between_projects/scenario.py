import sunya
from sunya import C as c
from sunya import R as r
from sunya import goal, it, the

scenario = sunya.add_scenario("s20_a_developer_switches_between_projects")


def run_scenario():
    r.developer = c.External.Actors.Developer
    r.shell = c.External.Actors.Shell
    r.zoo_entrypoint = c.Runtime.Entrypoints.Zoo
    r.activate_zoo_env_action = c.Zoo.Actions.ActivateZooEnv
    r.write_latest_zoo_env_scripts_action = c.Zoo.Actions.WriteLatestZooEnvScripts
    r.get_recent_zoo_env_rule = c.Zoo.Rules.GetRecentZooEnv
    r.install_fish_files_action = c.Zoo.Actions.InstallFishFiles

    with goal().switch_to(r.other_zoo_env):
        with the(r.developer).runs(r.zoo_entrypoint).with_the(r.env_name):
            with it().calls(r.activate_zoo_env_action):
                it().records_the(r.latest_env).as_the(r.previous_env)
                it().records_the(r.other_zoo_env).as_the(r.latest_env)
                it().calls(r.write_latest_zoo_env_scripts_action)
                it().returns_the(r.source_line)
            it().prints_the(r.source_line)
        the(r.shell).sources_the(r.activate_script).of_the(r.other_zoo_env)

    with goal().switch_back_to(r.previous_env):
        with the(r.developer).runs(r.zoo_entrypoint).with_a(r.dash):
            it().calls(r.get_recent_zoo_env_rule).for_the(r.previous_env)
            it().calls(r.activate_zoo_env_action).with_the(r.previous_env)
            it().prints_the(r.source_line)

    with goal().start_a(r.new_terminal).in_the(r.latest_env):
        the(r.shell).sources_the(r.latest_env_script).from_its(r.startup_file)
        it().sources_the(r.activate_script).of_the(r.latest_env)

    with goal().switch_to(r.other_zoo_env).with_the(r.zz_function):
        with the(r.developer).runs(r.zoo_entrypoint).with_the(r.install_fish_option):
            it().calls(r.install_fish_files_action)
        with the(r.developer).runs_the(r.zz_function).with_the(r.env_name):
            it().runs(r.zoo_entrypoint).with_the(r.env_name)
            it().sources_the(r.source_line)


markdown_node = sunya.add_markdown_node(
    scenario, "A developer switches between projects"
)

markdown_node.markdown = """
The developer works on several registered projects, and switches between them in the
same terminal. Like `cd -`, `zoo env -` goes back to the previous env. A new terminal
starts in the env that was activated last.

### Steps

#### It switches to another project

The developer runs `zoo env blog | source`.</br>
`activate_zoo_env` tracks the latest use zoo env (so that we can activate it when opening a new shell).</br>

#### It switches back

The developer runs `zoo env - | source`.</br>
`get_recent_zoo_env` returns the previous env, which `activate_zoo_env` activates as
before. Running `zoo env -` again goes back and forth between the two envs.</br>

#### It starts a new terminal in the latest project

The startup file of the shell sources `~/.config/jazzoo/latest.<shell>`.</br>
This script sources the activate script of the latest env, so the new terminal starts
with its venv active. No Python runs, and no `zoo` is needed on the `PATH`.</br>

#### It switches with zz

The developer runs `zoo env --install-fish` once, which installs the `zz` function and the
completions of `zz`, `jaz` and `zoo` in the fish config directory.</br>
`zz blog` runs `zoo env blog` and sources the line that it prints, so `zz -` and `zz --list`
work as their `zoo env` counterparts. Pressing tab after `zz` completes the names of the envs.</br>

### Diagram

```mermaid
sequenceDiagram
    actor Developer
    participant Shell
    participant Zoo as zoo (entrypoint)
    participant Act as ActivateZooEnv (action)
    participant WL as WriteLatestZooEnvScripts (action)
    participant GR as GetRecentZooEnv (rule)
    participant Zz as zz (fish function)

    Note over Developer,WL: Switch to another project
    Developer->>Zoo: zoo env blog
    Zoo->>Act: activate_zoo_env("blog")
    Act->>Act: record previous and latest env
    Act->>WL: write_latest_zoo_env_scripts("blog")
    Act-->>Zoo: source line
    Zoo-->>Shell: source .../envs/blog/activate.<shell>

    Note over Developer,GR: Switch back
    Developer->>Zoo: zoo env -
    Zoo->>GR: get_recent_zoo_env("previous")
    GR-->>Zoo: shop
    Zoo->>Act: activate_zoo_env("shop")
    Zoo-->>Shell: source .../envs/shop/activate.<shell>

    Note over Shell: Start a new terminal
    Shell->>Shell: source ~/.config/jazzoo/latest.<shell>
    Shell->>Shell: source .../envs/shop/activate.<shell>

    Note over Developer,Zz: Switch with zz
    Developer->>Zoo: zoo env --install-fish
    Developer->>Zz: zz blog
    Zz->>Zoo: zoo env blog
    Zoo-->>Zz: source .../envs/blog/activate.fish
    Zz->>Shell: source the line
```
"""
