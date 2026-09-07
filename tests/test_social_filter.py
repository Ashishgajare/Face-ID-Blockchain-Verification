from search.social_filter import filter_social_results


def test_filter_social_results_keeps_supported_platforms():
    results = [
        {"title": "Instagram post", "link": "https://www.instagram.com/p/abc123/", "source": "Instagram", "thumbnail": "https://example.com/a.jpg", "position": 1},
        {"title": "Random blog", "link": "https://exampleblog.com/article", "source": "Example", "thumbnail": "https://example.com/b.jpg", "position": 2},
        {"title": "X post", "link": "https://x.com/user/status/123", "source": "X", "thumbnail": "https://example.com/c.jpg", "position": 3},
    ]

    filtered = filter_social_results(results)

    assert [item["platform"] for item in filtered] == ["instagram", "x"]
    assert all(item["url"].startswith("https://") for item in filtered)
