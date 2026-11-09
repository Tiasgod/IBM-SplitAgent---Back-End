from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalizar_url_banco(url: str) -> str:
    """Ajusta a URL do Neon/Railway para o driver psycopg (v3) do SQLAlchemy."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]

    return url


class Settings(BaseSettings):
    """Configurações lidas de variáveis de ambiente e do arquivo .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SplitAgent API"
    app_version: str = "0.2.0"
    environment: str = "development"
    docs_enabled: bool = True
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Banco de dados
    database_url: str | None = None
    database_url_direct: str | None = None

    # Envio de e-mail para recuperação de senha
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    frontend_reset_url: str = "http://localhost:5173/redefinir-senha"

    # OAuth Google
    google_client_id: str | None = None

    # Cloudflare Workers AI
    cloudflare_account_id: str | None = None
    cloudflare_api_token: str | None = None
    cloudflare_model: str = "@cf/zai-org/glm-4.7-flash"
    cloudflare_timeout_seconds: int = 180

    # Importação de planilhas
    importacao_max_mb: int = 5
    importacao_max_linhas: int = 5000
    fuso_horario: str = "America/Sao_Paulo"

    # Provisório até a implementação completa do acesso e conta
    usuario_dev_id: int | None = None

    @field_validator("usuario_dev_id", mode="before")
    @classmethod
    def _vazio_vira_none(cls, valor):
        if isinstance(valor, str) and not valor.strip():
            return None
        return valor

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origem.strip()
            for origem in self.cors_origins.split(",")
            if origem.strip()
        ]

    @property
    def sqlalchemy_database_url(self) -> str | None:
        if not self.database_url or not self.database_url.strip():
            return None

        return normalizar_url_banco(self.database_url.strip())

    @property
    def sqlalchemy_migration_url(self) -> str | None:
        direta = (self.database_url_direct or "").strip()

        if direta:
            return normalizar_url_banco(direta)

        return self.sqlalchemy_database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()