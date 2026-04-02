"""
Shared fixtures and configuration for the Quantum MCAGI test suite.
"""

import sys
import os
import pytest

# Ensure backend/ is on sys.path so tests can import modules directly
backend_dir = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.insert(0, os.path.abspath(backend_dir))
