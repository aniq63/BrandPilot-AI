import re
import time
from collections import deque
from typing import Annotated
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup

from src.utilis.logging import logger, log_calls

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; StartupInfoBot/1.0)"}
SKIP_EXT = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".zip",
            ".mp4", ".mp3", ".css", ".js", ".ico", ".xml", ".json")
PRIORITY_WORDS = ("about", "team", "company", "product", "service", "solution",
                  "pricing", "contact", "career", "job", "blog", "news",
                  "press", "customer", "feature", "faq", "mission")
SOCIAL_DOMAINS = ("linkedin.com", "twitter.com", "x.com", "facebook.com",
                  "instagram.com", "youtube.com", "github.com", "crunchbase.com",
                  "tiktok.com", "medium.com")


def _normalize(url: str) -> str:
    url, _ = urldefrag(url)
    return url.rstrip("/")


def _same_site(url: str, base_netloc: str) -> bool:
    n = urlparse(url).netloc.lower().replace("www.", "")
    return n == base_netloc.lower().replace("www.", "")


def _priority(url: str) -> int:
    path = urlparse(url).path.lower()
    return 0 if any(w in path for w in PRIORITY_WORDS) else 1


@log_calls
def _fetch(url: str, timeout: int):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200 and "text/html" in r.headers.get("Content-Type", ""):
            return r.text
    except requests.RequestException as exc:
        logger.warning("Request failed for %s: %s", url, exc)
    return None


@log_calls
def _parse_page(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    raw_text = soup.get_text(" ", strip=True)

    meta = {}
    for tag in soup.find_all("meta"):
        key = tag.get("name") or tag.get("property")
        if key in ("description", "og:description", "og:title", "og:site_name", "keywords"):
            meta[key] = (tag.get("content") or "").strip()

    emails = set(re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", raw_text))
    emails |= {a["href"][7:].split("?")[0] for a in soup.select('a[href^="mailto:"]')}
    phones = {a["href"][4:] for a in soup.select('a[href^="tel:"]')}

    socials = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(url, a["href"])
        if any(d in urlparse(href).netloc for d in SOCIAL_DOMAINS):
            socials.add(href)

    links = {_normalize(urljoin(url, a["href"])) for a in soup.find_all("a", href=True)
             if a["href"].startswith(("http", "/", "./", "../")) or not a["href"].startswith(("mailto:", "tel:", "#", "javascript:"))}

    for t in soup(["script", "style", "noscript", "svg", "iframe", "form"]):
        t.decompose()

    headings = [(h.name.upper(), h.get_text(" ", strip=True))
                for h in soup.find_all(["h1", "h2", "h3"]) if h.get_text(strip=True)]
    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")
                  if len(p.get_text(strip=True)) > 40]
    bullets = [li.get_text(" ", strip=True) for li in soup.find_all("li")
               if 15 < len(li.get_text(strip=True)) < 300]

    return {
        "title": soup.title.get_text(strip=True) if soup.title else "",
        "meta": meta, "headings": headings, "paragraphs": paragraphs,
        "bullets": bullets, "emails": emails, "phones": phones,
        "socials": socials, "links": links,
    }


@log_calls
def extract_startup_info(
    website_url: Annotated[str, "The official website URL of the startup."],
    max_pages: Annotated[int, "Maximum number of pages to crawl."] = 25,
    timeout: Annotated[int, "Request timeout in seconds."] = 10,
    delay: Annotated[float, "Delay between requests in seconds (be polite)."] = 0.5,
) -> str:
    """Crawl a startup's website (same domain only) and return all extracted
    information as one formatted string."""
    if not website_url.startswith(("http://", "https://")):
        website_url = "https://" + website_url
    start = _normalize(website_url)
    base_netloc = urlparse(start).netloc

    queue, seen, pages = deque([start]), {start}, []
    all_emails, all_phones, all_socials = set(), set(), set()

    while queue and len(pages) < max_pages:
        url = queue.popleft()
        html = _fetch(url, timeout)
        if not html:
            continue
        data = _parse_page(html, url)
        data["url"] = url
        pages.append(data)
        all_emails |= data["emails"]
        all_phones |= data["phones"]
        all_socials |= data["socials"]

        new_links = [l for l in data["links"]
                     if l not in seen and _same_site(l, base_netloc)
                     and not l.lower().endswith(SKIP_EXT)]
        for l in sorted(new_links, key=_priority):
            seen.add(l)
            queue.append(l)
        # keep priority pages (about/team/pricing...) at the front
        queue = deque(sorted(queue, key=_priority))
        time.sleep(delay)

    if not pages:
        logger.warning("Could not fetch any content from %s", website_url)
        return f"Could not fetch any content from {website_url}."

    home = pages[0]
    out = []
    out.append("=" * 70)
    out.append(f"STARTUP WEBSITE REPORT: {base_netloc}")
    out.append("=" * 70)
    out.append(f"Homepage Title : {home['title']}")
    for k, v in home["meta"].items():
        out.append(f"{k:<15}: {v}")
    out.append(f"Pages crawled  : {len(pages)}")

    out.append("\n" + "-" * 70 + "\nCONTACT & SOCIAL\n" + "-" * 70)
    out.append("Emails  : " + (", ".join(sorted(all_emails)) or "N/A"))
    out.append("Phones  : " + (", ".join(sorted(all_phones)) or "N/A"))
    out.append("Socials :")
    out.extend(f"  - {s}" for s in sorted(all_socials)) if all_socials else out.append("  N/A")

    seen_text = set()
    for i, p in enumerate(pages, 1):
        out.append("\n" + "-" * 70)
        out.append(f"PAGE {i}: {p['title'] or '(no title)'}")
        out.append(f"URL: {p['url']}")
        out.append("-" * 70)
        if p["meta"].get("description"):
            out.append(f"Description: {p['meta']['description']}")
        if p["headings"]:
            out.append("\nHeadings:")
            for lvl, txt in p["headings"]:
                if txt not in seen_text:
                    seen_text.add(txt)
                    out.append(f"  [{lvl}] {txt}")
        paras = [t for t in p["paragraphs"] if t not in seen_text]
        if paras:
            out.append("\nContent:")
            for t in paras:
                seen_text.add(t)
                out.append(f"  {t}")
        bl = [t for t in p["bullets"] if t not in seen_text]
        if bl:
            out.append("\nKey points:")
            for t in bl:
                seen_text.add(t)
                out.append(f"  • {t}")

    return "\n".join(out)


# Usage:
# startup_info = extract_startup_info("https://www.cognifyanalytics.com/")