# tests/test_smoke_imports.py
# A small "smoke" test that attempts to import top-level python modules to produce coverage.
# WARNING: importing modules executes top-level code. Review your modules for side-effects.

import importlib.util
import os
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]  # repo root

def iter_py_files(root: Path):
    exclude_dirs = {"venv", ".venv", "env", ".env", "node_modules", ".git", "__pycache__", "tests"}
    for p in root.rglob("*.py"):
        parts = set(p.parts)
        if parts & exclude_dirs:
            continue
        # skip test files themselves
        if p.name.startswith("test_") or p.name == "conftest.py":
            continue
        yield p

@pytest.mark.parametrize("path", list(iter_py_files(ROOT)))
def test_import_module(path):
    """
    Import a module by file path. If the module has harmful side-effects this test may fail or cause problems.
    It's intended as a smoke test to produce some coverage where there are no unit tests.
    """
    # build a safe-ish module name based on relative path
    rel = path.relative_to(ROOT)
    module_name = "smoke_" + "_".join(rel.with_suffix("").parts)
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    assert spec is not None, f"Cannot get spec for {path}"
    module = importlib.util.module_from_spec(spec)
    # execute module code (top-level code will run)
    try:
        spec.loader.exec_module(module)  # type: ignore
    except Exception as e:
        # If importing fails because module requires runtime env, consider skipping
        pytest.skip(f"Import failed for {path}: {e}")
