from uuid import uuid4

from semantic_search import ContentItem, CreatorSearch, SearchRequest, visible_results


def main() -> None:
    service = CreatorSearch(collection=f"creator-content-example-{uuid4().hex}")
    prepared = False
    try:
        service.prepare()
        prepared = True
        service.index([
            ContentItem("delivery-101", "Digital asset delivery", "Signed download links for a paid bundle."),
            ContentItem("update-201", "Subscriber update", "A private note about this week's release.", True),
            ContentItem("processing-301", "Content processing", "Queue and process uploaded creator media."),
        ])
        request = SearchRequest("How do I deliver a paid digital bundle?")
        matches = visible_results(service.search(request), request.subscriber_id)
        for match in matches:
            print(match.get("metadata", {}).get("title", match.get("id")))
    finally:
        if prepared:
            service.cleanup()


if __name__ == "__main__":
    main()
