from datetime import timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.seguranca import get_usuario_atual_id
from app.models import Despesa, Recebivel, MovimentacaoManual
from app.schemas.assistente import ConversaRequest, ConversaResponse
from app.services.calculos_financeiros_service import calcular_fluxo_caixa
from app.services.ia_service import responder_assistente
from app.services.movimentacao_service import hoje

router = APIRouter(prefix="/assistente", tags=["Assistente Splito"])


def _pergunta_financeira(mensagem: str) -> bool:
    termos = (
        "finance", "caixa", "saldo", "conta", "pagar", "pagamento", "despesa",
        "gasto", "receber", "recebimento", "venda", "faturamento", "dívida",
        "divida", "tribut", "imposto", "crédito", "credito", "vencimento",
        "previsão", "previsao", "empresa", "compra", "dinheiro", "movimentação",
        "movimentacao", "entrada", "saída", "saida",
    )
    texto = mensagem.casefold()
    return any(termo in texto for termo in termos)


def _obter_contexto_financeiro(db: Session, usuario_id: int, mensagem: str) -> dict:
    data_hoje = hoje()
    horizonte = 30
    projecao = calcular_fluxo_caixa(
        db=db,
        usuario_id=usuario_id,
        aliquota_tributaria_percentual=Decimal("6.00"),
        saldo_minimo=Decimal("0.00"),
        data_base=data_hoje,
        horizonte_dias=horizonte,
    )

    limite = data_hoje + timedelta(days=30)
    termos_detalhe = ("conta", "pagar", "vencimento", "receber", "recebimento", "despesa", "lançamento", "lancamento")
    incluir_detalhes = any(termo in mensagem.casefold() for termo in termos_detalhe)

    despesas = db.scalars(
        select(Despesa)
        .where(Despesa.usuario_id == usuario_id, Despesa.vencimento >= data_hoje, Despesa.vencimento <= limite)
        .order_by(Despesa.vencimento.asc())
        .limit(20)
    ).all()
    recebiveis = db.scalars(
        select(Recebivel)
        .where(Recebivel.usuario_id == usuario_id, Recebivel.data_prevista >= data_hoje, Recebivel.data_prevista <= limite)
        .order_by(Recebivel.data_prevista.asc())
        .limit(20)
    ).all()
    movimentacoes_manuais = db.scalars(
        select(MovimentacaoManual)
        .where(MovimentacaoManual.usuario_id == usuario_id, MovimentacaoManual.data >= data_hoje, MovimentacaoManual.data <= limite)
        .order_by(MovimentacaoManual.data.asc())
        .limit(20)
    ).all()

    return {
        "data_consulta": data_hoje.isoformat(),
        "periodo_projecao_dias": horizonte,
        "saldo_atual_calculado": str(projecao["saldo_atual"]),
        "menor_saldo_previsto": str(projecao["menor_saldo_previsto"]),
        "data_menor_saldo_previsto": (projecao["data_menor_saldo_previsto"].isoformat() if projecao.get("data_menor_saldo_previsto") else None),
        "situacao_caixa": projecao["situacao_caixa"],
        "total_entradas_previstas_30_dias": str(sum((r.valor_esperado for r in recebiveis), Decimal("0.00"))),
        "total_despesas_importadas_30_dias": str(sum((d.valor for d in despesas), Decimal("0.00"))),
        "totais_previstos_30_dias": {
            "entradas_liquidas": str(sum((dia["total_entradas_liquidas"] for dia in projecao["dias"]), Decimal("0.00"))),
            "saidas": str(sum((dia["total_saidas"] for dia in projecao["dias"]), Decimal("0.00"))),
        },
        "detalhes_de_movimentacoes": ([
            {"vencimento": d.vencimento.isoformat(), "descricao": d.descricao, "valor": str(d.valor), "origem": "planilha"}
            for d in despesas
        ] + [
            {"data_prevista": r.data_prevista.isoformat(), "descricao": r.descricao or "Recebimento previsto", "valor": str(r.valor_esperado), "tipo": "entrada", "origem": "planilha"}
            for r in recebiveis
        ] + [
            {"data": m.data.isoformat(), "tipo": m.tipo, "descricao": m.descricao, "categoria": m.categoria, "valor": str(m.valor), "origem": "manual"}
            for m in movimentacoes_manuais
        ]) if incluir_detalhes else "Omitidos porque a pergunta não solicitou detalhes de contas ou lançamentos.",
        "observacao": "A projeção usa a alíquota padrão de 6% já adotada pelo módulo financeiro do SplitAgent. É uma estimativa demonstrativa, não uma apuração tributária individual. Os registros listados distinguem dados importados e lançamentos manuais.",
    }


@router.post("/conversar", response_model=ConversaResponse, summary="Conversa com o assistente Splito")
def conversar(
    dados: ConversaRequest,
    db: Session = Depends(get_db),
    usuario_id: int = Depends(get_usuario_atual_id),
) -> ConversaResponse:
    contexto = _obter_contexto_financeiro(db, usuario_id, dados.mensagem) if _pergunta_financeira(dados.mensagem) else None
    historico = [item.model_dump() for item in dados.historico]
    resultado = responder_assistente(dados.mensagem, contexto, historico)

    if resultado.get("status") != "ok" or not resultado.get("resposta"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=resultado.get("mensagem", "O assistente está temporariamente indisponível."),
        )

    return ConversaResponse(resposta=resultado["resposta"])
