import sunya
from sunya import C as c
from sunya import R as r
from sunya import goal, it, the

scenario = sunya.add_scenario("s30_a_script_reads_config_values")


def run_scenario():
    r.developer = c.External.Actors.Developer
    r.script = c.External.Actors.Script
    r.jaz_entrypoint = c.Runtime.Entrypoints.Jazzoo
    r.load_config_action = c.Environment.Actions.LoadConfig
    r.get_config_rule = c.Config.Rules.GetConfig
    r.get_loaded_config_rule = c.Config.Rules.GetLoadedConfig
    r.read_config_file_rule = c.Config.Rules.ReadConfigFile
    r.merge_config_util = c.Config.Utils.MergeConfig
    r.get_value_rule = c.Config.Rules.GetValue
    r.loaded_config = c.Config.Models.LoadedConfig

    with goal().name_the(r.config_files).in_the(r.jazzoo_file):
        with the(r.developer).runs(r.jaz_entrypoint).with_a(r.target):
            with it().calls(r.load_config_action).for_each(r.config_file):
                it().checks_that_the(r.config_file).exists()
                it().appends_it_to(r.jazzoo_config_files)
            it().runs_the(r.script).of_the(r.target)

    with goal().read_a(r.config_value).in_the(r.script):
        with the(r.script).calls(r.get_config_rule).with_a(r.config_path):
            with it().calls(r.get_loaded_config_rule):
                with it().builds_the(r.loaded_config).if_the(
                    r.jazzoo_config_files
                ).changed():
                    it().calls(r.read_config_file_rule).for_each(r.config_file)
                    it().calls(r.merge_config_util).for_the(r.file_trees)
                    it().copies_the(r.environment)
                it().returns_the(r.loaded_config)
            with it().calls(r.get_value_rule).with_the(r.config_path):
                it().finds_the(r.raw_value).in_the(r.merged_tree)
                it().expands_the(r.references).in_the(r.raw_value)
                it().caches_the(r.expanded_value)
            it().returns_the(r.expanded_value)


markdown_node = sunya.add_markdown_node(scenario, "A script reads config values")

markdown_node.markdown = """
A jazzoo file names the YAML config files of a project, and a script that it runs
(a Python shebang block, or any `python foo.py` shell line) reads values from the
merged config with `get_config`. Jazzoo only manages the list of config files; it
never reads them itself.

```
⚙️.load_config(path=⚙️.module.dirname / "config/base.yaml")
⚙️.load_config(path=⚙️.module.dirname / "config/local.yaml", required=false)

build:
    #!/usr/bin/env python3
    from jazzoo import get_config as get

    print(f"building {get('/root/src')}")
```

```yaml
# config/base.yaml
root:
  project_dir: ${PROJECT_DIR}
  src: ${/root/project_dir}/src
```

`get_config`, `prepare_config` and the config errors live in the self-contained
sub-package `jazzoo.config`, which imports only the standard library (and a vendored
copy of PyYAML). A project can copy it into its own source tree, and its
`get_config` reads the same list of config files that `jaz` sets.

### Steps

#### It names the config files

The developer runs a target with `jaz`.</br>
Each `⚙️.load_config` in the jazzoo file calls `load_config`, which checks that the
file exists (a missing file is skipped when it is not required), and appends its
absolute path to the environment variable `JAZZOO_CONFIG_FILES`.</br>
The script of the target inherits this variable.</br>

#### It reads a value

The script calls `get_config` with a path into the config, such as `/root/src`, and
optionally a default for a path that does not exist.</br>
`get_loaded_config` returns the cached `LoadedConfig`. When the value of
`JAZZOO_CONFIG_FILES` differs from the one that the cache was built from, it builds a
new one: `read_config_file` reads each file as plain YAML, `merge_config` merges them
in list order (a later file overrides an earlier one, recursively for dicts), and it
copies the environment.</br>
`get_value` finds the value at the path in the merged tree, and expands it lazily:
`${/a/b}` is replaced by another config value, `${NAME}` by a variable of the copied
environment, and references may be nested and chained. Only the value at the path
and what it references are expanded, and each expanded value is cached.</br>
`get_config` returns the expanded value.</br>

A script that changes its own environment first calls `prepare_config`, which builds
the `LoadedConfig` without expanding anything, so that every `get_config` sees the
environment as it was when the script started.</br>

### Diagram

```mermaid
sequenceDiagram
    actor Developer
    participant Jaz as jaz (entrypoint)
    participant Load as LoadConfig (action)
    participant Script
    participant Get as GetConfig (rule)
    participant Loaded as GetLoadedConfig (rule)
    participant Value as GetValue (rule)

    Note over Developer,Load: Name the config files
    Developer->>Jaz: jaz build
    Jaz->>Load: load_config(path, is_required)
    Load->>Load: append path to JAZZOO_CONFIG_FILES
    Jaz->>Script: run the block of build

    Note over Script,Value: Read a value
    Script->>Get: get_config("/root/src")
    Get->>Loaded: get_loaded_config()
    Loaded->>Loaded: read and merge the files, copy the environment (if the list changed)
    Loaded-->>Get: LoadedConfig
    Get->>Value: get_value(loaded, segments)
    Value->>Value: find, expand and cache the value
    Value-->>Get: expanded value
    Get-->>Script: expanded value
```
"""
