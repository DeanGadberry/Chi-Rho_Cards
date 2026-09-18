import sys

from src.svg_draft import main


if __name__ == "__main__":
    book = sys.argv[sys.argv.index("--book") + 1] if "--book" in sys.argv else "1peter"
    main(book)
