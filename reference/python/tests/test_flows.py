from assistant_core import flows as F

class Fake:
    """Handlers that record side effects instead of performing them."""
    def __init__(self, rule_fires=True, approval_needed=False):
        self.calls = []; self.rule_fires = rule_fires; self.approval_needed = approval_needed
    def tool(self, name, args, run):
        self.calls.append(("tool", name, args))
        if self.approval_needed and name == "erp.create_payment_reminder": return {"_wait": {"kind": "approval", "approval_id": "apr-1"}}
        if name == "crawler.diff_page": return {"summary": "robots changed to noindex,follow", "changes": [{"field": "robots"}]}
        return {"ok": True, "tool": name}
    def agent(self, p, run): self.calls.append(("agent", p["playbook"])); return {"summary": "triage done", "playbook": p["playbook"]}
    def notify(self, ch, text, run): self.calls.append(("notify", ch, text)); return {"channel": ch, "text": text}
    def task(self, p, run): self.calls.append(("task", p)); return {"task_id": "task-1"}
    def rule(self, rid, run): return self.rule_fires, {"rule": rid}
    def approval(self, p, run): self.calls.append(("approval", p["tool"], p["approver_role"])); return {"approval_id": "apr-9"}
    def delay(self, dur, run): self.calls.append(("delay", dur)); return {"timer_id": "tmr-1"}

def test_key_page_flow_parks_on_approval_then_resolves(flows):
    flow = flows["key-page-regression-response"]; h = Fake()
    ev = {"type": "seo.anomaly.detected", "subject": "/pricing", "data": {"path": "/pricing", "rule": "seo-organic-drop"}}
    assert F.trigger_matches(flow, ev)
    run = F.start(flow, ev, h)
    assert run.status == "waiting" and run.waiting["kind"] == "approval"
    assert [s.node_id for s in run.steps] == ["trigger", "diff", "deploys", "triage", "isnoindex", "notify", "approve"]
    assert run.steps[4].branch == "true"
    assert ("approval", "cms.remove_noindex", "seo_owner") in h.calls
    F.resume(run, flow, {"decision": "approved"}, "approved", h)
    assert run.status == "success" and run.summary == "Fix applied and page re-indexed"

def test_key_page_flow_rejected_goes_to_ticket(flows):
    flow = flows["key-page-regression-response"]; h = Fake()
    run = F.start(flow, {"type": "seo.anomaly.detected", "subject": "/pricing", "data": {"path": "/pricing"}}, h)
    F.resume(run, flow, {"decision": "rejected"}, "rejected", h)
    assert run.status == "success" and any(c[0] == "tool" and c[1] == "ticketing.create_issue" for c in h.calls)

def test_stuck_order_filter_and_rule(flows):
    flow = flows["stuck-order-follow-up"]
    assert not F.trigger_matches(flow, {"type": "erp.order.status_changed", "data": {"status": "paid"}})
    ev = {"type": "erp.order.status_changed", "subject": "SO-1", "data": {"status": "awaiting_payment", "order_id": "SO-1", "customer": "X", "days_in_status": 9}}
    run = F.start(flow, ev, Fake(rule_fires=False))
    assert run.status == "success" and run.steps[1].branch == "not fired" and run.summary.startswith("Timer will re-check")
    run = F.start(flow, ev, Fake(rule_fires=True))
    assert run.status == "waiting" and run.waiting["kind"] == "approval"

def test_invoice_ladder_delays_then_tool_policy_wait(flows):
    flow = flows["invoice-reminder-ladder"]; h = Fake(approval_needed=True)
    run = F.start(flow, {"type": "erp.invoice.posted", "subject": "INV-1", "data": {"invoice_id": "INV-1", "amount": 1250}}, h)
    assert run.status == "waiting" and run.waiting["kind"] == "timer"
    F.resume(run, flow, {"elapsed": True}, None, h)           # timer fired -> wait node (0s) -> timeout branch -> level 1 tool
    assert run.status == "waiting" and run.waiting["kind"] == "approval"
    assert ("tool", "erp.create_payment_reminder", {"invoice_id": "INV-1", "amount": 1250, "level": 1, "dry_run": False}) in h.calls

def test_templating_and_filters():
    ctx = {"data": {"path": "/p", "n": 5}, "nodes": {"diff": {"summary": "noindex here"}}}
    assert F.tpl("page {{data.path}} / {{missing|data.n}}", ctx) == "page /p / 5"
    assert F.eval_filter("nodes.diff.summary contains NOINDEX", ctx) and F.eval_filter("data.n > 3", ctx) and not F.eval_filter("data.n in 1,2", ctx)
