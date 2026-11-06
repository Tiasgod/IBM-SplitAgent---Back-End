from typing import Literal

from pydantic import BaseModel, Field


class MensagemHistorico(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ConversaRequest(BaseModel):
    mensagem: str = Field(min_length=1, max_length=2000)
    historico: list[MensagemHistorico] = Field(default_factory=list, max_length=10)


class ConversaResponse(BaseModel):
    resposta: str
    provedor: str = "Cloudflare Workers AI"
