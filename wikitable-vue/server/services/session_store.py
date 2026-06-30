from __future__ import annotations

from services.models import CompareSession


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, CompareSession] = {}

    def save(self, session: CompareSession) -> None:
        self._sessions[session.session_id] = session

    def get(self, session_id: str) -> CompareSession | None:
        return self._sessions.get(session_id)
