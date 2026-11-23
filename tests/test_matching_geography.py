
import pytest

from jobagent.models import Opportunity
from jobagent.matching import evaluate


@pytest.mark.parametrize(
    "company, description, location, restrictions, expected",
    [
        (
            "Empresa Brasil",
            "Estágio remoto com Python e SQL.",
            "Brasil",
            "Aceita residentes no Brasil",
            "candidate",
        ),
        (
            "Empresa EUA",
            "Estágio remoto com Python. US residents only.",
            "Remote",
            "",
            "rejected",
        ),
        (
            "Empresa Internacional",
            "Estágio remoto com Python e SQL.",
            "Remote",
            "",
            "review",
        ),
    ],
)
def test_geographic_eligibility(
    company, description, location, restrictions, expected
):
    vaga = Opportunity(
        title="Estágio em Análise de Dados",
        company=company,
        url="https://example.com/" + company.replace(" ", "-").lower(),
        description=description,
        location=location,
        country_restrictions=restrictions,
        track="br_internship",
        remote=True,
    )

    status, motivo = evaluate(vaga)

    assert status == expected
    assert motivo
