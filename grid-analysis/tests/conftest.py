"""
Shared pytest fixtures for the grid-analysis test suite.

Puts tasks/ on sys.path (so tests can `import task_1_1_data_cleaning` etc.
the same way the scripts import their own `report_utils` sibling), and
provides a session-scoped fixture that runs the real pipeline end-to-end via
subprocess - the same way a student actually invokes it per the README - so
integration tests exercise the real CLI entry points, not just internal
functions.
"""
import os
import subprocess
import sys

import pytest

GRID_ANALYSIS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS_DIR = os.path.join(GRID_ANALYSIS_DIR, "tasks")
DATA_DIR = os.path.join(GRID_ANALYSIS_DIR, "data")
CLEAN_DIR = os.path.join(DATA_DIR, "cleaned")
INTEGRATED_DIR = os.path.join(DATA_DIR, "integrated")
REPORTS_DIR = os.path.join(GRID_ANALYSIS_DIR, "reports")

sys.path.insert(0, TASKS_DIR)


def run_script(relative_path):
    result = subprocess.run(
        [sys.executable, relative_path],
        cwd=GRID_ANALYSIS_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"{relative_path} exited with {result.returncode}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    return result


@pytest.fixture(scope="session")
def run_pipeline_script():
    """Exposes run_script() to test functions that need to re-invoke a
    pipeline stage on demand (e.g. reproducibility checks)."""
    return run_script


@pytest.fixture(scope="session")
def pipeline():
    """Run generate_dataset.py -> Task 1.1 -> Task 1.2 -> Task 1.3 once per
    test session, exactly as the README instructs, and hand back the key
    directories so tests can inspect the real output files."""
    run_script("generate_dataset.py")
    run_script(os.path.join("tasks", "task_1_1_data_cleaning.py"))
    run_script(os.path.join("tasks", "task_1_2_eda.py"))
    run_script(os.path.join("tasks", "task_1_3_data_integration.py"))
    return {
        "raw": DATA_DIR,
        "clean": CLEAN_DIR,
        "integrated": INTEGRATED_DIR,
        "reports": REPORTS_DIR,
    }
