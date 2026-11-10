[comment]: <> (This file is auto-generated. Do not edit directly.)

# s35_a_config_file_includes_layers

## A config file includes layers

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

The script calls `get_config`, which reads each config file together with its layers.
The layers are applied in their order of appearance, followed by the file itself, so that a
file wins over its layers.</br>

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

