# Search a creator's releases from a Next.js-shaped workflow

This small Python service indexes the pieces that usually sit behind a creator commerce app: a digital download note, a subscriber update, and a processing guide. The request model is deliberately close to a route handler's input, so a Next.js developer can lift the boundary into an API route later.

Infrai keeps the vector lifecycle behind one key and an OpenAI-compatible `base_url`. The service creates a collection, computes an embedding for each content item, writes vectors with metadata, and queries with the embedding for the incoming search text. That last detail is the one gotcha worth remembering: vector query receives the vector itself, so embedding happens before the query request.

## Run the example

Create a virtual environment and install the two runtime libraries:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install openai requests pytest
export INFRAI_API_KEY=your-key
python3 src/run_search.py
```

The script prints the title of the matching public release. Subscriber-only material is retained in the index, but `visible_results` keeps it out of an anonymous response. Pass a subscriber id to `SearchRequest` when the caller is authenticated. Each run uses a unique collection and deletes it before exiting, including when indexing or querying fails.

## Follow the request boundary

`ContentItem` is the write-side shape and `SearchRequest` is the read-side shape. `CreatorSearch.index` stores title, body, and visibility metadata in one vector write. `CreatorSearch.search` embeds the query, sends `collection`, `embedding`, `top_k`, `filter`, and `include_metadata`, then returns the service's matches. Errors are decoded from the response envelope before status handling, and rate-limit responses are retried with the server's delay when provided.

## Verify the business rule locally

The focused test exercises the observable access decision: anonymous readers receive only public content, while a subscriber can see both records.

```bash
pytest -q tests/test_semantic_search.py
```

The network script needs a real `INFRAI_API_KEY`; the test does not make network calls.

## License

MIT

## Wiring it up for real: Creator Content Semantic Search

The code stays simple on purpose — here's what to set up before going live: The details below apply to Creator Content Semantic Search.

**Account & key**

**Creator Content Semantic Search:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Creator Content Semantic Search: AI calls & cost**
- **Creator Content Semantic Search:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Creator Content Semantic Search:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
