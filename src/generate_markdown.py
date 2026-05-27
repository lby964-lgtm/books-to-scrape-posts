import argparse
import json
from datetime import date
from pathlib import Path


def yaml_quote(value):
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def excerpt(value, limit=220):
    text = " ".join(str(value).split())
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "..."


def render_markdown(book, index, post_date):
    title = book["title"]
    body_excerpt = excerpt(book.get("description", ""))

    return f'''---
title: "{yaml_quote(title)}"
date: "{post_date}"
source: "{yaml_quote(book["source_url"])}"
category: "{yaml_quote(book["category"])}"
price: "{yaml_quote(book["price"])}"
rating: {book["rating"]}
availability: "{yaml_quote(book["availability"])}"
upc: "{yaml_quote(book["upc"])}"
reviews: "{yaml_quote(book["reviews"])}"
---

# {title}

Books to Scrape에서 수집한 {index}번째 책 정보입니다.

## 수집 정보

- 카테고리: {book["category"]}
- 가격: {book["price"]}
- 평점: {book["rating"]} / 5
- 재고: {book["availability"]}
- 리뷰 수: {book["reviews"]}
- UPC: {book["upc"]}

## 설명 메모

{body_excerpt}

출처: {book["source_url"]}
'''


def main():
    parser = argparse.ArgumentParser(description="Generate GitHub blog Markdown posts from crawled book data.")
    parser.add_argument("--input", default="data/books.json", help="Crawler JSON input path.")
    parser.add_argument("--output-dir", default="posts", help="Directory for generated Markdown posts.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Post date in YYYY-MM-DD format.")
    args = parser.parse_args()

    books = json.loads(Path(args.input).read_text(encoding="utf-8"))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for index, book in enumerate(books, start=1):
        filename = f'{args.date}-{index:02d}-{book["slug"]}.md'
        path = output_dir / filename
        path.write_text(render_markdown(book, index, args.date), encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
