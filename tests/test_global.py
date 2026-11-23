
import pytest

from jobagent.models import Opportunity
from jobagent.matching import evaluate
from jobagent.storage import connect, upsert, save_analysis, set_status
from jobagent.pilot import confirmed_count


def op(track="global_entry", title="Junior Data Analyst",
       loc="Worldwide", remote=True):
    return Opportunity(
        title, "Example", "https://example.org/jobs/1",
        "Python SQL analytics", loc, track, remote=remote
    )


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

    with pytest.raises(ValueError):
        set_status(conn, item.id, "aprovada")

    save_analysis(conn, item.id, {
        "score": 70,
        "analysis": "match",
        "draft": "hello",
        "language": "en",
    })

    set_status(conn, item.id, "aprovada")
    set_status(conn, item.id, "enviada_manualmente")

    assert conn.execute(
        "SELECT status FROM opportunities"
    ).fetchone()[0] == "enviada_manualmente"

    assert confirmed_count(conn) == 1

    with pytest.raises(ValueError):
        set_status(conn, item.id, "enviada_manualmente")

    assert confirmed_count(conn) == 1
