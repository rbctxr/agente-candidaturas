import pytest

from jobagent import policy
from jobagent.models import Opportunity


@pytest.mark.parametrize(
    "matching_status, expected_status",
    [
        ("rejected", "blocked"),
        ("review", "needs_eligibility"),
        ("candidate", "eligible"),
        ("unknown", "blocked"),
    ],
)
def test_eligibility_status(
    monkeypatch,
    matching_status,
    expected_status,
):
    op = Opportunity(
        title="Junior Data Analyst",
        company="Empresa Teste",
        url="https://example.org/job",
        description="Python, SQL and analytics",
        location="Brazil",
        remote=True,
    )

    monkeypatch.setattr(
        policy,
        "evaluate",
        lambda op: (matching_status, "Motivo de teste"),
    )

    status, reason = policy.eligibility(op)

    assert status == expected_status
    assert reason