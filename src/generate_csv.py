import csv
import argparse
import urllib.request
import json
import re
from pathlib import Path

try:
    from .book_config import BOOKS
except ImportError:
    from book_config import BOOKS

ROOT = Path(__file__).resolve().parent.parent

def clean_text(text):
    # 1. Strip Strong's concordance tags (<S></S>)
    text = re.sub(r'</?S>', '', text)
    # 2. Strip inline footnote superscripts (<sup>...</sup>)
    text = re.sub(r'<sup>.*?</sup>', '', text)
    # 3. Strip remaining raw digits if any
    text = re.sub(r'\d+', '', text)
    # 4. Fix floating spaces before punctuation (e.g. "seen , ye" -> "seen, ye")
    text = re.sub(r'\s+([,.?!;:"])', r'\1', text)
    # 5. Collapse multi-spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def fetch_book(book):
    all_verses = []
    for ch in range(book["chapter_start"], book["chapter_end"] + 1):
        req = urllib.request.urlopen(
            f"https://bolls.life/get-text/KJV/{book['api_book_id']}/{ch}/"
        )
        data = json.loads(req.read().decode('utf-8'))
        for item in data:
            all_verses.append({
                "chapter": ch,
                "verse": item["verse"],
                "text": clean_text(item["text"])
            })
    return all_verses


def build_csv(book_key):
    book = BOOKS[book_key]
    print(f"Fetching and thoroughly cleaning KJV text for {book['display_name']}...")
    raw_verses = fetch_book(book)
    rows = []
    for chapter in range(book["chapter_start"], book["chapter_end"] + 1):
        chunk = [verse for verse in raw_verses if verse["chapter"] == chapter]
        formatted_verses = []
        for verse in chunk:
            formatted_verses.append(
                f'<div class="verse-block"><span class="scripture-num">{verse["verse"]}</span>'
                f'<span class="verse-text">{verse["text"]}</span></div>'
            )
        rows.append({
            "id": chapter,
            "header": "" if chapter > 1 else book["display_name"],
            "verse_num": "",
            "text": " ".join(formatted_verses),
            "chapter": chapter,
            "footer_ref": f"{book['display_name']} {chapter}",
        })

    csv_path = ROOT / book["csv_path"]
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "header", "verse_num", "text", "chapter", "footer_ref"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {book['csv_path']} with {len(raw_verses)} verses.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", choices=BOOKS, default="1peter")
    args = parser.parse_args()
    build_csv(args.book)