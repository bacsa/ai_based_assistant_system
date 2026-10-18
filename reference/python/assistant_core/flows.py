"""Synchronous interpreter for flows/*.json.

Waits (approval, awaited event, delay) are *returned* to the caller as a Waiting result; the
caller (a Temporal workflow in production, a test here) resumes the run when the matching
event arrives. Node handlers for tools, agent steps, notifications and tasks are injected, so
the interpreter stays free of I/O.
"""
from __future__ import annotations
import json, re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

@dataclass
class Step:
    node_id: str; type: str; status: str; input: Any; output: Any; branch: Optional[str] = None; note: str = ""

@dataclass
class Run:
    flow_id: str; event: dict; steps: list[Step] = field(default_factory=list); outputs: dict = field(default_factory=dict)
    status: str = "running"; waiting: Optional[dict] = None; summary: str = ""; prev: Any = None

@dataclass
class Handlers:
    """Injected side effects. Each returns a dict output; tool may return {"_wait": {...}} to park the run."""
    tool: Callable[[str, dict, Run], dict]
    agent: Callable[[dict, Run], dict]
    notify: Callable[[str, str, Run], dict]
    task: Callable[[dict, Run], dict]
    rule: Callable[[str, Run], tuple[bool, dict]]
    approval: Callable[[dict, Run], dict]       # returns {"approval_id": ...}
    delay: Callable[[str, Run], dict]           # returns {"timer_id": ...}

def get_path(obj: Any, path: str) -> Any:
    for k in path.split("."):
        if obj is None: return None
        obj = obj.get(k) if isinstance(obj, dict) else None
    return obj

def tpl(s: str, ctx: dict) -> str:
    def rep(m):
        for alt in m.group(1).split("|"):
            v = get_path(ctx, alt.strip())
            if v not in (None, ""):
                return json.dumps(v) if isinstance(v, (dict, list)) else str(v)
        return ""
    return re.sub(r"\{\{([^}]+)\}\}", rep, s or "")

def eval_filter(expr: str, ctx: dict) -> bool:
    if not expr: return True
    m = re.match(r"^\s*([\w.]+)\s*(==|!=|>=|<=|>|<|contains|exists|in)\s*(.*)$", expr)
    if not m: return True
    v = get_path(ctx, m.group(1)); rhs = m.group(3).strip().strip("\"'")
    op = m.group(2)
    try:
        if op == "==": return str(v) == rhs
        if op == "!=": return str(v) != rhs
        if op == ">": return float(v) > float(rhs)
        if op == "<": return float(v) < float(rhs)
        if op == ">=": return float(v) >= float(rhs)
        if op == "<=": return float(v) <= float(rhs)
        if op == "contains": return rhs.lower() in str(v or "").lower()
        if op == "exists": return v is not None
        if op == "in": return str(v) in [x.strip() for x in rhs.split(",")]
    except (TypeError, ValueError):
        return False
    return True

def ctx_of(run: Run) -> dict:
    return {"data": run.event.get("data", {}), "event": run.event, "prev": run.prev, "nodes": run.outputs, "run": {"flow": run.flow_id}}

def out_edges(flow: dict, node_id: str, branch: Optional[str]):
    es = [e for e in flow["edges"] if e["from"] == node_id]
    if branch is None: return es
    hit = [e for e in es if e.get("label") == branch]
    return hit or [e for e in es if not e.get("label")]

def trigger_matches(flow: dict, event: dict) -> bool:
    t = flow["trigger"]
    return t["eventType"] == event["type"] and eval_filter(t.get("filter", ""), {"data": event.get("data", {}), "event": event})

def start(flow: dict, event: dict, h: Handlers) -> Run:
    run = Run(flow_id=flow["id"], event=event)
    _exec_from(run, flow, "trigger", {"data": event.get("data", {})}, h)
    return run

def resume(run: Run, flow: dict, output: Any, branch: Optional[str], h: Handlers) -> Run:
    w = run.waiting
    if not w: return run
    for s in run.steps:
        if s.node_id == w["node_id"] and s.status == "waiting":
            s.status, s.output, s.branch, s.note = "ok", output, branch, f"resumed: {branch}"
    run.outputs[w["node_id"]] = output; run.prev = output; run.waiting = None; run.status = "running"
    nxt = out_edges(flow, w["node_id"], branch)
    if not nxt:
        run.status, run.summary = "success", f"ended after {w['node_id']}"
    for e in nxt:
        _exec_from(run, flow, e["to"], output, h)
    return run

def _exec_from(run: Run, flow: dict, node_id: str, inp: Any, h: Handlers):
    queue = [(node_id, inp)]; guard = 0
    nodes = {n["id"]: n for n in flow["nodes"]}
    while queue and guard < 100:
        guard += 1
        nid, inp = queue.pop(0); node = nodes.get(nid)
        if not node: continue
        res = _exec_node(run, flow, node, inp, h)
        step = Step(nid, node["type"], res.get("status", "ok"), inp, res.get("output"), res.get("branch"), res.get("note", ""))
        run.steps.append(step); run.outputs[nid] = res.get("output"); run.prev = res.get("output")
        if res.get("status") == "failed":
            run.status, run.summary = "failed", f"failed at {nid}: {res.get('note')}"; return
        if res.get("wait"):
            run.status = "waiting"; run.waiting = {"node_id": nid, **res["wait"]}; step.status = "waiting"; return
        if node["type"] == "end":
            run.status = node["params"].get("status", "success"); run.summary = tpl(node["params"].get("summary", ""), ctx_of(run)); return
        nxt = out_edges(flow, nid, res.get("branch"))
        if not nxt:
            run.status, run.summary = "success", f"ended after {nid}"; return
        for e in nxt: queue.append((e["to"], res.get("output")))

def _exec_node(run: Run, flow: dict, node: dict, inp: Any, h: Handlers) -> dict:
    p = node.get("params", {}); ctx = ctx_of(run); t = node["type"]
    if t == "trigger": return {"output": {"data": run.event.get("data", {})}, "note": f"matched {run.event['type']}"}
    if t == "filter":
        ok = eval_filter(f"{p.get('field')} {p.get('op')} {p.get('value', '')}", ctx)
        return {"output": {"matched": ok}, "branch": "true" if ok else "false"}
    if t == "rule":
        fired, evidence = h.rule(p["ruleId"], run)
        return {"output": {"rule": p["ruleId"], "fired": fired, "evidence": evidence}, "branch": "fired" if fired else "not fired"}
    if t in ("tool", "approval"):
        try: args = json.loads(tpl(p.get("args", "{}"), ctx))
        except json.JSONDecodeError as e: return {"output": {"error": str(e)}, "status": "failed", "note": "arguments not valid JSON after templating"}
        if t == "approval":
            out = h.approval({"tool": p["tool"], "args": args, "approver_role": p.get("approverRole")}, run)
            return {"output": out, "wait": {"kind": "approval", "approval_id": out.get("approval_id")}, "note": "parked until approval.decided"}
        out = h.tool(p["tool"], args, run)
        if isinstance(out, dict) and out.get("_wait"): return {"output": out, "wait": out["_wait"], "note": "policy requires approval"}
        if isinstance(out, dict) and out.get("_forbidden"): return {"output": out, "status": "failed", "note": "forbidden by policy"}
        return {"output": out}
    if t == "agent": return {"output": h.agent({"playbook": p.get("playbook"), "instruction": tpl(p.get("instruction", ""), ctx)}, run)}
    if t == "notify": return {"output": h.notify(p.get("channel", ""), tpl(p.get("text", ""), ctx), run)}
    if t == "task": return {"output": h.task({"severity": p.get("severity"), "owner_role": p.get("ownerRole"), "title": tpl(p.get("title", ""), ctx)}, run)}
    if t == "wait":
        key_val = get_path(ctx, "data." + p.get("keyField", "")) or run.event.get("subject")
        if p.get("timeout") == "0s": return {"output": {"checked": p.get("eventType")}, "branch": "timeout", "note": "immediate check is the caller's job; defaulting to timeout branch"}
        return {"output": {"waiting_for": p.get("eventType"), "key": key_val}, "wait": {"kind": "event", "event_type": p.get("eventType"), "key_field": p.get("keyField"), "key": key_val, "timeout": p.get("timeout")}}
    if t == "delay":
        out = h.delay(p.get("duration", "1d"), run)
        return {"output": out, "wait": {"kind": "timer", "timer_id": out.get("timer_id")}}
    if t == "end": return {"output": {"status": p.get("status", "success")}}
    return {"output": {}, "note": "unknown node type"}
