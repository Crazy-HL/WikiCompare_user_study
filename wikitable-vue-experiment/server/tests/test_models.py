from services.models import ArticleAttribute, Citation, CompareSession, SourceRef


def test_source_ref_serializes_to_frontend_shape():
    source = SourceRef(
        id="left-info-1",
        side="left",
        source_type="infobox",
        text="GDP growth 1.5%",
        selector='[data-source-id="left-info-1"]',
    )

    assert source.to_dict() == {
        "id": "left-info-1",
        "side": "left",
        "sourceType": "infobox",
        "text": "GDP growth 1.5%",
        "selector": '[data-source-id="left-info-1"]',
    }


def test_citation_serializes_to_frontend_shape():
    citation = Citation(
        id="cite-1",
        label="Infobox: GDP growth",
        side="both",
        source_ids=["left-info-1", "right-info-1"],
    )

    assert citation.to_dict()["sourceIds"] == ["left-info-1", "right-info-1"]


def test_article_attribute_serializes_to_frontend_shape():
    attribute = ArticleAttribute(
        id="attr-1",
        side="right",
        key="GDP growth",
        value_text="1.5%",
        source="main_text",
        source_ids=["right-text-1"],
        section="Economy",
    )

    assert attribute.to_dict() == {
        "id": "attr-1",
        "side": "right",
        "key": "GDP growth",
        "valueText": "1.5%",
        "source": "main_text",
        "sourceIds": ["right-text-1"],
        "section": "Economy",
    }


def test_compare_session_serializes_to_frontend_shape():
    source = SourceRef(
        id="left-info-1",
        side="left",
        source_type="infobox",
        text="GDP growth 1.5%",
        selector='[data-source-id="left-info-1"]',
    )
    session = CompareSession(
        session_id="session-1",
        articles={"left": {"title": "Japan"}, "right": {"title": "Germany"}},
        outline_matches=[{"left": "Economy", "right": "Economy"}],
        attribute_pools={"GDP growth": [{"id": "attr-1"}]},
        aligned_attributes=[{"leftId": "attr-1", "rightId": "attr-2"}],
        ranked_rows=[{"key": "GDP growth", "score": 0.9}],
        source_map={"left-info-1": source},
        warnings=["Low confidence"],
    )

    assert session.to_dict() == {
        "sessionId": "session-1",
        "articles": {"left": {"title": "Japan"}, "right": {"title": "Germany"}},
        "outlineMatches": [{"left": "Economy", "right": "Economy"}],
        "attributePools": {"GDP growth": [{"id": "attr-1"}]},
        "alignedAttributes": [{"leftId": "attr-1", "rightId": "attr-2"}],
        "rankedRows": [{"key": "GDP growth", "score": 0.9}],
        "sourceMap": {
            "left-info-1": {
                "id": "left-info-1",
                "side": "left",
                "sourceType": "infobox",
                "text": "GDP growth 1.5%",
                "selector": '[data-source-id="left-info-1"]',
            }
        },
        "warnings": ["Low confidence"],
    }


def test_compare_session_serializes_dict_source_map_defensively():
    session = CompareSession(
        session_id="session-1",
        articles={},
        source_map={
            "left-info-1": {
                "id": "left-info-1",
                "side": "left",
                "sourceType": "infobox",
                "text": "GDP growth 1.5%",
                "selector": '[data-source-id="left-info-1"]',
            }
        },
    )

    serialized = session.to_dict()
    serialized["sourceMap"]["left-info-1"]["text"] = "mutated"

    assert session.source_map["left-info-1"]["text"] == "GDP growth 1.5%"
