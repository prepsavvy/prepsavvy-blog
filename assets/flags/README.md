# Country flags

PNG flags are supplied by [Flagcdn / Flagpedia](https://flagcdn.com/), based on Wikimedia Commons flag vectors. Files use ISO 3166-1 alpha-2 country codes. The seven flags identify the countries represented in the article's top twenty.

The browser uses a subset of Google's Noto Color Emoji for these same seven flag sequences, requested through the [Google Fonts text API](https://developers.google.com/fonts/docs/getting_started#optimizing_your_font_requests). Its SIL Open Font License is bundled in `assets/fonts/NotoColorEmoji-OFL.txt`.

Run `python scripts/flag_assets.py` to refresh these assets. Reproducing the charts uses the bundled files and needs no network access.
