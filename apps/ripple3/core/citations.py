"""Citation and source tracking for all AI-generated analyses.

Every analysis output should attach its data sources so users can verify
claims and understand where information came from.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Citation:
    title: str
    url: str
    snippet: str = ""
    relevance: str = ""


@dataclass
class CitationList:
    citations: list[Citation] = field(default_factory=list)
    _seen_urls: set[str] = field(default_factory=set, repr=False)

    def add(self, title: str, url: str, snippet: str = "", relevance: str = "") -> None:
        if url and url not in self._seen_urls:
            self._seen_urls.add(url)
            self.citations.append(Citation(
                title=title, url=url,
                snippet=snippet, relevance=relevance,
            ))

    def add_from_search(self, results: list) -> None:
        """Add citations from SearchResult or NewsResult objects."""
        for r in results:
            url = getattr(r, "url", "")
            title = getattr(r, "title", "")
            snippet = getattr(r, "snippet", "")
            if url:
                self.add(title, url, snippet)

    def to_markdown(self) -> str:
        if not self.citations:
            return ""
        lines = ["## 📚 参考来源\n"]
        for i, c in enumerate(self.citations, 1):
            line = f"{i}. [{c.title}]({c.url})"
            if c.relevance:
                line += f" — {c.relevance}"
            lines.append(line)
        return "\n".join(lines)

    def to_list(self) -> list[dict]:
        return [
            {"title": c.title, "url": c.url, "snippet": c.snippet, "relevance": c.relevance}
            for c in self.citations
        ]

    def __len__(self) -> int:
        return len(self.citations)


def format_sources_footer(search_results: list, news_results: list | None = None) -> str:
    """Build a markdown footer with all data sources used in an analysis."""
    cl = CitationList()
    cl.add_from_search(search_results)
    if news_results:
        cl.add_from_search(news_results)
    return cl.to_markdown()
