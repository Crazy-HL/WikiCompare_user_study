from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, quote, unquote, urlparse


class WikiUrlError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedWikiUrl:
    title: str
    normalized_url: str
    revision: str | None


def parse_english_wikipedia_url(url: str) -> ParsedWikiUrl:
    parsed = urlparse(url)
    if not _is_allowed_english_wikipedia_host(parsed):
        raise WikiUrlError("Only en.wikipedia.org URLs are supported")

    if parsed.path.startswith("/wiki/"):
        title = unquote(parsed.path.removeprefix("/wiki/")).replace(" ", "_")
        if not title:
            raise WikiUrlError("Wikipedia article URL must include a title")

        return ParsedWikiUrl(
            title=title,
            normalized_url=_normalized_article_url(title),
            revision=None,
        )

    if parsed.path == "/w/index.php":
        query = parse_qs(parsed.query)
        title_values = query.get("title")
        if not title_values or not title_values[0]:
            raise WikiUrlError("Wikipedia revision URL must include a title")

        title = title_values[0].replace(" ", "_")
        revision_values = query.get("oldid")
        revision = revision_values[0] if revision_values else None
        return ParsedWikiUrl(
            title=title,
            normalized_url=_normalized_article_url(title),
            revision=revision,
        )

    raise WikiUrlError("Unsupported English Wikipedia URL format")


def _is_allowed_english_wikipedia_host(parsed) -> bool:
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.hostname != "en.wikipedia.org":
        return False

    default_port = 443 if parsed.scheme == "https" else 80
    try:
        port = parsed.port
    except ValueError:
        return False
    return port in {None, default_port}


def _normalized_article_url(title: str) -> str:
    return f"https://en.wikipedia.org/wiki/{quote(title, safe=':_()')}"
