from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    telegram_bot_token: str = Field(alias='TELEGRAM_BOT_TOKEN')
    odds_provider: str = Field(default='mock', alias='ODDS_PROVIDER')
    odds_api_key: str | None = Field(default=None, alias='ODDS_API_KEY')
    sportsdataio_api_key: str | None = Field(default=None, alias='SPORTSDATAIO_API_KEY')
    gemini_api_key: str | None = Field(default=None, alias='GEMINI_API_KEY')
    default_bankroll: float = Field(default=1000.0, alias='DEFAULT_BANKROLL')
    default_kelly_fraction: float = Field(default=0.5, alias='DEFAULT_KELLY_FRACTION')
    default_min_edge: float = Field(default=0.02, alias='DEFAULT_MIN_EDGE')
    tz: str = Field(default='America/Vancouver', alias='TZ')


@lru_cache
def get_settings() -> Settings:
    return Settings()
