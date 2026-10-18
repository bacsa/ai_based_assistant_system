from datetime import date, timedelta
import random
from assistant_core import rules as R

def series(base=180, days=42, drop_last=0, drop=0.5, seed=1):
    rnd = random.Random(seed); today = date(2026, 10, 16); rows = []
    for d in range(days, 0, -1):
        day = today - timedelta(days=d); wk = 0.55 if day.weekday() >= 5 else 1.0
        v = round(base * wk * (0.86 + rnd.random() * 0.28))
        rows.append({"date": day.isoformat(), "clicks": v})
    for r in rows[len(rows) - drop_last:] if drop_last else []:
        r["clicks"] = round(r["clicks"] * (1 - drop))
    return rows

def test_threshold_does_not_fire_on_normal_data(rules):
    ev = R.evaluate_threshold(rules["seo-organic-drop"], series(), "clicks")
    assert ev["firings"] == [] and not ev["last_fired"]

def test_threshold_fires_after_consecutive_breaches(rules):
    ev = R.evaluate_threshold(rules["seo-organic-drop"], series(drop_last=3, drop=0.45), "clicks")
    assert ev["last_fired"] and len(ev["firings"]) == 1
    first = ev["firings"][0]; assert first["ratio"] < 0.7

def test_threshold_single_breach_is_not_enough(rules):
    ev = R.evaluate_threshold(rules["seo-organic-drop"], series(drop_last=1, drop=0.6), "clicks")
    assert not ev["last_fired"] and ev["points"][-1].breach

def test_time_rule_phases(rules):
    vat = rules["vat-return"]
    assert R.time_status(vat, date(2026, 10, 5))["phase"] == "upcoming"
    s = R.time_status(vat, date(2026, 10, 12)); assert s["phase"] == "reminding" and s["days_left"] == 8
    s = R.time_status(vat, date(2026, 10, 25)); assert s["due"] == "2026-11-20" and s["phase"] == "upcoming"

def test_reminder_dates_are_due_minus_lead(rules):
    ds = R.reminder_dates(rules["vat-return"], date(2026, 10, 1))
    assert [d.isoformat() for d in ds] == ["2026-10-10", "2026-10-17", "2026-10-19", "2026-10-20"]

def test_state_rule(rules):
    recs = [{"id": "SO-1", "status": "awaiting_payment", "days": 12}, {"id": "SO-2", "status": "awaiting_payment", "days": 3}, {"id": "SO-3", "status": "paid", "days": 30}]
    out = R.evaluate_state(rules["order-stuck-awaiting-payment"], [{**r, "days_in_status": r["days"]} for r in recs])
    assert [r["id"] for r in out] == ["SO-1"]

def test_pattern_rule(rules):
    r = rules["seo-key-page-meta-regression"]
    ev = {"type": "crawl.page.changed", "data": {"path": "/pricing", "changes": [{"field": "robots", "before": "index,follow", "after": "noindex,follow"}]}}
    assert R.evaluate_pattern(r, ev, key_pages=["/pricing"])
    assert not R.evaluate_pattern(r, ev, key_pages=["/"])
    assert not R.evaluate_pattern(r, {**ev, "data": {"path": "/pricing", "changes": [{"field": "content"}]}}, key_pages=["/pricing"])
