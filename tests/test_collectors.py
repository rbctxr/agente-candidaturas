
from jobagent.collectors import multi


def test_greenhouse_ignora_vagas_invalidas(monkeypatch):
    dados = {
        "jobs": [
            {
                "title": "Data Analyst",
                "absolute_url": "https://example.com/vaga-valida",
                "location": {"name": "Remote"},
                "content": "Python e SQL",
            },
            {
                "title": "Vaga sem URL",
                "location": {"name": "Remote"},
                "content": "Python",
            },
            {
                "title": "Vaga com URL inválida",
                "absolute_url": "url-invalida",
                "location": {"name": "Remote"},
                "content": "SQL",
            },
        ]
    }

    monkeypatch.setattr(multi, "get_json", lambda url: dados)

    resultado = multi.greenhouse("empresa-teste")

    assert len(resultado) == 1
    assert resultado[0].title == "Data Analyst"
    assert resultado[0].source == "greenhouse"


def test_lever_ignora_vagas_invalidas(monkeypatch):
    dados = [
        {
            "text": "Python Developer",
            "hostedUrl": "https://example.com/vaga-valida",
            "categories": {"location": "Remote"},
            "descriptionPlain": "Python",
        },
        {
            "text": "Vaga sem URL",
            "categories": {"location": "Remote"},
        },
        {
            "text": "Vaga com URL inválida",
            "hostedUrl": "url-invalida",
            "categories": {"location": "Remote"},
        },
    ]

    monkeypatch.setattr(multi, "get_json", lambda url: dados)

    resultado = multi.lever("empresa-teste")

    assert len(resultado) == 1
    assert resultado[0].title == "Python Developer"
    assert resultado[0].source == "lever"



def test_vaga_presencial_com_mencao_a_trabalho_remoto():
    resultado = multi.is_remote(
        "Data Analyst",
        "Office-based in London",
        "Our company offers remote work for other teams.",
    )

    assert resultado is False


def test_vaga_remota_com_mencao_a_equipes_hibridas():
    resultado = multi.is_remote(
        "Data Analyst",
        "Fully remote",
        "Other teams follow a hybrid work model.",
    )

    assert resultado is True












def test_vaga_totalmente_remota():
    assert multi.is_remote(
        "Data Analyst",
        "Remote",
        "Python and SQL",
    ) is True


def test_vaga_hibrida():
    assert multi.is_remote(
        "Data Analyst",
        "Hybrid",
        "Python and SQL",
    ) is False


def test_vaga_sem_indicacao_de_trabalho_remoto():
    assert multi.is_remote(
        "Data Analyst",
        "São Paulo",
        "Python and SQL",
    ) is False


def test_vaga_remota_em_portugues():
    assert multi.is_remote(
        "Analista de Dados",
        "100% remoto",
        "Python e SQL",
    ) is True


def test_modalidade_da_plataforma_tem_prioridade():
    assert multi.is_remote(
        title="Data Analyst",
        location="London",
        description="Other teams work remotely.",
        workplace_type="on-site",
    ) is False


def test_modalidade_remota_tem_prioridade():
    assert multi.is_remote(
        title="Data Analyst",
        location="London",
        description="Other teams work on-site.",
        workplace_type="remote",
    ) is True
