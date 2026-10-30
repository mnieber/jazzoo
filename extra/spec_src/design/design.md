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

# A linked jazzoo that pip understands

`zoo env --init --create-venv` creates a venv that uses the jazzoo that runs `zoo`, e.g.
a development checkout, without copying it. Today it symlinks the package into the
venv (`site-packages/jazzoo -> <checkout>/src/jazzoo`), and writes the console scripts.
pip does not know about this link, because it has no package metadata. When the
developer runs `pip install jazzoo==0.2.0` in the venv, pip writes the new files through
the symlink, into the checkout, and a later `pip uninstall jazzoo` deletes files of the
checkout.

Instead, `create_venv` makes a linked install, as `pip install -e` does: package metadata
that pip reads, and an import hook that finds the linked package. Then pip treats the
link like any other install:

```
$ pip list | grep jazzoo
jazzoo  0.1.0  /home/me/projects/jazzoo/src/src/jazzoo
$ pip install jazzoo==0.2.0      # uninstalls the link, installs 0.2.0
$ pip uninstall jazzoo           # removes the link; the checkout is not touched
```

## The files of the linked install

`create_venv` writes these files to the venv, and no symlink:

- `site-packages/_jazzoo_link.pth`, with the line `import _jazzoo_link`. Python runs it
  when the venv starts.
- `site-packages/_jazzoo_link.py`, an import hook: it adds a finder to the end of
  `sys.meta_path` that finds the package `jazzoo`, and only that package, in the
  directory of the linked package. Its subpackages are found through the package itself.
- `site-packages/jazzoo-<version>.dist-info/`, with:
  - `METADATA`: the name `jazzoo` and the version of the linked jazzoo.
  - `INSTALLER`: `zoo`.
  - `entry_points.txt`: the console scripts `zoo`, `jaz`, `jazzoo` and `jaz-run`.
  - `direct_url.json`: the linked directory as an editable install (PEP 610), so that
    `pip list` shows where it points to.
  - `RECORD`: every file above, and the four console scripts in `bin`.
- `bin/zoo`, `bin/jaz`, `bin/jazzoo` and `bin/jaz-run`, as today.

## Decisions

- **No symlink, and nothing of the checkout in RECORD.** pip uninstalls a distribution by
  removing the files in its `RECORD`. These are only the files that `create_venv` wrote,
  so uninstalling never touches the linked directory.
- **An import hook, not a path in the .pth file.** A path line in a `.pth` file puts a
  whole directory on `sys.path`. For a checkout this is `src/`, but for a jazzoo that pip
  installed, it is the `site-packages` of another environment, which would leak all its
  packages into the venv. The finder only answers for `jazzoo`.
- **A real install wins.** The finder is at the end of `sys.meta_path`, after the finder of
  `sys.path`. Should a real `jazzoo` package end up in `site-packages` (e.g. installed
  with `pip install --no-deps --ignore-installed`), that one is imported.
- **The version.** The version in `METADATA` is the version of the linked jazzoo, read with
  `importlib.metadata`. It has no local label (such as `+linked`), so that `pip list`
  shows the real version. A consequence: `pip install jazzoo==<the same version>` says
  "Requirement already satisfied", because pip sees that version installed. To replace
  the link with the released package of the same version, the developer adds
  `--force-reinstall`.
- **The metadata of the linked jazzoo.** `importlib.metadata` may find the metadata of
  another jazzoo than the one that is linked, e.g. when a source tree on `PYTHONPATH`
  runs `zoo`, and a jazzoo is also installed with pip. The version is only taken from a
  distribution `jazzoo` that describes the linked directory:
  - a regular install, whose package is the linked directory;
  - an editable install (such as `pip install -e` of a checkout, or a linked install of
    zoo), whose `direct_url.json` points to the linked directory or to a directory that
    contains it.
- **No version found.** When no distribution describes the linked jazzoo (e.g. it runs
  from a source tree on `PYTHONPATH`), the version is `0.0.0`.
- **The version is not updated.** `METADATA` is written when the venv is created. When
  the version of the linked jazzoo changes later (e.g. a checkout moves to a new
  version), the venv keeps the old version until it is created again. `pip install -e`
  behaves the same.
- **pip freeze.** `pip freeze` shows the link as `-e <the linked directory>`. That is the
  directory of the package, not of a project, so `pip install -r` cannot install it
  again. This is accepted: zoo creates these venvs for development, not to be frozen.
- **A linked directory that is gone.** When the linked directory is moved or removed,
  the finder finds nothing, and the console scripts of the venv fail with
  `ModuleNotFoundError: No module named 'jazzoo'`. There is no extra hint: the venv is
  created again with `zoo env --forget <name>` and `zoo env --init --create-venv`.
- **What is linked.** The directory of the package that runs `zoo`
  (`os.path.dirname(jazzoo.__file__)`), as today. When that `zoo` runs in a venv with a
  linked install, this is the directory of the link, not a link to a link.
- **Venvs that zoo did not create.** `--use-venv` registers a venv in which jazzoo is
  installed with pip; zoo does not change it.
- **Existing venvs.** Venvs that were created with the symlink keep it. There is no
  migration command: zoo is new, and such a venv can be created again with
  `zoo env --forget <name>` and `zoo env --init --create-venv`, after removing `.venv`.
  `create_venv` itself already refuses an existing directory.
- **Tests of pip.** The tests that run pip in a venv are end-to-end tests in
  `e2e_tests/` (next to `tests/`). They use a real pip, offline: the newer jazzoo is a
  small wheel that the test builds, installed with `--no-index --find-links`. pip is
  required to run them; they are not skipped when `ensurepip` is missing.
- **A copy of jazzoo in the tests.** Tests that uninstall the link, or that need a
  jazzoo without package metadata, link a copy of the jazzoo package in `tmp_path`,
  not the checkout that runs the tests. zoo runs from that copy in a subprocess with
  `PYTHONPATH`. The package metadata of the test run is still visible there, but it
  does not describe the copy, so the version of the copy is `0.0.0`.
- **Where the code lives.** In `jazzoo/zoo/actions/create_venv.py`, which writes the files
  (the contents of `_jazzoo_link.py` and of the metadata files are templates in this
  module, like the console scripts). The version is read by the rule
  `jazzoo/zoo/rules/get_jazzoo_version.py`.
