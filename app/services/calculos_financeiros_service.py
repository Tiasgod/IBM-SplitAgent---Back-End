from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.erros import RequisicaoInvalidaError
from app.models import Despesa, Recebivel, SaldoInicial, Venda, SaldoManual, MovimentacaoManual
from app.services.movimentacao_service import hoje

CENTAVOS = Decimal("0.01")
ZERO = Decimal("0.00")


def _dinheiro(valor) -> Decimal:
    return Decimal(str(valor or 0)).quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def _somar(db: Session, coluna, *filtros) -> Decimal:
    valor = db.scalar(select(func.coalesce(func.sum(coluna), 0)).where(*filtros))
    return _dinheiro(valor)


def _saldo_base(db: Session, usuario_id: int) -> tuple[date | None, Decimal]:
    importado = db.scalars(
        select(SaldoInicial).where(SaldoInicial.usuario_id == usuario_id)
        .order_by(SaldoInicial.data_referencia.desc(), SaldoInicial.id.desc()).limit(1)
    ).first()
    manual = db.scalars(
        select(SaldoManual).where(SaldoManual.usuario_id == usuario_id)
        .order_by(SaldoManual.data_referencia.desc(), SaldoManual.id.desc()).limit(1)
    ).first()
    candidatos = [item for item in (importado, manual) if item is not None]
    if not candidatos:
        return None, ZERO
    saldo = max(candidatos, key=lambda item: (item.data_referencia, isinstance(item, SaldoManual), item.id))
    return saldo.data_referencia, _dinheiro(saldo.saldo)


def _periodos_abaixo_minimo(dias: list[dict], minimo: Decimal) -> list[dict]:
    periodos: list[dict] = []
    atual = None
    for dia in dias:
        if dia["saldo_previsto"] < minimo:
            if atual is None:
                atual = {"data_inicio": dia["data"], "data_fim": dia["data"], "menor_saldo_no_periodo": dia["saldo_previsto"]}
            else:
                atual["data_fim"] = dia["data"]
                atual["menor_saldo_no_periodo"] = min(atual["menor_saldo_no_periodo"], dia["saldo_previsto"])
        elif atual is not None:
            periodos.append(atual)
            atual = None
    if atual is not None:
        periodos.append(atual)
    return periodos


def _situacao(menor: Decimal, minimo: Decimal) -> str:
    if menor < ZERO:
        return "critica"
    if menor < minimo:
        return "atencao"
    return "saudavel"


def calcular_visao_geral(
    db: Session,
    usuario_id: int,
    data_inicio: date | None,
    data_fim: date | None,
    aliquota_tributaria_percentual: Decimal,
    saldo_minimo: Decimal,
) -> dict:
    data_hoje = hoje()
    inicio = data_inicio or data_hoje.replace(day=1)
    fim = data_fim or data_hoje
    if fim < inicio:
        raise RequisicaoInvalidaError("data_fim não pode ser anterior à data_inicio.")
    if fim > data_hoje:
        raise RequisicaoInvalidaError("A visão geral de vendas aceita somente períodos até hoje.")

    vendas = _somar(
        db, Venda.valor_bruto,
        Venda.usuario_id == usuario_id, Venda.data >= inicio, Venda.data <= fim,
    )
    taxa = aliquota_tributaria_percentual / Decimal("100")
    tributos = _dinheiro(vendas * taxa)
    liquido = _dinheiro(vendas - tributos)

    fluxo = calcular_fluxo_caixa(db, usuario_id, aliquota_tributaria_percentual, saldo_minimo, data_hoje, 30)
    return {
        "data_inicio": inicio,
        "data_fim": fim,
        "aliquota_tributaria_percentual": aliquota_tributaria_percentual,
        "total_vendido": vendas,
        "tributos_estimados": tributos,
        "valor_liquido_vendas": liquido,
        "saldo_atual": fluxo["saldo_atual"],
        "saldo_minimo_configurado": saldo_minimo,
        "menor_saldo_previsto": fluxo["menor_saldo_previsto"],
        "data_menor_saldo_previsto": fluxo["data_menor_saldo_previsto"],
        "situacao_caixa": fluxo["situacao_caixa"],
        "periodos_abaixo_minimo": fluxo["periodos_abaixo_minimo"],
        "observacao_tributaria": "Estimativa simplificada sobre o faturamento bruto. A alíquota é configurável e não substitui cálculo contábil/fiscal.",
    }


def calcular_fluxo_caixa(
    db: Session,
    usuario_id: int,
    aliquota_tributaria_percentual: Decimal,
    saldo_minimo: Decimal,
    data_base: date | None = None,
    horizonte_dias: int = 30,
) -> dict:
    hoje_local = data_base or hoje()
    fim = hoje_local + timedelta(days=horizonte_dias)
    data_saldo, saldo_inicial = _saldo_base(db, usuario_id)
    if data_saldo is not None and data_saldo > hoje_local:
        # Um saldo informado com referência futura não pode ser usado como saldo atual.
        saldo_inicial = ZERO
        data_saldo = None

    # Estima o saldo atual usando o saldo inicial e os recebíveis/despesas com data posterior
    # à referência do saldo e até hoje. Recebíveis são informados em valor bruto.
    filtros_recebidos = [Recebivel.usuario_id == usuario_id, Recebivel.data_prevista <= hoje_local]
    filtros_pagos = [Despesa.usuario_id == usuario_id, Despesa.vencimento <= hoje_local]
    if data_saldo is not None:
        filtros_recebidos.append(Recebivel.data_prevista > data_saldo)
        filtros_pagos.append(Despesa.vencimento > data_saldo)
    recebidos_brutos = _somar(db, Recebivel.valor_esperado, *filtros_recebidos)
    despesas_passadas = _somar(db, Despesa.valor, *filtros_pagos)
    filtros_manuais = [MovimentacaoManual.usuario_id == usuario_id, MovimentacaoManual.data <= hoje_local]
    if data_saldo is not None:
        filtros_manuais.append(MovimentacaoManual.data > data_saldo)
    entradas_manuais_passadas = _somar(db, MovimentacaoManual.valor, *filtros_manuais, MovimentacaoManual.tipo == "entrada")
    saidas_manuais_passadas = _somar(db, MovimentacaoManual.valor, *filtros_manuais, MovimentacaoManual.tipo == "saida")
    taxa = aliquota_tributaria_percentual / Decimal("100")
    recebidos_liquidos = _dinheiro(recebidos_brutos * (Decimal("1") - taxa))
    saldo_atual = _dinheiro(saldo_inicial + recebidos_liquidos - despesas_passadas + entradas_manuais_passadas - saidas_manuais_passadas)

    # Agrupa entradas e saídas futuras por dia. A tributação é estimada sobre os recebíveis
    # brutos para não somar vendas e recebíveis como se fossem duas entradas distintas.
    entradas_por_dia: dict[date, Decimal] = defaultdict(lambda: ZERO)
    saidas_por_dia: dict[date, Decimal] = defaultdict(lambda: ZERO)
    entradas_manuais_por_dia: dict[date, Decimal] = defaultdict(lambda: ZERO)
    recebiveis_futuros = db.execute(
        select(Recebivel.data_prevista, func.sum(Recebivel.valor_esperado))
        .where(Recebivel.usuario_id == usuario_id, Recebivel.data_prevista > hoje_local, Recebivel.data_prevista <= fim)
        .group_by(Recebivel.data_prevista)
    ).all()
    for data, total in recebiveis_futuros:
        entradas_por_dia[data] += _dinheiro(total)
    despesas_futuras = db.execute(
        select(Despesa.vencimento, func.sum(Despesa.valor))
        .where(Despesa.usuario_id == usuario_id, Despesa.vencimento > hoje_local, Despesa.vencimento <= fim)
        .group_by(Despesa.vencimento)
    ).all()
    for data, total in despesas_futuras:
        saidas_por_dia[data] += _dinheiro(total)

    manuais_futuros = db.execute(
        select(MovimentacaoManual.data, MovimentacaoManual.tipo, func.sum(MovimentacaoManual.valor))
        .where(MovimentacaoManual.usuario_id == usuario_id, MovimentacaoManual.data > hoje_local, MovimentacaoManual.data <= fim)
        .group_by(MovimentacaoManual.data, MovimentacaoManual.tipo)
    ).all()
    for data, tipo_manual, total in manuais_futuros:
        if tipo_manual == "entrada":
            entradas_por_dia[data] += _dinheiro(total)
            entradas_manuais_por_dia[data] += _dinheiro(total)
        else:
            saidas_por_dia[data] += _dinheiro(total)

    dias: list[dict] = []
    saldo_corrente = saldo_atual
    for deslocamento in range(1, horizonte_dias + 1):
        data = hoje_local + timedelta(days=deslocamento)
        entrada_bruta = entradas_por_dia[data]
        imposto = _dinheiro((entrada_bruta - entradas_manuais_por_dia[data]) * taxa)
        entrada_liquida = _dinheiro(entrada_bruta - imposto)
        saldo_antes = saldo_corrente
        saldo_corrente = _dinheiro(saldo_corrente + entrada_liquida - saidas_por_dia[data])
        dias.append({
            "data": data,
            "saldo_inicial_dia": saldo_antes,
            "total_entradas_brutas": entrada_bruta,
            "tributos_estimados": imposto,
            "total_entradas_liquidas": entrada_liquida,
            "total_saidas": saidas_por_dia[data],
            "saldo_previsto": saldo_corrente,
            "abaixo_minimo": saldo_corrente < saldo_minimo,
        })

    if dias:
        menor_dia = min(dias, key=lambda item: (item["saldo_previsto"], item["data"]))
        menor_saldo = menor_dia["saldo_previsto"]
        data_menor = menor_dia["data"]
    else:
        menor_saldo, data_menor = saldo_atual, hoje_local
    periodos = _periodos_abaixo_minimo(dias, saldo_minimo)
    return {
        "data_inicio": hoje_local,
        "data_fim": fim,
        "saldo_atual": saldo_atual,
        "saldo_minimo_configurado": _dinheiro(saldo_minimo),
        "menor_saldo_previsto": menor_saldo,
        "data_menor_saldo_previsto": data_menor,
        "situacao_caixa": _situacao(menor_saldo, saldo_minimo),
        "periodos_abaixo_minimo": periodos,
        "dias": dias,
    }
