import sunya
from sunya import C as c
from sunya import R as r
from sunya import goal, it, the

scenario = sunya.add_scenario("s25_a_developer_switches_projects_with_zz")


def run_scenario():
    r.developer = c.External.Actors.Developer
    r.shell = c.External.Actors.Shell
    r.zoo_entrypoint = c.Runtime.Entrypoints.Zoo
    r.install_fish_files_action = c.Zoo.Actions.InstallFishFiles
    r.get_fish_config_dir_rule = c.Zoo.Rules.GetFishConfigDir
    r.fish_file_exists_error = c.Zoo.Errors.FishFileExistsError
    r.activate_zoo_env_action = c.Zoo.Actions.ActivateZooEnv
    r.list_zoo_envs_rule = c.Zoo.Rules.ListZooEnvs

    with goal().install_the(r.zz_function).in_the(r.fish_config_dir):
        with the(r.developer).runs(r.zoo_entrypoint).with_the(r.install_fish_option):
            with it().calls(r.install_fish_files_action):
                it().calls(r.get_fish_config_dir_rule)
                it().raises(r.fish_file_exists_error).if_a(
                    r.file_of_the_developer
                ).is_in_the_way()
                it().writes_the(r.zz_function).and_its(r.completions)
                it().writes_the(r.completions).of(r.jaz_and_zoo)
                it().writes_the(r.startup_file)
            it().prints_the(r.written_files)

    with goal().switch_to(r.other_zoo_env).with_the(r.zz_function):
        with the(r.developer).runs_the(r.zz_function).with_the(r.env_name):
            it().finds_the(r.zoo_script).of_the(r.active_env).or_a(r.zoo_link)
            with it().runs_the(r.zoo_script).with_the(r.fish_shell):
                it().calls(r.activate_zoo_env_action)
                it().prints_the(r.source_line)
            it().sources_the(r.activate_script).of_the(r.other_zoo_env)

    with goal().complete_the(r.env_name):
        with the(r.shell).runs_the(r.completions).of_the(r.zz_function):
            with it().runs_the(r.zoo_script).with_the(r.names_option):
                it().calls(r.list_zoo_envs_rule)
                it().prints_the(r.env_names)


markdown_node = sunya.add_markdown_node(
    scenario, "A developer switches projects with zz"
)

markdown_node.markdown = """
A program cannot change the shell that runs it, so `zoo env` only prints the line that
activates an env, and the shell sources it. In fish, the developer installs the `zz`
function once, which sources the line itself: `zz blog` switches to blog, `zz -` goes
back, and `zz` alone lists the envs. In bash, the developer defines it in `.bashrc`:
`zz() { eval "$(zoo env "$@")"; }`.

### Steps

#### It installs zz

The developer runs `zoo env --install-fish`.</br>
`install_fish_files` writes these files to the fish config directory
(`$XDG_CONFIG_HOME/fish`, or `~/.config/fish`): the `zz` function in `functions/`, the
completions of `zz`, `jaz`, `jazzoo` and `zoo` in `completions/`, and
`conf.d/zoo.fish`, which makes a new interactive fish start in the latest env.</br>
The completions of `jaz`, `jazzoo` and `zoo` pass the command line to
`<command> --complete`, which prints the candidates. It reads the jazzoo file without
running its top-level statements, so that pressing tab has no side effects.</br>
Each file starts with `# managed by zoo env --install-fish`. A file with this line is
overwritten, so running the installer again updates the files. When a file of the
developer is in the way, it raises a `FishFileExistsError` that lists such files, and
writes nothing.</br>
`zoo` prints the files that it wrote to stderr: its stdout is for lines to source.</br>

#### It switches to another project

The developer runs `zz blog`.</br>
`zz` runs the `zoo` of the active env, or, when no env is active, the `zoo-<name>` link
of any registered env: every `zoo` can switch to every env.</br>
It runs `zoo env blog` with `SHELL` set to `fish`, because `zoo` picks the activate
script from `SHELL`, which is the login shell. `activate_zoo_env` activates blog, and
`zoo` prints the line that sources its fish activate script.</br>
`zz` sources the line, which activates the venv of blog. When `zoo env` fails, it
sources nothing. With `--list` or `--forget`, which activate nothing, `zz` only runs
`zoo env`.</br>

#### It completes the name of an env

The developer types `zz` and presses tab.</br>
The completions run `zz --list --names`, which prints the names of the registered envs,
one per line. Fish offers these names and `-`.</br>

### Diagram

```mermaid
sequenceDiagram
    actor Developer
    participant Shell as fish
    participant Zz as zz (fish function)
    participant Zoo as zoo (entrypoint)
    participant Inst as InstallFishFiles (action)
    participant Act as ActivateZooEnv (action)
    participant List as ListZooEnvs (rule)

    Note over Developer,Inst: Install zz
    Developer->>Zoo: zoo env --install-fish
    Zoo->>Inst: install_fish_files()
    Inst->>Inst: check, write zz, completions, conf.d/zoo.fish
    Inst-->>Zoo: written files
    Zoo-->>Developer: Wrote ... (stderr)

    Note over Developer,Act: Switch to another project
    Developer->>Zz: zz blog
    Zz->>Zoo: SHELL=fish zoo env blog
    Zoo->>Act: activate_zoo_env("blog")
    Act-->>Zoo: source line
    Zoo-->>Zz: source .../envs/blog/activate.fish
    Zz->>Shell: source the line

    Note over Developer,List: Complete the name of an env
    Developer->>Shell: zz <TAB>
    Shell->>Zz: zz --list --names
    Zz->>Zoo: zoo env --list --names
    Zoo->>List: list_zoo_envs()
    List-->>Zoo: envs
    Zoo-->>Shell: blog, shop
```
"""
