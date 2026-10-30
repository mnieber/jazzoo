import os
import typing as T

from jazzoo.settings import get_zoo_bin_dir, get_zoo_config_dir
from jazzoo.zoo.errors import FishFileExistsError
from jazzoo.zoo.rules.get_fish_config_dir import get_fish_config_dir

MANAGED_LINE = "# managed by zoo env --install-fish"

ZZ_FUNCTION = """{managed_line}
function zz --description "Switch to a zoo environment"
    # The zoo of the active env, or else the zoo of any registered env
    set -l zoo (command -s zoo)
    if test -z "$zoo"
        set zoo {bin_dir}/zoo-*
        set zoo $zoo[1]
    end
    if test -z "$zoo"
        echo "zz: no zoo found; register a project with zoo env --init" >&2
        return 1
    end

    # zoo env picks the activate script from SHELL, which is the login shell
    if test (count $argv) -eq 0
        SHELL=fish $zoo env --list
    else if contains -- --list $argv; or contains -- --forget $argv
        SHELL=fish $zoo env $argv
    else
        set -l lines (SHELL=fish $zoo env $argv)
        or return
        printf "%s\\n" $lines | source
    end
end
"""

ZZ_COMPLETIONS = """{managed_line}
complete -c zz -f -n __fish_is_first_arg -a "(zz --list --names) -"
"""

STARTUP = """{managed_line}
if status is-interactive; and test -f {latest}
    source {latest}
end
"""


def install_fish_files() -> T.List[str]:
    fish_dir = get_fish_config_dir()
    values = dict(
        managed_line=MANAGED_LINE,
        bin_dir=_quote(get_zoo_bin_dir()),
        latest=_quote(os.path.join(get_zoo_config_dir(), "latest.fish")),
    )
    texts = {
        os.path.join(fish_dir, "functions", "zz.fish"): ZZ_FUNCTION.format(**values),
        os.path.join(fish_dir, "completions", "zz.fish"): ZZ_COMPLETIONS.format(
            **values
        ),
        os.path.join(fish_dir, "conf.d", "zoo.fish"): STARTUP.format(**values),
    }

    # Nothing is written when a file of the developer is in the way
    foreign = [path for path in texts if os.path.exists(path) and not _is_managed(path)]
    if foreign:
        raise FishFileExistsError(
            "these files exist, and were not written by zoo env --install-fish; "
            "remove them first: " + ", ".join(foreign)
        )

    for path, text in texts.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    return list(texts)


def _is_managed(path: str) -> bool:
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.readline().rstrip("\n") == MANAGED_LINE


def _quote(path: str) -> str:
    # A single-quoted fish string, in which only \ and ' are escaped
    return "'" + path.replace("\\", "\\\\").replace("'", "\\'") + "'"
