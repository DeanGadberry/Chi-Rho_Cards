# Chi-Rho Cards

SVG-first KJV scripture card generation with measured EB Garamond pagination, trim/bleed exports, alternating gradient sides, and per-book themes.

The result is a print-ready card system: vector source files, 300 DPI bleed PNGs, derived trim previews, and responsive galleries for reviewing an entire passage at a glance.

## Card Showcase

| Book or Passage | Cards | Accent | Gallery | Upload PNGs |
|---|---:|---|---|---|
| 1 Peter | 28 | Royal blue | [View gallery](output/1_peter/gallery.html) | [Open PNG folder](output/1_peter/full_bleed_png/) |
| James | 25 | Oxblood | [View gallery](output/james/gallery.html) | [Open PNG folder](output/james/full_bleed_png/) |
| Colossians | 23 | Olive | [View gallery](output/colossians/gallery.html) | [Open PNG folder](output/colossians/full_bleed_png/) |
| 1 John | 26 | Brown | [View gallery](output/1_john/gallery.html) | [Open PNG folder](output/1_john/full_bleed_png/) |
| Sermon on the Mount | 27 | Warm umber | [View gallery](output/sermon_on_the_mount/gallery.html) | [Open PNG folder](output/sermon_on_the_mount/full_bleed_png/) |
| Psalm 1 | 2 | Blue gray | [View gallery](output/psalm_1/gallery.html) | [Open PNG folder](output/psalm_1/full_bleed_png/) |
| Hebrews 11 | 11 | Brown gold | [View gallery](output/hebrews_11/gallery.html) | [Open PNG folder](output/hebrews_11/full_bleed_png/) |
| Exodus 20 | 7 | Slate | [View gallery](output/exodus_20/gallery.html) | [Open PNG folder](output/exodus_20/full_bleed_png/) |

## Generate A Book

```text
python generate_csv.py --book 1peter
python svg_draft.py --book 1peter

python generate_csv.py --book james
python svg_draft.py --book james

python generate_csv.py --book sermon_on_the_mount
python svg_draft.py --book sermon_on_the_mount
```

Outputs are written to `output/1_peter/` and `output/james/`. Each book includes:

- `full_bleed_png/`: upload-ready PNGs named `{book}_card_{number}.png`
- `gallery.html`: responsive cut-card gallery
- `vector_card_sources/`: canonical `{book}_card_{number}` SVGs, previews, and derived cut PNGs

Configured titles currently include:

- `1peter`
- `james`
- `colossians`
- `1john`
- `sermon_on_the_mount`
- `psalm_1`
- `hebrews_11`
- `exodus_20`

Add future books or passages in `src/book_config.py` with their API ID, chapter span, reference name, accent color, data path, and output path.

## Validate

```text
python -m py_compile src/*.py generate_csv.py svg_draft.py
```

The old browser renderer is preserved under `legacy/` for comparison only.