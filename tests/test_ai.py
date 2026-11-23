
import json
from types import SimpleNamespace

import pytest

from jobagent import ai
from jobagent.models import Opportunity


@pytest.fixture
def oportunidade():
    return Opportunity(
        title="Estágio em Dados",
        company="Empresa Teste",
        url="https://example.com/vaga",
        description="Python, SQL e análise de dados",
        location="Brasil",
        track="br_internship",
        source="manual",
        remote=True,
    )


@pytest.fixture
def simular_gemini(monkeypatch):
    def configurar(resposta):
        monkeypatch.setenv("GEMINI_API_KEY", "chave-falsa-para-testes")

        class ClienteFalso:
            def __init__(self, api_key):
                self.models = self

            def generate_content(self, **kwargs):
                return SimpleNamespace(text=resposta)

        monkeypatch.setattr(ai.genai, "Client", ClienteFalso)

    return configurar


def test_gemini_sem_score(oportunidade, simular_gemini):
    resposta = {
        "analysis": "Perfil compatível.",
        "draft": "Tenho interesse na vaga.",
    }

    simular_gemini(json.dumps(resposta))

    with pytest.raises(ValueError, match="score"):
        ai.analyze(oportunidade, {})


def test_gemini_json_invalido(oportunidade, simular_gemini):
    simular_gemini("{json inválido")

    with pytest.raises(ValueError, match="formato inválido"):
        ai.analyze(oportunidade, {})


def test_gemini_score_acima_de_100(oportunidade, simular_gemini):
    resposta = {
        "score": 150,
        "analysis": "Perfil compatível.",
        "draft": "Tenho interesse na vaga.",
    }

    simular_gemini(json.dumps(resposta))

    resultado = ai.analyze(oportunidade, {})

    assert resultado["score"] == 100
    assert resultado["language"] == "pt-BR"
    assert resultado["analysis"] == "Perfil compatível."


def test_gemini_score_negativo(oportunidade, simular_gemini):
    resposta = {
        "score": -20,
        "analysis": "Experiência insuficiente.",
        "draft": "Gostaria de participar do processo.",
    }

    simular_gemini(json.dumps(resposta))

    resultado = ai.analyze(oportunidade, {})

    assert resultado["score"] == 0


def test_gemini_resposta_vazia(oportunidade, simular_gemini):
    simular_gemini("")

    with pytest.raises(ValueError, match="resposta vazia"):
        ai.analyze(oportunidade, {})
