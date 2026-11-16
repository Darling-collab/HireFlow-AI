import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _secret(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st
        return str(st.secrets.get(name, default))
    except Exception:
        return default


@dataclass(frozen=True)
class Settings:
    database_url: str
    deepseek_api_key: str
    deepseek_base_url: str
    deepseek_model: str
    ai_mode: str
    app_env: str

    @property
    def ai_enabled(self) -> bool:
        return self.ai_mode == "deepseek" and bool(self.deepseek_api_key)


def get_settings() -> Settings:
    cloud_runtime = os.getenv("STREAMLIT_RUNTIME_ENVIRONMENT", "").lower() == "cloud" or os.getenv("STREAMLIT_SHARING_MODE", "").lower() in {"1", "true", "yes"}
    default_db = "sqlite:///./data/hireflow-demo.db" if cloud_runtime else "sqlite:///./data/hireflow.db"
    database_url = _secret("DATABASE_URL", default_db)
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg2://", 1)
    default_env = "cloud-demo" if cloud_runtime and database_url.startswith("sqlite") else "local"
    return Settings(database_url, _secret("DEEPSEEK_API_KEY"), _secret("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/"), _secret("DEEPSEEK_MODEL", "deepseek-chat"), _secret("AI_MODE", "mock").lower(), _secret("APP_ENV", default_env))
