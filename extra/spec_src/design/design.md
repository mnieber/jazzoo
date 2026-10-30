# Design: a Jazzoo file reads config values

## What the developer does

A Jazzoo file can read a value of the merged config with `⚙️.get_config`, without running a Python script:

```
⚙️.load_config(path=⚙️.module.dirname / "config/base.yaml")
⚙️.load_config(path=⚙️.module.dirname / "config/local.yaml", required=false)

# Build from Dockerfile.local when local is true (default: /compose/use_dockerfile_local)
build(local=⚙️.get_config(path="/compose/use_dockerfile_local", default=false)):
    🐆.local-flag = "--local" if 🐆.local else ""
    ⚙️.python build.py 🐆.local-flag

deploy():
    echo "deploying to {{ ⚙️.get_config(path="/deploy/host") }}"
```

## What should happen

`⚙️.get_config(path, default)` is an expression: it yields the value at `path` in the merged config, as a jazzoo
value. It can be used wherever an expression can, e.g. in an assignment, in `{{ }}` and as a parameter default.

1. It reads the config list as it is when the call runs, and returns what `get_config(path)` of `jazzoo-config.md`
   returns for that list: the same path syntax, merge order, includes and `${...}` expansion.
2. A string, number, boolean or `null` becomes the same jazzoo value; a list becomes an array and a dict an object.
3. When the path does not exist, it yields `default`. Without `default`, a missing path is an `ExecutionError` that
   names the path and the segment that was not found (the message of `ConfigKeyError`).
4. Every other error of `get_config` (a path that does not start with `/`, a missing or invalid config file, an
   unset environment variable in a value) is an `ExecutionError` with the same message.
5. A value that is not a JSON value (e.g. a YAML timestamp, or a dict with a non-string key) is an `ExecutionError`
   that names the path.

## Decisions

- **The name and parameters follow `get_config`** (`path`, `default`), so that a value is read the same way in a
  Jazzoo file and in a Python script. As with `⚙️.load_config`, the arguments are passed by name.
- **`default` takes any value**, including `null`; only an omitted `default` makes a missing path an error. As in
  Python, `default` only covers a missing path, and it is not expanded.
- **The config list at the time of the call.** A top-level assignment that calls `⚙️.get_config` before a later
  `⚙️.load_config` does not see the later file. This is consistent with `⚙️.load_config` in a function body, which
  also takes effect from that line on: not every line of a Jazzoo file sees the same config.
- **Parsed on first use.** A run that does not call `⚙️.get_config` does not parse the YAML, so `jaz` stays as fast
  as before. Within a run, the parsed config is reused until the config list changes (the cache of `get_config`).
- **A non-JSON value is an error**, not a conversion to a string: a Jazzoo value is a JSON value, and a silent
  conversion would hide a typo in the config (e.g. an unquoted date).
- **The arguments are checked at load time**, like those of `⚙️.load_env` and `⚙️.load_config`: a call without
  `path`, or with an unknown parameter, is an `ArgumentError` when the module is loaded.
- **A parameter default may be a call.** A default is an expression (`jazzoo-language.md`, section 8.3), so the
  function header accepts a call with its own parentheses (e.g. `⚙️.get_config(...)` or `🐭.f(x="y")`) as a
  default, and a parenthesis inside a string default is part of the string.
- `⚙️.get_config` has no side effect: `⚙️.load_env` and `⚙️.load_config` stay the only built-ins with one.
- `jazzoo-language.md` (section 7.4, and a new section next to it) and `jazzoo-config.md` (section 1, which says
  that jazzoo never reads the config) describe `⚙️.get_config`.
