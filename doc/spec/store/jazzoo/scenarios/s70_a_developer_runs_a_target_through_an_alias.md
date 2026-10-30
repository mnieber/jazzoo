[comment]: <> (This file is auto-generated. Do not edit directly.)

# s70_a_developer_runs_a_target_through_an_alias

## A developer runs a target through an alias

The developer gives short names to the targets that they run often. The aliases are
personal: they live in the developer's config directory, and apply to every Jazzoo
file that the developer runs, as the aliases of git do.

### Steps

#### It defines aliases

The developer writes an `[alias]` section in `~/.config/jazzoo/config` (or in
`$XDG_CONFIG_HOME/jazzoo/config`), which is an INI file:</br>

```ini
[alias]
b = build
fb = fe.build mode=debug
dep = deploy --confirm
```

An expansion is a target, followed by arguments and options of `jaz`, as on the
command line.</br>

#### It runs a target through an alias

The developer runs `jaz fb mode=release`.</br>
`jaz` looks up `fb` as a target of the root module. Only when there is no such target,
it calls `expand_alias`, so an alias never changes what an existing target does.</br>
`expand_alias` reads the aliases of the config file with `read_aliases`, and returns
the expansion of `fb` split into tokens. A config file that does not exist has no
aliases; an invalid config file or expansion raises an `AliasError`.</br>
`jaz` adds the options of the expansion (`--confirm`, `--trace`) to those of the
command line. The arguments of the expansion are presets: an argument on the command
line overrides the one of the expansion for the same parameter. So `jaz fb
mode=release` runs `fe.build` with `mode=release`.</br>
The target of an expansion must be a real target: aliases are not chained.</br>

### Diagram

```mermaid
sequenceDiagram
    actor Developer
    participant Jaz as jaz (entrypoint)
    participant EA as ExpandAlias (rule)
    participant GF as GetAliasConfigFile (rule)
    participant RA as ReadAliases (rule)

    Note over Developer: Define aliases
    Developer->>Developer: write [alias] in ~/.config/jazzoo/config

    Note over Developer,RA: Run a target through an alias
    Developer->>Jaz: jaz fb mode=release
    Jaz->>Jaz: no target fb in the root module
    Jaz->>EA: expand_alias("fb")
    EA->>GF: get_alias_config_file()
    GF-->>EA: ~/.config/jazzoo/config
    EA->>RA: read_aliases(config_file)
    RA-->>EA: {"fb": "fe.build mode=debug", ...}
    EA-->>Jaz: ["fe.build", "mode=debug"]
    Jaz->>Jaz: merge options and arguments
    Jaz->>Jaz: run fe.build(mode="release")
```

