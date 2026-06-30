from services.models import CompareSession
from services.session_store import SessionStore


def test_session_store_saves_and_gets_session():
    store = SessionStore()
    session = CompareSession(session_id="s1", articles={})

    store.save(session)

    assert store.get("s1") is session
    assert store.get("missing") is None
