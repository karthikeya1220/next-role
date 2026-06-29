"""The progress callback is optional by design — the CLIs pass nothing and must
keep working, while the UI passes a callback to drive its progress bar."""
import inspect

from app.api import pipeline
from app.api.pipeline import KINDS, LABELS
from app.ingestion.enrich import enrich
from app.ingestion.pipeline import run_ingestion


def test_progress_callback_is_optional_on_both_entry_points() -> None:
    """A required callback would have broken every existing CLI invocation."""
    for func in (run_ingestion, enrich):
        param = inspect.signature(func).parameters["on_progress"]
        assert param.default is None


def test_every_kind_has_a_human_label() -> None:
    """The 409 message names the running step, so a missing label would leak an id."""
    assert set(KINDS) == set(LABELS)
    assert all(LABELS[kind] for kind in KINDS)


def test_scoring_is_not_something_the_user_can_choose_to_skip() -> None:
    """Fetching without scoring leaves an app where nothing is rankable and
    nothing looks broken, so "enrich" is no longer a kind you can ask for."""
    assert "enrich" not in KINDS
    assert "ingest" in KINDS


def test_a_fetch_scores_what_it_fetched(monkeypatch) -> None:
    """Order matters: scoring before fetching would score yesterday's jobs."""
    calls: list[tuple] = []
    monkeypatch.setattr(
        pipeline, "run_ingestion", lambda db, on_progress=None: calls.append(("fetch",))
    )
    monkeypatch.setattr(
        pipeline, "enrich", lambda db, top=None, on_progress=None: calls.append(("score", top))
    )

    pipeline.ingest_and_score(db=None, progress=lambda *a: None)

    assert calls == [("fetch",), ("score", pipeline.SCORE_DEPTH)]
    assert pipeline.SCORE_DEPTH == 25, "deeper than this and a fetch stops feeling quick"
