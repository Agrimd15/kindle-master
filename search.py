import os
import re
import shutil
import ssl
import subprocess
from concurrent.futures import ThreadPoolExecutor

import requests
from requests.adapters import HTTPAdapter
import cloudscraper
from bs4 import BeautifulSoup

# Anna's Archive mirrors — tried in order, first that returns results wins
ANNA_MIRRORS = [
    "https://annas-archive.gl",
    "https://annas-archive.org",
    "https://annas-archive.se",
    "https://welib.org",
]

# Libgen mirrors — all queried, URLs aggregated
LIBGEN_MIRRORS = [
    "https://libgen.li",
    "https://libgen.pw",
    "https://libgen.rs",
    "https://libgen.is",
]

scraper = cloudscraper.create_scraper()

# Separate session for CDN downloads with SSL verification disabled.
# verify=False on cloudscraper broke in Python 3.14 — need a proper HTTPAdapter.
class _NoVerifyAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        try:
            ctx.set_ciphers("DEFAULT:@SECLEVEL=0")
        except ssl.SSLError:
            pass
        kwargs["ssl_context"] = ctx
        super().init_poolmanager(*args, **kwargs)

_dl_session = requests.Session()
_dl_session.headers["User-Agent"] = "Mozilla/5.0"
_dl_session.mount("https://", _NoVerifyAdapter())
_dl_session.mount("http://", _NoVerifyAdapter())

_CALIBRE = shutil.which("ebook-convert")

_EXCLUDE_SOURCES = ["zlib", "upload", "ia", "hathi", "duxiu", "nexusstc", "zlibzh", "magzdb", "scihub"]


def _search_one(query: str, ext: str, limit: int, base: str) -> list[dict]:
    params = [("q", query), ("ext", ext)]
    for src in _EXCLUDE_SOURCES:
        params.append(("src", f"anti__{src}"))
    try:
        resp = scraper.get(f"{base}/search", params=params, timeout=20)
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
            "url": base + href,
            "md5": href[len("/md5/"):],
        })
        if len(results) >= limit:
            break

    return results


def _search_ia(query: str, limit: int) -> list[dict]:
    """Search Internet Archive for epub books."""
    try:
        resp = scraper.get(
            "https://archive.org/advancedsearch.php",
            params=[
                ("q", f"{query} format:epub mediatype:texts"),
                ("fl[]", "identifier"),
                ("fl[]", "title"),
                ("fl[]", "creator"),
                ("rows", limit),
                ("output", "json"),
                ("sort", "downloads desc"),
            ],
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    results = []
    for doc in data.get("response", {}).get("docs", []):
        ia_id = doc.get("identifier", "")
        title = doc.get("title", "")
        creator = doc.get("creator", "")
        if isinstance(creator, list):
            creator = ", ".join(creator)
        if not ia_id or not title:
            continue
        results.append({
            "title": title,
            "author": creator,
            "url": f"https://archive.org/details/{ia_id}",
            "ia_id": ia_id,
        })

    return results


def search_books(query: str, limit: int = 8) -> list[dict]:
    """Search for epub books across Anna's Archive mirrors, falling back to Internet Archive."""
    seen: set[str] = set()
    combined: list[dict] = []

    def _add(results: list[dict]) -> None:
        for r in results:
            key = r.get("md5") or r.get("ia_id", "")
            if key and key not in seen:
                seen.add(key)
                combined.append(r)

    # Try Anna's Archive mirrors in order — stop at first that returns results
    for mirror in ANNA_MIRRORS:
        results = _search_one(query, "epub", limit, mirror)
        if results:
            _add(results)
            # Bonus pass with author last name to surface alternate CDN copies
            author = results[0].get("author", "")
            last_name = author.split()[-1] if author else ""
            if last_name and last_name.lower() not in query.lower():
                _add(_search_one(f"{query} {last_name}", "epub", 4, mirror))
            break

    # Fall back to Internet Archive if no Anna's Archive results
    if not combined:
        _add(_search_ia(query, limit))

    return combined


def _fetch_mirror_urls(mirror: str, md5: str) -> list[str]:
    try:
        resp = scraper.get(f"{mirror}/ads.php?md5={md5}", timeout=15)
        resp.raise_for_status()
    except Exception:
        return []
    return [f"{mirror}/{m}" for m in re.findall(r'href="(get\.php\?md5=[^"]+)"', resp.text)]


def get_download_urls(md5: str) -> list[str]:
    """Return direct download URLs from all libgen mirrors in parallel, deduplicated."""
    seen: set[str] = set()
    urls: list[str] = []
    with ThreadPoolExecutor(max_workers=len(LIBGEN_MIRRORS)) as ex:
        for mirror_urls in ex.map(_fetch_mirror_urls, LIBGEN_MIRRORS, [md5] * len(LIBGEN_MIRRORS)):
            for url in mirror_urls:
                if url not in seen:
                    seen.add(url)
                    urls.append(url)
    return urls


def get_download_urls_for_book(book: dict) -> list[str]:
    """Unified resolver: returns download URLs for any book result (libgen or IA)."""
    if "ia_id" in book:
        url = get_ia_download_url(book["ia_id"])
        return [url] if url else []
    return get_download_urls(book["md5"])


def get_ia_download_url(ia_id: str) -> str | None:
    """Find the epub download URL for an Internet Archive item."""
    try:
        resp = scraper.get(f"https://archive.org/metadata/{ia_id}", timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None

    for f in data.get("files", []):
        name = f.get("name", "")
        if name.lower().endswith(".epub"):
            return f"https://archive.org/download/{ia_id}/{name}"

    return None


def download_book(url: str, dest_path: str) -> str:
    """Download epub/mobi from libgen CDN or Internet Archive. Returns path to an epub.
    Mobi files are converted to epub via calibre if available.
    Raises on unsupported format or error page.
    """
    # Follow the get.php redirect to find the real CDN URL
    redirect = scraper.get(url, allow_redirects=False, timeout=15)
    final_url = redirect.headers.get("Location", url) if redirect.status_code in (301, 302, 307, 308) else url

    # Use SSL-bypassing session for CDN downloads
    response = _dl_session.get(final_url, stream=True, timeout=30)
    response.raise_for_status()

    cd = response.headers.get("Content-Disposition", "")
    ext_match = re.search(r"\.(\w+)[\"'\s]?\s*$", cd, re.IGNORECASE)
    real_ext = ("." + ext_match.group(1).lower()) if ext_match else ".epub"

    if real_ext not in (".epub", ".pdf", ".mobi"):
        raise ValueError(f"Unsupported format: {real_ext}")

    base = dest_path.rsplit(".", 1)[0] if "." in os.path.basename(dest_path) else dest_path
    file_path = base + real_ext

    with open(file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=16384):
            if chunk:
                f.write(chunk)

    # Reject HTML error pages masquerading as files
    with open(file_path, "rb") as f:
        magic = f.read(4)
    if magic[:1] in (b"<", b"{") or magic == b"":
        os.remove(file_path)
        raise ValueError("Server returned an error page instead of the ebook")

    # Convert mobi → epub via calibre
    if real_ext == ".mobi":
        if not _CALIBRE:
            os.remove(file_path)
            raise ValueError("mobi format requires calibre (brew install calibre)")
        epub_path = base + ".epub"
        subprocess.run([_CALIBRE, file_path, epub_path], check=True, timeout=120, capture_output=True)
        os.remove(file_path)
        return epub_path

    return file_path
