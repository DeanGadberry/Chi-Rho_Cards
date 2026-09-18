import csv
import argparse
import html
import os
import re
from pathlib import Path

import cairosvg
from fontTools.ttLib import TTFont

try:
    from .book_config import BOOKS
except ImportError:
    from book_config import BOOKS


ROOT = Path(__file__).resolve().parent.parent
FONT_PATH = ROOT / "assets" / "fonts" / "EBGaramond-Regular.ttf"
OUTPUT = ROOT / "output" / "svg_draft"

CARD_WIDTH = 225
CARD_HEIGHT = 315
BLEED = 11.25
TEXT_LEFT = 31
TEXT_RIGHT = 198
TEXT_WIDTH = TEXT_RIGHT - TEXT_LEFT
BODY_TOP = 45
FOOTER_Y = 300
FONT_SIZE = 11.0
LINE_HEIGHT = 13.0
VERSE_GAP = 2
BODY_BOTTOM = 278
CUT_GRADIENT_WIDTH = 15.625
BACKGROUND_OPACITY = 0.03


def load_metrics():
    font = TTFont(str(FONT_PATH))
    cmap = font.getBestCmap()
    widths = font["hmtx"].metrics
    units = font["head"].unitsPerEm

    def measure(text):
        total = 0
        for character in text:
            glyph = cmap.get(ord(character), ".notdef")
            total += widths[glyph][0]
        return total * FONT_SIZE / units

    return measure


def parse_verses(raw_text):
    pattern = re.compile(
        r'<div class="verse-block"><span class="scripture-num">(\d+)</span>'
        r'<span class="verse-text">(.*?)</span></div>'
    )
    verses = []
    for number, text in pattern.findall(raw_text):
        plain_text = html.unescape(re.sub(r"<[^>]+>", "", text)).strip()
        verses.append((number, plain_text))
    return verses


def wrap_words(text, measure):
    lines = []
    current = ""
    for word in text.split():
        candidate = word if not current else f"{current} {word}"
        if current and measure(candidate) > TEXT_WIDTH - 12:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def paginate(verses, measure):
    costs = [len(wrap_words(verse[2], measure)) * LINE_HEIGHT + VERSE_GAP for verse in verses]
    prefix = [0]
    for cost in costs:
        prefix.append(prefix[-1] + cost)

    verse_count = len(verses)
    capacity = BODY_BOTTOM - BODY_TOP
    for card_count in range(1, verse_count // 2 + 1):
        best = [[float("inf")] * (verse_count + 1) for _ in range(card_count + 1)]
        previous = [[None] * (verse_count + 1) for _ in range(card_count + 1)]
        best[0][0] = 0

        for current_cards in range(1, card_count + 1):
            for end in range(current_cards * 2, verse_count + 1):
                for start in range((current_cards - 1) * 2, end - 1):
                    if best[current_cards - 1][start] == float("inf"):
                        continue
                    block_cost = prefix[end] - prefix[start]
                    candidate = max(best[current_cards - 1][start], block_cost)
                    if candidate <= capacity and candidate < best[current_cards][end]:
                        best[current_cards][end] = candidate
                        previous[current_cards][end] = start

        if best[card_count][verse_count] == float("inf"):
            continue

        boundaries = []
        end = verse_count
        for current_cards in range(card_count, 0, -1):
            start = previous[current_cards][end]
            boundaries.append((start, end))
            end = start
        return [[verses[index] for index in range(start, finish)] for start, finish in reversed(boundaries)]

    raise ValueError("Unable to paginate verses within the configured card bounds")


def escape(text):
    return html.escape(text, quote=True)


def format_reference(book_name, start_chapter, start_verse, end_chapter, end_verse):
    if start_chapter == end_chapter:
        return f"{book_name} {start_chapter}:{start_verse}-{end_verse}"
    return f"{book_name} {start_chapter}:{start_verse}-{end_chapter}:{end_verse}"


def trim_view(svg):
    return (
        svg.replace('viewBox="0 0 247.5 337.5"', 'viewBox="11.25 11.25 225 315"')
        .replace('width="2.75in" height="3.75in"', 'width="2.5in" height="3.5in"')
    )


def card_svg(card_id, total_cards, header, verses, edge_side, form, measure, accent, font_href):
    is_cut = form == "cut"
    canvas_width = CARD_WIDTH if is_cut else 247.5
    canvas_height = CARD_HEIGHT if is_cut else 337.5
    gradient_width = CUT_GRADIENT_WIDTH if is_cut else CUT_GRADIENT_WIDTH + BLEED
    working_shift = CUT_GRADIENT_WIDTH if edge_side == "left" else 0
    content_x = working_shift if is_cut else BLEED + working_shift
    content_y = 0 if is_cut else BLEED
    content_transform = f"translate({content_x},{content_y})"
    if edge_side == "right":
        gradient_x = (CARD_WIDTH - CUT_GRADIENT_WIDTH) if is_cut else BLEED + CARD_WIDTH - CUT_GRADIENT_WIDTH
    else:
        gradient_x = 0
    y = BODY_TOP
    text_elements = []
    line_count = 0
    for number, verse in verses:
        lines = wrap_words(verse, measure)
        for index, line in enumerate(lines):
            number_text = escape(number) if index == 0 else ""
            text_elements.append(
                f'<text x="17" y="{y:.2f}" class="scripture-num">{number_text}</text>'
            )
            text_elements.append(
                f'<text x="{TEXT_LEFT}" y="{y:.2f}" class="scripture-text">{escape(line)}</text>'
            )
            y += LINE_HEIGHT
            line_count += 1
        y += 2

    gradient_id = f"edge-{edge_side}-{card_id}"
    header_svg = (
        f'<text x="17" y="25" class="header-title">{escape(header)}</text>'
        f'<line x1="17" y1="30" x2="190" y2="30" class="header-rule" />'
        if header
        else ""
    )
    physical_number = f"{(card_id + 1) // 2}/{(total_cards + 1) // 2}"
    footer_left, footer_right = (
        ("CHI-RHO", physical_number)
        if edge_side == "right"
        else (physical_number, "CHI-RHO")
    )
    footer = (
        f'<line x1="17" y1="290" x2="190" y2="290" class="footer-rule" />'
        f'<text x="17" y="300" class="footer-text">{footer_left}</text>'
        '<text x="103.5" y="300" text-anchor="middle" class="footer-text">KJV</text>'
        f'<text x="190" y="300" text-anchor="end" class="footer-text">{footer_right}</text>'
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_width} {canvas_height}" width="{'2.5in' if is_cut else '2.75in'}" height="{'3.5in' if is_cut else '3.75in'}">
    <defs>
        {BACKGROUND.replace("{BACKGROUND_OPACITY}", str(BACKGROUND_OPACITY))}
    <style>
    @font-face {{ font-family: "EB Garamond"; src: url("{font_href}"); }}
    .header-title {{ font: 700 12px "EB Garamond", serif; letter-spacing: 1.5px; fill: {accent}; }}
    .scripture-num {{ font: 700 8.25px "EB Garamond", serif; fill: {accent}; }}
    .scripture-text {{ font: {FONT_SIZE}px "EB Garamond", serif; fill: #1A1A1A; }}
    .footer-text {{ font: 600 6.5px "EB Garamond", serif; letter-spacing: .8px; fill: #666; }}
    .header-rule {{ stroke: {accent}; stroke-width: .5; opacity: .4; }}
      .footer-rule {{ stroke: #1A1A1A; stroke-width: .5; opacity: .3; }}
    </style>
    <linearGradient id="{gradient_id}" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{accent}" />
    <stop offset="100%" stop-color="{accent}" stop-opacity="0" />
    </linearGradient>
        <clipPath id="trim-{card_id}"><rect x="0" y="0" width="225" height="315" rx="12.5" /></clipPath>
  </defs>
    <rect width="{canvas_width}" height="{canvas_height}" fill="#FDFBF7" />
    <rect width="{canvas_width}" height="{canvas_height}" fill="url(#chi-rho-tessellation-background)" />
    <rect x="{gradient_x}" y="0" width="{gradient_width}" height="{canvas_height}" fill="url(#{gradient_id})" />
    <g transform="{content_transform}" clip-path="url(#trim-{card_id})">
    {header_svg}
    {''.join(text_elements)}
    {footer}
  </g>
</svg>'''


BACKGROUND = '''
  <g id="chi-rho-symbol-background">
    <line x1="-18" y1="-22" x2="18" y2="22" stroke="#1A1A1A" stroke-width="2.5" stroke-linecap="round" />
    <line x1="-18" y1="22" x2="18" y2="-22" stroke="#1A1A1A" stroke-width="2.5" stroke-linecap="round" />
    <line x1="-21" y1="-20" x2="-15" y2="-24" stroke="#1A1A1A" stroke-width="2" stroke-linecap="round" />
    <line x1="15" y1="24" x2="21" y2="20" stroke="#1A1A1A" stroke-width="2" stroke-linecap="round" />
    <line x1="-21" y1="20" x2="-15" y2="24" stroke="#1A1A1A" stroke-width="2" stroke-linecap="round" />
    <line x1="15" y1="-24" x2="21" y2="-20" stroke="#1A1A1A" stroke-width="2" stroke-linecap="round" />
    <line x1="0" y1="-32" x2="0" y2="28" stroke="#1A1A1A" stroke-width="2.5" stroke-linecap="round" />
    <line x1="-5" y1="28" x2="5" y2="28" stroke="#1A1A1A" stroke-width="2" stroke-linecap="round" />
    <path d="M 0,-32 C 14,-32 14,-10 0,-10" fill="none" stroke="#1A1A1A" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
  </g>
    <pattern id="chi-rho-tessellation-background" width="30" height="17.32" patternUnits="userSpaceOnUse" patternTransform="scale(1.15)">
    <g opacity="{BACKGROUND_OPACITY}" transform="scale(0.25)">
      <use href="#chi-rho-symbol-background" x="30" y="34.641016" />
      <use href="#chi-rho-symbol-background" x="90" y="0" />
      <use href="#chi-rho-symbol-background" x="90" y="69.282032" />
      <use href="#chi-rho-symbol-background" x="-30" y="0" />
      <use href="#chi-rho-symbol-background" x="-30" y="69.282032" />
      <use href="#chi-rho-symbol-background" x="30" y="-34.641016" />
      <use href="#chi-rho-symbol-background" x="30" y="103.923048" />
    </g>
  </pattern>
'''


def main(book_key):
    global OUTPUT
    book = BOOKS[book_key]
    OUTPUT = ROOT / book["output_dir"] / "vector_card_sources"
    png_output = ROOT / book["output_dir"] / "full_bleed_png"
    font_href = Path(os.path.relpath(FONT_PATH, OUTPUT)).as_posix()
    measure = load_metrics()
    rows = list(csv.DictReader((ROOT / book["csv_path"]).open(encoding="utf-8")))
    verses = []
    for row in rows:
        chapter = row["chapter"]
        if chapter:
            verses.extend((chapter, number, text) for number, text in parse_verses(row["text"]))

    paginated = paginate(verses, measure)

    print(f"Font: EB Garamond {FONT_SIZE}px / {LINE_HEIGHT}px line height")
    print(f"Measured text width: {TEXT_WIDTH - 12:.2f}px; body height: {BODY_BOTTOM - BODY_TOP:.2f}px")
    print(f"Scripture verses: {len(verses)}; calculated cards: {len(paginated)}")
    for card_number, card_records in enumerate(paginated, 1):
        start_chapter, start_verse = card_records[0][:2]
        end_chapter, end_verse = card_records[-1][:2]
        print(f"  {card_number}: {start_chapter}:{start_verse}-{end_chapter}:{end_verse} ({len(card_records)} verses)")

    total_cards = len(paginated)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    png_output.mkdir(parents=True, exist_ok=True)
    for stale_file in OUTPUT.glob("card_*"):
        stale_file.unlink()
    for stale_file in png_output.glob("*.png"):
        stale_file.unlink()
    gallery_rows = []
    for card_number, card_records in enumerate(paginated, 1):
        card_verses = [(number, text) for _, number, text in card_records]
        start_chapter, start_verse = card_records[0][:2]
        end_chapter, end_verse = card_records[-1][:2]
        header = format_reference(book["display_name"], start_chapter, start_verse, end_chapter, end_verse)
        edge_side = "right" if card_number % 2 else "left"
        svg = card_svg(card_number, total_cards, header, card_verses, edge_side, "uncut", measure, book["accent"], font_href)
        file_prefix = f"{book_key}_card_{card_number:03d}"
        svg_path = OUTPUT / f"{file_prefix}_uncut_{edge_side}.svg"
        svg_path.write_text(svg, encoding="utf-8")
        cairosvg.svg2png(
            bytestring=svg.encode("utf-8"),
            write_to=str(svg_path.with_suffix(".png")),
            output_width=825,
            output_height=1125,
        )
        cairosvg.svg2png(
            bytestring=svg.encode("utf-8"),
            write_to=str(png_output / f"{book_key}_card_{card_number:03d}.png"),
            output_width=825,
            output_height=1125,
        )

        cut_path = OUTPUT / f"{file_prefix}_cut_{edge_side}.png"
        cairosvg.svg2png(
            bytestring=trim_view(svg).encode("utf-8"),
            write_to=str(cut_path),
            output_width=750,
            output_height=1050,
        )
        gallery_cells = (
            f'<figure><img src="vector_card_sources/{cut_path.name}" alt="Card {card_number}, {edge_side} gradient">'
            f'<figcaption>{edge_side} gradient</figcaption></figure>'
        )
        gallery_rows.append(
            f'<section><h2>Card {card_number}: {header} ({len(card_verses)} verses)</h2>'
            f'<div class="pair">{gallery_cells}</div></section>'
        )

    (OUTPUT.parent / "gallery.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>1 Peter Card Gallery</title>'
        '<style>body{font-family:system-ui,sans-serif;margin:24px;background:#202020;color:#eee}'
        'h1{margin:0 0 24px;font-size:24px}.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:24px;align-items:start}'
        'section{min-width:0;margin:0}.pair{display:block}figure{margin:0}img{display:block;width:100%;height:auto;background:#fff}'
        'figcaption{text-align:center;margin-top:8px;color:#bbb;font-size:13px}h2{font-size:14px;font-weight:500;line-height:1.25;margin:0 0 10px}</style>'
        f'<h1>{book["display_name"]} Card Gallery</h1><main class="gallery">' + "".join(gallery_rows) + '</main>',
        encoding="utf-8",
    )
    print(f"Generated {book['display_name']} deck: {total_cards} cards, verbose PNG exports in {png_output}, and output/gallery.html")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", choices=BOOKS, default="1peter")
    args = parser.parse_args()
    main(args.book)