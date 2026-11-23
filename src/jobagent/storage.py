
import sqlite3
from pathlib import Path

STATUSES = {
    "nova",
    "para_revisao",
    "aprovada",
    "rejeitada",
    "enviada_manualmente",
}


def connect(path="data/global_jobs.db"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    conn.execute("""
        CREATE TABLE IF NOT EXISTS opportunities (
            id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            url TEXT,
            description TEXT,
            location TEXT,
            track TEXT,
            source TEXT,
            remote INTEGER,
            country_restrictions TEXT,
            budget TEXT,
            eligibility TEXT,
            eligibility_reason TEXT,
            score INTEGER,
            analysis TEXT,
            draft TEXT,
            language TEXT,
            status TEXT NOT NULL DEFAULT 'nova',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    return conn


def upsert(conn, op, eligibility, reason):
    conn.execute("""
        INSERT INTO opportunities (
            id, title, company, url, description, location,
            track, source, remote, country_restrictions,
            budget, eligibility, eligibility_reason
        )
        VALUES (
            :id, :title, :company, :url, :description, :location,
            :track, :source, :remote, :country_restrictions,
            :budget, :eligibility, :eligibility_reason
        )
        ON CONFLICT(id) DO NOTHING
    """, {
        **op.asdict(),
        "eligibility": eligibility,
        "eligibility_reason": reason,
    })

    conn.commit()


def all_jobs(conn, track=None):
    if track:
        return conn.execute(
            "SELECT * FROM opportunities WHERE track=? "
            "ORDER BY created_at DESC",
            (track,),
        ).fetchall()

    return conn.execute(
        "SELECT * FROM opportunities ORDER BY created_at DESC"
    ).fetchall()


def save_analysis(conn, id, result):
    conn.execute("""
        UPDATE opportunities
        SET score=?, analysis=?, draft=?, language=?,
            status='para_revisao'
        WHERE id=?
          AND status IN ('nova', 'para_revisao')
    """, (
        result["score"],
        result["analysis"],
        result["draft"],
        result["language"],
        id,
    ))

    conn.commit()


def save_draft(conn, id, draft):
    conn.execute("""
        UPDATE opportunities
        SET draft=?
        WHERE id=? AND status='para_revisao'
    """, (draft, id))

    conn.commit()


def set_status(conn, id, status):
    if status not in STATUSES:
        raise ValueError("Status inválido")

    allowed = {
        "nova": {"rejeitada"},
        "para_revisao": {"aprovada", "rejeitada"},
        "aprovada": {"enviada_manualmente", "rejeitada"},
        "rejeitada": {"para_revisao"},
        "enviada_manualmente": set(),
    }

    try:
        if conn.in_transaction:
            conn.commit()

        conn.execute("BEGIN IMMEDIATE")

        old = conn.execute(
            "SELECT status FROM opportunities WHERE id=?",
            (id,),
        ).fetchone()

        if old is None:
            raise ValueError("Vaga inexistente")

        if status not in allowed[old["status"]]:
            raise ValueError("Transição não permitida")

        if status == "enviada_manualmente":
            from .pilot import init

            init(conn)

            existing = conn.execute("""
                SELECT 1
                FROM application_events
                WHERE opportunity_id=?
                  AND event IN (
                      'submitted_manual',
                      'submitted_automatic'
                  )
            """, (id,)).fetchone()

            if existing:
                raise ValueError("Candidatura já registrada como enviada")

            conn.execute("""
                INSERT INTO application_events (
                    opportunity_id, event, note
                )
                VALUES (?, 'submitted_manual', ?)
            """, (
                id,
                "Envio manual confirmado pela pessoa usuária",
            ))

        conn.execute(
            "UPDATE opportunities SET status=? WHERE id=?",
            (status, id),
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise
