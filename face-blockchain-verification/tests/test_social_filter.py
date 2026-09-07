from reverse_search.result_parser import SearchResult
from reverse_search.social_filter import filter_social_results


def test_social_filter_detects_instagram():
    r = SearchResult(title="post", link="https://www.instagram.com/p/ABC/", source="www.instagram.com", thumbnail=None, position=1, raw={})
    out = filter_social_results([r])
    assert len(out) == 1
    assert out[0].platform in ("www", "instagram", "www.instagram") or "instagram" in out[0].platform


def test_social_filter_ignores_other():
    r = SearchResult(title="blog", link="https://example.com/photo.jpg", source="example.com", thumbnail=None, position=1, raw={})
    out = filter_social_results([r])
    assert len(out) == 0


def test_social_filter_normalizes_supported_domains():
    urls = [
        "https://www.instagram.com/p/ABC/",
        "https://www.facebook.com/example/",
        "https://x.com/example/status/1",
        "https://twitter.com/example/status/1",
        "https://www.linkedin.com/in/example/",
    ]
    results = [
        SearchResult(title="post", link=url, source=None, thumbnail=None, position=index, raw={})
        for index, url in enumerate(urls, start=1)
    ]

    out = filter_social_results(results)

    assert [candidate.platform for candidate in out] == [
        "instagram",
        "facebook",
        "x",
        "twitter",
        "linkedin",
    ]
