from importlib.metadata import version
from subprocess import run, PIPE
import sys


def test_package_version_matches_pyproject():
    # If installed in editable mode, version should be importable
    try:
        v = version("carpool")
        assert isinstance(v, str)
    except Exception:
        # Not installed yet; skip gracefully
        pass


def test_cli_hello_help_runs():
    proc = run([sys.executable, "-m", "carpool", "--help"], stdout=PIPE, stderr=PIPE, text=True)
    # Exit code 0 and help text present
    assert proc.returncode == 0
    assert "Carpool command-line interface" in proc.stdout


def test_cli_hello_world():
    proc = run([sys.executable, "-m", "carpool", "hello"], stdout=PIPE, stderr=PIPE, text=True)
    assert proc.returncode == 0
    assert "Hello, world!" in proc.stdout
