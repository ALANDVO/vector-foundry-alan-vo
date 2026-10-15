# Vector Foundry - LLM Tests
"""Tests for LLM service (with mocked providers)."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.models.issue import TrackingIssue, IssueAnalysis
from app.services.llm import (
    OpenAICompatibleProvider,
    AnthropicProvider,
    GeminiProvider,
    OllamaProvider,
    create_provider,
    generate_issue_summary,
    explain_blockers,
)


@pytest_asyncio.fixture
async def issue_with_analysis(db_session: AsyncSession):
    """Create an issue with analysis for LLM testing."""
    issue = TrackingIssue(
        number=31844,
        title="Tracking issue for specialization (RFC 1210)",
        body="Specialization tracking issue with soundness concerns.",
        html_url="https://github.com/rust-lang/rust/issues/31844",
        state="open",
        comments=323,
        labels=[{"name": "F-specialization", "color": "ff0000"}],
        author_login="rust-lang",
        author_avatar_url="https://github.com/rust-lang.png",
        created_at=datetime(2019, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(issue)
    await db_session.flush()

    analysis = IssueAnalysis(
        issue_id=issue.id,
        readiness_score=45,
        blocking_dependencies=["Lifetime dispatch soundness hole"],
        unresolved_questions=[
            {"category": "Soundness", "question": "Should associated type be specializable?"},
        ],
        progress_summary="Partial implementation with unresolved soundness issues.",
        checklist_completed=1,
        checklist_total=7,
    )
    db_session.add(analysis)
    await db_session.commit()
    return issue, analysis


@pytest.mark.asyncio
async def test_openai_compatible_provider():
    """Test OpenAI-compatible provider with mocked response."""
    provider = OpenAICompatibleProvider(
        base_url="https://api.example.com/v1",
        api_key="test-key",
        model="test-model",
    )

    # Mock the HTTP client
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Test summary"}}],
        "model": "test-model",
        "usage": {"prompt_tokens": 10, "completion_tokens": 20},
    }
    mock_response.raise_for_status = MagicMock()

    provider.client.post = AsyncMock(return_value=mock_response)

    result = await provider.generate("Test prompt")

    assert result.content == "Test summary"
    assert result.model == "test-model"
    assert result.provider == "openai-compatible"
    assert result.error is None

    await provider.close()


@pytest.mark.asyncio
async def test_anthropic_provider():
    """Test Anthropic provider with mocked response."""
    provider = AnthropicProvider(
        api_key="test-key",
        model="claude-3-haiku-20240307",
    )

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "content": [{"text": "Test summary"}],
        "model": "claude-3-haiku-20240307",
        "usage": {"input_tokens": 10, "output_tokens": 20},
    }
    mock_response.raise_for_status = MagicMock()

    provider.client.post = AsyncMock(return_value=mock_response)

    result = await provider.generate("Test prompt", "System prompt")

    assert result.content == "Test summary"
    assert result.provider == "anthropic"
    assert result.error is None

    await provider.close()


@pytest.mark.asyncio
async def test_gemini_provider():
    """Test Gemini provider with mocked response."""
    provider = GeminiProvider(
        api_key="test-key",
        model="gemini-1.5-flash",
    )

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Test summary"}]}}],
        "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 20},
    }
    mock_response.raise_for_status = MagicMock()

    provider.client.post = AsyncMock(return_value=mock_response)

    result = await provider.generate("Test prompt", "System prompt")

    assert result.content == "Test summary"
    assert result.provider == "gemini"
    assert result.error is None

    await provider.close()


@pytest.mark.asyncio
async def test_ollama_provider():
    """Test Ollama provider with mocked response."""
    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3.1",
    )

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "response": "Test summary",
    }
    mock_response.raise_for_status = MagicMock()

    provider.client.post = AsyncMock(return_value=mock_response)

    result = await provider.generate("Test prompt", "System prompt")

    assert result.content == "Test summary"
    assert result.provider == "ollama"
    assert result.error is None

    await provider.close()


@pytest.mark.asyncio
async def test_provider_error_handling():
    """Test provider handles errors gracefully."""
    provider = OpenAICompatibleProvider(
        base_url="https://api.example.com/v1",
        api_key="test-key",
        model="test-model",
    )

    provider.client.post = AsyncMock(side_effect=Exception("Connection failed"))

    result = await provider.generate("Test prompt")

    assert result.error is not None
    assert "Connection failed" in result.error
    assert result.content == ""

    await provider.close()


@pytest.mark.asyncio
async def test_create_provider_no_key():
    """Test create_provider returns None when no API key."""
    with patch("app.services.llm.settings") as mock_settings:
        mock_settings.llm_api_key = ""
        mock_settings.llm_provider = "openai-compatible"
        mock_settings.llm_model = "gpt-4o-mini"
        mock_settings.llm_base_url = ""

        provider = create_provider()
        assert provider is None


@pytest.mark.asyncio
async def test_generate_issue_summary(issue_with_analysis):
    """Test generating issue summary with mocked provider."""
    issue, analysis = issue_with_analysis
    mock_provider = AsyncMock()
    mock_provider.generate = AsyncMock(return_value=MagicMock(
        content="This feature is in early development with soundness concerns.",
        error=None,
    ))

    summary = await generate_issue_summary(issue, analysis, mock_provider)

    assert "AI Summary - Advisory Only" in summary
    assert "early development" in summary.lower() or "soundness" in summary.lower()


@pytest.mark.asyncio
async def test_explain_blockers(issue_with_analysis):
    """Test explaining blockers with mocked provider."""
    issue, analysis = issue_with_analysis
    mock_provider = AsyncMock()
    mock_provider.generate = AsyncMock(return_value=MagicMock(
        content="The main blocker is a soundness hole in lifetime dispatch.",
        error=None,
    ))

    explanation = await explain_blockers(analysis, mock_provider)

    assert "AI Explanation - Advisory Only" in explanation
    assert "soundness" in explanation.lower()


@pytest.mark.asyncio
async def test_llm_summary_endpoint(client: AsyncClient, issue_with_analysis):
    """Test LLM summary endpoint requires API key."""
    issue, analysis = issue_with_analysis
    response = await client.post(
        "/api/v1/llm/summary",
        json={"issue_number": issue.number},
    )
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_llm_explain_endpoint(client: AsyncClient, issue_with_analysis):
    """Test LLM explain blockers endpoint requires API key."""
    issue, analysis = issue_with_analysis
    response = await client.post(
        "/api/v1/llm/explain-blockers",
        json={"issue_number": issue.number},
    )
    assert response.status_code == 503