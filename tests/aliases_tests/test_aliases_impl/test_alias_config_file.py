import os

from aliases_tests.aliases_test_env import Context, TestEnv

from jazzoo import JazzooError


def create_env(context: Context):
    return Env(context)


def test_alias_config_file(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a project, an alias x in $XDG_CONFIG_HOME/jazzoo/config, and an
    # alias h in ~/.config/jazzoo/config. We set XDG_CONFIG_HOME.
    if env.step(
        env.write_jazzoo(),
        env.write_aliases("[alias]\nx = build mode=xdg\n", path="xdg/jazzoo/config"),
        env.write_aliases("[alias]\nh = build mode=home\n"),
        env.set_env("XDG_CONFIG_HOME", env.path("xdg")),
    ):
        pass

    # We run jaz x and jaz h.
    #
    # The aliases should be read from $XDG_CONFIG_HOME/jazzoo/config, and
    # ~/.config/jazzoo/config should be ignored.
    if env.step(
        env.run_jaz("x"),
    ):
        assert env.output_lines() == ["build mode=xdg"]

    if env.step(
        env.run_jaz_and_catch_error("h"),
    ):
        assert isinstance(env.error, JazzooError)
        assert env.error.message == "no such target: h"

    # We set XDG_CONFIG_HOME to an empty value, and run jaz h.
    #
    # The aliases should be read from ~/.config/jazzoo/config.
    if env.step(
        env.set_env("XDG_CONFIG_HOME", ""),
        env.run_jaz("h"),
    ):
        assert env.output_lines() == ["build mode=home"]

    # We write ~/.jazzoo.config with an alias j, and run jaz j.
    #
    # ~/.jazzoo.config is not read, so j should not be an alias.
    if env.step(
        env.write_aliases("[alias]\nj = build\n", path="home/.jazzoo.config"),
        env.run_jaz_and_catch_error("j"),
    ):
        assert isinstance(env.error, JazzooError)
        assert env.error.message == "no such target: j"

    # We remove ~/.config/jazzoo/config, and run jaz h.
    #
    # Without a config file there are no aliases, so this should be the usual
    # error.
    if env.step(
        env.remove_file("home/.config/jazzoo/config"),
        env.run_jaz_and_catch_error("h"),
    ):
        assert isinstance(env.error, JazzooError)
        assert env.error.message == "no such target: h"

    # We write a config file without an [alias] section, and run jaz h.
    #
    # Other sections are ignored, so h should not be an alias.
    if env.step(
        env.write_aliases("[core]\nh = build\n"),
        env.run_jaz_and_catch_error("h"),
    ):
        assert isinstance(env.error, JazzooError)
        assert env.error.message == "no such target: h"

    # We write a config file with the alias h in a [DEFAULT] section, and run jaz h.
    #
    # [DEFAULT] is an ordinary section, whose keys do not end up in [alias].
    if env.step(
        env.write_aliases("[DEFAULT]\nh = build\n\n[alias]\nb = build\n"),
        env.run_jaz_and_catch_error("h"),
    ):
        assert isinstance(env.error, JazzooError)
        assert env.error.message == "no such target: h"

    # We add an [alias] section next to the other section, and run jaz h.
    #
    # The alias should be found.
    if env.step(
        env.write_aliases("[core]\nh = greet\n\n[alias]\nh = build mode=home\n"),
        env.run_jaz("h"),
    ):
        assert env.output_lines() == ["build mode=home"]


class Env(TestEnv):
    def remove_file(self, name: str):
        os.remove(self.path(name))
