# Vector Foundry - LLM Service
"""Optional LLM-powered insights service (advisory, grounded in data)."""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict
import httpx

from app.core.config import get_settings
from app.models.issue import TrackingIssue, IssueAnalysis


settings = get_settings()


@dataclass
class LLMResponse:
    """Standardized LLM response."""
    content: str
    model: str
    provider: str
    usage: Optional[Dict] = None
    error: Optional[str] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get provider name."""
        pass


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI-compatible provider (OpenAI, LiteLLM, OpenRouter, Ollama)."""

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=settings.llm_timeout,
        )

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            resp = await self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 1000,
                },
            )
            resp.raise_for_status()
            data = resp.json()

            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=self.model,
                provider=self.get_name(),
                usage=data.get("usage"),
            )
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.model,
                provider=self.get_name(),
                error=f"Provider error: {str(e)}",
            )

    def get_name(self) -> str:
        return "openai-compatible"

    async def close(self):
        await self.client.aclose()


class AnthropicProvider(LLMProvider):
    """Anthropic Messages API provider."""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.client = httpx.AsyncClient(
            base_url="https://api.anthropic.com",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            timeout=settings.llm_timeout,
        )

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        messages = [{"role": "user", "content": prompt}]

        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.3,
            }
            if system_prompt:
                payload["system"] = system_prompt

            resp = await self.client.post("/v1/messages", json=payload)
            resp.raise_for_status()
            data = resp.json()

            return LLMResponse(
                content=data["content"][0]["text"],
                model=self.model,
                provider=self.get_name(),
                usage=data.get("usage"),
            )
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.model,
                provider=self.get_name(),
                error=f"Provider error: {str(e)}",
            )

    def get_name(self) -> str:
        return "anthropic"

    async def close(self):
        await self.client.aclose()


class GeminiProvider(LLMProvider):
    """Google Gemini API provider."""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.client = httpx.AsyncClient(
            base_url="https://generativelanguage.googleapis.com",
            timeout=settings.llm_timeout,
        )

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        try:
            contents = []
            if system_prompt:
                contents.append({"role": "user", "parts": [{"text": system_prompt}]})
                contents.append({"role": "model", "parts": [{"text": "Understood."}]})
            contents.append({"role": "user", "parts": [{"text": prompt}]})

            resp = await self.client.post(
                f"/v1beta/models/{self.model}:generateContent",
                params={"key": self.api_key},
                json={"contents": contents, "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1000}},
            )
            resp.raise_for_status()
            data = resp.json()

            content = data["candidates"][0]["content"]["parts"][0]["text"]

            return LLMResponse(
                content=content,
                model=self.model,
                provider=self.get_name(),
                usage=data.get("usageMetadata"),
            )
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.model,
                provider=self.get_name(),
                error=f"Provider error: {str(e)}",
            )

    def get_name(self) -> str:
        return "gemini"

    async def close(self):
        await self.client.aclose()


class OllamaProvider(LLMProvider):
    """Ollama local provider."""

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=settings.llm_timeout,
        )

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

            resp = await self.client.post(
                "/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 1000},
                },
            )
            resp.raise_for_status()
            data = resp.json()

            return LLMResponse(
                content=data.get("response", ""),
                model=self.model,
                provider=self.get_name(),
            )
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.model,
                provider=self.get_name(),
                error=f"Provider error: {str(e)}",
            )

    def get_name(self) -> str:
        return "ollama"

    async def close(self):
        await self.client.aclose()


def create_provider() -> Optional[LLMProvider]:
    """Create LLM provider based on configuration."""
    if not settings.llm_api_key:
        return None

    provider_type = settings.llm_provider.lower()

    if provider_type in ("openai-compatible", "openai", "litellm", "openrouter"):
        base_url = settings.llm_base_url or "https://api.openai.com/v1"
        return OpenAICompatibleProvider(base_url, settings.llm_api_key, settings.llm_model or "gpt-4o-mini")

    elif provider_type == "anthropic":
        return AnthropicProvider(settings.llm_api_key, settings.llm_model or "claude-3-haiku-20240307")

    elif provider_type == "gemini":
        return GeminiProvider(settings.llm_api_key, settings.llm_model or "gemini-1.5-flash")

    elif provider_type == "ollama":
        base_url = settings.llm_base_url or "http://localhost:11434"
        return OllamaProvider(base_url, settings.llm_model or "llama3.1")

    return None


async def generate_issue_summary(
    issue: TrackingIssue,
    analysis: IssueAnalysis,
    provider: LLMProvider,
) -> str:
    """Generate human-readable summary of issue progress."""
    checklist_text = ""
    if analysis.checklist_total > 0:
        checklist_text = f"\nChecklist: {analysis.checklist_completed}/{analysis.checklist_total} completed."

    blockers_text = ""
    if analysis.blocking_dependencies:
        blockers_text = f"\nBlocking dependencies: {'; '.join(analysis.blocking_dependencies[:3])}."

    questions_text = ""
    if analysis.unresolved_questions:
        questions_text = f"\nUnresolved questions ({len(analysis.unresolved_questions)}): " + \
            "; ".join([q["question"][:80] for q in analysis.unresolved_questions[:3]])

    prompt = f"""You are a technical writer summarizing Rust compiler feature stabilization progress.
Given the following tracking issue data, write a concise 3-4 sentence summary for developers.
Focus on: what the feature does, current progress, key blockers, and estimated timeline.
Be factual and grounded in the data provided. Do not speculate beyond the data.

Feature: {issue.title}
GitHub: {issue.html_url}
Readiness Score: {analysis.readiness_score}/100
Progress Summary: {analysis.progress_summary}{checklist_text}{blockers_text}{questions_text}

Write a concise summary:"""

    system_prompt = """You are a technical writer for Rust compiler feature tracking.
Write concise, factual summaries grounded in the provided data.
Never invent information not present in the data.
Label any uncertainty clearly."""

    response = await provider.generate(prompt, system_prompt)

    if response.error:
        return f"[LLM Error: {response.error}]"

    return f"[AI Summary - Advisory Only] {response.content}"


async def explain_blockers(
    analysis: IssueAnalysis,
    provider: LLMProvider,
) -> str:
    """Generate plain-language explanation of technical blockers."""
    if not analysis.blocking_dependencies and not analysis.unresolved_questions:
        return "No significant blockers identified."

    prompt = f"""Explain the following technical blockers from a Rust compiler feature tracking issue in plain language for a developer audience.
Focus on what each blocker means practically and what needs to happen to resolve it.
Be concise and avoid jargon where possible.

Blocking Dependencies:
{chr(10).join(f"- {b}" for b in analysis.blocking_dependencies) if analysis.blocking_dependencies else "None"}

Unresolved Questions:
{chr(10).join(f"- [{q['category']}] {q['question']}" for q in analysis.unresolved_questions) if analysis.unresolved_questions else "None"}

Provide a clear explanation:"""

    system_prompt = """You are a Rust compiler expert explaining technical blockers to library authors.
Explain clearly what each blocker means and what resolution looks like.
Ground your explanation in the provided data only."""

    response = await provider.generate(prompt, system_prompt)

    if response.error:
        return f"[LLM Error: {response.error}]"

    return f"[AI Explanation - Advisory Only] {response.content}"