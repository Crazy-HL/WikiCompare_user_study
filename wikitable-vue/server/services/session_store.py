from __future__ import annotations

from services.models import CompareSession


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, CompareSession] = {}
        self._pair_index: dict[str, str] = {}

    def save(self, session: CompareSession, pair_key: str | None = None) -> None:
        self._sessions[session.session_id] = session
        if pair_key:
            self._pair_index[pair_key] = session.session_id

    def get(self, session_id: str) -> CompareSession | None:
        return self._sessions.get(session_id)

    def get_by_pair_key(self, pair_key: str) -> CompareSession | None:
        session_id = self._pair_index.get(pair_key)
        if session_id is None:
            return None
        return self.get(session_id)

    def clear(self) -> None:
        self._sessions.clear()
        self._pair_index.clear()
