
"""Conectores públicos: Greenhouse, Lever e importação manual.

A coleta depende do identificador público correto da empresa.
A indicação de trabalho remoto não confirma elegibilidade no Brasil.
"""

import re
from html import unescape

import requests

from ..models import Opportunity


def clean(value):
    return re.sub(r"<[^>]+>", " ", unescape(str(value or ""))).strip()


def get_json(url, timeout=15):
    response = requests.get(
        url,
        timeout=timeout,
        headers={
            "User-Agent": "jobagent-research/0.3 (personal job search)"
        },
    )
    response.raise_for_status()
    return response.json()


def is_remote(*values):
    """Identifica indicação explícita de trabalho remoto."""
    text = " ".join(str(value or "") for value in values).casefold()

    remote_patterns = (
        r"\bremote\b",
        r"\bremoto\b",
        r"\bremota\b",
        r"\bwork from home\b",
        r"\bfully distributed\b",
        r"\b100%\s*(?:remote|remoto|remota)\b",
    )

    non_remote_patterns = (
        r"\bhybrid\b",
        r"\bhíbrido\b",
        r"\bhibrido\b",
        r"\bon[- ]site\b",
        r"\bpresencial\b",
        r"\bnot remote\b",
        r"\bno remote\b",
    )

    if any(re.search(pattern, text) for pattern in non_remote_patterns):
        return False

    return any(re.search(pattern, text) for pattern in remote_patterns)


def greenhouse(board_token, track="global_entry"):
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", board_token):
        raise ValueError("Board inválido")

    data = get_json(
        f"https://boards-api.greenhouse.io/v1/boards/"
        f"{board_token}/jobs?content=true"
    )

    result = []

    for job in data.get("jobs", []):
        location = (job.get("location") or {}).get("name", "")
        description = clean(job.get("content"))

        try:
            opportunity = Opportunity(
                title=job.get("title") or "",
                company=board_token,
                url=job.get("absolute_url") or "",
                description=description,
                location=location,
                source="greenhouse",
                track=track,
                remote=is_remote(
                    job.get("title"),
                    location,
                    description,
                ),
            )
        except ValueError:
            # Ignora a vaga inválida e continua a coleta.
            continue

        result.append(opportunity)

    return result


def lever(company_slug, track="global_entry"):
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", company_slug):
        raise ValueError("Slug inválido")

    data = get_json(
        f"https://api.lever.co/v0/postings/"
        f"{company_slug}?mode=json"
    )

    result = []

    for job in data:
        categories = job.get("categories") or {}
        location = categories.get("location") or ""
        description = clean(
            job.get("descriptionPlain") or job.get("description")
        )

        workplace_type = job.get("workplaceType") or ""
        commitment = categories.get("commitment") or ""

        try:
            opportunity = Opportunity(
                title=job.get("text") or "",
                company=company_slug,
                url=job.get("hostedUrl") or "",
                description=description,
                location=location,
                source="lever",
                track=track,
                remote=is_remote(
                    job.get("text"),
                    location,
                    description,
                    workplace_type,
                    commitment,
                ),
            )
        except ValueError:
            # Ignora a vaga inválida e continua a coleta.
            continue

        result.append(opportunity)

    return result


def manual(
    title,
    company,
    url,
    description,
    location,
    track,
    remote=False,
):
    return Opportunity(
        title=title,
        company=company,
        url=url,
        description=description,
        location=location,
        track=track,
        remote=remote,
        source="manual",
    )
