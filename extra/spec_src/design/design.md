# The zz shortcut for fish

A developer switches between zoo environments many times a day. `zoo env <name>` can only
print the line that activates the env, because a program cannot change the shell that
runs it, so the developer types `zoo env blog | source`. A shell function can source the
line itself. The developer installs one, once per machine:

```
$ zoo env --install-fish
Wrote ~/.config/fish/functions/zz.fish
Wrote ~/.config/fish/completions/zz.fish
Wrote ~/.config/fish/conf.d/zoo.fish
Open a new fish shell to use zz.
```

From then on:

```
$ zz blog                    # switch to blog (same as: zoo env blog | source)
$ zz -                       # switch back to the previous env
$ zz                         # list the envs, with the active one marked
$ zz <TAB>                   # complete the name of an env
$ zz --init --create-venv    # register the current directory, and switch to it
```

A new fish shell starts in the env that was activated last, without a line in
`config.fish`.

## The files

`zoo env --install-fish` writes three files to the fish config directory:

- `functions/zz.fish`: the `zz` function.
- `completions/zz.fish`: completes the names of the envs, and `-`, for the first
  argument of `zz`.
- `conf.d/zoo.fish`: sources `latest.fish` of the zoo registry when the shell starts.

## The zz function

- `zz` without arguments runs `zoo env --list`.
- `zz` with `--list` or `--forget` among its arguments runs `zoo env` with the same
  arguments, and does not source anything: these options do not activate an env.
- Otherwise, `zz` runs `zoo env` with the same arguments, and sources the line that it
  prints. When `zoo env` fails, `zz` sources nothing and returns its exit code; the error
  of `zoo` is shown as it is.

## Listing the names of the envs

`zoo env --list --names` prints the names of the registered envs, one per line, without
the marker of the active env and without the root directories. The completions of `zz`
use it. `--names` is only valid with `--list`.

## Decisions

- **The command.** The installer is an option of `zoo env`, next to `--init`, `--forget`
  and `--list`. It is not a jaz target (e.g. `zoo env.install-fish`): every `zoo` command
  other than `zoo env` runs a target of the active env, so it would need an active env,
  and every project would have to carry the target. `--install-fish` excludes a name,
  `-`, `--latest`, `--init`, `--forget` and `--list`.
- **The name.** The function is `zz`: short, easy to type, and it reads as "zoo".
  There is no key binding: `zz` and the completion of names are as fast.
- **The shell.** `zz` runs `zoo` with `SHELL` set to `fish`. `zoo env` picks the
  activate script from `SHELL`, which is the login shell: a developer whose login shell
  is bash, and who starts fish from it, would get the bash script. `zz` only runs in
  fish, so it says so.
- **Finding zoo.** `zz` runs the `zoo` on the `PATH`, which is the `zoo` of the active
  env. When no env is active, it runs the first `zoo-<name>` link in `~/.local/bin`,
  which is the `zoo` of a registered env. When there is neither, `zz` prints
  `zz: no zoo found; register a project with zoo env --init` and fails. Every `zoo` can
  switch to every env, because the registry is shared.
- **The fish config directory.** `$XDG_CONFIG_HOME/fish`, or `~/.config/fish` when
  `XDG_CONFIG_HOME` is unset or empty, as fish itself does.
- **Startup.** `conf.d/zoo.fish` sources `latest.fish` only in an interactive shell
  (`status is-interactive`), so that a fish script does not run in a venv that it did
  not ask for. It names `latest.fish` by its absolute path in the zoo registry at the
  time of the install, and skips it when it does not exist. A `config.fish` that
  already sources `latest.fish` does no harm: activating the same env twice gives the
  same result.
- **Only its own files.** Each file starts with the line
  `# managed by zoo env --install-fish`. The installer overwrites a file that starts
  with this line, so running it again updates the files after an upgrade of jazzoo.
  When one of the files exists without the line, the installer writes nothing, and
  fails with a `FishFileExistsError` (a `ZooError`) that lists every such file. It
  never edits a file of the developer, such as `config.fish`.
- **Output.** The installer prints the files that it wrote, and a reminder to open a
  new shell, to stderr, like the other messages of `zoo env`. The stdout of `zoo env` is
  either a line to source or the list of envs.
- **Tests without fish.** The tests that run the installed files in a real `fish` are
  skipped when `fish` is not installed, so that the other tests still run on a machine
  without fish.
- **Only fish.** There is no installer for bash. A bash user can define the function in
  `.bashrc`: `zz() { eval "$(zoo env "$@")"; }`. The scenario of zz shows it.
- **Where the code lives.** In the feature package `jazzoo.zoo`:
  `actions/install_fish_files.py` (checks and writes the files; the file contents are
  templates in this module, like the activate scripts in `init_zoo_env.py`),
  `rules/get_fish_config_dir.py`, and `FishFileExistsError` in `errors.py`. The
  entrypoint `zoo.py` handles `--install-fish` and `--names`.
