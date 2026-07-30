from __future__ import annotations

import logging
import time
from typing import ClassVar, Optional

from config import settings

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = settings.GEMINI_MODEL


class GeminiRateLimitError(Exception):
    """Raised when Gemini returns 429 after retries are exhausted."""


class GeminiClient:
    """
    Thin, reusable wrapper around the google-genai SDK.

    Agents receive a shared instance via dependency injection so
    a single SDK client is reused across all calls.

    The underlying ``genai.Client`` is created lazily on first use so
    that importing this module without a valid API key does not raise.
    """

    _rate_limited_until: ClassVar[float] = 0.0

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = _DEFAULT_MODEL,
    ) -> None:
        self._api_key = api_key or settings.GEMINI_API_KEY
        self._model = model
        self._client = None

    @property
    def api_key(self) -> str:
        return (self._api_key or settings.GEMINI_API_KEY or "").strip()

    @property
    def has_api_key(self) -> bool:
        key = self.api_key
        return bool(key and key not in ("YOUR_API_KEY", "YOUR_GEMINI_API_KEY"))

    @classmethod
    def is_rate_limited(cls) -> bool:
        return time.time() < cls._rate_limited_until

    @classmethod
    def mark_rate_limited(cls) -> None:
        cooldown = max(0.0, settings.GEMINI_RATE_LIMIT_COOLDOWN_SECONDS)
        cls._rate_limited_until = time.time() + cooldown
        logger.warning(
            "Gemini rate limit cooldown active for %.0fs — skipping further API calls",
            cooldown,
        )

    @classmethod
    def reset_rate_limit(cls) -> None:
        cls._rate_limited_until = 0.0

    @staticmethod
    def _is_rate_limit_error(exc: Exception) -> bool:
        err_msg = str(exc)
        return "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg

    def _get_client(self):
        if not self.has_api_key:
            raise ValueError("No valid GEMINI_API_KEY configured.")
        if self._client is None:
            from google import genai  # noqa: PLC0415

            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.4,
        max_output_tokens: int = 2048,
    ) -> str:
        if self.is_rate_limited():
            raise GeminiRateLimitError(
                "Gemini API is in rate-limit cooldown; using local fallback."
            )

        from google.genai import types  # noqa: PLC0415

        client = self._get_client()
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

        max_retries = 3
        last_exc: Exception | None = None

        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config=config,
                )
                text: str = response.text or ""
                logger.debug(
                    "GeminiClient.generate | model=%s | prompt_chars=%d | response_chars=%d",
                    self._model,
                    len(prompt),
                    len(text),
                )
                return text
            except Exception as exc:
                last_exc = exc
                if self._is_rate_limit_error(exc) and attempt < max_retries - 1:
                    sleep_s = 2 ** (attempt + 1)
                    logger.warning(
                        "Gemini API rate limit 429 hit. Retrying in %ds (attempt %d/%d)...",
                        sleep_s,
                        attempt + 1,
                        max_retries,
                    )
                    time.sleep(sleep_s)
                    continue
                break

        assert last_exc is not None
        if self._is_rate_limit_error(last_exc):
            self.mark_rate_limited()
            raise GeminiRateLimitError(str(last_exc)) from last_exc
        raise last_exc

    @property
    def model(self) -> str:
        return self._model
