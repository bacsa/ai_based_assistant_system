from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from statistics import median
from typing import Any, Iterable, Optional

@dataclass
class Point:
    date: str; value: float; baseline: Optional[float]; ratio: Optional[float]; breach: bool; fired: bool; first: bool

def evaluate_threshold(rule: dict, rows: list[dict], field: str) -> dict:
    """Same-weekday-median baseline over `baseline.window_days`; fires after `condition.consecutive` breaches.
    rows: ascending daily rows with 'date' and the field. Mirrors evalThreshold in the console."""
    n = max(2, int(rule["baseline"].get("window_days", 28)) // 7)
    thr = float(rule["condition"]["ratio_lt"]); need = int(rule["condition"].get("consecutive", 1)); min_b = float(rule["condition"].get("min_baseline", 0))
    pts: list[Point] = []; firings = []; run = 0
    for i, r in enumerate(rows):
        hist = [rows[i - 7 * k][field] for k in range(1, n + 1) if i - 7 * k >= 0]
        baseline = ratio = None; breach = False
        if len(hist) >= 2:
            baseline = median(hist); ratio = (r[field] / baseline) if baseline > 0 else None
            breach = ratio is not None and ratio < thr and baseline >= min_b
        run = run + 1 if breach else 0
        fired = run >= need
        pts.append(Point(r["date"], r[field], baseline, ratio, breach, fired, fired and run == need))
        if fired and run == need:
            firings.append({"date": r["date"], "ratio": ratio, "value": r[field], "baseline": baseline})
    return {"points": pts, "firings": firings, "last_fired": bool(pts and pts[-1].fired)}

def time_status(rule: dict, today: date) -> dict:
    """Next due date, days left, phase (upcoming | reminding | overdue) and next reminder for a time rule."""
    due = rule["due"]
    if "date" in due:
        d = date.fromisoformat(due["date"])
    else:
        dom = min(int(due["day_of_month"]), 28)
        d = today.replace(day=dom)
        if d < today:
            d = (d.replace(day=1) + timedelta(days=32)).replace(day=dom)
    days_left = (d - today).days
    leads = sorted((int(x) for x in rule.get("lead_times_days", [])), reverse=True)
    phase = "overdue" if days_left < 0 else ("reminding" if any(days_left <= l for l in leads) else "upcoming")
    nxt = [l for l in leads if l < days_left]
    return {"due": d.isoformat(), "days_left": days_left, "phase": phase, "leads": leads, "next_reminder_in": (days_left - nxt[0]) if nxt else None}

def reminder_dates(rule: dict, today: date) -> list[date]:
    """The durable timers the timer service arms for a time rule: due - lead for every lead time."""
    ts = time_status(rule, today); due = date.fromisoformat(ts["due"])
    return [due - timedelta(days=l) for l in ts["leads"]] + [due]

def evaluate_state(rule: dict, records: Iterable[dict]) -> list[dict]:
    """Generic state rule: records matching `where` whose numeric field exceeds `condition.<field>_gt`."""
    where = rule.get("where", {}); cond = rule.get("condition", {})
    out = []
    for rec in records:
        if any(rec.get(k) != v for k, v in where.items()):
            continue
        ok = True
        for k, v in cond.items():
            if k.endswith("_gt"):
                f = k[:-3]
                if float(rec.get(f, 0)) <= float(v): ok = False
            elif k.endswith("_lt"):
                f = k[:-3]
                if float(rec.get(f, 0)) >= float(v): ok = False
        if ok: out.append(rec)
    return out

def evaluate_pattern(rule: dict, event: dict, key_pages: Iterable[str] = ()) -> bool:
    """Pattern rule on a single event (the 'after X within Y' part is kept as state by the stream processor)."""
    p = rule["pattern"]
    if event.get("type") != p["on"]:
        return False
    where = p.get("where", {}); data = event.get("data", {})
    if "path_in" in where and data.get("path") not in set(key_pages):
        return False
    fields = set(where.get("changed_fields_any", []))
    if fields and not any(c.get("field") in fields for c in data.get("changes", [])):
        return False
    return True
