import os
import sys

# The e2e tests extend the test envs in tests/
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "tests")
)

# Test files whose code is not written yet
DISABLED_TEST_FILES = [
    "zoo_e2e_tests/test_zoo_e2e/test_replace_the_linked_jazzoo_with_pip.py",
    "zoo_e2e_tests/test_zoo_e2e_impl/test_pip_uninstall_the_link.py",
    "zoo_e2e_tests/test_zoo_e2e_impl/test_pip_install_the_same_version.py",
]

collect_ignore = DISABLED_TEST_FILES
