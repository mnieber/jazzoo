# Config includes

A config file can pull in other config files, its **layers**, with `/jazzoo/includes`.
The layers are logically part of the file: the config is bigger than what the file
itself contains.

```yaml
# env/local/config/base.yaml
jazzoo:
  includes:
    - tmux.yaml
    - docker.yaml

root:
  project_dir: ${PROJECT_DIR}
```

```yaml
# env/local/config/docker.yaml
jazzoo:
  includes:
    - common.yaml

docker:
  compose_project: blogs
```

The Jazzoo file still loads only `base.yaml`:

```
⚙️.load_config(path=⚙️.module.dirname / "env/local/config/base.yaml")
```

When `get_config` reads `base.yaml`, it also reads `common.yaml`, `docker.yaml` and
`tmux.yaml`, and merges them into the config.

## The expanded includes list

The loader drills into the includes of a file recursively, and builds the expanded
list of all the layer files that it found. In the merged config, `/jazzoo/includes`
holds this list, as absolute paths, instead of the lists that the files contain:

```python
get("/jazzoo/includes")
# ["/app/env/local/config/tmux.yaml",
#  "/app/env/local/config/common.yaml",
#  "/app/env/local/config/docker.yaml"]
```

A tool that opens or lists the config files of a project (e.g. an `edit-config`
target) reads this key to find the layers.

## Decisions

- **Merge order.** The layers of a file are merged first, in the order of the expanded
  list, and the file's own content is merged on top: the file is the most specific, so
  its values win over those of its layers. The expanded list is built depth-first: a
  layer's own includes come before the layer. In the example, the order is
  `tmux.yaml`, `common.yaml`, `docker.yaml`, `base.yaml`.
- **Several files in the config list.** Each file in `JAZZOO_CONFIG_FILES` is expanded
  in this way, and the results are merged in list order, as before.
  `/jazzoo/includes` is the one key that is not replaced by a later file: the expanded
  lists of all the files are joined, in list order, without duplicates.
- **Each file is read once.** A file that is reached a second time, anywhere in the
  config list, is skipped: it keeps its first position. This covers a cycle (a layer
  that includes a file that includes it), a diamond (two layers that include the same
  file), a layer that two files in the config list include, and a file in the config
  list that an earlier file already included. Skipping is silent.
- **Paths.** An include path is relative to the directory of the file that contains
  it, or absolute.
- **Expansion.** Environment variables are expanded in include paths, with the same
  rules as in values: `${NAME}`, `${NAME:-default}`, and `$${` for a literal `${`.
  They read the same copy of the environment as values do, because includes are
  resolved when the cache is built. A reference to a config value (`${/...}`) is not
  allowed, because the config is not built yet. A leading `~` is the home directory,
  taken from `HOME` in the same copy of the environment.
- **Errors.** These are a `ConfigFileError` that names the file that contains the
  include:
  - an include that does not exist;
  - a `/jazzoo/includes` that is not a list of strings;
  - a `${/...}` in an include path;
  - an unset environment variable in an include path.

  There are no optional includes (like `required=false` of `⚙️.load_config`).
- **When the includes are read.** `⚙️.load_config` still only checks that the file
  that it is given exists; `jaz` never reads the YAML. The includes are resolved by
  `get_config` and `prepare_config` when they build the cache, so a missing include
  shows up when a script first reads the config, like a YAML syntax error.
- **The `/jazzoo` key is reserved.** The whole `/jazzoo` subtree of the config is
  reserved for Jazzoo, so that later Jazzoo keys do not clash with project config. A
  `/jazzoo` that is not a mapping is a `ConfigFileError`. A `/jazzoo` or
  `/jazzoo/includes` that is `null` means no includes. Other keys under `/jazzoo` are
  merged like any other config.
- **No includes.** When no file has `/jazzoo/includes`, the key does not exist in the
  merged config. A file with `includes: []` gives an empty list.
- **Normalized paths.** The paths in the expanded list are made absolute and
  normalized (`./a.yaml` and `a.yaml` are the same file); symlinks are not resolved.
  The files in `JAZZOO_CONFIG_FILES` are not in the list themselves, only their
  layers. A file in `JAZZOO_CONFIG_FILES` that an earlier file already included stays
  in the list as a layer.
- **`get` returns the paths as they are.** `get("/jazzoo/includes")` does not expand
  the paths again, so a path that contains `${` (written as `$${` in the include)
  comes back unchanged.
- **Error messages.** An include error starts with the file that contains the include,
  and names the include path or the environment variable.
- **Values from a layer.** An error about a value (e.g. a `ConfigExpansionError`)
  names the layer file that supplied the value, not the file that included it.
- **No glob patterns.** An include is a single file. An explicit list shows the merge
  order, and a missing file is an error.
- **Selecting files.** The rule that the Jazzoo file is the one place that decides
  which files are loaded still holds for the files in the config list. A config file
  does not select files: its includes are unconditional, and they define what the
  file is made of.
- **Where the code lives.** The includes are implemented in `jazzoo.config`, so that
  a vendored copy of the sub-package supports them too.
