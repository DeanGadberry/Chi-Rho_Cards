import sys

from src.generate_csv import build_csv


if __name__ == "__main__":
    book = sys.argv[sys.argv.index("--book") + 1] if "--book" in sys.argv else "1peter"
    build_csv(book)
