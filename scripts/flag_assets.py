"""Fetch the seven country flags and a matching browser font subset."""
from pathlib import Path
import re
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
FLAGS = ROOT / 'assets' / 'flags'
FLAGS.mkdir(parents=True, exist_ok=True)
CODES = ['GB', 'US', 'CH', 'AU', 'NL', 'DE', 'FI']
for code in CODES:
    url = f'https://flagcdn.com/w80/{code.lower()}.png'
    (FLAGS / f'{code.lower()}.png').write_bytes(urllib.request.urlopen(url, timeout=30).read())
text = ''.join(chr(127397 + ord(c)) for code in CODES for c in code)
css_url = 'https://fonts.googleapis.com/css2?family=Noto+Color+Emoji&text=' + urllib.parse.quote(text)
request = urllib.request.Request(css_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'})
css = urllib.request.urlopen(request, timeout=30).read().decode()
font_url = re.search(r'src:\s*url\(([^)]+)\)', css).group(1)
font = ROOT / 'assets/fonts/NotoColorEmoji-flags.woff2'
font.write_bytes(urllib.request.urlopen(font_url, timeout=30).read())
license_url = 'https://raw.githubusercontent.com/google/fonts/main/ofl/notocoloremoji/OFL.txt'
(ROOT / 'assets/fonts/NotoColorEmoji-OFL.txt').write_bytes(urllib.request.urlopen(license_url, timeout=30).read())
(FLAGS / 'README.md').write_text('''# Country flags

PNG flags are supplied by [Flagcdn / Flagpedia](https://flagcdn.com/), based on Wikimedia Commons flag vectors. Files use ISO 3166-1 alpha-2 country codes. The seven flags identify the countries represented in the article's top twenty.

The browser uses a subset of Google's Noto Color Emoji for these same seven flag sequences, requested through the [Google Fonts text API](https://developers.google.com/fonts/docs/getting_started#optimizing_your_font_requests). Its SIL Open Font License is bundled in `assets/fonts/NotoColorEmoji-OFL.txt`.

Run `python scripts/flag_assets.py` to refresh these assets. Reproducing the charts uses the bundled files and needs no network access.
''', encoding='utf-8')
print(f'Saved seven flag PNGs and {font.stat().st_size:,}-byte font subset')
