from unittest.mock import MagicMock

import requests

from app.ingest import fetcher


def test_extract_text_strips_scripts_styles_and_tags():
    html = "<html><style>p{}</style><script>var x=1</script><body><h1>Title</h1><p>Hello <b>world</b></p></body></html>"

    assert fetcher.extract_text(html) == "Title Hello world"


def test_fetch_full_text_returns_extracted_text(monkeypatch):
    response = MagicMock(text="<p>Full article body</p>", headers={"content-type": "text/html; charset=utf-8"})
    monkeypatch.setattr(fetcher.requests, "get", lambda url, timeout: response)

    assert fetcher.fetch_full_text("https://a.com/x") == "Full article body"


def test_fetch_full_text_returns_none_on_request_error(monkeypatch):
    def boom(url, timeout):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(fetcher.requests, "get", boom)

    assert fetcher.fetch_full_text("https://a.com/x") is None


def test_fetch_full_text_returns_none_for_non_html(monkeypatch):
    response = MagicMock(text="%PDF", headers={"content-type": "application/pdf"})
    monkeypatch.setattr(fetcher.requests, "get", lambda url, timeout: response)

    assert fetcher.fetch_full_text("https://a.com/x.pdf") is None
