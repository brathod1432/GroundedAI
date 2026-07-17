"""Tests for the corrective prompt builder."""

from __future__ import annotations

from app.core.corrective_prompt import build_corrective_prompt


def test_prompt_includes_question() -> None:
    """The corrective prompt must contain the original question."""
    prompt = build_corrective_prompt(
        question="What is the capital of France?",
        failed_answer="Berlin is the capital of France.",
        evidence=[{"snippet": "Paris is the capital of France.", "source": "wikipedia"}],
        contradicted_claims=["Berlin is the capital of France."],
        unsupported_claims=[],
    )
    assert "What is the capital of France?" in prompt


def test_prompt_includes_contradicted_claims() -> None:
    """Contradicted claims should appear in the prompt."""
    contradicted = ["The Earth is flat.", "Water boils at 50°C."]
    prompt = build_corrective_prompt(
        question="Tell me about science.",
        failed_answer="The Earth is flat. Water boils at 50°C.",
        evidence=[{"snippet": "The Earth is roughly spherical.", "source": "nasa"}],
        contradicted_claims=contradicted,
        unsupported_claims=[],
    )
    for claim in contradicted:
        assert claim in prompt


def test_prompt_includes_unsupported_claims() -> None:
    """Unsupported claims should appear in the prompt."""
    unsupported = ["Mars has 5 moons."]
    prompt = build_corrective_prompt(
        question="How many moons does Mars have?",
        failed_answer="Mars has 5 moons.",
        evidence=[],
        contradicted_claims=[],
        unsupported_claims=unsupported,
    )
    for claim in unsupported:
        assert claim in prompt


def test_prompt_includes_evidence() -> None:
    """Trusted evidence snippets should appear in the prompt."""
    evidence = [
        {"snippet": "Paris is the capital of France.", "source": "wikipedia", "url": "https://en.wikipedia.org/wiki/Paris"},
        {"snippet": "France has 67 million people.", "source": "world-bank"},
    ]
    prompt = build_corrective_prompt(
        question="What is the capital of France?",
        failed_answer="Berlin is the capital of France.",
        evidence=evidence,
        contradicted_claims=["Berlin is the capital of France."],
        unsupported_claims=[],
    )
    assert "Paris is the capital of France." in prompt
    assert "France has 67 million people." in prompt
    assert "wikipedia" in prompt
    assert "https://en.wikipedia.org/wiki/Paris" in prompt


def test_prompt_gives_clear_instructions() -> None:
    """The prompt must contain explicit rewriting instructions."""
    prompt = build_corrective_prompt(
        question="Test question",
        failed_answer="Bad answer.",
        evidence=[{"snippet": "Good fact.", "source": "test"}],
        contradicted_claims=["Bad answer."],
        unsupported_claims=[],
    )
    assert "ONLY" in prompt
    assert "Rewrite" in prompt or "rewrite" in prompt
    assert "evidence" in prompt.lower()


def test_prompt_handles_empty_evidence() -> None:
    """Prompt should still be valid when no evidence is provided."""
    prompt = build_corrective_prompt(
        question="Question?",
        failed_answer="Answer.",
        evidence=[],
        contradicted_claims=["Answer."],
        unsupported_claims=[],
    )
    assert "Question?" in prompt
    assert "Answer." in prompt
    # Should still have instructions even without evidence
    assert "Instructions" in prompt


def test_prompt_handles_no_failed_claims() -> None:
    """Prompt should work even with empty claim lists."""
    prompt = build_corrective_prompt(
        question="A question",
        failed_answer="An answer",
        evidence=[{"snippet": "Some evidence", "source": "src"}],
        contradicted_claims=[],
        unsupported_claims=[],
    )
    assert "A question" in prompt
    assert "An answer" in prompt
