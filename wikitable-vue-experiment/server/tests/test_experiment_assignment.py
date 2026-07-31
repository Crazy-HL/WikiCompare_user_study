import pytest

from experiment.assignment import assignment_for_code, normalize_participant_code


def test_normalize_participant_code_accepts_lowercase_and_numbers():
    assert normalize_participant_code("p1") == "P01"
    assert normalize_participant_code(" P09 ") == "P09"
    assert normalize_participant_code("12") == "P12"


@pytest.mark.parametrize(
    "code,group,first_condition,first_material,second_condition,second_material",
    [
        ("P01", "S1", "wikicompare", "M1", "chatgpt", "M2"),
        ("P02", "S2", "chatgpt", "M2", "wikicompare", "M1"),
        ("P03", "S3", "chatgpt", "M1", "wikicompare", "M2"),
        ("P04", "S4", "wikicompare", "M2", "chatgpt", "M1"),
        ("P05", "S1", "wikicompare", "M1", "chatgpt", "M2"),
        ("P16", "S4", "wikicompare", "M2", "chatgpt", "M1"),
    ],
)
def test_assignment_for_code_uses_four_group_cycle(
    code,
    group,
    first_condition,
    first_material,
    second_condition,
    second_material,
):
    assignment = assignment_for_code(code)
    assert assignment["participantCode"] == normalize_participant_code(code)
    assert assignment["group"] == group
    assert assignment["stages"] == [
        {"stageIndex": 1, "condition": first_condition, "materialId": first_material},
        {"stageIndex": 2, "condition": second_condition, "materialId": second_material},
    ]


@pytest.mark.parametrize("bad_code", ["", "P0", "PX", "A01", "P-1"])
def test_invalid_participant_codes_raise_value_error(bad_code):
    with pytest.raises(ValueError):
        assignment_for_code(bad_code)
