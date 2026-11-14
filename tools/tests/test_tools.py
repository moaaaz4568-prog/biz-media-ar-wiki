"""Pytest entry: re-exports the test functions from run_all.py so both
`python3 tools/tests/run_all.py` and `pytest tools/tests` work."""

import importlib.util
import os

_spec = importlib.util.spec_from_file_location(
    'kf_run_all', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run_all.py'))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

for _name in dir(_mod):
    if _name.startswith('test_'):
        globals()[_name] = getattr(_mod, _name)
