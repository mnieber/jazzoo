# Zoo: projects and their environments

This document describes `zoo`, which registers projects as zoo environments, switches
between them, and runs their targets from any directory.

---

## 1. Overview

A **zoo environment** (env) is a registered project: a name, the root directory of the
project (which has a root jazzoo file), and a venv in which jazzoo is installed.

```
$ cd ~/projects/blog
$ eval "$(zoo env --init --create-venv)"   # register blog, with a new venv, and activate it
$ cd /tmp
$ zoo build                                # runs the target build of blog
$ eval "$(zoo env shop)"                   # switch to shop
$ eval "$(zoo env -)"                      # switch back to blog
$ zoo --which                              # which env is active?
blog  /home/jane/projects/blog
```

With the fish function `zz` (section 6), the last lines become `zz shop` and `zz -`.

A program cannot change the shell that runs it, so `zoo env` only **prints** the line
that activates an env, and the shell sources it (`eval "$(...)"` in bash,
`... | source` in fish). The messages of `zoo env` go to stderr, so that its stdout only
has lines to source.

## 2. Registering a project

```
zoo env --init [<name>] --create-venv [--without-pip]
zoo env --init [<name>] --use-venv <venv>
```

`zoo env --init` registers the current directory as an env, and activates it (it
prints the line to source). The name defaults to the name of the directory; it consists
of letters, digits, `-`, `_` and `.`, and does not start with `-` or `.`.

- `--create-venv` creates the venv `.venv` in the project directory. The venv gets a
  **linked install** of the jazzoo that runs `zoo` (e.g. a development checkout): the
  venv uses that jazzoo without copying it, as `pip install -e` would. pip sees it as an
  editable install, so `pip install jazzoo==<version>` replaces it with a release, and
  `pip uninstall jazzoo` removes it, without touching the linked directory. The venv
  has the scripts `zoo`, `jaz`, `jazzoo` and `jaz-run`. `--without-pip` creates the venv
  without pip.
- `--use-venv <venv>` registers an existing venv, which must have jazzoo installed
  (a `bin/zoo`), and must not belong to another env.

Registering fails, and writes nothing, when the env exists, when the directory has no
root jazzoo file (`jazzoo` or `jazzoo.jaz`), or when the venv is not valid.

**What is written.** The env directory `~/.config/jazzoo/envs/<name>` (below
`$XDG_CONFIG_HOME` when it is set) has links to the root directory and the venv, and
the activate scripts `activate.bash` and `activate.fish`. The link
`~/.local/bin/zoo-<name>` points to the `zoo` of the venv, so that the env can be used
when no env is active; `zoo` warns when `~/.local/bin` is not on the `PATH`.

## 3. Switching between projects

```
zoo env <name>      # activate an env
zoo env -           # activate the previous env, like cd -
zoo env --latest    # activate the env that was activated last
```

Activating an env prints the line that sources its activate script, for the shell in
`SHELL` (fish, or bash for every other shell). The script sets `JAZZOO_ENV` to the name
of the env, deactivates the active venv, and activates the venv of the env.

`zoo` remembers the latest and the previous env in `~/.config/jazzoo/recent.json`, so
`zoo env -` goes back and forth between two envs. When there is no previous (or
latest) env, it is an error.

**New terminals** start in the latest env when the startup file of the shell sources
`~/.config/jazzoo/latest.<shell>`, which `zoo` rewrites whenever an env is activated.
In fish, `zoo env --install-fish` sets this up (section 6); in bash, add this line to
`.bashrc`:

```
source ~/.config/jazzoo/latest.bash
```

No Python runs at startup, and `zoo` does not need to be on the `PATH`.

## 4. Running targets

```
zoo [<jaz options>] <target> [arg=value ...]
```

`zoo` runs a target of the env whose venv it runs in: the `zoo` on the `PATH` of an
active env, or the link `zoo-<name>` of any env. It changes to the root directory of
the env and runs `jaz` there, with the same arguments, so `zoo` takes the options of
`jaz`, and `zoo` alone lists the targets. `⚙️.invocation_dir` is the directory that
`zoo` was called from.

`zoo` always runs the root jazzoo file of the env, so `--file` is an error; import a
second jazzoo file into the root jazzoo file as a layer instead. A `zoo` whose venv
belongs to no env fails with `not in a zoo environment`. To run a target whose name is
`env`, write `zoo -- env`.

## 5. Inspecting envs

```
zoo env --list [--names]   # list the registered envs
zoo --which                # print the active env
zoo --which <path>         # print the file that defines a target of the env
```

`zoo env --list` lists every env with its root directory, and marks the active env
(the one in `JAZZOO_ENV`) with `*`. An env whose root directory or venv no longer
exists is marked `(root dir missing)` or `(venv missing)`. With `--names`, it prints
only the names, one per line.

```
$ zoo env --list
  blog    /home/jane/projects/blog
  groupy  /home/jane/projects/groupy (venv missing)
* shop    /home/jane/projects/shop
```

`zoo --which` prints the line of the active env, as `zoo env --list` does but without
the marker. When no env is active, it prints nothing and succeeds; when `JAZZOO_ENV`
names an env that is not registered, it is an error. It does not need to run in the
venv of an env.

`zoo --which <path>` is `jaz --which <path>` in the root directory of the env: it
prints the file that defines the target at the path (`jazzoo-language.md`, section
11.3).

**Forgetting an env.** `zoo env --forget <name>` removes the env directory, and the link
`zoo-<name>` while it points into the venv of the env. The project and the venv are not
removed.

## 6. Fish: `zz` and completions

```
zoo env --install-fish
```

This writes, to the fish config directory (`$XDG_CONFIG_HOME/fish`, or
`~/.config/fish`):

- the function `zz` in `functions/zz.fish`, and its completions;
- the completions of `jaz`, `jazzoo` and `zoo` in `completions/`;
- `conf.d/zoo.fish`, which makes a new interactive fish start in the latest env.

Each file starts with `# managed by zoo env --install-fish`, and is overwritten when
the installer runs again. When a file of the developer is in the way, nothing is
written, and the error lists the files. Open a new fish to use `zz`.

`zz` runs `zoo env` and sources its output: `zz shop` switches to shop, `zz -` switches
back, and `zz --list` lists the envs. It runs the `zoo` of the active env or, when no
env is active, the `zoo-<name>` link of any env, since every `zoo` can switch to every
env. Pressing tab after `zz` offers the names of the envs.

The completions of `jaz`, `jazzoo` and `zoo` read the jazzoo file without running its
top-level statements, so pressing tab has no side effects.

In bash, define `zz` in `.bashrc`:

```
zz() { eval "$(zoo env "$@")"; }
```
