"""Evidence-driven topic explainer with an observable Think/Act/Observe loop."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import re
import sys
from typing import Callable, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen


class ResearchError(Exception):
    """A research operation could not produce reliable evidence."""


@dataclass(frozen=True)
class Article:
    title: str
    extract: str
    url: str


class KnowledgeSource(Protocol):
    def search(self, topic: str) -> list[str]: ...
    def read(self, title: str) -> Article: ...


class Wikipedia:
    endpoint = "https://en.wikipedia.org/w/api.php"

    def _request(self, params: dict[str, str]) -> dict:
        request = Request(
            self.endpoint + "?" + urlencode({"format": "json", **params}),
            headers={"User-Agent": "WikiTopicAgent/0.1 (educational topic research)"},
        )
        try:
            with urlopen(request, timeout=20) as response:
                data = json.load(response)
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            raise ResearchError(f"Wikipedia request failed: {exc}") from exc
        if "error" in data:
            raise ResearchError("Wikipedia rejected the request.")
        return data

    def search(self, topic: str) -> list[str]:
        data = self._request({"action": "query", "list": "search", "srsearch": topic,
                              "srlimit": "3"})
        return [result["title"] for result in data.get("query", {}).get("search", [])]

    def read(self, title: str) -> Article:
        data = self._request({"action": "query", "prop": "extracts", "titles": title,
                              "explaintext": "1", "exintro": "1", "redirects": "1"})
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            if "missing" not in page and page.get("extract", "").strip():
                resolved = page["title"]
                return Article(resolved, page["extract"].strip(),
                               "https://en.wikipedia.org/wiki/" + quote(resolved.replace(" ", "_")))
        raise ResearchError(f"No introductory text found for {title!r}.")


class TopicAgent:
    """Bounded research loop. Trace entries are decision summaries, not private reasoning."""

    def __init__(self, source: KnowledgeSource, trace: Callable[[str], None] = print):
        self.source = source
        self.trace = trace

    def explain(self, topic: str) -> str:
        topic = topic.strip()
        if not topic:
            raise ValueError("Please enter a nonempty topic.")
        if len(topic) > 500:
            raise ValueError("Please limit the topic to 500 characters.")
        self.trace("THINK: Find reference articles relevant to the requested topic.")
        self.trace(f"ACT: Search Wikipedia for {topic!r}.")
        titles = self.source.search(topic)
        self.trace(f"OBSERVE: Found {len(titles)} candidate article(s).")
        if not titles:
            raise ResearchError("No articles found. Try a more specific topic.")
        articles: list[Article] = []
        for title in titles[:3]:
            self.trace("THINK: Read an introduction to collect grounded explanatory material.")
            self.trace(f"ACT: Read {title!r}.")
            try:
                article = self.source.read(title)
            except ResearchError as exc:
                self.trace(f"OBSERVE: {exc}")
                continue
            if article.url not in {a.url for a in articles}:
                articles.append(article)
            self.trace(f"OBSERVE: Retrieved introductory text for {article.title!r}.")
        if not articles:
            raise ResearchError("Could not retrieve evidence; no explanation was generated.")
        self.trace("THINK: Enough evidence is available for a concise, cited overview.")
        self.trace("ACT: Assemble the explanation from the retrieved introductions.")
        answer = self._answer(topic, articles)
        self.trace("OBSERVE: Explanation contains source references and evidence limitations.")
        return answer

    @staticmethod
    def _answer(topic: str, articles: list[Article]) -> str:
        sections = [f"Topic: {topic}",
                    "Reference-based overview (excerpts from Wikipedia introductions):"]
        for index, article in enumerate(articles, 1):
            sentences = re.split(r"(?<=[.!?])\s+", article.extract)
            excerpt = " ".join(sentences[:4])
            sections.append(f"{article.title} [{index}]\n{excerpt}")
        sections.append("For further study: distinguish the definition, underlying mechanism, "
                        "typical applications, and limitations. The references below offer more detail.")
        sections.append("Sources:\n" + "\n".join(
            f"[{i}] {a.title}: {a.url}" for i, a in enumerate(articles, 1)))
        sections.append("Limitations: search matches may include related or ambiguous topics. "
                        "This is a reference overview, not a peer-reviewed literature review; "
                        "verify academic claims against primary sources.")
        return "\n\n".join(sections)


def main() -> int:
    parser = argparse.ArgumentParser(description="Explain a topic using a Think/Act/Observe research loop.")
    parser.add_argument("topic", nargs="?", help="Topic to explain (prompts if omitted)")
    parser.add_argument("--quiet", action="store_true", help="Hide the stage trace")
    args = parser.parse_args()
    try:
        topic = args.topic if args.topic is not None else input("Enter a topic: ")
        agent = TopicAgent(Wikipedia(), (lambda _: None) if args.quiet else print)
        print("\nFINAL ANSWER\n" + agent.explain(topic))
        return 0
    except (ValueError, ResearchError, EOFError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
