import os
import re
import ssl
import urllib.request
import cloudscraper
from bs4 import BeautifulSoup

BASE = "https://annas-archive.gl"
LIBGEN = "https://libgen.li"

scraper = cloudscraper.create_scraper()

# SSL context that ignores cert errors — handles CDNs with broken certs (cdn2/cdn3.booksdl.lc)
_no_verify_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
_no_verify_ctx.check_hostname = False
_no_verify_ctx.verify_mode = ssl.CERT_NONE
try:
    _no_verify_ctx.set_ciphers("DEFAULT:@SECLEVEL=0")
except ssl.SSLError:
    pass

_EXCLUDE_SOURCES = ["zlib", "upload", "ia", "hathi", "duxiu", "nexusstc", "zlibzh", "magzdb", "scihub"]


def _search_one(query: str, ext: str, limit: int) -> list[dict]:
    params = [("q", query), ("ext", ext)]
    for src in _EXCLUDE_SOURCES:
        params.append(("src", f"anti__{src}"))
    try:
        resp = scraper.get(f"{BASE}/search", params=params, timeout=20)
        resp.raise_for_status()
    except Exception:
        return []

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


def search_books(query: str, limit: int = 8) -> list[dict]:
    """Search Anna's Archive for epub books, filtered to Libgen sources."""
    seen: set[str] = set()
    combined: list[dict] = []

    def _add(results: list[dict]) -> None:
        for r in results:
            if r["md5"] not in seen:
                seen.add(r["md5"])
                combined.append(r)

    _add(_search_one(query, "epub", limit))

    # Bonus pass with author last name — surfaces copies on alternate CDNs
    if combined:
        author = combined[0].get("author", "")
        last_name = author.split()[-1] if author else ""
        if last_name and last_name.lower() not in query.lower():
            _add(_search_one(f"{query} {last_name}", "epub", 4))

    return combined


def get_download_urls(md5: str) -> list[str]:
    """Return all direct download URLs from libgen.li ads.php."""
    try:
        resp = scraper.get(f"{LIBGEN}/ads.php?md5={md5}", timeout=15)
        resp.raise_for_status()
    except Exception:
        return []
    matches = re.findall(r'href="(get\.php\?md5=[^"]+)"', resp.text)
    return [f"{LIBGEN}/{m}" for m in matches]


def download_book(url: str, dest_path: str) -> str:
    """Download epub from libgen CDN. Returns actual saved path.
    Raises if the file is not epub or appears to be an error page.
    """
    # Follow the get.php redirect to find the real CDN URL
    redirect = scraper.get(url, allow_redirects=False, timeout=15)
    if redirect.status_code in (301, 302, 307, 308):
        final_url = redirect.headers.get("Location", url)
    else:
        final_url = url

    # Open connection and check Content-Disposition BEFORE downloading body
    req = urllib.request.Request(
        final_url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; kindle-master/1.0)"},
    )
    with urllib.request.urlopen(req, context=_no_verify_ctx, timeout=30) as response:
        cd = response.headers.get("Content-Disposition", "")
        ext_match = re.search(r"\.(\w+)[\"'\s]?\s*$", cd, re.IGNORECASE)
        real_ext = ("." + ext_match.group(1).lower()) if ext_match else ".epub"

        if real_ext not in (".epub", ".pdf"):
            raise ValueError(f"Unsupported format: {real_ext}")

        base = dest_path.rsplit(".", 1)[0] if "." in os.path.basename(dest_path) else dest_path
        dest_path = base + ".epub"

        import socket
        
        with open(dest_path, "wb") as f:
            while True:
                # Enforce a socket timeout specifically for reading chunk data
                # to prevent slow-loris server hangs
                socket.setdefaulttimeout(15) 
                chunk = response.read(16384)
                if not chunk:
                    break
                f.write(chunk)

    # Reject HTML error pages masquerading as files
    with open(dest_path, "rb") as f:
        magic = f.read(4)
    if magic[:1] in (b"<", b"{") or magic == b"":
        os.remove(dest_path)
        raise ValueError("Server returned an error page instead of the ebook")

    return dest_path
