from app.config import get_settings


class GeminiExplainer:
    def __init__(self):
        self.settings = get_settings()

    async def explain_bet(self, matchup: str, model_prob: float, implied_prob: float, edge: float, note: str) -> str:
        if not self.settings.gemini_api_key:
            return 'Gemini is not configured yet. Add GEMINI_API_KEY later to enable richer explanations.'
        return (
            f'Gemini explanation placeholder for {matchup}: '
            f'model {model_prob:.3f}, market {implied_prob:.3f}, edge {edge:.3f}. {note}'
        )
