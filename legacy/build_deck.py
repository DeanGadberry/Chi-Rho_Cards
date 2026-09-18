import os
import random
import shutil
from pathlib import Path
import pandas as pd
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
os.makedirs(ROOT / "output" / "legacy_browser", exist_ok=True)
df = pd.read_csv(ROOT / "data" / "verses" / "1peter.csv")

VARIANTS = {
    "compact": {"foreground_size": 29, "line_height": 35, "pattern_scale": 4},
    "balanced": {"foreground_size": 31.667, "line_height": 38.333, "pattern_scale": 5},
    "bold": {"foreground_size": 34, "line_height": 41, "pattern_scale": 6},
}

for variant_name in VARIANTS:
    variant_path = ROOT / "output" / "legacy_browser" / variant_name
    if variant_path.exists():
        shutil.rmtree(variant_path)
    variant_path.mkdir(parents=True)

for stale_file in (ROOT / "output" / "legacy_browser").glob("card_*.png"):
    stale_file.unlink()

card_ids = sorted(int(card_id) for card_id in df["id"])
test_card_ids = {card_ids[0], random.choice(card_ids[1:])}
df = df[df["id"].isin(test_card_ids)]
print(f"Rendering test cards: {sorted(test_card_ids)}")

with open(ROOT / "legacy" / "template.html", "r") as f:
    template_src = f.read()

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 825, "height": 1125})

    for variant_name, variant in VARIANTS.items():
        for _, row in df.iterrows():
            card_id = int(row["id"])
            chapter = "" if pd.isna(row["chapter"]) else str(int(row["chapter"]))
            header = "" if pd.isna(row["header"]) else str(row["header"])
            header_class = "has-header" if header else "no-header"

            for form, clip in (
                ("uncut", {"x": 0, "y": 0, "width": 825, "height": 1125}),
                ("cut", {"x": 0, "y": 0, "width": 750, "height": 1050}),
            ):
                for side in ("right", "left"):
                    card_html = template_src
                    replacements = {
                        "{{HEADER}}": header,
                        "{{TEXT}}": str(row["text"]),
                        "{{EDGE_SIDE}}": side,
                        "{{HEADER_CLASS}}": header_class,
                        "{{FORM_CLASS}}": form,
                        "{{CHAPTER}}": chapter,
                        "{{CARD_NUMBER}}": str(card_id),
                        "{{FOREGROUND_SIZE}}": str(variant["foreground_size"]),
                        "{{LINE_HEIGHT}}": str(variant["line_height"]),
                        "{{PATTERN_SCALE}}": str(variant["pattern_scale"]),
                    }
                    for token, value in replacements.items():
                        card_html = card_html.replace(token, value)

                    page.set_content(card_html)
                    page.wait_for_load_state("networkidle")

                    output_path = ROOT / "output" / "legacy_browser" / variant_name / f"card_{card_id:03d}_{form}_{side}.png"
                    page.screenshot(path=str(output_path), clip=clip)
                    print(f"Generated: {output_path}")

    browser.close()
print("All cards generated successfully in /output!")
