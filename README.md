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
