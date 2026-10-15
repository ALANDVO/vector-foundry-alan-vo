# Vector Foundry - Analysis Service
"""Core domain engine: deterministic stabilization readiness analysis."""

import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone

from app.models.issue import TrackingIssue, ChecklistItem, IssueAnalysis


@dataclass
class AnalysisResult:
    """Result of the analysis computation."""
    readiness_score: int
    blocking_dependencies: List[str]
    unresolved_questions: List[Dict[str, str]]
    progress_summary: str
    checklist_completed: int
    checklist_total: int


# Patterns for parsing tracking issues
CHECKLIST_PATTERN = re.compile(
    r'^\s*[-*]\s+\[([ xX])\]\s*(.+)$',
    re.MULTILINE
)

SUB_CHECKLIST_PATTERN = re.compile(
    r'^\s{2,}[-*]\s+\[([ xX])\]\s*(.+)$',
    re.MULTILINE
)

LINKED_ISSUE_PATTERN = re.compile(
    r'#(\d+)',
)

URL_PATTERN = re.compile(
    r'https?://github\.com/rust-lang/rust/(?:issues|pull)/(\d+)',
)

UNRESOLVED_QUESTION_PATTERN = re.compile(
    r'(?:^|\n)###\s*Unresolved Questions?\s*\n(.*?)(?:\n###|\n##|\Z)',
    re.DOTALL | re.IGNORECASE
)

QUESTION_ITEM_PATTERN = re.compile(
    r'^\s*[-*]\s+(?:\[[ xX]\]\s*)?(.+?)(?:\s*\(.*?\))?$',
    re.MULTILINE
)

BLOCKER_KEYWORDS = [
    'blocked', 'blocking', 'depends on', 'dependency', 'waiting for',
    'requires', 'prerequisite', 'pre-requisite', 'blocked by',
    'soundness', 'unsound',
]

PROGRESS_KEYWORDS = {
    'implemented': 10,
    'landed': 15,
    'merged': 15,
    'stabilized': 25,
    'stabilization': 20,
    'fcp': 15,
    'final comment period': 15,
    'rfc': 5,
    'tracking': 2,
}


def parse_checklist(body: str) -> List[Tuple[str, bool, int]]:
    """Parse checklist items from issue body."""
    items = []

    # Find main checklist section
    lines = body.split('\n')
    in_checklist = False
    checklist_content = []

    for line in lines:
        if re.match(r'^##+\s*(?:Implementation )?(?:Steps|Checklist|Tasks)', line, re.IGNORECASE):
            in_checklist = True
            continue
        elif in_checklist and re.match(r'^##+\s', line):
            in_checklist = False
            break
        elif in_checklist:
            checklist_content.append(line)

    checklist_text = '\n'.join(checklist_content)

    # Parse top-level items
    for match in CHECKLIST_PATTERN.finditer(checklist_text):
        completed = match.group(1).lower() == 'x'
        text = match.group(2).strip()
        items.append((text, completed, 0))

        # Look for sub-items after this item
        # Find position of this match
        pos = match.end()
        next_match = CHECKLIST_PATTERN.search(checklist_text, pos)
        end_pos = next_match.start() if next_match else len(checklist_text)
        sub_text = checklist_text[pos:end_pos]

        for sub_match in SUB_CHECKLIST_PATTERN.finditer(sub_text):
            sub_completed = sub_match.group(1).lower() == 'x'
            sub_text_clean = sub_match.group(2).strip()
            items.append((sub_text_clean, sub_completed, 1))

    return items


def extract_linked_issues(body: str) -> List[int]:
    """Extract linked issue/PR numbers from body."""
    numbers = set()
    for match in LINKED_ISSUE_PATTERN.finditer(body):
        numbers.add(int(match.group(1)))
    for match in URL_PATTERN.finditer(body):
        numbers.add(int(match.group(1)))
    return list(numbers)


def extract_unresolved_questions(body: str) -> List[Dict[str, str]]:
    """Extract unresolved questions from issue body."""
    questions = []

    # Find unresolved questions section
    match = UNRESOLVED_QUESTION_PATTERN.search(body)
    if not match:
        return questions

    section = match.group(1)
    for q_match in QUESTION_ITEM_PATTERN.finditer(section):
        question_text = q_match.group(1).strip()
        if question_text:
            # Categorize question
            category = categorize_question(question_text)
            questions.append({
                "category": category,
                "question": question_text,
            })

    return questions


def categorize_question(question: str) -> str:
    """Categorize an unresolved question."""
    q_lower = question.lower()

    if any(kw in q_lower for kw in ['name', 'naming', 'bikeshed', 'called']):
        return 'Naming'
    elif any(kw in q_lower for kw in ['sound', 'unsound', 'safety', 'ub', 'undefined behavior']):
        return 'Soundness'
    elif any(kw in q_lower for kw in ['api', 'interface', 'signature', 'method', 'function']):
        return 'API Design'
    elif any(kw in q_lower for kw in ['impl', 'implementation', 'compiler', 'ice', 'crash']):
        return 'Implementation'
    elif any(kw in q_lower for kw in ['doc', 'documentation', 'guide', 'example']):
        return 'Documentation'
    elif any(kw in q_lower for kw in ['generic', 'variance', 'lifetime', 'parameter']):
        return 'Generics/Lifetimes'
    elif any(kw in q_lower for kw in ['stabiliz', 'stable', 'release']):
        return 'Stabilization'
    else:
        return 'General'


def detect_blockers(body: str, linked_issues: List[int]) -> List[str]:
    """Detect blocking dependencies from issue body."""
    blockers = []
    body_lower = body.lower()

    # Check for explicit blocker mentions
    for keyword in BLOCKER_KEYWORDS:
        if keyword in body_lower:
            # Find context around keyword
            idx = body_lower.index(keyword)
            start = max(0, idx - 100)
            end = min(len(body), idx + 100)
            context = body[start:end].strip()
            blockers.append(f"Mentions '{keyword}': ...{context}...")

    # Add linked issues as potential dependencies
    for issue_num in linked_issues:
        blockers.append(f"References rust-lang/rust#{issue_num}")

    return blockers[:10]  # Limit


def calculate_readiness_score(
    issue: TrackingIssue,
    checklist_items: List[ChecklistItem],
    linked_issues: List[int],
    unresolved_questions: List[Dict[str, str]],
    blockers: List[str],
) -> int:
    """Calculate deterministic readiness score (0-100)."""
    score = 0

    # Base score from checklist progress
    if checklist_items:
        completed = sum(1 for item in checklist_items if item.completed)
        total = len(checklist_items)
        checklist_ratio = completed / total
        score += int(checklist_ratio * 40)  # Up to 40 points
    else:
        # No checklist = minimal progress tracking
        score += 5

    # Points for linked PRs/implementation work
    implementation_links = len([n for n in linked_issues if n > 0])
    score += min(implementation_links * 3, 15)  # Up to 15 points

    # Points for comment activity (community engagement)
    if issue.comments > 100:
        score += 10
    elif issue.comments > 50:
        score += 7
    elif issue.comments > 20:
        score += 5
    elif issue.comments > 10:
        score += 3

    # Points for issue age (older issues more likely to be worked on)
    age_days = (datetime.now(timezone.utc) - issue.created_at).days
    if age_days > 1000:
        score += 5
    elif age_days > 500:
        score += 3
    elif age_days > 100:
        score += 1

    # Deduct for unresolved questions
    question_penalty = min(len(unresolved_questions) * 2, 15)
    score -= question_penalty

    # Deduct for blockers
    blocker_penalty = min(len(blockers) * 3, 20)
    score -= blocker_penalty

    # Deduct for soundness issues
    body_lower = issue.body.lower()
    if 'unsound' in body_lower or 'soundness hole' in body_lower:
        score -= 15

    # Bonus for stabilization PR / FCP
    if any(kw in body_lower for kw in ['stabilization pr', 'final comment period', 'fcp']):
        score += 10

    # Bonus for implemented status
    if any(kw in body_lower for kw in ['implemented', 'landed', 'merged']):
        score += 10

    # Clamp to 0-100
    return max(0, min(100, score))


def generate_progress_summary(
    issue: TrackingIssue,
    checklist_items: List[ChecklistItem],
    readiness_score: int,
    blockers: List[str],
    unresolved_questions: List[Dict[str, str]],
) -> str:
    """Generate human-readable progress summary."""
    lines = []

    # Overall status
    if readiness_score >= 80:
        lines.append("This feature is approaching stabilization readiness.")
    elif readiness_score >= 60:
        lines.append("Active development in progress with significant work completed.")
    elif readiness_score >= 40:
        lines.append("Early-stage implementation with foundational work done.")
    else:
        lines.append("Feature is blocked or stalled with significant unresolved issues.")

    # Checklist progress
    if checklist_items:
        completed = sum(1 for item in checklist_items if item.completed)
        total = len(checklist_items)
        lines.append(f"Checklist progress: {completed}/{total} items completed ({int(completed/total*100)}%).")
    else:
        lines.append("No structured checklist found in the tracking issue.")

    # Blockers
    if blockers:
        lines.append(f"Identified {len(blockers)} potential blocking dependencies.")
    else:
        lines.append("No explicit blocking dependencies detected.")

    # Unresolved questions
    if unresolved_questions:
        categories = set(q['category'] for q in unresolved_questions)
        lines.append(f"{len(unresolved_questions)} unresolved questions across {len(categories)} categories: {', '.join(sorted(categories))}.")
    else:
        lines.append("No unresolved questions section found.")

    # Recent activity
    if issue.comments > 50:
        lines.append(f"High community engagement ({issue.comments} comments).")
    elif issue.comments > 10:
        lines.append(f"Moderate discussion activity ({issue.comments} comments).")
    else:
        lines.append(f"Limited recent discussion ({issue.comments} comments).")

    return ' '.join(lines)


def analyze_issue(issue: TrackingIssue) -> AnalysisResult:
    """Perform complete deterministic analysis of a tracking issue."""
    # Parse checklist
    checklist_data = parse_checklist(issue.body)

    # Extract linked issues
    linked_issues = extract_linked_issues(issue.body)

    # Extract unresolved questions
    unresolved_questions = extract_unresolved_questions(issue.body)

    # Detect blockers
    blockers = detect_blockers(issue.body, linked_issues)

    # Calculate readiness score
    # We need to create temporary ChecklistItem objects for scoring
    temp_checklist = [
        ChecklistItem(text=text, completed=completed, level=level, position=i)
        for i, (text, completed, level) in enumerate(checklist_data)
    ]
    readiness_score = calculate_readiness_score(
        issue, temp_checklist, linked_issues, unresolved_questions, blockers
    )

    # Generate summary
    progress_summary = generate_progress_summary(
        issue, temp_checklist, readiness_score, blockers, unresolved_questions
    )

    return AnalysisResult(
        readiness_score=readiness_score,
        blocking_dependencies=blockers,
        unresolved_questions=unresolved_questions,
        progress_summary=progress_summary,
        checklist_completed=sum(1 for item in temp_checklist if item.completed),
        checklist_total=len(temp_checklist),
    )


async def update_issue_analysis(db, issue: TrackingIssue) -> IssueAnalysis:
    """Update or create analysis for an issue."""
    result = analyze_issue(issue)

    # Get or create analysis record
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    stmt = select(IssueAnalysis).where(IssueAnalysis.issue_id == issue.id)
    existing = await db.execute(stmt)
    analysis = existing.scalar_one_or_none()

    if not analysis:
        analysis = IssueAnalysis(issue_id=issue.id)
        db.add(analysis)

    # Update fields
    analysis.readiness_score = result.readiness_score
    analysis.blocking_dependencies = result.blocking_dependencies
    analysis.unresolved_questions = result.unresolved_questions
    analysis.progress_summary = result.progress_summary
    analysis.checklist_completed = result.checklist_completed
    analysis.checklist_total = result.checklist_total
    analysis.last_analyzed = datetime.now(timezone.utc)
    analysis.analysis_version = "1.0"

    await db.commit()
    await db.refresh(analysis)

    return analysis