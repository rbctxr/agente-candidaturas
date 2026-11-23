
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
