import re
import requests
import sqlite3
from bs4 import BeautifulSoup
from pathlib import Path

DB_NAME = "book_list.db"
URL = "https://books.toscrape.com/"

def get_db_path() -> Path:
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / DB_NAME

def ensure_schema(db_path: Path):
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS book (
            id INTEGER PRIMARY KEY,
            book_name TEXT NOT NULL,
            price REAL,
            rating INTEGER
        );
        """)
        conn.commit()

if __name__ == "__main__":
    db_path = get_db_path()
    ensure_schema(db_path)
    print("Database located at:", db_path)

ua = {
    "User-Agent": "EduCrawler/1.0 (+contact: you@example.com; purpose=study; respect-robots)",
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi,en;q=0.9"
}

_price_re = re.compile(r"([£€$])\s*([0-9]+(?:\.[0-9]+)?)")

def parse_price_to_float(raw: str):
    if not raw:
        return None
    m = _price_re.search(raw)
    if not m:
        return None
    return float(m.group(2))

html = requests.get(URL, headers=ua, timeout=15).text
soup = BeautifulSoup(html, "html.parser")

x = input("Enter the rating you like (1..5): ")
try:
    rating = int(x)
    if rating not in range(1, 6):
        print("Only numbers from 1 to 5 are accepted")
        raise SystemExit
    else:
        print("You chose:", rating)
except ValueError:
    print("Please enter an integer between 1 and 5")
    raise SystemExit

RATING_MAP = {"One":1, "Two":2, "Three":3, "Four":4, "Five":5}

def word_to_int(star_tag):
    if not star_tag:
        return None
    classes = [c.capitalize() for c in star_tag.get("class", [])]
    for key in RATING_MAP:
        if key in classes:
            return RATING_MAP[key]
    return None

with sqlite3.connect(get_db_path()) as conn:
    cur = conn.cursor()

    for pod in soup.select("article.product_pod"):
        star_tag = pod.select_one("p.star-rating")
        book_rating = word_to_int(star_tag)

        title_el = pod.select_one("h3 a[title]")
        title = title_el.get("title") if title_el else "(no title)"

        price_el = pod.select_one("p.price_color")
        raw_price = price_el.get_text(strip=True) if price_el else None
        price = parse_price_to_float(raw_price)

        if book_rating is not None and book_rating == rating:
            print(f"[{book_rating}★] {title} - {raw_price}")
            cur.execute(
                "INSERT INTO book (book_name, price, rating) VALUES (?, ?, ?)",
                (title, price, book_rating)
            )

    conn.commit()





