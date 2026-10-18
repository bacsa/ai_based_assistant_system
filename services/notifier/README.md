# notifier
**Job:** turn `task.created`, `approval.requested`, `*.detected`, `producer.silent` into messages; one message per task updated in place; routing from `inventory/people.yaml` (role → person → channel, quiet hours, backup); buttons (acknowledge, approve, reject) post back as events through the gateway.
