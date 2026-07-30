from __future__ import annotations

import logging
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "gemini-2.0-flash"


class GeminiClient:
    """
    Thin, reusable wrapper around the google-genai SDK.

    Agents receive a shared instance via dependency injection so
    a single SDK client is reused across all calls.

    The underlying ``genai.Client`` is created lazily on first use so
    that importing this module without a valid API key does not raise.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = _DEFAULT_MODEL,
    ) -> None:
        self._api_key = api_key or settings.GEMINI_API_KEY
        self._model = model
        self._client = None  # created lazily on first generate() call

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_client(self):
        """Return (and lazily create) the genai.Client instance."""
        if self._client is None:
            from google import genai  # noqa: PLC0415
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.4,
        max_output_tokens: int = 2048,
    ) -> str:
        """
        Send *prompt* to Gemini and return the text response.

        Parameters
        ----------
        prompt:
            The full prompt string to send.
        temperature:
            Sampling temperature (0 = deterministic, 1 = creative).
        max_output_tokens:
            Upper bound on the generated token count.

        Returns
        -------
        str
            The raw text content of the model's first candidate.
        """
        from google.genai import types  # noqa: PLC0415

        client = self._get_client()

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

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

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    @property
    def model(self) -> str:
        return self._model
