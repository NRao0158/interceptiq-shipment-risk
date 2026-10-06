# Requirements and acceptance

- Predict movement before clearance within 60 simulated minutes when a screening/brokerage stop is applied.
- Accept validated events from all three sources through APIs.
- Store immutable package events and recompute active stops in event time.
- Detect HOLD/REJECT followed by movement or delivery; release is source-specific.
- Deduplicate repeated event submissions and repeated movement alerts.
- Preserve acknowledgement and alert revision history, including late-event retractions.
- Store publication work atomically, retry failures and deduplicate consumed message IDs.
- Reproduce exact demo counts: 1,000 packages, 500 screening events, 300 brokerage events, 50 escape scenarios.
- Supply risk/event replay demo, baseline evaluation, architecture, code, tests, setup, model card and limitations.

Approved scope is entirely synthetic. No actual shipment ingestion, production messaging or confidential data. No live scanning network. Public hosting is the lightweight demo; full infrastructure stays local. Resume changes wait until results are reviewed. This repository includes resume wording as a separate artifact.
