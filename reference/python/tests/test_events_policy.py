from assistant_core import events as E, policy as P

def test_envelope_defaults_and_chain():
    ev = E.Event(type="cms.page.published", source="/cms", subject="/pricing", data={"path": "/pricing"})
    assert ev.partitionkey == "/pricing" and ev.correlationid == ev.id and ev.idempotencykey.startswith("cms.page.published:/pricing:")
    child = ev.caused("crawl.page.changed", {"path": "/pricing", "changes": []})
    assert child.correlationid == ev.id and child.causationid == ev.id and child.id != ev.id

def test_ulid_is_time_ordered():
    a = E.ulid(1_000_000); b = E.ulid(2_000_000)
    assert a[:10] < b[:10] and len(a) == 26

def test_subject_matching():
    assert E.matches(">", "anything.at.all") and E.matches("erp.>", "erp.invoice.posted")
    assert not E.matches("erp.>", "cms.page.published") and E.matches("task.created", "task.created")

def test_idempotency_store():
    s = E.IdempotencyStore(ttl_seconds=10)
    assert not s.seen_before("k", now=0) and s.seen_before("k", now=5) and not s.seen_before("k", now=20)

def test_policy_payment_reminders(tools):
    assert P.decide("erp.create_payment_reminder", {"amount": 120, "level": 1}, tools).allow == "auto"
    d = P.decide("erp.create_payment_reminder", {"amount": 2450, "level": 3}, tools)
    assert d.allow == "approve" and d.approver_role == "finance_lead"
    assert P.decide("erp.create_payment_reminder", {"amount": 10, "level": 4}, tools).allow == "forbid"

def test_policy_cms_and_default(tools):
    assert P.decide("cms.remove_noindex", {"path": "/pricing", "dry_run": True}, tools).allow == "auto"
    assert P.decide("cms.remove_noindex", {"path": "/pricing", "dry_run": False}, tools, key_pages={"/pricing"}).allow == "approve"
    assert P.decide("kb.search", {"query": "x"}, tools).allow == "auto"
