"""Kho mô tả SGK: data/library/<mã sách>/manifest.json."""
import json
import re
from typing import List, Optional

from .config import settings
from .schemas import BookPages, BookSummary

_BOOK_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def _manifest_path(book: str):
    return settings.data_dir / "library" / book / "manifest.json"


def get_book(book: str) -> Optional[BookPages]:
    if not _BOOK_ID.match(book):
        return None
    path = _manifest_path(book)
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    pages = sorted(data.get("pages", []), key=lambda p: p.get("page", 0))
    return BookPages(book=data.get("book", book), title=data.get("title", book), pages=pages)


def list_books() -> List[BookSummary]:
    root = settings.data_dir / "library"
    if not root.is_dir():
        return []
    books = []
    for folder in sorted(root.iterdir()):
        if folder.is_dir() and _BOOK_ID.match(folder.name):
            book = get_book(folder.name)
            if book:
                books.append(BookSummary(book=book.book, title=book.title, page_count=len(book.pages)))
    return books
