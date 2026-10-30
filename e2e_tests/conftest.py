import os
import sys

# The e2e tests extend the test envs in tests/
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "tests")
)

# Test files whose code is not written yet
DISABLED_TEST_FILES = []

collect_ignore = DISABLED_TEST_FILES
