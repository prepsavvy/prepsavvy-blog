"""Verify source bundle integrity and independently reproduce every school row."""
import csv
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[1]
data=root/'data'/'2026-10-23'
manifest=json.loads((data/'manifest.json').read_text(encoding='utf-8'))
for name,digest in manifest['files'].items():
    assert hashlib.sha256((data/name).read_bytes()).hexdigest()==digest, name
subprocess.run([sys.executable,'calculate.py'],cwd=data,check=True)
reference=list(csv.DictReader((data/'schools.csv').open(encoding='utf-8')))
actual=list(csv.DictReader((data/'reproduced-schools.csv').open(encoding='utf-8')))
assert len(reference)==len(actual)==112
for expected,observed in zip(reference,actual):
    for key,value in expected.items():
        if value==observed[key]:continue
        try: assert math.isclose(float(value),float(observed[key]),rel_tol=1e-8,abs_tol=1e-8),(key,value,observed[key])
        except ValueError: raise AssertionError((key,value,observed[key]))
assert json.loads((data/'sensitivity.json').read_text())==json.loads((data/'reproduced-sensitivity.json').read_text())
print(f"Verified {len(manifest['files'])} file hashes, all 112 school rows and sensitivity scenarios")
