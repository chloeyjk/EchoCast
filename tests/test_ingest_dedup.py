from app.ingest.dedup import content_hash, normalize_url


def test_normalize_url_drops_tracking_params_fragment_and_trailing_slash():
    url = "HTTPS://Example.com/news/story/?utm_source=x&id=7&utm_medium=y#section"

    assert normalize_url(url) == "https://example.com/news/story?id=7"


def test_normalize_url_sorts_remaining_query_params():
    assert normalize_url("https://a.com/p?b=2&a=1") == normalize_url("https://a.com/p?a=1&b=2")


def test_content_hash_ignores_whitespace_and_case():
    assert content_hash("Hello   World\n") == content_hash("hello world")


def test_content_hash_differs_for_different_text():
    assert content_hash("one") != content_hash("two")
