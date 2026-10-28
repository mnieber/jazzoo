from config_tests.config_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


# get_config caches the config per list of files, so every step writes files with
# new names.
def test_merging(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have three config files that each set part of the server section.
    #
    # The dicts should be merged recursively, and a later file should win.
    if env.step(
        env.write_config(
            "server_a.yaml",
            """
            server:
              host: a.example.com
              port: 8001
              tls:
                cert: a.pem
            """,
        ),
        env.write_config(
            "server_b.yaml",
            """
            server:
              port: 8002
              tls:
                key: b.key
            """,
        ),
        env.write_config(
            "server_c.yaml",
            """
            server:
              host: c.example.com
            """,
        ),
        env.use_config_files("server_a.yaml", "server_b.yaml", "server_c.yaml"),
        env.get("/server"),
    ):
        assert env.value == {
            "host": "c.example.com",
            "port": 8002,
            "tls": {"cert": "a.pem", "key": "b.key"},
        }

    # We have two config files that both set a list of tags.
    #
    # The later list should replace the earlier one.
    if env.step(
        env.write_config("tags_a.yaml", "tags: [web, api]\n"),
        env.write_config("tags_b.yaml", "tags: [worker]\n"),
        env.use_config_files("tags_a.yaml", "tags_b.yaml"),
        env.get("/tags"),
    ):
        assert env.value == ["worker"]

    # A later config file sets the tls section to null.
    #
    # The null should replace the earlier value, and the key should still exist.
    if env.step(
        env.write_config("tls_a.yaml", "server:\n  tls:\n    cert: a.pem\n"),
        env.write_config("tls_b.yaml", "server:\n  tls: null\n"),
        env.use_config_files("tls_a.yaml", "tls_b.yaml"),
        env.get("/server"),
    ):
        assert env.value == {"tls": None}

    # A later config file replaces the database dict with a string.
    #
    # The string should replace the dict.
    if env.step(
        env.write_config("db_dict.yaml", "database:\n  host: localhost\n"),
        env.write_config("db_str.yaml", "database: sqlite\n"),
        env.use_config_files("db_dict.yaml", "db_str.yaml"),
        env.get("/database"),
    ):
        assert env.value == "sqlite"

    # In the opposite order, a dict replaces the string.
    #
    # The dict should replace the string.
    if env.step(
        env.use_config_files("db_str.yaml", "db_dict.yaml"),
        env.get("/database"),
    ):
        assert env.value == {"host": "localhost"}

    # One of the config files is empty.
    #
    # It should count as an empty dict.
    if env.step(
        env.write_config("empty.yaml", ""),
        env.use_config_files("db_dict.yaml", "empty.yaml"),
        env.get("/"),
    ):
        assert env.value == {"database": {"host": "localhost"}}

    # JAZZOO_CONFIG_FILES is unset.
    #
    # The config should be empty.
    if env.step(
        env.unset_env("JAZZOO_CONFIG_FILES"),
        env.get("/"),
    ):
        assert env.value == {}

    # JAZZOO_CONFIG_FILES is empty.
    #
    # The config should be empty.
    if env.step(
        env.set_env("JAZZOO_CONFIG_FILES", ""),
        env.get("/"),
    ):
        assert env.value == {}


class Env(TestEnv):
    pass
