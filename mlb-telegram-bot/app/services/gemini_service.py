"""
Gemini explanation service.
Set GEMINI_API_KEY in .env to enable real explanations.
"""
from __future__ import annotations
import logging
import os

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False


class GeminiExplainer:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.enabled = bool(self.api_key) and _GENAI_AVAILABLE
        if self.enabled:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.model = None

    async def explain_bet(
        self,
        matchup: str,
        model_prob: float,
        implied_prob: float,
        edge: float,
        note: str,
    ) -> str:
        if not self.enabled:
            return f"Gemini offline. Edge: {edge:.1%}, model: {model_prob:.1%} vs implied: {implied_prob:.1%}."
        try:
            prompt = (
                f"MLB game: {matchup}. "
                f"Our model gives {model_prob:.1%} win probability. "
                f"The market implies {implied_prob:.1%}. "
                f"Edge: {edge:.1%}. Note: {note}. "
                "In 2-3 sentences, explain why this might be a value bet and flag any risks. "
                "Be concise and direct."
            )
            response = await self.model.generate_content_async(prompt)
            return response.text.strip()
        except Exception as exc:
            logger.error("Gemini error: %s", exc)
            return f"Gemini unavailable. Edge {edge:.1%}."
