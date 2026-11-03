from decimal import Decimal

from sqlalchemy.orm import Session

from app.agents.orchestrator import SplitAgentOrchestrator
from app.services.calculos_financeiros_service import calcular_fluxo_caixa
from app.services.ia_service import interpretar_analise_financeira
from app.services.movimentacao_service import hoje


def analisar_financas_com_agentes(
    db: Session,
    usuario_id: int,
    aliquota_tributaria_percentual: Decimal,
    saldo_minimo: Decimal,
    horizonte_dias: int,
    incluir_ia: bool = True,
) -> dict:
    projecao = calcular_fluxo_caixa(
        db,
        usuario_id,
        aliquota_tributaria_percentual,
        saldo_minimo,
        hoje(),
        horizonte_dias,
    )

    # Utiliza o fluxo consolidado pelo serviço financeiro
    # (planilhas + lançamentos manuais).
    movimentos = []
    total_entradas = Decimal("0.00")
    total_saidas = Decimal("0.00")

    for dia in projecao["dias"]:
        data_iso = dia["data"].isoformat()

        entradas = Decimal(str(dia["total_entradas_liquidas"]))
        saidas = Decimal(str(dia["total_saidas"]))

        if entradas > 0:
            movimentos.append({
                "type": "income",
                "amount": format(entradas, ".2f"),
                "date": data_iso,
                "description": "Entradas previstas consolidadas",
            })
            total_entradas += entradas

        if saidas > 0:
            movimentos.append({
                "type": "expense",
                "amount": format(saidas, ".2f"),
                "date": data_iso,
                "description": "Saídas previstas consolidadas",
            })
            total_saidas += saidas

    orchestrator = SplitAgentOrchestrator()

    tributos_ja_calculados = sum(
        (
            Decimal(str(dia["tributos_estimados"]))
            for dia in projecao["dias"]
        ),
        Decimal("0.00"),
    )

    taxa = Decimal(str(aliquota_tributaria_percentual))

    # Reconstrói uma base equivalente a partir dos tributos já calculados.
    base_tributavel_equivalente = (
        tributos_ja_calculados * Decimal("100") / taxa
        if taxa > 0
        else Decimal("0.00")
    )

    resultado_agentes = orchestrator.process_financial(
        movimentos,
        projecao["data_fim"].isoformat(),
        format(projecao["saldo_atual"], ".2f"),
        format(base_tributavel_equivalente, ".2f"),
        format(taxa, ".2f"),
    )

    # A projeção existente continua sendo a fonte oficial dos valores.
    resultado_agentes["results"]["tax"][
        "tributos_estimados_calculo_financeiro"
    ] = format(tributos_ja_calculados, ".2f")

    resultado_agentes["results"]["tax"]["observacao"] = (
        "Estimativa demonstrativa alinhada à alíquota informada. "
        "O valor da projeção financeira é a referência e não substitui "
        "apuração contábil/fiscal."
    )

    # Somente indicadores já calculados são enviados à IA.
    dados_ia = {
        "saldo_atual": format(projecao["saldo_atual"], ".2f"),
        "saldo_minimo": format(
            projecao["saldo_minimo_configurado"], ".2f"
        ),
        "menor_saldo_previsto": format(
            projecao["menor_saldo_previsto"], ".2f"
        ),
        "data_menor_saldo_previsto": (
            projecao["data_menor_saldo_previsto"].isoformat()
        ),
        "situacao_caixa": projecao["situacao_caixa"],
        "total_entradas_liquidas_previstas": format(
            total_entradas, ".2f"
        ),
        "total_saidas_previstas": format(
            total_saidas, ".2f"
        ),
        "periodos_abaixo_minimo": [
            {
                "data_inicio": periodo["data_inicio"].isoformat(),
                "data_fim": periodo["data_fim"].isoformat(),
                "menor_saldo_no_periodo": format(
                    periodo["menor_saldo_no_periodo"], ".2f"
                ),
            }
            for periodo in projecao["periodos_abaixo_minimo"]
        ],
    }

    if incluir_ia:
        interpretacao = interpretar_analise_financeira(dados_ia)
    else:
        interpretacao = {
            "status": "ignorada",
            "provedor": "Cloudflare Workers AI",
            "recomendacao": None,
        }

    return {
        "agentes": resultado_agentes,
        "ia_generativa": interpretacao,
        "observacao": (
            "Os valores numéricos são calculados pelo back-end e pelos "
            "agentes determinísticos. A IA do Cloudflare Workers AI "
            "apenas interpreta os indicadores e não altera os cálculos."
        ),
    }


def simular_divisao(dados: dict) -> dict:
    return SplitAgentOrchestrator().process_split_payment(dados)


def analisar_credito(dados: dict) -> dict:
    return SplitAgentOrchestrator().process_credit(dados)


def estimar_tributos(total: Decimal, aliquota: Decimal) -> dict:
    from app.agents.tax import TaxAgent

    return TaxAgent().process_with_rate(total, aliquota) 