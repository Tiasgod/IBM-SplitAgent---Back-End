import logging
from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class DatabaseNotConfiguredError(RuntimeError):
    """A variável DATABASE_URL não foi definida."""


@lru_cache
def get_engine() -> Engine:
    url = get_settings().sqlalchemy_database_url
    if not url:
        raise DatabaseNotConfiguredError("DATABASE_URL não configurada.")

    opcoes: dict = {"pool_pre_ping": True}
    if url.startswith("postgresql"):
        # O Neon suspende o banco quando ocioso: recicla conexões e aceita a demora do primeiro acesso.
        opcoes["pool_recycle"] = 300
        opcoes["connect_args"] = {"connect_timeout": 15}
    return create_engine(url, **opcoes)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """Dependência do FastAPI: abre uma sessão por requisição e sempre a encerra."""
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def check_connection() -> None:
    """Executa um SELECT 1 para confirmar que o banco responde."""
    with get_engine().connect() as conexao:
        conexao.execute(text("SELECT 1"))
