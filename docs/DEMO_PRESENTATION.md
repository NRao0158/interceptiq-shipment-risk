# Final demonstration outline

1. Problem: packages under screening/brokerage stops can continue moving; inspect risk early and detect violations reliably.
2. Scope: independent prototype, fully synthetic shipments, no carrier claims.
3. Architecture: prediction branch alongside deterministic event processor; transactional outbox to RabbitMQ.
4. ML: causal hold-time context; chronological package split; baselines and selected model; threshold tradeoff.
5. Demo: score a held package, then CREATED → HOLD → SCAN → confirmed alert.
6. Reliability: repeat event, delayed hold, late release, retracted alert; persistent history.
7. Evaluation: model ranking and false positives; exact 50 scripted escapes; executed tests; Docker-specific verification pending.
8. Handoff: README commands, API docs, reproducibility, future calibration and domain-data collection.
