
"""Verificação conservadora de elegibilidade geográfica."""

from .matching import evaluate


def eligibility(op):
    status, reason = evaluate(op)

    if status == "rejected":
        return "blocked", reason

    if status == "review":
        return "needs_eligibility", reason

    return (
        "eligible",
        "Filtros iniciais atendidos; confirmar elegibilidade no anúncio original",
    )
