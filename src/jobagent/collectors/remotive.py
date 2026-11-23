
"""Coleta vagas públicas da Remotive.

Vagas anunciadas como remotas ainda exigem verificação
de elegibilidade para candidatos residentes no Brasil.
"""

import re
from html import unescape

import requests

from jobagent.matching import (
    ENTRY,
    FREELANCE,
    INTERNSHIP,
    contains_term,
)
from jobagent.models import Opportunity

URL = "https://remotive.com/api/remote-jobs"


def clean(value):
    text = unescape(str(value or ""))
    return re.sub(r"<[^>]+>", " ", text).strip()


def classify_track(title):
    if contains_term(title, INTERNSHIP):
        return "br_internship"

    if contains_term(title, FREELANCE):
        return "global_freelance"

    return "global_entry"


def fetch(limit=100):
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("O limite deve ser um inteiro positivo")

    response = requests.get(
        URL,
        timeout=20,
        headers={"User-Agent": "jobagent-research/0.3"},
    )
    response.raise_for_status()

    results = []

    for item in response.json().get("jobs", [])[:limit]:
        title = item.get("title") or ""
        location = item.get("candidate_required_location") or ""

        try:
            results.append(
                Opportunity(
                    title=title,
                    company=item.get("company_name") or "",
                    url=item.get("url") or "",
                    description=clean(item.get("description")),
                    location=location,
                    track=classify_track(title),
                    source="remotive",
                    remote=True,
                    country_restrictions=location,
                )
            )
        except ValueError:
            continue

    return results
