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
    "zoo_tests/test_zoo_impl/test_list_names.py",
    "zoo_tests/test_zoo_impl/test_install_fish_usage_errors.py",
    "zoo_tests/test_zoo/test_install_the_fish_shortcut.py",
    "zoo_tests/test_zoo_impl/test_install_fish_errors.py",
    "zoo_tests/test_zoo_impl/test_install_fish_locations.py",
    "zoo_tests/test_zoo/test_switch_projects_with_zz.py",
    "zoo_tests/test_zoo_impl/test_zz_errors.py",
    "zoo_tests/test_zoo_impl/test_zz_finds_zoo.py",
    "zoo_tests/test_zoo_impl/test_fish_startup.py",
]

collect_ignore = [
    package for package in ALL_TEST_PACKAGES if package not in ENABLED_TEST_PACKAGES
] + DISABLED_TEST_FILES
