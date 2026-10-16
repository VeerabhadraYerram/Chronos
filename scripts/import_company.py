#!/usr/bin/env python3
"""Import an explicitly supplied local company data pack without touching prior graphs."""

import argparse
import json
from pathlib import Path
from chronos.company.importer import import_workspace

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("file", type=Path)
args = parser.parse_args()
workspace = import_workspace(json.loads(args.file.read_text()))
print("Imported new isolated workspace: " + workspace)
print("Inspection link: http://127.0.0.1:8000/database#workspace=" + workspace)
print("Prototype link: http://127.0.0.1:5173/?workspace=" + workspace)
