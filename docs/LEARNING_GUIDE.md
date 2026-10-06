# Understand InterceptIQ

1. Read simulation.py and features.py. Separate information available at hold time from future information used only as labels. Explain why a chosen synthetic generator cannot establish real-world prediction quality.
2. Read train.py. Explain chronological split, average precision, baseline, threshold and false-positive burden. More complex models must earn their complexity on validation.
3. Read rules.py. Explain independent hold sources and why release from brokerage cannot clear screening. A risk score never substitutes for a confirmed rule violation.
4. Read store.py. Explain event idempotency, event-time recomputation, alert revisions and transactional outbox. Explain why a late release might retract an earlier alert.
5. Read worker.py. Explain publisher confirms, consumer acknowledgements and the crash window that makes delivery at least once rather than exactly once.
6. Run tests and the complete ingestion fixture. Send events twice and demonstrate stable alert/message counts.
7. Run Docker stack after installation, verify queue confirms and persisted inbox rows. Until then, describe broker integration as implemented but unverified.

## Two-minute demonstration

Score a held package in Risk studio. Show the inspection priority while explaining that normal hold enforcement still applies. Replay CREATED, HOLD, SCAN to show a confirmed violation. Open Model evidence, compare the prevalence and departure heuristics, then discuss false positives and the shifted-facility test. Open local API docs and ingest duplicate or late events to demonstrate backend reliability.

## Interview talking points

Prediction estimates a future event; rules identify a historical violation. The simulator has hidden noise, and labels come from future event timelines rather than an exported risk field. All model features precede the hold. A single package contributes one snapshot and appears in only one chronological split. An outbox avoids losing alerts between database and broker. Exactly-once delivery is not claimed; consumer idempotency is required.

AI-assisted initial implementation should be understood, reproduced and improved before presenting personal ownership. The project is independent work, not an internship or carrier deployment. No real escape prevention or cost savings were measured.
