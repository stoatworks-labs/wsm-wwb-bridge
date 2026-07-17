#!/bin/bash
# Runs the full test suite. -t . (top-level dir = project root) is required
# so the tests/ package resolves correctly for the relative imports some
# test modules use to share fixture data (e.g. test_detect.py importing
# sample XML from test_wwb_xml.py) -- plain `unittest discover -s tests`
# without it fails with "attempted relative import with no known parent
# package".
cd "$(dirname "$0")"
python3 -m unittest discover -s tests -t . -v
