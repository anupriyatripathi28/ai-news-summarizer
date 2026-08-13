"""
scraper.py
----------
Fetches and extracts article content from news websites.

Uses several extraction strategies:
1. JSON-LD Article/NewsArticle data
2. Common article containers
3. Meta description fallback
4. General paragraph fallback
"""

import json
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

REQUEST_TIMEOUT = 15

UNWANTED_TAGS = [
    "script",
    "style",
    "nav",
    "footer",
    "header",
    "aside",
    "form",
    "noscript",
    "iframe",
]

ARTICLE_SELECTORS = [
    "article",
    "[itemprop='articleBody']",
    ".article-body",
    ".article-content",
    ".artText",
    ".story-body",
    ".story-content",
    ".entry-content",
    ".post-content",
    "main",
]


class ScraperError(Exception):
    """Custom exception for scraping failures."""
    pass


def fetch_article(url):
    """
    Download the page and extract (title, article_text).
    """

    if not url or not url.startswith(("http://", "https://")):
        raise ScraperError(
            "Please enter a valid URL starting with http:// or https://"
        )

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        response.raise_for_status()

    except requests.exceptions.Timeout:
        raise ScraperError(
            "The request timed out. The website may be slow or unreachable."
        )

    except requests.exceptions.HTTPError as e:
        raise ScraperError(
            f"The website returned an error: {e}"
        )

    except requests.exceptions.RequestException as e:
        raise ScraperError(
            f"Could not reach the website: {e}"
        )

    soup = BeautifulSoup(response.text, "lxml")

    # ---------------------------------------------------------
    # Remove obvious non-article content
    # ---------------------------------------------------------
    for tag in soup(UNWANTED_TAGS):
        tag.decompose()

    title = _extract_title(soup)

    # ---------------------------------------------------------
    # Strategy 1: JSON-LD
    # Many news websites expose articleBody here.
    # ---------------------------------------------------------
    content = _extract_jsonld_article(soup)

    if _is_valid_content(content):
        return title, content

    # ---------------------------------------------------------
    # Strategy 2: Known article containers
    # ---------------------------------------------------------
    content = _extract_from_selectors(soup)

    if _is_valid_content(content):
        return title, content

    # ---------------------------------------------------------
    # Strategy 3: Metadata description
    # Useful as a small fallback, but normally too short
    # for a complete article.
    # ---------------------------------------------------------
    description = _extract_meta_description(soup)

    if _is_valid_content(description, minimum_words=20):
        return title, description

    # ---------------------------------------------------------
    # Strategy 4: All paragraphs
    # ---------------------------------------------------------
    paragraphs = soup.find_all("p")
    content = _paragraphs_to_text(paragraphs)

    if _is_valid_content(content):
        return title, content

    raise ScraperError(
        "Couldn't find enough readable article text on this page. "
        "The website may require JavaScript, block automated requests, "
        "or use a page structure that this scraper does not recognize."
    )


def _extract_title(soup):
    """Extract the article title."""

    # Prefer h1
    h1 = soup.find("h1")

    if h1:
        title = h1.get_text(" ", strip=True)
        if title:
            return title

    # OpenGraph title
    og_title = soup.find("meta", property="og:title")

    if og_title and og_title.get("content"):
        return og_title["content"].strip()

    # Normal HTML title
    if soup.title:
        title = soup.title.get_text(" ", strip=True)
        if title:
            return title

    return "Untitled Article"


def _extract_jsonld_article(soup):
    """
    Try extracting articleBody from JSON-LD.

    Many modern news websites include Article/NewsArticle
    metadata in <script type="application/ld+json">.
    """

    scripts = soup.find_all(
        "script",
        type="application/ld+json"
    )

    for script in scripts:

        raw = script.string or script.get_text()

        if not raw.strip():
            continue

        try:
            data = json.loads(raw)

        except (json.JSONDecodeError, TypeError):
            continue

        candidates = []

        if isinstance(data, dict):
            candidates.append(data)

            # Handle @graph
            graph = data.get("@graph")

            if isinstance(graph, list):
                candidates.extend(
                    item for item in graph
                    if isinstance(item, dict)
                )

        elif isinstance(data, list):
            candidates.extend(
                item for item in data
                if isinstance(item, dict)
            )

        for item in candidates:

            article_body = item.get("articleBody")

            if isinstance(article_body, str):
                cleaned = article_body.strip()

                if _is_valid_content(cleaned):
                    return cleaned

    return ""


def _extract_from_selectors(soup):
    """Try common article-body selectors."""

    for selector in ARTICLE_SELECTORS:

        container = soup.select_one(selector)

        if not container:
            continue

        # Prefer paragraphs inside the container
        paragraphs = container.find_all("p")

        if paragraphs:
            text = _paragraphs_to_text(paragraphs)

            if _is_valid_content(text):
                return text

        # Fallback to all text inside the container
        text = container.get_text(
            " ",
            strip=True
        )

        if _is_valid_content(text):
            return text

    return ""


def _extract_meta_description(soup):
    """Extract OpenGraph/meta description."""

    for attribute, value in [
        ("property", "og:description"),
        ("name", "description"),
    ]:

        tag = soup.find(
            "meta",
            attrs={attribute: value}
        )

        if tag and tag.get("content"):
            return tag["content"].strip()

    return ""


def _paragraphs_to_text(paragraphs):
    """Clean and join article paragraphs."""

    lines = []

    for paragraph in paragraphs:

        text = paragraph.get_text(
            " ",
            strip=True
        )

        # Ignore very short navigation/junk fragments
        if len(text.split()) >= 5:
            lines.append(text)

    return "\n\n".join(lines)


def _is_valid_content(text, minimum_words=30):
    """Check whether extracted text is sufficiently large."""

    if not text:
        return False

    return len(text.split()) >= minimum_words