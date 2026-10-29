# The test packages are enabled in the order in which their code is implemented
ENABLED_TEST_PACKAGES = [
    "config_tests",
    "commands_tests",
    "interactive_tests",
]

ALL_TEST_PACKAGES = [
    "config_tests",
    "commands_tests",
    "interactive_tests",
    "confirm_tests",
]

# Test files whose code is not written yet
DISABLED_TEST_FILES = [
    # run confirms
    "commands_tests/test_commands/test_script_confirms_commands.py",
    "commands_tests/test_commands_impl/test_confirm_answers.py",
    "commands_tests/test_commands_impl/test_confirm_errors.py",
    "commands_tests/test_commands_impl/test_confirm_prompt.py",
    "commands_tests/test_commands_impl/test_confirm_skip.py",
    "commands_tests/test_commands_impl/test_confirm_switch.py",
    # jaz-run
    "commands_tests/test_commands/test_shell_script_runs_commands.py",
    "commands_tests/test_commands_impl/test_commands_vendoring.py",
    "commands_tests/test_commands_impl/test_jaz_run_arguments.py",
    "commands_tests/test_commands_impl/test_jaz_run_confirm.py",
    "commands_tests/test_commands_impl/test_jaz_run_exit_codes.py",
]

collect_ignore = [
    package for package in ALL_TEST_PACKAGES if package not in ENABLED_TEST_PACKAGES
] + DISABLED_TEST_FILES
