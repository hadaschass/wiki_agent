# Wiki Topic Agent

A small Python research agent that accepts a topic and returns a cited introductory
explanation. Its bounded processing cycle is **Think → Act → Observe**, repeated
until it has enough evidence for a final answer. Think entries describe the next
decision briefly; they do not expose private chain-of-thought.

## Run

Requires Python 3.10+ and HTTPS access to `en.wikipedia.org`. No packages or API keys
are required.

```sh
python wiki_agent.py "software engineering"
python wiki_agent.py                 # interactive topic prompt
python wiki_agent.py --quiet "dependency injection"
```

The agent searches Wikipedia, reads up to three article introductions, and
assembles excerpts with numbered source links. It reports retrieval failures and
does not invent an answer when no evidence can be read. This first version uses
deterministic decisions and source excerpts, rather than an LLM, so it requires no
model credentials. It provides a reference overview, not an original synthesis or
a peer-reviewed literature survey. Search matches can be ambiguous.

## Development

```sh
python -m unittest -v
```

Tests use an injected knowledge source and need no network. A live smoke test is
`python wiki_agent.py --quiet "software engineering"`; verify that the final
answer includes retrieved introductory text and Wikipedia source URLs.

The `KnowledgeSource` protocol makes alternative sources or an LLM-backed
synthesis layer possible. Retrieved text must be treated as evidence, not as
instructions. The loop reads at most three candidates, uses request timeouts,
and keeps failures distinct from successful observations.

## Browser interface

```sh
python web_app.py
```

Open `http://127.0.0.1:8000` in a browser on the same machine. Enter a topic and
select **Explain topic**. The page shows the explanation and expandable research
stages, with loading and error messages. No additional packages are needed.

Use `--port 8080` to select a different port. The server binds to loopback by
 default; it is a local development interface without authentication. Wikipedia
access is still required for actual explanations. Interface tests use a fake
source to verify HTTP requests without external network access.

## Publish on Render

This repository includes a Render Blueprint (`render.yaml`) for a free web
service using Gunicorn. Render provides the public HTTPS endpoint. The free
service can sleep when idle, so the first request may take longer.

1. Sign in to Render and choose **New → Blueprint**.
2. Connect `hadaschass/wiki_agent`, select `main`, and apply the Blueprint.
3. Wait for the deployment to become live, then open the URL shown by Render
   and submit a topic to verify the explanation and citations.

No application secrets are needed. Wikipedia must be reachable from the host.
For production-server checks locally, install `requirements.txt` in a virtual
 environment and run `gunicorn wsgi_app:application --bind 127.0.0.1:8000
 --workers 1 --threads 4 --timeout 120`. This is a small public demo; there is no
user authentication or persistent user data.
