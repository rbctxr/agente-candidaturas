import sqlite3
from jobagent.pilot import init, event, confirmed_count, can_auto_submit, enable_auto, disable_auto
from jobagent.policy import eligibility
from jobagent.models import Opportunity

def test_pilot_blocks_automatic():
    db=sqlite3.connect(':memory:');init(db)
    allowed,why=can_auto_submit(db,'job1',True,True,True,True,True)
    assert not allowed and why

def test_ten_distinct_and_opt_in():
    db=sqlite3.connect(':memory:');init(db)
    for i in range(10): event(db,str(i),'submitted_manual')
    event(db,'0','submitted_manual')
    assert confirmed_count(db)==10
    try: enable_auto(db,'wrong')
    except ValueError: pass
    else: assert False
    enable_auto(db,'EU AUTORIZO ENVIO AUTOMATICO')
    allowed, reasons=can_auto_submit(db,'new',True,True,True,True,True)
    assert not allowed and any('Limite' in x for x in reasons)
    db.execute("UPDATE application_events SET created_at=datetime('now','-8 days')")
    allowed,_=can_auto_submit(db,'new',True,True,True,True,True)
    assert allowed
    disable_auto(db)
    assert not can_auto_submit(db,'new',True,True,True,True,True)[0]

def test_remote_unknown_needs_review():
    op=Opportunity(title='Junior Data Analyst',company='X',url='https://example.org/j',
        description='SQL analytics',location='Remote',remote=True)
    assert eligibility(op)[0]=='needs_eligibility'

def test_geography_block():
    op=Opportunity(title='Junior Data Analyst',company='X',url='https://example.org/j2',
        description='Remote job US only SQL analytics',location='Remote',remote=True)
    assert eligibility(op)[0]=='blocked'
