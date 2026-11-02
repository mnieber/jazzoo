import sunya
from sunya import C as c
from sunya import R as r
from sunya import goal, it, the

scenario = sunya.add_scenario("s35_a_config_file_includes_layers")


def run_scenario():
    r.developer = c.External.Actors.Developer
    r.script = c.External.Actors.Script
    r.get_config_rule = c.Config.Rules.GetConfig
    r.get_loaded_config_rule = c.Config.Rules.GetLoadedConfig
    r.read_config_layers_rule = c.Config.Rules.ReadConfigLayers
    r.expand_include_path_rule = c.Config.Rules.ExpandIncludePath
    r.read_config_file_rule = c.Config.Rules.ReadConfigFile
    r.merge_config_util = c.Config.Utils.MergeConfig
    r.loaded_config = c.Config.Models.LoadedConfig

    with goal().split_the(r.config_file).into(r.layers):
        the(r.developer).moves_parts_of_the(r.config_file).into(r.layer_files)
        it().lists_the(r.layer_files).in_the(r.includes_key).of_the(r.config_file)

    with goal().read_a(r.config_value).from_a(r.layer):
        with the(r.script).calls(r.get_config_rule).with_a(r.config_path):
            with it().calls(r.get_loaded_config_rule):
                it().copies_the(r.environment)
                with it().calls(r.read_config_layers_rule).for_each(r.config_file):
                    it().calls(r.read_config_file_rule).for_the(r.config_file)
                    with it().takes_the(r.includes).from_the(r.file_tree):
                        it().calls(r.expand_include_path_rule).for_each(r.include)
                        it().skips_an(r.include).if_it_was_read_already()
                        it().calls(r.read_config_layers_rule).for_the(r.include)
                    it().returns_the(r.file_trees).in_merge_order()
                it().calls(r.merge_config_util).for_the(r.file_trees)
                it().adds_the(r.expanded_includes_list).to_the(r.merged_tree)
                it().returns_the(r.loaded_config)
            it().returns_the(r.config_value)

    with goal().find_all_the(r.config_files).of_the(r.project):
        the(r.script).calls(r.get_config_rule).with_the(r.includes_path)
        it().receives_the(r.expanded_includes_list)


markdown_node = sunya.add_markdown_node(scenario, "A config file includes layers")

markdown_node.markdown = """
A config file can pull in other config files, its layers, with `/jazzoo/includes`.
The layers are logically part of the file, so the jazzoo file only loads the file
itself, and a script reads the values of its layers as if they were in the file.

```yaml
# env/local/config/base.yaml
jazzoo:
  includes:
    - tmux.yaml
    - docker.yaml

docker:
  shell: bash
```

```yaml
# env/local/config/docker.yaml
jazzoo:
  includes:
    - common.yaml

docker:
  compose_project: blogs
  shell: sh
```

The includes are resolved when the config is read (by `get_config` or
`⚙️.get_config`), not when `⚙️.load_config` adds a file to the list. The whole
`/jazzoo` subtree of the config is reserved for Jazzoo.

### Steps

#### It splits a config file into layers

The developer moves parts of a config file into layer files, and lists them in the
`/jazzoo/includes` of the file. An include is a path relative to the file that
contains it (or absolute), and may use environment variables (`${NAME}`,
`${NAME:-default}`) and a leading `~`. It cannot reference a config value, because
the config is not built yet. A layer may include layers of its own.</br>

#### It reads a value from a layer

The script calls `get_config`, and `get_loaded_config` builds the `LoadedConfig`. It
first copies the environment, which include paths and values both read.</br>
For each file in `JAZZOO_CONFIG_FILES`, `read_config_layers` reads the file with
`read_config_file`, and takes the includes out of its tree. `expand_include_path`
turns each include into an absolute path, and `read_config_layers` reads that layer
in the same way, depth-first.</br>
Every file is read once in the whole config list, at its first position: a file
that was read already (a cycle, a layer that two files include, or a file in the
list that an earlier file included) is skipped.</br>
`read_config_layers` returns the files in merge order: the layers of a file come
before the file, a layer's own includes before the layer. So a file wins over its
layers. `merge_config` merges all the files in this order.</br>
`get_config` reads the value from the merged tree as usual. An error about a value
names the layer that supplied it.</br>

#### It finds all the config files of a project

The expanded includes list is added to the merged tree at `/jazzoo/includes`: the
absolute paths of the layers of all the files in `JAZZOO_CONFIG_FILES`, in merge
order. A tool that opens or lists the config files of a project (e.g. an
`edit-config` target) reads it with `get_config`.</br>

### Diagram

```mermaid
sequenceDiagram
    actor Developer
    participant Script
    participant Get as GetConfig (rule)
    participant Loaded as GetLoadedConfig (rule)
    participant Layers as ReadConfigLayers (rule)
    participant Expand as ExpandIncludePath (rule)

    Note over Developer: Split a config file into layers
    Developer->>Developer: list the layer files in /jazzoo/includes

    Note over Script,Expand: Read a value from a layer
    Script->>Get: get_config("/docker/shell")
    Get->>Loaded: get_loaded_config()
    Loaded->>Loaded: copy the environment
    Loaded->>Layers: read_config_layers(base.yaml)
    Layers->>Expand: expand_include_path("docker.yaml")
    Expand-->>Layers: absolute path
    Layers->>Layers: read the layer and its includes (once per file)
    Layers-->>Loaded: file trees in merge order
    Loaded->>Loaded: merge the trees, add /jazzoo/includes
    Loaded-->>Get: LoadedConfig
    Get-->>Script: "bash"

    Note over Script,Get: Find all the config files
    Script->>Get: get_config("/jazzoo/includes")
    Get-->>Script: absolute paths of the layers
```
"""
