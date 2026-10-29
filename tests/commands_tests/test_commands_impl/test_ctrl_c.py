from commands_tests.commands_test_env import Context, TestEnv

# Each script runs in its own session (see run_python_script), so `kill -INT 0`
# sends SIGINT to the script and its command, as a ctrl-c in a terminal does.

# The command sends SIGINT to its parent, the script, and then ends normally
PARENT_SIGNALED_SCRIPT = """
from jazzoo.commands import run

run("kill -INT $PPID; sleep 0.2")
print("survived", flush=True)
"""

# A ctrl-c reaches the whole process group: the script and its command
CTRL_C_SCRIPT = """
from jazzoo.commands import run

try:
    run("kill -INT 0; sleep 2; echo not-interrupted")
except KeyboardInterrupt:
    print("interrupted", flush=True)
"""

CTRL_C_CAPTURED_SCRIPT = """
from jazzoo.commands import run

try:
    run("kill -INT 0; sleep 2; echo not-interrupted", capture=True)
except KeyboardInterrupt:
    print("interrupted", flush=True)
"""

HANDLER_RESTORED_SCRIPT = """
import signal

from jazzoo.commands import run


def on_sigint(signum, frame):
    pass


signal.signal(signal.SIGINT, on_sigint)
run("true")
print("restored" if signal.getsignal(signal.SIGINT) is on_sigint else "changed")
"""

THREAD_SCRIPT = """
import signal
import threading

from jazzoo.commands import run

handlers = []


def in_thread():
    result = run("echo from-thread", capture=True)
    handlers.append(signal.getsignal(signal.SIGINT))
    print(result.stdout, end="", flush=True)


thread = threading.Thread(target=in_thread)
thread.start()
thread.join()
print("untouched" if handlers == [signal.default_int_handler] else "touched")
"""


def create_env(context: Context):
    return Env(context)


def test_ctrl_c(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a script whose command sends SIGINT to the script, and then ends
    # normally. We run the script.
    #
    # While the command runs, the script should ignore SIGINT, so it survives, and
    # run returns normally.
    if env.step(
        env.write_file("parent_signaled.py", PARENT_SIGNALED_SCRIPT),
        env.run_python_script("parent_signaled.py"),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completed.stdout == "survived\n"

    # We have a script whose command sends SIGINT to the whole process group, as
    # a ctrl-c does. We run the script.
    #
    # The command should be interrupted (the script must not have passed on its
    # ignored SIGINT to the command), and run should raise KeyboardInterrupt.
    if env.step(
        env.write_file("ctrl_c.py", CTRL_C_SCRIPT),
        env.run_python_script("ctrl_c.py"),
    ):
        assert env.completed.stdout == "interrupted\n"

    # We do the same with a captured command.
    #
    # The same rules should apply.
    if env.step(
        env.write_file("ctrl_c_captured.py", CTRL_C_CAPTURED_SCRIPT),
        env.run_python_script("ctrl_c_captured.py"),
    ):
        assert env.completed.stdout == "interrupted\n"

    # We have a script that installs its own SIGINT handler and runs a command.
    #
    # After run, the script's own handler should be back.
    if env.step(
        env.write_file("handler_restored.py", HANDLER_RESTORED_SCRIPT),
        env.run_python_script("handler_restored.py"),
    ):
        assert env.completed.stdout == "restored\n"

    # We have a script that runs a command in a thread other than the main thread.
    #
    # The command should run, and run should leave the SIGINT handler alone.
    if env.step(
        env.write_file("thread.py", THREAD_SCRIPT),
        env.run_python_script("thread.py"),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completed.stdout == "from-thread\nuntouched\n"


class Env(TestEnv):
    pass
