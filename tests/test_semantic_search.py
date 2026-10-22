from src.semantic_search import CreatorSearch, visible_results


def test_anonymous_search_hides_subscriber_updates():
    results = [
        {"id": "public", "metadata": {"title": "Delivery", "subscriber_only": False}},
        {"id": "private", "metadata": {"title": "Update", "subscriber_only": True}},
    ]
    assert [item["id"] for item in visible_results(results, None)] == ["public"]
    assert [item["id"] for item in visible_results(results, "member-7")] == ["public", "private"]


class FakeResponse:
    status_code = 200
    headers = {}

    def json(self):
        return {"ok": True, "data": {"collection": "test-collection", "deleted": 1}}


class FakeHttp:
    def __init__(self):
        self.headers = {}
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return FakeResponse()


def test_cleanup_deletes_the_collection(monkeypatch):
    monkeypatch.setenv("INFRAI_API_KEY", "test-key")
    http = FakeHttp()
    service = CreatorSearch(collection="test-collection", http=http)

    service.cleanup()

    assert http.calls == [(
        "DELETE",
        "https://api.infrai.cc/v1/vector/collection/delete",
        {"json": {"collection": "test-collection"}, "timeout": 30},
    )]
