[comment]: <> (This file is auto-generated. Do not edit directly.)

# s20_a_developer_switches_between_projects

## A developer switches between projects

The developer works on several registered projects, and switches between them in the
same terminal. Like `cd -`, `zoo env -` goes back to the previous env. A new terminal
starts in the env that was activated last.

### Steps

#### It switches to another project

The developer runs `eval "$(zoo env blog)"` (in fish: `zoo env blog | source`).</br>
`activate_zoo_env` records the latest env as the previous one, and `blog` as the latest
one, in `~/.config/jazzoo/recent.json`.</br>
It calls `write_latest_zoo_env_scripts`, which rewrites `latest.bash` and
`latest.fish` in `~/.config/jazzoo` to source the activate scripts of `blog`.</br>
`zoo` prints the line that sources the activate script of `blog`. The shell sources
it, which deactivates the active venv and activates the venv of `blog`.</br>

#### It switches back

The developer runs `eval "$(zoo env -)"`.</br>
`get_recent_zoo_env` returns the previous env, which `activate_zoo_env` activates as
before. Running `zoo env -` again goes back and forth between the two envs.</br>

#### It starts a new terminal in the latest project

The startup file of the shell sources `~/.config/jazzoo/latest.<shell>`. In fish, this
is `conf.d/zoo.fish`, which `zoo env --install-fish` writes, and which only does this in
an interactive shell. In bash, the developer adds the line to `.bashrc`.</br>
This script sources the activate script of the latest env, so the new terminal starts
with its venv active. No Python runs, and no `zoo` is needed on the `PATH`.</br>

### Diagram

```mermaid
sequenceDiagram
    actor Developer
    participant Shell
    participant Zoo as zoo (entrypoint)
    participant Act as ActivateZooEnv (action)
    participant WL as WriteLatestZooEnvScripts (action)
    participant GR as GetRecentZooEnv (rule)

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
```

