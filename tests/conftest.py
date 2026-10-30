# The test packages are enabled in the order in which their code is implemented
ENABLED_TEST_PACKAGES = [
    "config_tests",
    "commands_tests",
    "interactive_tests",
    "confirm_tests",
    "zoo_tests",
    "docker_tests",
    "aliases_tests",
]

ALL_TEST_PACKAGES = [
    "config_tests",
    "commands_tests",
    "interactive_tests",
    "confirm_tests",
    "zoo_tests",
    "docker_tests",
    "aliases_tests",
]

# Test files whose code is not written yet
DISABLED_TEST_FILES = [
    "zoo_tests/test_zoo/test_create_a_venv.py",
    "zoo_tests/test_zoo_impl/test_linked_install_metadata.py",
    "zoo_tests/test_zoo_impl/test_linked_import_hook.py",
    "zoo_tests/test_zoo_impl/test_link_of_a_link.py",
    "zoo_tests/test_zoo_impl/test_linked_source_tree.py",
]

collect_ignore = [
    package for package in ALL_TEST_PACKAGES if package not in ENABLED_TEST_PACKAGES
] + DISABLED_TEST_FILES
