from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


Side = Literal["left", "right", "both"]


@dataclass
class SourceRef:
    id: str
    side: Literal["left", "right"]
    source_type: str
    text: str
    selector: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "side": self.side,
            "sourceType": self.source_type,
            "text": self.text,
            "selector": self.selector,
        }


@dataclass
class Citation:
    id: str
    label: str
    side: Side
    source_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "side": self.side,
            "sourceIds": self.source_ids,
        }


@dataclass
class ArticleAttribute:
    id: str
    side: Literal["left", "right"]
    key: str
    value_text: str
    source: Literal["infobox", "main_text"]
    source_ids: list[str]
    section: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "side": self.side,
            "key": self.key,
            "valueText": self.value_text,
            "source": self.source,
            "sourceIds": self.source_ids,
            "section": self.section,
        }


@dataclass
class CompareSession:
    session_id: str
    articles: dict[str, Any]
    outline_matches: list[dict[str, Any]] = field(default_factory=list)
    attribute_pools: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    aligned_attributes: list[dict[str, Any]] = field(default_factory=list)
    ranked_rows: list[dict[str, Any]] = field(default_factory=list)
    source_map: dict[str, SourceRef] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sessionId": self.session_id,
            "articles": self.articles,
            "outlineMatches": self.outline_matches,
            "attributePools": self.attribute_pools,
            "alignedAttributes": self.aligned_attributes,
            "rankedRows": self.ranked_rows,
            "sourceMap": {
                source_id: source_ref.to_dict()
                for source_id, source_ref in self.source_map.items()
            },
            "warnings": self.warnings,
        }
