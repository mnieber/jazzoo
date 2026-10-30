# The test packages are enabled in the order in which their code is implemented
ENABLED_TEST_PACKAGES = [
    "config_tests",
    "commands_tests",
    "interactive_tests",
    "confirm_tests",
    "zoo_tests",
    "docker_tests",
    "aliases_tests",
    "completions_tests",
    "which_tests",
]

ALL_TEST_PACKAGES = [
    "config_tests",
    "commands_tests",
    "interactive_tests",
    "confirm_tests",
    "zoo_tests",
    "docker_tests",
    "aliases_tests",
    "completions_tests",
    "which_tests",
]

# Test files whose code is not written yet
DISABLED_TEST_FILES = []

collect_ignore = [
    package for package in ALL_TEST_PACKAGES if package not in ENABLED_TEST_PACKAGES
] + DISABLED_TEST_FILES
