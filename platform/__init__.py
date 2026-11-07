"""Platform integration module for Keyboard Shotgun.

Preserves compatibility with Python's standard library `platform` module
while exposing platform-specific modules `windows` and `macos`.
"""

import sys
import importlib
import importlib.machinery
import importlib.util

# Load the real standard library platform module to prevent shadowing breakages
_stdlib_spec = None
for _p in sys.path:
    if _p and _p not in (".", sys.path[0]):
        try:
            _finder = importlib.machinery.PathFinder.find_spec("platform", [_p])
            if _finder and _finder.origin and "site-packages" not in _finder.origin:
                _stdlib_spec = _finder
                break
        except Exception:
            pass

if _stdlib_spec and _stdlib_spec.loader:
    _real_platform = importlib.util.module_from_spec(_stdlib_spec)
    _stdlib_spec.loader.exec_module(_real_platform)
    for _attr in dir(_real_platform):
        if not _attr.startswith("__") or _attr in ("__doc__",):
            globals()[_attr] = getattr(_real_platform, _attr)

