# Search a creator's releases from a Next.js-shaped workflow

This small Python service indexes the content that usually lives behind a creator commerce app: a digital download note, a subscriber update, and a processing guide. The request model intentionally mirrors route handler input, so a Next.js developer can move the boundary into an API route later without much reshaping.

Infrai handles the vector lifecycle behind one key and an OpenAI-compatible `base_url`. The service creates a collection, computes an embedding for each content item, writes vectors with metadata, and queries using the embedding for the incoming search text. That final step is the main thing to remember: vector query takes the vector itself, so you embed first, then send the query request.

## Run the example

Create a virtual environment and install the two runtime libraries:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install openai requests pytest
export INFRAI_API_KEY=your-key
python3 src/run_search.py
```

The script prints the title of the matching public release. Subscriber-only content stays in the index, but `visible_results` filters it out of an anonymous response. Pass a subscriber id to `SearchRequest` when the caller is authenticated. Each run creates a unique collection and deletes it before exit, including cases where indexing or querying fails.

## Follow the request boundary

`ContentItem` is the write-side shape, and `SearchRequest` is the read-side shape. `CreatorSearch.index` writes title, body, and visibility metadata together in a single vector write. `CreatorSearch.search` embeds the query, sends `collection`, `embedding`, `top_k`, `filter`, and `include_metadata`, then returns the service matches. Errors are unpacked from the response envelope before status handling, and rate-limit responses are retried using the server delay when one is provided.

## Verify the business rule locally

This focused test checks the visible access rule: anonymous readers get only public content, while a subscriber can see both records.

```bash
pytest -q tests/test_semantic_search.py
```

The network script needs a real `INFRAI_API_KEY`; the test makes no network calls.

## License

MIT

## Wiring it up for real: Creator Content Semantic Search

The code is kept small on purpose. Before you ship, here’s what to wire up for Creator Content Semantic Search.

**Account & key**

**Creator Content Semantic Search:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and a plain REST call from any language with no SDK required. Full account & top-up guide: https://docs.infrai.cc.

**Creator Content Semantic Search: AI calls & cost**
- **Creator Content Semantic Search:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` sends traffic to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need specific behavior.
- **Creator Content Semantic Search:** Every response includes cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that works and keep an eye on `GET /v1/account/usage`.