import re

GROUP_STAGES = {
    "S1": [
        {"stageIndex": 1, "condition": "wikicompare", "materialId": "M1"},
        {"stageIndex": 2, "condition": "chatgpt", "materialId": "M2"},
    ],
    "S2": [
        {"stageIndex": 1, "condition": "chatgpt", "materialId": "M2"},
        {"stageIndex": 2, "condition": "wikicompare", "materialId": "M1"},
    ],
    "S3": [
        {"stageIndex": 1, "condition": "chatgpt", "materialId": "M1"},
        {"stageIndex": 2, "condition": "wikicompare", "materialId": "M2"},
    ],
    "S4": [
        {"stageIndex": 1, "condition": "wikicompare", "materialId": "M2"},
        {"stageIndex": 2, "condition": "chatgpt", "materialId": "M1"},
    ],
}


def normalize_participant_code(value):
    raw = str(value or "").strip().upper()
    if not raw:
        raise ValueError("Participant code is required")
    if raw.isdigit():
        number = int(raw)
    else:
        match = re.fullmatch(r"P(\d+)", raw)
        if not match:
            raise ValueError("Participant code must look like P01")
        number = int(match.group(1))
    if number < 1:
        raise ValueError("Participant code number must be at least 1")
    return f"P{number:02d}"


def group_for_number(number):
    return ["S1", "S2", "S3", "S4"][(number - 1) % 4]


def assignment_for_code(value):
    participant_code = normalize_participant_code(value)
    number = int(participant_code[1:])
    group = group_for_number(number)
    return {
        "participantCode": participant_code,
        "group": group,
        "stages": [dict(stage) for stage in GROUP_STAGES[group]],
    }
