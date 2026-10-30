# Aliases

A developer defines short names for targets that they run often, in a personal
config file `~/.config/jazzoo/config`:

```ini
# ~/.config/jazzoo/config
[alias]
b = build
fb = fe.build mode=debug
dep = deploy --confirm
```

`jaz` looks up an alias when the target on the command line does not exist, and
substitutes the alias's expansion for it:

```
$ jaz b                  # runs: jaz build
$ jaz fb                 # runs: jaz fe.build mode=debug
$ jaz fb mode=release    # runs: jaz fe.build mode=release
$ jaz dep staging        # runs: jaz deploy staging --confirm
```

This works like the aliases of git and dodo-commands. The aliases are personal: they
live in the developer's home directory, and apply to every Jazzoo file that the
developer runs.

## The expansion

The expansion of an alias is split into tokens as in a shell (`shlex.split`). The
first token is the target, a dotted path (`fe.build`) like on the command line. The
other tokens are arguments (`name=value`, or a positional argument for the first
parameter), and options of `jaz` (`--confirm`, `--trace`).

`jaz` replaces the alias with its expansion, and then processes the command line as
usual: `jaz dep staging` runs exactly what `jaz deploy staging --confirm` runs.

## Decisions

- **Targets win.** An alias is only looked up when the root module has no target with
  that name (as git does, and unlike dodo-commands, where an alias wins). So an alias
  never changes what an existing target does, and a Jazzoo file that later adds a
  target with the same name as an alias shadows the alias. Shadowing is silent.
- **Only the target is expanded.** Only the token that names the target can be an
  alias, not an argument or an option. `jaz --list <path>` and `jaz --list-all` do not
  expand aliases: they describe the Jazzoo file.
- **The user's arguments win.** The arguments in the expansion act as presets: an
  argument on the command line overrides an argument of the expansion for the same
  parameter, also when one of them is given positionally (it names the first
  parameter). In `jaz fb mode=release`, `mode` is `release`; when the expansion has
  `target=a` and the command line a positional `b`, `target` is `b`, without an error. A positional argument on
  the command line may follow the arguments of the expansion: the rule that a
  positional argument comes first applies to the command line and to the expansion
  separately. Within the expansion, and within the command line, the usual rules hold
  (e.g. naming a parameter both positionally and by name is an error).
- **Options combine.** The options of the expansion are added to those on the command
  line. `jaz --trace dep` runs `deploy` with `--trace` and `--confirm`. An option that
  is given twice counts once. The check that `--confirm` needs a terminal happens
  after the alias is expanded, so it also covers a `--confirm` in an expansion. `--file` is not allowed in an expansion: an alias names
  a target, and the file is chosen by the directory where `jaz` runs. `--list`,
  `--list-all` and `--help` are not allowed either.
- **No chaining.** The target of an expansion must be a real target; it is not looked
  up as an alias again. This avoids cycles, and keeps aliases simple to read.
- **Unknown targets.** A name that is neither a target nor an alias is
  `no such target: <name>`, as before. When the target of an expansion does not exist
  in the Jazzoo file (aliases are shared by all files), the error names both:
  `no such target: build (the expansion of alias "b")`.
- **The file format.** The config file is an INI file, as git and dodo-commands
  use, read with the standard library (`configparser`). Aliases go in the `[alias]`
  section; other sections are ignored, so that later features can add their own.
  Alias names are case-sensitive. An alias name follows the rules of a target path:
  a name that does not makes the whole file an error, also when another alias is
  looked up, so that a typo does not go unnoticed. An expansion that is empty is an
  error. There is no interpolation: a `%` in an expansion is taken as it is. An alias
  that is defined twice makes the file malformed.
- **A missing file.** When the config file does not exist, there are no aliases.
  The file is only read when the target on the command line does not exist, so a
  broken config file does not affect `jaz` when no alias is needed.
- **Errors.** An unreadable or malformed config file, an empty expansion, an
  expansion with unbalanced quotes, and an expansion with a forbidden option are a
  `AliasError` (a `JazzooError`) that names the config file and, where it applies,
  the alias.
- **Where the code lives.** In the feature package `jazzoo.aliases`:
  `rules/get_alias_config_file.py` (the path of the config file),
  `rules/read_aliases.py` (reads the `[alias]` section), `rules/expand_alias.py`
  (turns an alias into a target, arguments and options), and `errors.py`
  (`AliasError`).
- **The location.** The file is `config` in the Jazzoo config directory, next to the
  zoo registry: `$XDG_CONFIG_HOME/jazzoo/config`, or `~/.config/jazzoo/config` when
  `XDG_CONFIG_HOME` is unset or empty (`~` is taken from `HOME`). There is no other
  location.
- **No listing.** `jaz --list` does not show aliases, and there is no option to list
  them: they are in one file that the developer wrote.
- **Only `jaz`.** Aliases apply to the targets of `jaz`. The `zoo` command does not
  use them.
