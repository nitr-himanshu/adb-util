"""
Setup script for adb-util package.

This file provides backward compatibility with older pip versions
that don't support pyproject.toml. For modern installations,
use pip install -e . which will use pyproject.toml.
"""

from setuptools import setup

# This setup.py is minimal and delegates to pyproject.toml
# For full configuration, see pyproject.toml
if __name__ == "__main__":
    setup()
