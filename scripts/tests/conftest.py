import importlib.util
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


validator = _load("validate_odyssey_task")
leaks = _load("scan_bundle_leaks")
novelty = _load("check_novelty")
difficulty = _load("check_difficulty_design")
