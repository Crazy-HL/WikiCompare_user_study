from services.models import Citation, SourceRef


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
