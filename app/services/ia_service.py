"""Integração com Cloudflare Workers AI para interpretação financeira."""

import json
import logging
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _credenciais_configuradas(settings) -> bool:
    """Verifica se as credenciais do Cloudflare foram configuradas."""
    return bool(
        settings.cloudflare_account_id
        and settings.cloudflare_api_token
    )


def _extrair_resposta(payload: dict[str, Any]) -> str:
    """Extrai o texto gerado pelos diferentes formatos de resposta da API."""

    resultado = payload.get("result") or {}

    if isinstance(resultado, dict):
        resposta = resultado.get("response")

        if isinstance(resposta, str) and resposta.strip():
            return resposta.strip()

        resposta = resultado.get("output")

        if isinstance(resposta, str) and resposta.strip():
            return resposta.strip()

        resposta = resultado.get("text")

        if isinstance(resposta, str) and resposta.strip():
            return resposta.strip()

        escolhas = resultado.get("choices") or []

        if escolhas:
            mensagem = escolhas[0].get("message") or {}
            conteudo = mensagem.get("content")

            if isinstance(conteudo, str) and conteudo.strip():
                return conteudo.strip()

    raise ValueError("A API do Cloudflare não retornou um texto válido.")


def interpretar_analise_financeira(
    dados: dict[str, Any],
) -> dict[str, Any]:
    """Solicita ao Cloudflare uma interpretação dos indicadores financeiros."""

    settings = get_settings()

    if not _credenciais_configuradas(settings):
        return {
            "status": "nao_configurada",
            "provedor": "Cloudflare Workers AI",
            "mensagem": (
                "Configure CLOUDFLARE_ACCOUNT_ID e "
                "CLOUDFLARE_API_TOKEN para habilitar as recomendações "
                "generativas."
            ),
            "recomendacao": None,
        }

    prompt = (
        "Você é um assistente de apoio à gestão financeira de pequenos negócios. "
        "Interprete exclusivamente os indicadores financeiros fornecidos. "
        "Não invente valores, datas, transações ou causas. "
        "Não faça cálculos nem altere os valores recebidos. "
        "Diferencie fatos calculados de hipóteses. "
        "Se faltarem dados, informe essa limitação. "
        "Não dê aconselhamento contábil, tributário ou de crédito oficial. "
        "Responda em português brasileiro, de forma objetiva, apresentando: "
        "1. Situação financeira; "
        "2. Principais pontos de atenção; "
        "3. Até três recomendações práticas; "
        "4. Limitações da análise. "
        "Dados financeiros calculados pelo backend: "
        + json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    )

    url = (
        "https://api.cloudflare.com/client/v4/accounts/"
        f"{settings.cloudflare_account_id}/ai/run/"
        f"{settings.cloudflare_model}"
    )

    headers = {
        "Authorization": f"Bearer {settings.cloudflare_api_token}",
        "Content-Type": "application/json",
    }

    corpo = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "Você é um assistente financeiro objetivo. "
                    "Responda sempre em português brasileiro. "
                    "Nunca invente ou recalcule dados financeiros."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    }

    try:
        with httpx.Client(
            timeout=settings.cloudflare_timeout_seconds
        ) as client:
            response = client.post(
                url,
                headers=headers,
                json=corpo,
            )

            response.raise_for_status()

            payload = response.json()
            recomendacao = _extrair_resposta(payload)

            return {
                "status": "ok",
                "provedor": "Cloudflare Workers AI",
                "modelo": settings.cloudflare_model,
                "recomendacao": recomendacao,
            }

    except httpx.TimeoutException:
        logger.warning("Tempo limite excedido na chamada ao Cloudflare Workers AI.")

        return {
            "status": "indisponivel",
            "provedor": "Cloudflare Workers AI",
            "mensagem": (
                "A IA demorou mais que o esperado para responder. "
                "Os cálculos financeiros continuam disponíveis."
            ),
            "recomendacao": None,
        }

    except httpx.HTTPStatusError as exc:
        logger.warning(
            "Cloudflare Workers AI retornou HTTP %s.",
            exc.response.status_code,
        )

        return {
            "status": "indisponivel",
            "provedor": "Cloudflare Workers AI",
            "mensagem": (
                "Não foi possível obter a interpretação generativa. "
                "Verifique a configuração e a disponibilidade do serviço. "
                "Os cálculos financeiros continuam disponíveis."
            ),
            "recomendacao": None,
        }

    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        logger.exception("Falha ao interpretar a análise financeira com Cloudflare.")

        return {
            "status": "indisponivel",
            "provedor": "Cloudflare Workers AI",
            "mensagem": (
                "Não foi possível obter a interpretação generativa. "
                "Os cálculos financeiros continuam disponíveis."
            ),
            "recomendacao": None,
        }