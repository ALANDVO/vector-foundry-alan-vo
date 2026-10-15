# Vector Foundry - Analysis Tests
"""Tests for the deterministic analysis engine."""

import pytest
from datetime import datetime, timezone

from app.models.issue import TrackingIssue, ChecklistItem
from app.services.analysis import (
    parse_checklist,
    extract_linked_issues,
    extract_unresolved_questions,
    categorize_question,
    detect_blockers,
    calculate_readiness_score,
    generate_progress_summary,
    analyze_issue,
)


@pytest.fixture
def sample_issue():
    """Create a sample tracking issue for testing."""
    return TrackingIssue(
        id=1,
        number=31844,
        title="Tracking issue for specialization (RFC 1210)",
        body="""
This is a tracking issue for specialization (rust-lang/rfcs#1210).

## Implementation Steps
- [x] Land https://github.com/rust-lang/rust/pull/30652 =)
- [ ] Restrictions around lifetime dispatch (currently a **soundness hole**)
- [ ] `default impl` (https://github.com/rust-lang/rust/issues/37653)
- [ ] Integration with associated consts
- [ ] Bounds not always properly enforced (https://github.com/rust-lang/rust/issues/33017)
- [ ] Should we permit empty impls if parent has no `default` members? https://github.com/rust-lang/rust/issues/48444
- [ ] implement "always applicable" impls https://github.com/rust-lang/rust/issues/48538

### Unresolved Questions

- Should associated type be specializable at all?
- When should projection reveal a `default type`? Never during typeck? Or when monomorphic?
- Should default trait items be considered `default` (i.e. specializable)?
- Should we have `default impl` (where all items are `default`) or `partial impl`?
- How should we deal with lifetime dispatchability?

Note that the `specialization` feature as implemented currently is *unsound*.
""",
        html_url="https://github.com/rust-lang/rust/issues/31844",
        state="open",
        comments=323,
        labels=[{"name": "F-specialization", "color": "ff0000"}],
        author_login="rust-lang",
        author_avatar_url="https://github.com/rust-lang.png",
        created_at=datetime(2019, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )


def test_parse_checklist(sample_issue):
    """Test parsing checklist items from issue body."""
    items = parse_checklist(sample_issue.body)

    assert len(items) >= 7
    # Check first item is completed
    assert items[0][1] is True  # completed
    assert "Land" in items[0][0]
    # Check second item is not completed
    assert items[1][1] is False
    assert "lifetime dispatch" in items[1][0]


def test_extract_linked_issues(sample_issue):
    """Test extracting linked issue numbers."""
    numbers = extract_linked_issues(sample_issue.body)

    assert 30652 in numbers
    assert 37653 in numbers
    assert 33017 in numbers
    assert 48444 in numbers
    assert 48538 in numbers
    assert 1210 in numbers  # from RFC reference


def test_extract_unresolved_questions(sample_issue):
    """Test extracting unresolved questions."""
    questions = extract_unresolved_questions(sample_issue.body)

    assert len(questions) >= 5
    categories = {q["category"] for q in questions}
    # Questions may be categorized as General, Implementation, Generics/Lifetimes, etc.
    # depending on keyword matching
    assert len(categories) > 0
    for q in questions:
        assert "category" in q
        assert "question" in q
        assert len(q["question"]) > 0


def test_categorize_question():
    """Test question categorization."""
    assert categorize_question("What should it be named?") == "Naming"
    assert categorize_question("Is this sound? Could cause UB") == "Soundness"
    assert categorize_question("API design question about method signatures") == "API Design"
    assert categorize_question("Implementation detail about compiler crash") == "Implementation"
    assert categorize_question("Documentation needs updating") == "Documentation"
    assert categorize_question("Generic variance and lifetime parameters") == "Generics/Lifetimes"
    assert categorize_question("Stabilization timeline question") == "Stabilization"
    assert categorize_question("Some random question") == "General"


def test_detect_blockers(sample_issue):
    """Test detecting blocking dependencies."""
    linked = extract_linked_issues(sample_issue.body)
    blockers = detect_blockers(sample_issue.body, linked)

    assert len(blockers) > 0
    # Should detect soundness hole mention
    assert any("soundness" in b.lower() for b in blockers)
    # Should include linked issues
    assert any("#37653" in b for b in blockers)


def test_calculate_readiness_score(sample_issue):
    """Test readiness score calculation."""
    checklist_items = [
        ChecklistItem(text="Item 1", completed=True, level=0, position=0),
        ChecklistItem(text="Item 2", completed=False, level=0, position=1),
        ChecklistItem(text="Item 3", completed=False, level=0, position=2),
        ChecklistItem(text="Item 4", completed=False, level=0, position=3),
        ChecklistItem(text="Item 5", completed=False, level=0, position=4),
        ChecklistItem(text="Item 6", completed=False, level=0, position=5),
        ChecklistItem(text="Item 7", completed=False, level=0, position=6),
    ]
    linked = extract_linked_issues(sample_issue.body)
    questions = extract_unresolved_questions(sample_issue.body)
    blockers = detect_blockers(sample_issue.body, linked)

    score = calculate_readiness_score(sample_issue, checklist_items, linked, questions, blockers)

    assert 0 <= score <= 100
    # With 1/7 checklist, many questions, blockers, and unsound mention
    assert score < 50


def test_generate_progress_summary(sample_issue):
    """Test progress summary generation."""
    checklist_items = [
        ChecklistItem(text="Item 1", completed=True, level=0, position=0),
        ChecklistItem(text="Item 2", completed=False, level=0, position=1),
    ]
    blockers = ["Blocker 1", "Blocker 2"]
    questions = [{"category": "Soundness", "question": "Is it sound?"}]

    summary = generate_progress_summary(
        sample_issue, checklist_items, 45, blockers, questions
    )

    assert isinstance(summary, str)
    assert len(summary) > 50
    assert "checklist" in summary.lower() or "progress" in summary.lower()


def test_analyze_issue_full(sample_issue):
    """Test full analysis pipeline."""
    result = analyze_issue(sample_issue)

    assert isinstance(result.readiness_score, int)
    assert 0 <= result.readiness_score <= 100
    assert isinstance(result.blocking_dependencies, list)
    assert isinstance(result.unresolved_questions, list)
    assert isinstance(result.progress_summary, str)
    assert len(result.progress_summary) > 20
    assert isinstance(result.checklist_completed, int)
    assert isinstance(result.checklist_total, int)
    assert result.checklist_completed <= result.checklist_total


def test_analyze_issue_no_checklist():
    """Test analysis with no checklist."""
    issue = TrackingIssue(
        id=2,
        number=99999,
        title="Issue without checklist",
        body="Just a description with no structured checklist.",
        html_url="https://github.com/rust-lang/rust/issues/99999",
        state="open",
        comments=5,
        labels=[],
        author_login="user",
        author_avatar_url="https://github.com/user.png",
        created_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2023, 6, 1, tzinfo=timezone.utc),
    )

    result = analyze_issue(issue)

    assert result.checklist_total == 0
    assert result.checklist_completed == 0
    assert result.readiness_score >= 0


def test_analyze_issue_high_readiness():
    """Test analysis of near-ready feature."""
    issue = TrackingIssue(
        id=3,
        number=88581,
        title="Tracking Issue for int_roundings",
        body="""
## Steps
- [x] Implement div_floor
- [x] Implement div_ceil
- [x] Implement next_multiple_of
- [x] Implement checked_next_multiple_of
- [x] Stabilization PR

This feature is stable since 1.73.0 for unsigned integers.
""",
        html_url="https://github.com/rust-lang/rust/issues/88581",
        state="open",
        comments=176,
        labels=[{"name": "F-int_roundings", "color": "00ff00"}],
        author_login="rust-lang",
        author_avatar_url="https://github.com/rust-lang.png",
        created_at=datetime(2021, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )

    result = analyze_issue(issue)

    assert result.checklist_completed == 5
    assert result.checklist_total == 5
    assert result.readiness_score >= 60  # Good score with all checklist items done