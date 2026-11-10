[comment]: <> (This file is auto-generated. Do not edit directly.)

# s20_a_developer_switches_between_projects

## A developer switches between projects

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

