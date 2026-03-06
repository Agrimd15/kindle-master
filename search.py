import re
import cloudscraper
from bs4 import BeautifulSoup

BASE = "https://annas-archive.gl"
LIBGEN = "https://libgen.li"

scraper = cloudscraper.create_scraper()


def search_books(query: str, limit: int = 10) -> list[dict]:
    """Search Anna's Archive for epub books matching query."""
    resp = scraper.get(
        f"{BASE}/search",
        params={"q": query, "ext": "epub", "sort": ""},
        timeout=20,
    )
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")
    results = []

    # Title links have js-vim-focus class and href="/md5/..."
    for a in soup.find_all("a", class_="js-vim-focus", href=True):
        href = a["href"]
        if not href.startswith("/md5/"):
            continue

        title = a.get_text(strip=True)
        if not title:
            continue

        # Author: next <a> inside the same parent div pointing to /search?q=
        parent = a.find_parent("div")
        author_a = (
            parent.find("a", href=lambda h: h and h.startswith("/search?q="))
            if parent
            else None
        )
        # Get text from NavigableStrings only (CSS icon spans have no text content)
        author = (
            " ".join(t.strip() for t in author_a.strings if t.strip())
            if author_a
            else ""
        )

        # Meta line: small monospace text above the title
        meta_div = a.find_previous_sibling("div")
        meta = meta_div.get_text(strip=True) if meta_div else ""

        results.append({
            "title": title,
            "author": author,
            "meta": meta,
            "url": BASE + href,
        })

        if len(results) >= limit:
            break

    return results


def _libgen_md5_from_detail(book_url: str) -> str | None:
    """Extract the libgen MD5 from Anna's Archive book detail page."""
    md5_match = re.search(r"/md5/([a-f0-9]+)", book_url)
    return md5_match.group(1) if md5_match else None


def get_download_url(book_url: str) -> str | None:
    """Return a direct epub download URL.

    Uses libgen.li: ads.php → get.php flow which gives a time-limited key.
    Returns the final get.php URL with the key embedded.
    """
    md5 = _libgen_md5_from_detail(book_url)
    if not md5:
        return None

    # Step 1: visit ads.php to get the GET key
    ads_url = f"{LIBGEN}/ads.php?md5={md5}"
    try:
        resp = scraper.get(ads_url, timeout=15)
        resp.raise_for_status()
    except Exception:
        return None

    # Step 2: find get.php?md5=...&key=... link
    match = re.search(r'href="(get\.php\?md5=[^"]+)"', resp.text)
    if not match:
        return None

    get_path = match.group(1)
    return f"{LIBGEN}/{get_path}"


def download_epub(url: str, dest_path: str) -> str:
    """Download epub bytes from url to dest_path. Returns dest_path."""
    resp = scraper.get(url, stream=True, timeout=120, allow_redirects=True)
    resp.raise_for_status()

    with open(dest_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=16384):
            if chunk:
                f.write(chunk)

    return dest_path
