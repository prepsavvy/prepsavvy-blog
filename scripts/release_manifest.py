"""Record every reproducibility and editorial artifact in the current release."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
files = {}
for directory in ['data', 'figures', 'assets', 'articles', 'analysis', 'profiles', 'scripts', '.github/workflows']:
    for path in sorted((ROOT / directory).rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts and not path.name.startswith('reproduced-'):
            files[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
for name in ['README.md', 'requirements.txt', 'LICENSE']:
    files[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
(ROOT / 'release-manifest.json').write_text(json.dumps({
    'edition': '2026-10-23', 'editorial_revision': 3,
    'article': 'https://prepsavvy.ai/blog/top-philosophy-schools',
    'article_status': 'editorial draft', 'files': files,
}, indent=2) + '\n', encoding='utf-8')
print(f'Recorded {len(files)} release artifact hashes')
