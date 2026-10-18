# timer-service
**Job:** durable timers. `arm(id, fire_at, type, key, reason)` and `cancel(predicate)` are driven by events (invoice posted → reminder timers; invoice paid → cancel; deadline registered → lead-time timers; TLS observed → re-arm; order awaiting payment → +7 d; flow delay node → `flow.delay.elapsed`). Fires by publishing the timer's event.
**Storage:** Postgres `timers(id, fire_at, type, key, reason, created_by_event, fired_at)`; leader-elected scheduler loop (or Temporal timers). Also emits `day.closed` at 00:05 local business time.
**Reference:** `assistant_core.rules.reminder_dates`.
