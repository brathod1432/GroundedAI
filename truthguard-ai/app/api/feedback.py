"""Feedback endpoint — capture human corrections to verdict outputs.

Uses SQLite for zero-dependency persistence. The database is created
automatically on first use in a 'data/' directory relative to where
the app is run.
"""
from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Database location — created on first use
_DB_PATH = Path("data") / "feedback.db"

feedback_router = APIRouter(prefix="/feedback", tags=["feedback"])


def _get_connection() -> sqlite3.Connection:
    """Open (and create) the feedback SQLite database."""
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT,
            claim_index INTEGER,
            predicted_verdict TEXT,
            correct_verdict TEXT,
            comment TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    return conn


class FeedbackRequest(BaseModel):
    """A human correction for a claim verdict."""

    request_id: str = Field(..., description="Identifier linking back to the verify request.")
    claim_index: int = Field(..., ge=0, description="Index of the claim being corrected.")
    predicted_verdict: str = Field(..., description="What the system predicted.")
    correct_verdict: str = Field(
        ...,
        description="The correct verdict (SUPPORTED/CONTRADICTED/NOT_ENOUGH_EVIDENCE).",
    )
    comment: str = Field(default="", max_length=2000, description="Optional human comment.")


class FeedbackResponse(BaseModel):
    """Confirmation of feedback submission."""

    id: int
    message: str


class FeedbackSummary(BaseModel):
    """Aggregate feedback statistics."""

    total_feedback: int
    verdict_corrections: dict[str, int]


@feedback_router.post("/", response_model=FeedbackResponse)
def submit_feedback(req: FeedbackRequest) -> FeedbackResponse:
    """Submit a correction for a claim verdict.

    Stored locally in SQLite for future calibration of thresholds.
    """
    created_at = datetime.now(timezone.utc).isoformat()
    with _get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO feedback
               (request_id, claim_index, predicted_verdict, correct_verdict, comment, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                req.request_id,
                req.claim_index,
                req.predicted_verdict,
                req.correct_verdict,
                req.comment,
                created_at,
            ),
        )
        row_id = cursor.lastrowid
    logger.info(
        "Feedback recorded id=%d: predicted=%s → correct=%s",
        row_id,
        req.predicted_verdict,
        req.correct_verdict,
    )
    return FeedbackResponse(id=row_id, message="Feedback recorded. Thank you.")


@feedback_router.get("/summary", response_model=FeedbackSummary)
def feedback_summary() -> FeedbackSummary:
    """Return aggregate feedback statistics."""
    with _get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
        rows = conn.execute(
            "SELECT predicted_verdict, correct_verdict, COUNT(*) FROM feedback GROUP BY 1, 2"
        ).fetchall()

    corrections: dict[str, int] = {}
    for predicted, correct, count in rows:
        if predicted != correct:
            key = f"{predicted}→{correct}"
            corrections[key] = corrections.get(key, 0) + count

    return FeedbackSummary(total_feedback=total, verdict_corrections=corrections)
