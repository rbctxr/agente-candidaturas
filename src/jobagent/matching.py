
import re
import unicodedata

from .models import TRACKS


# termos relacionados às áreas de interesse
TOPICS = (
    "data",
    "dados",
    "analytics",
    "analyst",
    "analysis",
    "analise",
    "business intelligence",
    "bi analyst",
    "sql",
    "python",
    "dashboard",
    "power bi",
    "tableau",
    "machine learning",
    "artificial intelligence",
    "ai",
    "inteligencia artificial",
    "research",
    "pesquisa",
    "automation",
    "automacao",
    "data annotation",
    "ai evaluation",
    "llm",
    "generative ai",
)

FREELANCE = (
    "freelance",
    "freelancer",
    "contract",
    "contractor",
    "project based",
    "gig",
    "consultant",
    "fixed price",
    "hourly",
)

ENTRY = (
    "entry level",
    "junior",
    "jr",
    "graduate",
    "associate",
    "intern",
    "internship",
    "trainee",
    "early career",
)

INTERNSHIP = (
    "intern",
    "internship",
    "estagio",
    "estagiario",
    "estagiaria",
)

EXCLUDE = (
    "senior",
    "sr",
    "staff",
    "principal",
    "lead",
    "director",
    "manager",
    "mid level",
)

# restrições explícitas incompatíveis com residência no brasil
RESTRICTED = (
    "us only",
    "usa only",
    "united states only",
    "us residents only",
    "usa residents only",
    "must reside in the us",
    "must reside in the usa",
    "must be based in the us",
    "must be located in the united states",
    "remote within the united states",
    "remote in the united states",
    "must reside in california",
    "must be based in california",
    "canada only",
    "canadian residents only",
    "must be located in canada",
    "uk only",
    "uk residents only",
    "eu only",
    "europe only",
    "europe based applicants only",
    "remote within north america",
    "north america only",
)

# localidades que sugerem possível contratação no brasil
BRAZIL = (
    "brazil",
    "brasil",
    "br",
)

INTERNATIONAL = (
    "worldwide",
    "global",
    "anywhere",
    "latin america",
    "latam",
    "south america",
)

# indícios de vagas presenciais ou híbridas
NOT_REMOTE = (
    "hybrid",
    "hibrido",
    "onsite",
    "on site",
    "presencial",
)


def normalize(text):
    """padroniza texto para comparação de palavras."""
    text = str(text or "").casefold()

    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )

    text = re.sub(r"[^a-z0-9]+", " ", text)

    return " ".join(text.split())


def contains_term(text, terms):
    """procura termos completos, evitando correspondências parciais."""
    normalized_text = f" {normalize(text)} "

    for term in terms:
        normalized_term = normalize(term)

        if f" {normalized_term} " in normalized_text:
            return True

    return False


def evaluate(op):
    """classifica uma oportunidade sem realizar candidaturas."""

    if op.track not in TRACKS:
        return (
            "rejected",
            "trilha de candidatura inválida",
        )

    title = normalize(op.title)
    description = normalize(op.description)
    location = normalize(op.location)
    restrictions = normalize(op.country_restrictions)

    body = f"{title} {description[:2500]}"
    geographic_text = f"{location} {restrictions}"

    reasons = []

    # verifica compatibilidade com dados e ia
    if not contains_term(body, TOPICS):
        return (
            "rejected",
            "fora das áreas de dados/ia",
        )

    # exige confirmação de trabalho remoto
    if not op.remote:
        return (
            "rejected",
            "trabalho 100% remoto não confirmado",
        )

    # identifica modalidades presenciais ou híbridas
    if contains_term(
        f"{title} {geographic_text}",
        NOT_REMOTE,
    ):
        return (
            "rejected",
            "anúncio indica trabalho híbrido ou presencial",
        )

    # identifica restrições geográficas explícitas
    if contains_term(
        f"{geographic_text} {description}",
        RESTRICTED,
    ):
        return (
            "rejected",
            "restrição geográfica incompatível com o brasil",
        )

    # identifica possível compatibilidade geográfica
    accepts_brazil = contains_term(
        geographic_text,
        BRAZIL,
    )

    international_scope = contains_term(
        geographic_text,
        INTERNATIONAL,
    )

    # vagas de estágio no brasil
    if op.track == "br_internship":

        if not contains_term(title, INTERNSHIP):
            return (
                "rejected",
                "a oportunidade não é de estágio",
            )

        if not accepts_brazil:
            reasons.append(
                "confirmar elegibilidade para estágio no brasil"
            )

    # vagas internacionais de início de carreira
    elif op.track == "global_entry":

        if contains_term(title, EXCLUDE):
            return (
                "rejected",
                "senioridade acima de entry-level",
            )

        if not contains_term(title, ENTRY):
            reasons.append(
                "senioridade entry-level não comprovada"
            )

        if not accepts_brazil:
            if international_scope:
                reasons.append(
                    "confirmar se a contratação global inclui residentes no brasil"
                )
            else:
                reasons.append(
                    "confirmar se aceita profissionais residentes no brasil"
                )

    # projetos internacionais freelance
    elif op.track == "global_freelance":

        if not contains_term(
            f"{title} {description[:1200]}",
            FREELANCE,
        ):
            reasons.append(
                "modalidade freelance não comprovada"
            )

        if not accepts_brazil:
            if international_scope:
                reasons.append(
                    "confirmar se o projeto aceita profissionais no brasil"
                )
            else:
                reasons.append(
                    "confirmar contratação internacional a partir do brasil"
                )

    # oportunidades com dúvidas exigem revisão humana
    if reasons:
        return (
            "review",
            "; ".join(reasons),
        )

    return (
        "candidate",
        "filtros iniciais atendidos; validar anúncio original",
    )
