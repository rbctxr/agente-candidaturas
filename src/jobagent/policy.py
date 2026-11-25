"""Política conservadora de elegibilidade de oportunidades."""

from .matching import evaluate


def eligibility(op):
    """Interpreta os filtros iniciais de uma oportunidade."""

    status, reason = evaluate(op)

    if status == "rejected":
        return "blocked", reason

    if status == "review":
        return "needs_eligibility", reason

    if status == "candidate":
        return (
            "eligible",
            "Filtros iniciais atendidos; "
            "confirmar elegibilidade no anúncio original",
        )

    return (
        "blocked",
        f"Resultado de classificação desconhecido: {status}",
    )