# Chi-Rho Cards

SVG-first KJV scripture card generation with measured EB Garamond pagination, trim/bleed exports, alternating gradient sides, and per-book themes.

## Generate A Book

```text
python generate_csv.py --book 1peter
python svg_draft.py --book 1peter

python generate_csv.py --book james
python svg_draft.py --book james
```

Outputs are written to `output/1_peter/` and `output/james/`. Each book includes:

- `full_bleed_png/`: upload-ready PNGs named `{book}_card_{number}.png`
- `gallery.html`: responsive cut-card gallery
- `vector_card_sources/`: canonical `{book}_card_{number}` SVGs, previews, and derived cut PNGs

Add future books in `src/book_config.py` with their API ID, chapter count, accent color, data path, and output path.

## Validate

```text
python -m py_compile src/*.py generate_csv.py svg_draft.py
```

The old browser renderer is preserved under `legacy/` for comparison only.