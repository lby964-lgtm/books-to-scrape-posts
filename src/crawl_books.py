import argparse
import html
import json
import re
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen


BASE_URL = "https://books.toscrape.com/"
RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


@dataclass
class Book:
    title: str
    slug: str
    category: str
    price: str
    rating: int
    availability: str
    upc: str
    reviews: str
    source_url: str
    description: str


class ProductListParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.products = []
        self._in_article = False
        self._current = None
        self._capture_price = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        class_names = attrs.get("class", "").split()

        if tag == "article" and "product_pod" in class_names:
            self._in_article = True
            self._current = {"href": "", "title": "", "rating": 0, "price": ""}

        if not self._in_article:
            return

        if tag == "p" and "star-rating" in class_names:
            for name, value in RATINGS.items():
                if name in class_names:
                    self._current["rating"] = value

        if tag == "a" and attrs.get("href") and not self._current["href"]:
            self._current["href"] = attrs["href"]

        if tag == "a" and attrs.get("title"):
            self._current["title"] = html.unescape(attrs["title"])

        if tag == "p" and "price_color" in class_names:
            self._capture_price = True

    def handle_data(self, data):
        if self._in_article and self._capture_price:
            text = clean_text(data)
            if text:
                self._current["price"] = fix_price(text)
                self._capture_price = False

    def handle_endtag(self, tag):
        if tag == "article" and self._in_article:
            self.products.append(self._current)
            self._in_article = False
            self._current = None
            self._capture_price = False


class DetailParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.description = ""
        self.table = {}
        self.breadcrumbs = []
        self._capture = None
        self._last_th = ""
        self._in_breadcrumb = False
        self._description_is_next = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        class_names = attrs.get("class", "").split()

        if tag == "ul" and "breadcrumb" in class_names:
            self._in_breadcrumb = True

        if self._in_breadcrumb and tag == "a":
            self._capture = "breadcrumb"
        elif tag == "h1":
            self._capture = "title"
        elif tag == "th":
            self._capture = "th"
        elif tag == "td":
            self._capture = "td"
        elif tag == "div" and attrs.get("id") == "product_description":
            self._description_is_next = True
        elif self._description_is_next and tag == "p":
            self._capture = "description"
            self._description_is_next = False

    def handle_data(self, data):
        text = clean_text(data)
        if not text:
            return

        if self._capture == "breadcrumb":
            self.breadcrumbs.append(text)
        elif self._capture == "title":
            self.title = text
        elif self._capture == "th":
            self._last_th = text
        elif self._capture == "td" and self._last_th:
            self.table[self._last_th] = fix_price(text)
            self._last_th = ""
        elif self._capture == "description":
            self.description = text

    def handle_endtag(self, tag):
        if tag in {"a", "h1", "th", "td", "p"}:
            self._capture = None
        if tag == "ul" and self._in_breadcrumb:
            self._in_breadcrumb = False


def clean_text(value):
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def fix_price(value):
    return value.replace("Â", "")


def slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:80] or "book"


def fetch_html(url):
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 book-crawler"})
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8")


def parse_catalogue(count):
    parser = ProductListParser()
    parser.feed(fetch_html(BASE_URL))
    return parser.products[:count]


def parse_detail(product):
    source_url = urljoin(BASE_URL, product["href"])
    parser = DetailParser()
    parser.feed(fetch_html(source_url))

    title = parser.title or product["title"]
    category = parser.breadcrumbs[-1] if parser.breadcrumbs else "Books"

    return Book(
        title=title,
        slug=slugify(title),
        category=category,
        price=parser.table.get("Price (incl. tax)", product["price"]),
        rating=product["rating"],
        availability=parser.table.get("Availability", "In stock"),
        upc=parser.table.get("UPC", ""),
        reviews=parser.table.get("Number of reviews", "0"),
        source_url=source_url,
        description=parser.description or "No product description is available.",
    )


def crawl_books(count):
    products = parse_catalogue(count)
    return [parse_detail(product) for product in products]


def main():
    arg_parser = argparse.ArgumentParser(description="Crawl book data from Books to Scrape.")
    arg_parser.add_argument("--count", type=int, default=5, help="Number of book detail pages to crawl.")
    arg_parser.add_argument("--output", default="data/books.json", help="JSON output path.")
    args = arg_parser.parse_args()

    books = crawl_books(args.count)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps([asdict(book) for book in books], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Saved {len(books)} books to {output}")


if __name__ == "__main__":
    main()
