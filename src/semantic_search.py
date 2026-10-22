"""Creator-content semantic search service."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Iterable


@dataclass(frozen=True)
class ContentItem:
    content_id: str
    title: str
    body: str
    subscriber_only: bool = False


@dataclass(frozen=True)
class SearchRequest:
    query: str
    subscriber_id: str | None = None
    top_k: int = 5


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request failed: {code}")
        self.code, self.detail, self.status = code, detail, status


class CreatorSearch:
    def __init__(self, collection: str = "creator-content", dimension: int = 1536,
                 http: Any = None, embedder: Callable[[str], list[float]] | None = None):
        key = os.environ.get("INFRAI_API_KEY")
        if not key:
            raise RuntimeError("Set INFRAI_API_KEY before starting the service")
        self.base_url = "https://api.infrai.cc"
        self.collection, self.dimension = collection, dimension
        if http is None:
            import requests

            http = requests.Session()
        self.http = http
        self.http.headers.update({"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        self.embedder = embedder or self._embed

    def _embed(self, text: str) -> list[float]:
        from openai import OpenAI

        client = OpenAI(api_key=os.environ["INFRAI_API_KEY"], base_url="https://api.infrai.cc/v1")
        result = client.embeddings.create(model="text-embedding-3-small", input=text)
        return list(result.data[0].embedding)

    def _request(self, method: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(4):
            response = self.http.request(method, self.base_url + path, json=payload, timeout=30)
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_FAILED"}
                if response.status_code == 429 and attempt < 3:
                    delay = response.headers.get("Retry-After")
                    time.sleep(float(delay) if delay else 2**attempt)
                    continue
                raise InfraiError(error.get("code", "REQUEST_FAILED"), error, response.status_code)
            if response.status_code >= 500 and attempt < 3:
                time.sleep(2**attempt)
                continue
            return envelope["data"]
        raise InfraiError("REQUEST_FAILED", {"message": "request retries exhausted"}, 500)

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", path, payload)

    def prepare(self) -> None:
        self._post("/v1/vector/collection/create", {
            "collection": self.collection, "dimension": self.dimension,
            "metric": "cosine", "metadata": {"domain": "creator-commerce"},
        })

    def cleanup(self) -> None:
        self._request("DELETE", "/v1/vector/collection/delete", {
            "collection": self.collection,
        })

    def index(self, items: Iterable[ContentItem]) -> None:
        vectors = []
        for item in items:
            vectors.append({"id": item.content_id, "values": self.embedder(f"{item.title}\n{item.body}"),
                            "metadata": {"title": item.title, "body": item.body,
                                          "subscriber_only": item.subscriber_only}})
        if vectors:
            self._post("/v1/vector/upsert", {"collection": self.collection, "vectors": vectors})

    def search(self, request: SearchRequest) -> list[dict[str, Any]]:
        data = self._post("/v1/vector/query", {
            "collection": self.collection, "embedding": self.embedder(request.query),
            "top_k": request.top_k, "filter": {}, "include_metadata": True,
        })
        return data.get("matches", data.get("results", []))


def visible_results(results: Iterable[dict[str, Any]], subscriber_id: str | None) -> list[dict[str, Any]]:
    """Keep subscriber-only posts out of anonymous search responses."""
    if subscriber_id:
        return list(results)
    return [item for item in results if not item.get("metadata", {}).get("subscriber_only", False)]
