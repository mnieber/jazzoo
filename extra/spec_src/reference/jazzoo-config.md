# Jazzoo Config Files

This document describes how the scripts that a Jazzoo file runs read values from
YAML config files.

---

## 1. Overview

A Jazzoo file names one or more YAML config files with `⚙️.load_config`
(`jazzoo-language.md`, section 7.4). A script that the file runs — a Python shebang
block, or any `python foo.py` shell line — reads values from the merged config with a
single call:

```
⚙️.load_config(path=⚙️.module.dirname / "config/base.yaml")
⚙️.load_config(path=⚙️.module.dirname / "config/local.yaml", required=false)

build:
    #!/usr/bin/env python3
    from jazzoo import get_config as get

    src = get("/root/src")
    print(f"building {src}")
```

```yaml
# config/base.yaml
root:
  project_dir: ${PROJECT_DIR}
  src: ${/root/project_dir}/src
  build_dir: ${/root/project_dir}/build
```

Jazzoo only manages the list of config files; it never reads them itself.

## 2. `get_config`

```python
from jazzoo import get_config as get

get("/root/src")                # a value: str, int, float, bool, None, list or dict
get("/root/tags/0")             # a list element, by index
get("/")                        # the whole config
get("/root/port", default=80)   # 80 if the path does not exist
```

- The argument is a path into the config: `/`-separated keys, starting with `/`. A
  segment that addresses a list is an integer index. Empty segments are ignored, so
  `/root/` is the same as `/root`.
- A path that does not start with `/` is a `ValueError`; `default` does not apply.
- `get` returns the value at the path, fully expanded (section 5). A dict or list
  is expanded recursively.
- A path that does not exist raises `ConfigKeyError`, which names the path and the
  first segment that was not found.
- With `default=<value>`, `get` returns `<value>` instead of raising `ConfigKeyError`
  when the path does not exist. The default is returned as is; it is not expanded.
  It only covers a missing path: an error while expanding a value that exists (e.g.
  an unset environment variable) is still raised.
- `get` reads the config list from `JAZZOO_CONFIG_FILES`. When the variable is unset
  or empty, the config is `{}`.

## 3. Caching and the environment

- `get` builds the config just in time and caches it. The cache key is the value of
  `JAZZOO_CONFIG_FILES`; when the list changes, the cache is rebuilt.
- The cache holds the merged raw tree, a copy of the environment, and every value
  expanded so far. `${NAME}` reads from the copy, not from the live environment, so
  every `get` sees the environment as it was at the first `get`. The result
  therefore does not depend on the order in which values are expanded: lazy
  expansion gives the same values as expanding the whole config up front would. A
  later change to the environment is only seen after the cache is rebuilt.
- Expansion is lazy: `get("/root/src")` expands only `/root/src` and whatever it
  references. A broken value elsewhere in the config (e.g. an unset environment
  variable in a section the script never reads) does not make `get` fail.

`prepare_config()` builds the cache for the current `JAZZOO_CONFIG_FILES` now,
instead of at the first `get`:

```python
from jazzoo import prepare_config

prepare_config()
os.environ["SHOP_USER"] = "deploy"   # does not affect later get calls
```

- It reads and merges the files and copies the environment. It expands nothing and
  returns `None`.
- A script that changes its environment calls it first, so that `get` keeps seeing
  the environment as it was when the script started.
- File errors (`ConfigFileError`) are raised by `prepare_config`, so they show up at
  the start of the script. A broken value does not make it fail, because nothing is
  expanded.
- When the cache for the current list already exists, it does nothing; in
  particular, it does not take a new copy of the environment.

## 4. Reading and merging files

Config files are read as plain YAML (no Python object tags). A file must contain a
single YAML document whose top level is a mapping, or be empty, which counts as
`{}`. Anything else is a `ConfigFileError` that names the file, as is a YAML syntax
error (with the file and line), a Python object tag such as `!!python/object`, and a
file in the list that no longer exists.

The files are merged in list order; a later file overrides an earlier one:

- two dicts are merged key by key, recursively;
- in all other cases the later value replaces the earlier one. This includes lists:
  a later list replaces an earlier list, it is not appended to;
- `null` is an ordinary value: it replaces the earlier value, it does not delete the
  key.

Merging happens before expansion, so a reference always sees the merged value. A
`local.yaml` that sets `/root/project_dir` also changes `/root/src` in `base.yaml`.

## 5. Expansion

Expansion applies to string values only. Keys are never expanded.

**References to other config values.** `${/a/b}` is replaced by the value at path
`/a/b` in the merged config.

- If the whole string is one reference, the result is the referenced value with its
  own type, which may be a number, list or dict: `threads: ${/build/nr_of_threads}`
  yields the number `2`.
- If the reference is part of a longer string, the referenced value is rendered into
  it as in Jazzoo substitution (`jazzoo-language.md`, section 4.3): a string as is,
  a number as JSON, a boolean as `true` or `false`, and `null` as the empty string. A
  list or dict is a `ConfigExpansionError`.
- The referenced value is expanded first, so references may chain.
- A reference to a path that does not exist is a `ConfigExpansionError`.
- A reference cycle (`/a` references `/b`, which references `/a`) is a
  `ConfigExpansionError` that lists the paths in the cycle.

**Nested references.** A reference may contain other references; the inner ones are
expanded first, and the result is used as the path:

```yaml
env: prod
urls:
  dev: http://localhost:8000
  prod: https://example.com
api_url: ${/urls/${/env}} # https://example.com
```

- An inner reference must yield a string or number, which becomes part of the path.
  A list, dict, boolean or `null` is a `ConfigExpansionError`.
- An inner reference may be an environment variable: `${/urls/${ENV_NAME}}`.
- Nesting may be any number of levels deep.

**Environment variables.** `${NAME}` (no leading `/`) is replaced by the environment
variable `NAME`.

- An unset variable is a `ConfigExpansionError`.
- `${NAME:-default}` yields `default` when `NAME` is unset or empty.
- `$NAME` without braces is not expanded; it stays literal text, so shell snippets
  stored in a config (`echo $HOME`) are left alone.
- The environment is that of the script that calls `get`, as copied when the cache
  was built (section 3). Variables that the Jazzoo file loaded with `⚙️.load_env`
  are therefore visible.

**Escapes.** `$${` yields a literal `${`.

## 6. The `jazzoo.config` sub-package

`get_config`, `prepare_config` and the config errors live in the sub-package
`jazzoo.config`, and are re-exported by `jazzoo`, so `from jazzoo import get_config`
works.

The sub-package is self-contained: it imports only the standard library and its own
modules, and its internal imports are relative. A project that does not want to
depend on `jazzoo`, or whose interpreter does not have `jazzoo` installed (e.g.
because `jaz` was installed with `pipx`), can copy the sub-package into its own
source tree under any name and call its `get_config`. It reads the same
`JAZZOO_CONFIG_FILES` that `jaz` sets.

Jazzoo has no runtime dependencies, so YAML is read with a vendored, pure-Python
copy of PyYAML inside the sub-package. It is never imported as `yaml`, so a PyYAML
installed in the same venv is neither used nor affected.

## 7. Config errors

| Class                  | Meaning                                                          |
| ---------------------- | ---------------------------------------------------------------- |
| `ConfigFileError`      | a config file is missing, is not valid YAML, or is not a mapping |
| `ConfigKeyError`       | `get` was given a path that does not exist, without a default    |
| `ConfigExpansionError` | a `${...}` cannot be expanded                                    |

All three subclass `ConfigError(Exception)`, defined in `jazzoo.config`. They are not
`JazzooError`s, so that the sub-package stays self-contained. A `ConfigFileError`
names the file and, for a syntax error, starts with `<file>:<line>:` like Jazzoo's
own errors. The other two name the config path involved and, where it is known, the
config file that supplied the value.

```python
class ConfigError(Exception): ...
class ConfigFileError(ConfigError): ...       # a config file that cannot be read
class ConfigKeyError(ConfigError): ...        # a get_config path that does not exist
class ConfigExpansionError(ConfigError): ...  # a ${...} that cannot be expanded
```

## 8. Unspecified

- **Preset config values.** Values that `get_config` could provide without a config
  file defining them — the directory of the module that loaded a config file, the
  root module's directory, or the directory of the config file itself (to anchor
  relative paths inside it) — are not yet specified.
