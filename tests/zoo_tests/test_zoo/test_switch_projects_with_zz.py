from zoo_tests.zoo_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_switch_projects_with_zz(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the registered projects shop and blog, and install the fish files.
    if env.step(
        env.add_project("shop", runnable_zoo=True),
        env.init_env("shop"),
        env.add_project("blog", runnable_zoo=True),
        env.init_env("blog"),
        env.run_zoo("env", "--install-fish"),
    ):
        pass

    # In fish, we run `zz shop`.
    #
    # zz should source the line that zoo prints, which activates shop and its
    # venv in this shell. SHELL is /bin/bash, the login shell, so zz should tell
    # zoo that it runs in fish, to get the fish activate script.
    if env.step(
        env.run_fish(
            """
            zz shop
            echo $JAZZOO_ENV
            echo $VIRTUAL_ENV
            """
        ),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.fish_lines() == ["shop", env.path("projects/shop/.venv")]

    # We switch to blog, and then back with `zz -`.
    #
    # Like `cd -`, `zz -` should go back to the previous env, which is shop.
    if env.step(
        env.run_fish(
            """
            zz shop
            zz blog
            zz -
            echo $JAZZOO_ENV
            """
        ),
    ):
        assert env.fish_lines() == ["shop"]

    # We run zz without arguments, while shop is active.
    #
    # It should list the envs, with shop marked as the active one.
    if env.step(
        env.run_fish(
            """
            zz shop
            zz
            """
        ),
    ):
        assert env.fish_lines() == [
            "  blog  " + env.path("projects/blog"),
            "* shop  " + env.path("projects/shop"),
        ]

    # We ask fish for the completions of `zz `.
    #
    # They should be the names of the envs, and `-` for the previous env.
    if env.step(
        env.run_fish('complete -C "zz "'),
    ):
        assert env.completions() == ["-", "blog", "shop"]


class Env(TestEnv):
    # Queries

    def completions(self):
        # A completion may have a description after a tab
        return sorted(line.split("\t")[0] for line in self.fish_lines())
