
import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from jobagent.models import Opportunity, TRACKS
from jobagent.matching import evaluate
from jobagent.collectors.remotive import fetch
from jobagent.storage import (
    connect,
    upsert,
    all_jobs,
    save_analysis,
    save_draft,
    set_status,
)
from jobagent.ai import analyze


# configurações iniciais
load_dotenv()

st.set_page_config(
    page_title="agente global de candidaturas",
    layout="wide",
)

st.title("agente global de candidaturas")
st.caption(
    "brasil · entry-level global · freelance global | "
    "nenhuma candidatura é enviada automaticamente"
)


# banco de dados e perfil
conn = connect(
    os.getenv("DATABASE_PATH", "data/global_jobs.db")
)

profile_file = Path("data/profile.json")

if not profile_file.exists():
    st.warning(
        "revise profile.example.json e salve uma cópia "
        "como data/profile.json antes de analisar vagas."
    )

profile = (
    json.loads(profile_file.read_text(encoding="utf-8"))
    if profile_file.exists()
    else None
)


# barra lateral
with st.sidebar:
    st.header("fontes e perfil")

    if st.button("buscar na remotive"):
        try:
            fetched = fetch()

            for op in fetched:
                eligibility, reason = evaluate(op)

                if eligibility != "rejected":
                    upsert(conn, op, eligibility, reason)

            st.success(
                f"analisados {len(fetched)} anúncios; "
                "candidatos e vagas para revisão foram salvos. "
                "a cobertura da fonte é limitada."
            )

        except Exception as exc:
            st.error(f"erro na coleta: {exc}")

    st.caption(
        "a classificação da fonte é heurística. "
        "verifique cada anúncio."
    )

    track_filter = st.selectbox(
        "trilha",
        ["Todas", *TRACKS],
    )


# cadastro manual de oportunidades
st.subheader("adicionar oportunidade manualmente")

with st.form("manual"):
    title = st.text_input("título")
    company = st.text_input("empresa / cliente")
    url = st.text_input("url do anúncio")

    desc = st.text_area(
        "descrição integral (cole o texto do anúncio)"
    )

    location = st.text_input(
        "região de contratação (conforme anúncio)",
        value="Unknown",
    )

    track = st.selectbox("trilha", TRACKS)

    remote = st.checkbox(
        "o anúncio confirma trabalho 100% remoto"
    )

    restrictions = st.text_input(
        "restrições geográficas explícitas (se houver)"
    )

    budget = st.text_input(
        "orçamento / taxa (freelance, se houver)"
    )

    if st.form_submit_button("salvar e avaliar filtros"):
        try:
            if (
                not title.strip()
                or not company.strip()
                or not desc.strip()
            ):
                raise ValueError(
                    "preencha título, empresa e descrição"
                )

            op = Opportunity(
                title,
                company,
                url,
                desc,
                location,
                track,
                "manual",
                remote,
                restrictions,
                budget,
            )

            eligibility, reason = evaluate(op)

            if eligibility == "rejected":
                st.warning(reason)

            else:
                upsert(conn, op, eligibility, reason)

                st.success(
                    f"salvo como {eligibility}: {reason}"
                )

        except ValueError as exc:
            st.error(str(exc))


# listagem de oportunidades
st.subheader("oportunidades")

rows = all_jobs(
    conn,
    None if track_filter == "Todas" else track_filter,
)

for row in rows:
    j = dict(row)

    with st.expander(
        f"{j['title']} — {j['company']} | "
        f"{j['track']} | {j['status']}"
    ):
        st.write(
            "elegibilidade:",
            j["eligibility"],
            "—",
            j["eligibility_reason"],
        )

        st.write("localidade:", j["location"])

        st.link_button(
            "abrir anúncio original",
            j["url"],
        )

        st.text(j["description"][:3500])

        # análise com gemini
        if (
            j["status"] in ("nova", "para_revisao")
            and st.button(
                "analisar e gerar rascunho",
                key="an_" + j["id"],
            )
        ):
            if not profile:
                st.error(
                    "configure o perfil factual primeiro"
                )

            elif not os.getenv("GEMINI_API_KEY"):
                st.error(
                    "configure GEMINI_API_KEY no .env"
                )

            else:
                try:
                    op = Opportunity(
                        j["title"],
                        j["company"],
                        j["url"],
                        j["description"],
                        j["location"],
                        j["track"],
                        j["source"],
                        bool(j["remote"]),
                        j["country_restrictions"],
                        j["budget"],
                        j["id"],
                    )

                    save_analysis(
                        conn,
                        j["id"],
                        analyze(op, profile),
                    )

                    st.rerun()

                except Exception as exc:
                    st.error(
                        f"falha na análise: {exc}"
                    )

        # resultado da análise
        if j["analysis"]:
            st.metric(
                "compatibilidade heurística",
                f"{j['score']}/100",
            )

            st.write(j["analysis"])

            # revisão manual do rascunho
            with st.form("edit_" + j["id"]):
                revised = st.text_area(
                    "rascunho editável — revise fatos, "
                    "elegibilidade e tom",
                    value=j["draft"] or "",
                    height=220,
                )

                if st.form_submit_button(
                    "salvar revisão"
                ):
                    try:
                        save_draft(
                            conn,
                            j["id"],
                            revised,
                        )

                        st.success("revisão salva")

                    except ValueError as exc:
                        st.error(str(exc))

            # aprovação ou rejeição manual
            if j["status"] == "para_revisao":
                a, b = st.columns(2)

                if a.button(
                    "aprovar material",
                    key="ok_" + j["id"],
                ):
                    set_status(
                        conn,
                        j["id"],
                        "aprovada",
                    )
                    st.rerun()

                if b.button(
                    "rejeitar",
                    key="no_" + j["id"],
                ):
                    set_status(
                        conn,
                        j["id"],
                        "rejeitada",
                    )
                    st.rerun()

            # registro de envio manual
            if j["status"] == "aprovada":
                st.info(
                    "material aprovado. envie manualmente "
                    "no site original; não houve envio automático."
                )

                if st.button(
                    "marcar como enviada manualmente",
                    key="sent_" + j["id"],
                ):
                    set_status(
                        conn,
                        j["id"],
                        "enviada_manualmente",
                    )
                    st.rerun()
