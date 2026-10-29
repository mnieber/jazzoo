from zoo_tests.zoo_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_latest_env_scripts(context: Context):
    # Create the test environment
    env = create_env(context)

    # We look at the registry before any env was activated.
    #
    # There should be no latest-env scripts yet.
    if env.step():
        assert not env.exists(env.latest_script("bash"))
        assert not env.exists(env.latest_script("fish"))

    # We register the projects shop and blog, and activate shop in bash.
    #
    # Both latest-env scripts should source the activate script of shop for
    # their shell, if it still exists. The fish one is written too, although we
    # use bash.
    if env.step(
        env.add_project("shop"),
        env.init_env("shop"),
        env.add_project("blog"),
        env.init_env("blog"),
        env.run_zoo("env", "shop"),
    ):
        assert env.read_lines(env.latest_script("bash")) == env.bash_lines("shop")
        assert env.read_lines(env.latest_script("fish")) == env.fish_lines("shop")

    # We activate blog.
    #
    # Both scripts should now source the activate script of blog.
    if env.step(
        env.run_zoo("env", "blog"),
    ):
        assert env.read_lines(env.latest_script("bash")) == env.bash_lines("blog")
        assert env.read_lines(env.latest_script("fish")) == env.fish_lines("blog")

    # We go back to the previous env.
    if env.step(
        env.run_zoo("env", "-"),
    ):
        assert env.read_lines(env.latest_script("bash")) == env.bash_lines("shop")
        assert env.read_lines(env.latest_script("fish")) == env.fish_lines("shop")

    # We forget blog, which is not the latest env.
    #
    # The scripts should be left alone.
    if env.step(
        env.run_zoo("env", "--forget", "blog"),
    ):
        assert env.read_lines(env.latest_script("bash")) == env.bash_lines("shop")

    # We forget shop, which is the latest env.
    #
    # The scripts should no longer source anything, so that a new terminal
    # starts without an env.
    if env.step(
        env.run_zoo("env", "--forget", "shop"),
    ):
        assert "source" not in env.read_file(env.latest_script("bash"))
        assert "source" not in env.read_file(env.latest_script("fish"))


class Env(TestEnv):
    # Queries

    def latest_script(self, shell: str) -> str:
        return f"{self.config_dir()}/latest.{shell}"

    def bash_lines(self, name: str):
        activate = f"{self.env_dir(name)}/activate.bash"
        return [f"[ -f {activate} ] && source {activate}"]

    def fish_lines(self, name: str):
        activate = f"{self.env_dir(name)}/activate.fish"
        return [f"test -f {activate}; and source {activate}"]
