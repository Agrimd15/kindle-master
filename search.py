import os
import re
import cloudscraper
from bs4 import BeautifulSoup

BASE = "https://annas-archive.gl"
LIBGEN = "https://libgen.li"

scraper = cloudscraper.create_scraper()


# Exclude sources that don't have Libgen download links
_EXCLUDE_SOURCES = ["zlib", "upload", "ia", "hathi", "duxiu", "nexusstc", "zlibzh", "magzdb", "scihub"]


def search_books(query: str, limit: int = 3) -> list[dict]:
    """Search Anna's Archive for epub books, filtered to Libgen sources."""
    params = [("q", query), ("ext", "epub")]
    for src in _EXCLUDE_SOURCES:
        params.append(("src", f"anti__{src}"))
    resp = scraper.get(
        f"{BASE}/search",
        params=params,
        timeout=20,
    )
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")
    results = []

    for a in soup.find_all("a", class_="js-vim-focus", href=True):
        href = a["href"]
        if not href.startswith("/md5/"):
            continue

        title = a.get_text(strip=True)
        if not title:
            continue

        parent = a.find_parent("div")
        author_a = (
            parent.find("a", href=lambda h: h and h.startswith("/search?q="))
            if parent else None
        )
        author = (
            " ".join(t.strip() for t in author_a.strings if t.strip())
            if author_a else ""
        )

        results.append({
            "title": title,
            "author": author,
            "url": BASE + href,
            "md5": href[len("/md5/"):],
        })

        if len(results) >= limit:
            break

    return results


def get_download_url(md5: str) -> str | None:
    """Return a direct epub download URL via libgen.li ads.php → get.php."""
    try:
        resp = scraper.get(f"{LIBGEN}/ads.php?md5={md5}", timeout=15)
        resp.raise_for_status()
    except Exception:
        return None

    match = re.search(r'href="(get\.php\?md5=[^"]+)"', resp.text)
    if not match:
        return None

    return f"{LIBGEN}/{match.group(1)}"


def download_epub(url: str, dest_path: str) -> str:
    """Download ebook. Returns actual saved path (extension corrected from Content-Disposition)."""
    resp = scraper.get(url, stream=True, timeout=120, allow_redirects=True)
    resp.raise_for_status()

    # Use the real extension from Content-Disposition (mobi, epub, azw, etc.)
    cd = resp.headers.get("content-disposition", "")
    ext_match = re.search(r"\.(\w+)[\"'\s]?\s*$", cd, re.IGNORECASE)
    if ext_match:
        real_ext = "." + ext_match.group(1).lower()
        base = dest_path.rsplit(".", 1)[0] if "." in os.path.basename(dest_path) else dest_path
        dest_path = base + real_ext

    with open(dest_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=16384):
            if chunk:
                f.write(chunk)

    # Reject HTML error pages
    with open(dest_path, "rb") as f:
        magic = f.read(4)
    if magic[:1] in (b"<", b"{") or magic == b"":
        os.remove(dest_path)
        raise ValueError("Server returned an error page instead of the ebook")

    return dest_path
