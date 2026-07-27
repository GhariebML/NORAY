"""
_module_loader.py
=================
Small helper to import the numbered pipeline files (01_documents.py,
02_preprocessing.py, ...) as regular Python modules.

Python's `import` statement cannot import a module whose name starts
with a digit (e.g. `import 01_documents` is a SyntaxError), but the
lab spec requires these exact filenames. This helper loads them by
file path instead, so every other file just does:

    from _module_loader import load_module
    documents_mod = load_module("01_documents")
    docs = documents_mod.load_documents()
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_BASE_DIR = Path(__file__).parent


def load_module(filename_without_ext: str):
    """Loads e.g. '03_chunking' -> the module defined in 03_chunking.py,
    caching it in sys.modules so repeated calls are cheap."""
    if filename_without_ext in sys.modules:
        return sys.modules[filename_without_ext]

    path = _BASE_DIR / f"{filename_without_ext}.py"
    if not path.exists():
        raise FileNotFoundError(f"Pipeline module not found: {path}")

    spec = importlib.util.spec_from_file_location(filename_without_ext, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[filename_without_ext] = module
    spec.loader.exec_module(module)
    return module
