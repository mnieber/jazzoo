from zoo_tests.zoo_test_env import Context, TestEnv

# The jazzoo file of shop, with the layer fe
JAZZOO = """
from ./fe.jaz export (build, test) as fe

build(mode="debug"):
    @echo "build mode=🐆.mode"

deploy():
    @echo "deploy"
"""

FE_JAZ = """
build():
    @echo "fe.build"

test():
    @echo "fe.test"
"""


def create_env(context: Context):
    return Env(context)


def test_complete_in_fish(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the registered projects shop and blog, and install the fish files.
    if env.step(
        env.add_project("shop", JAZZOO, runnable_zoo=True),
        env.write_file("projects/shop/fe.jaz", FE_JAZ),
        env.init_env("shop"),
        env.add_project("blog", runnable_zoo=True),
        env.init_env("blog"),
        env.run_zoo("env", "--install-fish"),
    ):
        pass

    # In fish, we switch to shop, go to its directory, and ask for the
    # completions of `jaz `.
    #
    # They should be the targets and the layer of shop, and build should have its
    # signature as description.
    if env.step(
        env.run_fish_in_shop('complete -C "jaz "'),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completions() == ["build", "deploy", "fe."]
        assert 'build\tbuild(mode="debug")' in env.fish_lines()

    # We ask for the completions of `jazzoo fe.`.
    #
    # jazzoo is the same program as jaz, so they should be the members of fe.
    if env.step(
        env.run_fish_in_shop('complete -C "jazzoo fe."'),
    ):
        assert env.completions() == ["fe.build", "fe.test"]

    # We ask for the completions of `zoo `.
    #
    # They should be env, and the targets and the layer of shop.
    if env.step(
        env.run_fish_in_shop('complete -C "zoo "'),
    ):
        assert env.completions() == ["build", "deploy", "env", "fe."]

    # We ask for the completions of `zoo env `.
    #
    # They should include the names of the envs, and `-` for the previous env.
    if env.step(
        env.run_fish_in_shop('complete -C "zoo env "'),
    ):
        assert {"-", "blog", "shop"} <= set(env.completions())

    # We ask for the completions of `jaz build mode=`.
    #
    # They should be the files of the current directory, after `mode=`.
    if env.step(
        env.run_fish_in_shop('complete -C "jaz build mode="'),
    ):
        assert "mode=fe.jaz" in env.completions()
        assert "mode=jazzoo" in env.completions()


class Env(TestEnv):
    def run_fish_in_shop(self, script: str):
        """Runs script in a new fish, after switching to shop with zz and changing
        to its directory."""
        self.run_fish(f"zz shop\ncd {self.path('projects/shop')}\n{script}\n")

    # Queries

    def completions(self):
        # A completion may have a description after a tab
        return sorted(line.split("\t")[0] for line in self.fish_lines())
