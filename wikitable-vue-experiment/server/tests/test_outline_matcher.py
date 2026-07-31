from services.outline_matcher import build_outline_matches


def test_build_outline_matches_links_exact_and_related_headings_once():
    left_outline = [
        {"id": "left-heading-1", "level": 1, "text": "Example A"},
        {"id": "left-heading-2", "level": 2, "text": "Economy"},
        {"id": "left-heading-3", "level": 2, "text": "History"},
        {"id": "left-heading-4", "level": 2, "text": "See also"},
    ]
    right_outline = [
        {"id": "right-heading-1", "level": 1, "text": "Example B"},
        {"id": "right-heading-2", "level": 2, "text": "Historical background"},
        {"id": "right-heading-3", "level": 2, "text": "Economy"},
        {"id": "right-heading-4", "level": 2, "text": "References"},
    ]

    matches = build_outline_matches(left_outline, right_outline)

    assert {
        (match["leftId"], match["rightId"], match["label"])
        for match in matches
    } == {
        ("left-heading-2", "right-heading-3", "Economy"),
        ("left-heading-3", "right-heading-2", "History"),
    }
