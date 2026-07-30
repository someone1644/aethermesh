from __future__ import annotations

import logging
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = settings.GEMINI_MODEL


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

    @property
    def api_key(self) -> str:
        return (self._api_key or settings.GEMINI_API_KEY or "").strip()

    @property
    def has_api_key(self) -> bool:
        key = self.api_key
        return bool(key and key not in ("YOUR_API_KEY", "YOUR_GEMINI_API_KEY"))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_client(self):
        """Return (and lazily create) the genai.Client instance."""
        if not self.has_api_key:
            raise ValueError("No valid GEMINI_API_KEY configured.")
        if self._client is None:
            from google import genai  # noqa: PLC0415
            self._client = genai.Client(api_key=self.api_key)
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
        import time
        from google.genai import types  # noqa: PLC0415

        client = self._get_client()

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

        max_retries = 3
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
                err_msg = str(exc)
                if ("429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg) and attempt < max_retries - 1:
                    sleep_s = 2 ** (attempt + 1)
                    logger.warning(
                        "Gemini API rate limit 429 hit. Retrying in %ds (attempt %d/%d)...",
                        sleep_s,
                        attempt + 1,
                        max_retries,
                    )
                    time.sleep(sleep_s)
                    continue
                raise exc

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    @property
    def model(self) -> str:
        return self._model
