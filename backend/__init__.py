"""Backend package bootstrap utilities.

This module ensures root-level imports such as ``import backend.app`` work
even when internal modules still import ``api``, ``core``, ``models``, and
``services`` as top-level packages.
"""

from __future__ import annotations

import sys
from pathlib import Path

_CURRENT_DIR = Path(__file__).resolve().parent
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))
