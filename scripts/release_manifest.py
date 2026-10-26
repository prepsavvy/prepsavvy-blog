"""Record every reproducibility and editorial artifact in the current release."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
files = {}
# Only committed/staged artifacts belong to a release. Concurrent draft files
# and ignored local calculations must never enter a public integrity manifest.
tracked = subprocess.check_output(['git', 'ls-files', '--cached', '-z'], cwd=ROOT).decode().split('\0')
for name in sorted(set(tracked)):
    if not name or name == 'release-manifest.json':
        continue
    path = ROOT / name
    if path.is_file():
        files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
studies = json.loads((ROOT / 'studies.json').read_text(encoding='utf-8'))
(ROOT / 'release-manifest.json').write_text(json.dumps({
    'schema_version': 2,
    'studies': studies,
    'files': files,
}, indent=2) + '\n', encoding='utf-8')
print(f'Recorded {len(files)} release artifact hashes')
