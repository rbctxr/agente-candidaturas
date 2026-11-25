
import sqlite3

import pytest

from jobagent.models import Opportunity
from jobagent.matching import evaluate
from jobagent.storage import (
    connect,
    upsert,
    save_analysis,
    set_status,
    confirm_eligibility,
)
from jobagent.pilot import confirmed_count


def op(track="global_entry", title="Junior Data Analyst",
       loc="Worldwide", remote=True):
    return Opportunity(
        title, "Example", "https://example.org/jobs/1",
        "Python SQL analytics", loc, track, remote=remote
    )


def prepare_analysis(conn, item):
    save_analysis(conn, item.id, {
        "score": 70,
        "analysis": "match",
        "draft": "hello",
        "language": "en",
    })


def test_global_entry():
    assert evaluate(op())[0] == "review"


def test_restrict_us():
    assert evaluate(op(loc="US only"))[0] == "rejected"


def test_remote_required():
    assert evaluate(op(remote=False))[0] == "rejected"


def test_internship_title():
    assert evaluate(
        op("br_internship", "Senior Data Analyst", "Brazil")
    )[0] == "rejected"

    assert evaluate(
        op("br_internship", "Data Intern", "Brazil")
    )[0] == "candidate"


def test_freelance_review():
    assert evaluate(
        op("global_freelance", "Data Dashboard Project", "Unknown")
    )[0] == "review"


def test_approval_gate(tmp_path):
    conn = connect(tmp_path / "db.sqlite")
    item = op()
    upsert(conn, item, *evaluate(item))

    with pytest.raises(ValueError, match="Transição não permitida"):
        set_status(conn, item.id, "aprovada")

    prepare_analysis(conn, item)

    with pytest.raises(ValueError, match="Confirme a elegibilidade"):
        set_status(conn, item.id, "aprovada")

    confirm_eligibility(conn, item.id)

    set_status(conn, item.id, "aprovada")
    set_status(conn, item.id, "enviada_manualmente")

    assert conn.execute(
        "SELECT status FROM opportunities"
    ).fetchone()[0] == "enviada_manualmente"

    assert confirmed_count(conn) == 1

    with pytest.raises(ValueError):
        set_status(conn, item.id, "enviada_manualmente")

    assert confirmed_count(conn) == 1

    conn.close()


def test_eligibility_default(tmp_path):
    conn = connect(tmp_path / "db.sqlite")
    item = op()
    upsert(conn, item, *evaluate(item))

    row = conn.execute(
        "SELECT eligibility_confirmed FROM opportunities"
    ).fetchone()

    assert row["eligibility_confirmed"] == 0

    conn.close()


def test_eligibility_persistence(tmp_path):
    path = tmp_path / "db.sqlite"

    conn = connect(path)
    item = op()
    upsert(conn, item, *evaluate(item))

    confirm_eligibility(conn, item.id)
    conn.close()

    conn = connect(path)

    row = conn.execute(
        "SELECT eligibility_confirmed FROM opportunities"
    ).fetchone()

    assert row["eligibility_confirmed"] == 1

    conn.close()


def test_rejected_eligibility_cannot_be_confirmed(tmp_path):
    conn = connect(tmp_path / "db.sqlite")
    item = op(loc="US only")
    upsert(conn, item, *evaluate(item))

    with pytest.raises(ValueError, match="não pode ser confirmada"):
        confirm_eligibility(conn, item.id)

    conn.close()


def test_candidate_requires_confirmation(tmp_path):
    conn = connect(tmp_path / "db.sqlite")

    item = op(
        "br_internship",
        "Data Intern",
        "Brazil",
    )

    assert evaluate(item)[0] == "candidate"

    upsert(conn, item, *evaluate(item))
    prepare_analysis(conn, item)

    with pytest.raises(ValueError, match="Confirme a elegibilidade"):
        set_status(conn, item.id, "aprovada")

    confirm_eligibility(conn, item.id)
    set_status(conn, item.id, "aprovada")

    conn.close()


def test_rejection_resets_confirmation(tmp_path):
    conn = connect(tmp_path / "db.sqlite")
    item = op()

    upsert(conn, item, *evaluate(item))
    prepare_analysis(conn, item)
    confirm_eligibility(conn, item.id)

    set_status(conn, item.id, "rejeitada")

    row = conn.execute(
        "SELECT eligibility_confirmed FROM opportunities"
    ).fetchone()

    assert row["eligibility_confirmed"] == 0

    set_status(conn, item.id, "para_revisao")

    with pytest.raises(ValueError, match="Confirme a elegibilidade"):
        set_status(conn, item.id, "aprovada")

    conn.close()


def test_manual_submission_requires_confirmation(tmp_path):
    conn = connect(tmp_path / "db.sqlite")
    item = op()

    upsert(conn, item, *evaluate(item))
    prepare_analysis(conn, item)

    # simula uma candidatura aprovada antes da migração
    conn.execute(
        "UPDATE opportunities SET status='aprovada' WHERE id=?",
        (item.id,),
    )
    conn.commit()

    with pytest.raises(ValueError, match="Confirme a elegibilidade"):
        set_status(conn, item.id, "enviada_manualmente")

    assert confirmed_count(conn) == 0

    confirm_eligibility(conn, item.id)
    set_status(conn, item.id, "enviada_manualmente")

    assert confirmed_count(conn) == 1

    conn.close()


def test_eligibility_migration(tmp_path):
    path = tmp_path / "legacy.db"

    # simula um banco criado pela versão anterior
    legacy = sqlite3.connect(path)

    legacy.execute("""
        CREATE TABLE opportunities (
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

    legacy.execute("""
        INSERT INTO opportunities (
            id, title, eligibility, status
        )
        VALUES (
            'legacy-1', 'Data Analyst', 'review', 'aprovada'
        )
    """)

    legacy.commit()
    legacy.close()

    conn = connect(path)

    row = conn.execute("""
        SELECT id, title, eligibility, status,
               eligibility_confirmed
        FROM opportunities
    """).fetchone()

    assert row["id"] == "legacy-1"
    assert row["title"] == "Data Analyst"
    assert row["eligibility"] == "review"
    assert row["status"] == "aprovada"
    assert row["eligibility_confirmed"] == 0

    conn.close()

    # verifica se a migração pode ser executada novamente
    conn = connect(path)

    columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(opportunities)"
        )
    ]

    assert columns.count("eligibility_confirmed") == 1

    conn.close()
