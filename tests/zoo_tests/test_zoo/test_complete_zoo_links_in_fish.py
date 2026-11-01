from zoo_tests.zoo_test_env import Context, TestEnv

# The jazzoo file of blog, whose targets differ from those of shop
BLOG_JAZZOO = """
publish():
    @echo "publish"
"""


def create_env(context: Context):
    return Env(context)


def test_complete_zoo_links_in_fish(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the registered projects shop and blog, and install the fish files.
    if env.step(
        env.add_project("shop", runnable_zoo=True),
        env.init_env("shop"),
        env.add_project("blog", BLOG_JAZZOO, runnable_zoo=True),
        env.init_env("blog"),
        env.run_zoo("env", "--install-fish"),
    ):
        pass

    # In fish, we switch to shop, and ask for the completions of `zoo-blog `.
    #
    # zoo-blog runs the zoo of blog, so they should be env and the targets of
    # blog, also while shop is active.
    if env.step(
        env.run_fish('zz shop\ncomplete -C "zoo-blog "\n'),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completions() == ["env", "publish"]

    # We ask for the completions of `zoo-shop gr`.
    #
    # They should be the matching target of shop.
    if env.step(
        env.run_fish('complete -C "zoo-shop gr"\n'),
    ):
        assert env.completions() == ["greet"]

    # We forget blog, which removes zoo-blog, and ask for the completions of
    # `zoo-blog ` in a new fish.
    #
    # The completions of the removed link should be gone.
    if env.step(
        env.run_zoo("env", "--forget", "blog"),
        env.run_fish('complete -C "zoo-blog "\n'),
    ):
        assert "publish" not in env.completions()
        assert "env" not in env.completions()

    # We also forget shop, so that no zoo-<name> link is left, and start a fish.
    #
    # The startup file should find no links, and print no errors.
    if env.step(
        env.run_zoo("env", "--forget", "shop"),
        env.run_fish("true\n"),
    ):
        assert env.completed.returncode == 0
        assert env.completed.stderr == ""


class Env(TestEnv):
    # Queries

    def completions(self):
        # A completion may have a description after a tab
        return sorted(line.split("\t")[0] for line in self.fish_lines())
