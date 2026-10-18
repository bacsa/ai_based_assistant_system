from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class Decision:
    allow: str                 # auto | approve | forbid
    rule: str
    why: str
    approver_role: Optional[str] = None

def _truthy(v: Any) -> bool:
    return v is True or str(v).lower() == "true"

def decide(tool: str, args: dict, tool_catalogue: dict[str, dict], key_pages: set[str] = frozenset()) -> Decision:
    """Policy decision for a tool call. Mirrors policyDecision in the console; in production the
    decision table comes from rules/policy-*.yaml and is evaluated by the guardrail service."""
    if tool == "erp.create_payment_reminder":
        amt = float(args.get("amount") or 0); lvl = int(args.get("level") or 1); flagged = _truthy(args.get("customer_flagged"))
        if lvl > 3: return Decision("forbid", "policy-payment-reminders", "reminder level above 3 is never sent by the assistant")
        if lvl == 3 or flagged: return Decision("approve", "policy-payment-reminders", "level 3 is a collection notice" if lvl == 3 else "customer is flagged", "finance_lead")
        if amt < 500 and lvl <= 2: return Decision("auto", "policy-payment-reminders", "amount below 500 and level <= 2")
        return Decision("approve", "policy-payment-reminders", "amount 500 or above", "finance_lead")
    if tool.startswith("cms."):
        if _truthy(args.get("dry_run")): return Decision("auto", "policy-cms-writes", "dry run changes nothing")
        if args.get("path") in key_pages: return Decision("approve", "policy-cms-writes", f"{args.get('path')} is a key page", "seo_owner")
        return Decision("auto", "policy-cms-writes", "not a key page")
    if tool == "slack.post_message":
        if args.get("channel") == "#general": return Decision("approve", "policy-communication", "company-wide channel", "marketing_lead")
        return Decision("auto", "policy-communication", "team channel")
    spec = tool_catalogue.get(tool, {})
    if spec.get("class") == "write" and spec.get("risk") == "high":
        return Decision("approve", "default", "high-risk write without a specific policy", "finance_lead")
    return Decision("auto", "default", "read-only tool" if spec.get("class") == "read" else "low-risk action")
