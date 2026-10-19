import logging
from html.parser import HTMLParser

import requests

logger = logging.getLogger(__name__)

FETCH_TIMEOUT_SECONDS = 10
SKIPPED_TAGS = frozenset({"script", "style", "noscript"})


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in SKIPPED_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in SKIPPED_TAGS and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data):
        if not self._skip_depth:
            self.parts.append(data)


def extract_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return " ".join(" ".join(parser.parts).split())


def fetch_full_text(url: str) -> str | None:
    """Download a page and return its visible text, or None if it cannot be read."""
    try:
        response = requests.get(url, timeout=FETCH_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("full-text fetch failed for %s: %s", url, exc)
        return None
    if "html" not in response.headers.get("content-type", ""):
        return None
    return extract_text(response.text) or None
