#!/usr/bin/env python3
"""
kindle-master — search → download → send to Kindle in one shot.

Usage:
  python main.py "Atomic Habits"
  python main.py "James Clear" --author
  python main.py --image /path/to/photo.jpg
"""

import os
import sys
import tempfile
import click
from search import search_books, get_download_urls_for_book, download_book
from sender import send_to_kindle
import config


def pick_book(results: list[dict]) -> dict | None:
    if not results:
        click.echo("No epub results found.")
        return None

    click.echo("\nResults:\n")
    for i, book in enumerate(results, 1):
        click.echo(f"  [{i}] {book['title']}")
        click.echo(f"      {book['author']}")
        click.echo()

    choice = click.prompt("Pick a number (or 0 to cancel)", type=int, default=1)
    if choice == 0 or choice > len(results):
        return None
    return results[choice - 1]


def run(query: str):
    config.validate()

    click.echo(f'\nSearching Anna\'s Archive for: "{query}" ...')
    results = search_books(query)

    if not results:
        click.echo("No results found. Try a different query.")
        sys.exit(1)

    book = pick_book(results)
    if not book:
        click.echo("Cancelled.")
        sys.exit(0)

    click.echo(f"\nFetching download link for: {book['title']} ...")
    dl_urls = get_download_urls_for_book(book)

    if not dl_urls:
        click.echo("Could not find a direct download link. Try another result.")
        sys.exit(1)

    dl_url = dl_urls[0]

    safe_title = "".join(c for c in book["title"] if c.isalnum() or c in " _-")[:60]
    dest = os.path.join(tempfile.gettempdir(), f"{safe_title}.epub")

    click.echo(f"Downloading epub → {dest} ...")
    download_book(dl_url, dest)
    size_kb = os.path.getsize(dest) // 1024
    click.echo(f"Downloaded {size_kb} KB")

    click.echo(f"Sending to Kindle ({config.KINDLE_EMAIL}) ...")
    send_to_kindle(dest, book["title"])

    click.echo(f'\nDone! "{book["title"]}" is on its way to your Kindle.')
    os.remove(dest)


@click.command()
@click.argument("query", required=False)
@click.option("--image", "-i", type=click.Path(exists=True), help="Path to a photo of the book cover/title")
@click.option("--author", "-a", is_flag=True, help="Treat query as author name")
def cli(query, image, author):
    """Search Anna's Archive for an epub and send it to your Kindle."""
    if image:
        try:
            from ocr import extract_text_from_image
        except ImportError:
            click.echo("pytesseract not installed. Run: pip install pytesseract Pillow")
            sys.exit(1)
        click.echo(f"Reading text from image: {image}")
        query = extract_text_from_image(image)
        click.echo(f"Detected text: {query}")
        if not query.strip():
            click.echo("Could not read text from image.")
            sys.exit(1)

    if not query:
        query = click.prompt("Enter book title or author")

    if author:
        query = f"author:{query}"

    run(query)


if __name__ == "__main__":
    cli()
