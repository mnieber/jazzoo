# The test packages are enabled in the order in which their code is implemented
ENABLED_TEST_PACKAGES = [
    "config_tests",
    "commands_tests",
    "interactive_tests",
    "confirm_tests",
    "zoo_tests",
    "docker_tests",
]

ALL_TEST_PACKAGES = [
    "config_tests",
    "commands_tests",
    "interactive_tests",
    "confirm_tests",
    "zoo_tests",
    "docker_tests",
]

# Test files whose code is not written yet
DISABLED_TEST_FILES = [
    "interactive_tests/test_interactive_impl/test_attribute_lists.py",
]

collect_ignore = [
    package for package in ALL_TEST_PACKAGES if package not in ENABLED_TEST_PACKAGES
] + DISABLED_TEST_FILES
