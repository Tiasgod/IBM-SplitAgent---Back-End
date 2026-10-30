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
    """Configurações lidas de variáveis de ambiente (e do arquivo .env, em desenvolvimento)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "SplitAgent API"
    app_version: str = "0.2.0"
    environment: str = "development"
    docs_enabled: bool = True
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Banco. DATABASE_URL_DIRECT (sem pooler) é opcional e usada só nas migrações do Alembic.
    database_url: str | None = None
    database_url_direct: str | None = None

    # Envio de e-mail para recuperação de senha (obrigatório em produção).
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    frontend_reset_url: str = "http://localhost:5173/redefinir-senha"

    # OAuth Google: ID do cliente OAuth Web criado no Google Cloud Console.
    google_client_id: str | None = None

    # Importação de planilhas
    importacao_max_mb: int = 5
    importacao_max_linhas: int = 5000
    fuso_horario: str = "America/Sao_Paulo"

    # PROVISÓRIO até o card B02 (Acesso e conta): usuário fixo para desenvolvimento.
    # Sem esta variável, os endpoints de dados financeiros respondem 501 (não implementado).
    usuario_dev_id: int | None = None

    @field_validator("usuario_dev_id", mode="before")
    @classmethod
    def _vazio_vira_none(cls, valor):
        if isinstance(valor, str) and not valor.strip():
            return None
        return valor

    @property
    def cors_origins_list(self) -> list[str]:
        return [origem.strip() for origem in self.cors_origins.split(",") if origem.strip()]

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
