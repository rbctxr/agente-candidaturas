
"""Controle do piloto de candidaturas.

Exige 10 candidaturas manuais únicas antes de permitir
a ativação explícita do modo automático.

Este módulo não envia candidaturas.
"""

PILOT_TARGET = 10
DAILY_LIMIT = 5
WEEKLY_LIMIT = 20

VALID_STATES = {
    "discovered",
    "needs_eligibility",
    "drafted",
    "approved",
    "submitted_manual",
    "submitted_automatic",
    "rejected",
    "blocked",
    "failed",
}


def init(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS application_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            opportunity_id TEXT NOT NULL,
            event TEXT NOT NULL,
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS pilot_settings (
            singleton INTEGER PRIMARY KEY CHECK(singleton=1),
            mode TEXT NOT NULL DEFAULT 'pilot',
            auto_opt_in INTEGER NOT NULL DEFAULT 0
        )
    """)

    conn.execute("""
        INSERT OR IGNORE INTO pilot_settings (
            singleton, mode, auto_opt_in
        )
        VALUES (1, 'pilot', 0)
    """)


def event(conn, opportunity_id, name, note=""):
    if name not in VALID_STATES:
        raise ValueError("Evento inválido")

    init(conn)

    conn.execute("""
        INSERT INTO application_events (
            opportunity_id, event, note
        )
        VALUES (?, ?, ?)
    """, (opportunity_id, name, note))

    conn.commit()


def confirmed_count(conn):
    init(conn)

    return conn.execute("""
        SELECT COUNT(DISTINCT opportunity_id)
        FROM application_events
        WHERE event='submitted_manual'
    """).fetchone()[0]


def limits_ok(conn):
    init(conn)

    query = """
        SELECT COUNT(DISTINCT opportunity_id)
        FROM application_events
        WHERE event IN (
            'submitted_manual',
            'submitted_automatic'
        )
        AND created_at >= datetime('now', ?)
    """

    today = conn.execute(query, ("-1 day",)).fetchone()[0]
    week = conn.execute(query, ("-7 days",)).fetchone()[0]

    return today < DAILY_LIMIT and week < WEEKLY_LIMIT


def can_auto_submit(
    conn,
    opportunity_id,
    platform_allowed,
    eligibility_confirmed,
    approved,
    truthful,
    adapter_ready=False,
):
    init(conn)

    setting = conn.execute("""
        SELECT mode, auto_opt_in
        FROM pilot_settings
        WHERE singleton=1
    """).fetchone()

    reasons = []

    if confirmed_count(conn) < PILOT_TARGET:
        reasons.append(
            "Piloto de 10 candidaturas ainda não concluído"
        )

    if setting[0] != "auto" or not setting[1]:
        reasons.append(
            "Automação não habilitada explicitamente"
        )

    if not platform_allowed:
        reasons.append(
            "Plataforma não autoriza envio automatizado"
        )

    if not eligibility_confirmed:
        reasons.append(
            "Elegibilidade geográfica/contratual não confirmada"
        )

    if not approved:
        reasons.append(
            "Candidatura fora do escopo autorizado"
        )

    if not truthful:
        reasons.append(
            "Conteúdo não validado contra perfil factual"
        )

    if not adapter_ready:
        reasons.append(
            "Nenhum adaptador autorizado implementado"
        )

    if not limits_ok(conn):
        reasons.append("Limite de envios atingido")

    existing = conn.execute("""
        SELECT 1
        FROM application_events
        WHERE opportunity_id=?
          AND event IN (
              'submitted_manual',
              'submitted_automatic'
          )
    """, (opportunity_id,)).fetchone()

    if existing:
        reasons.append("Candidatura já enviada")

    return not reasons, reasons


def enable_auto(conn, explicit_confirmation):
    init(conn)

    if explicit_confirmation != "EU AUTORIZO ENVIO AUTOMATICO":
        raise ValueError(
            "Confirmação explícita necessária"
        )

    if confirmed_count(conn) < PILOT_TARGET:
        raise ValueError(
            "Concluir 10 candidaturas manuais confirmadas primeiro"
        )

    conn.execute("""
        UPDATE pilot_settings
        SET mode='auto', auto_opt_in=1
        WHERE singleton=1
    """)

    conn.commit()


def disable_auto(conn):
    init(conn)

    conn.execute("""
        UPDATE pilot_settings
        SET mode='pilot', auto_opt_in=0
        WHERE singleton=1
    """)

    conn.commit()
