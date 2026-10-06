# Resume wording

**InterceptIQ — Shipment Escape Risk Prediction** | Python, scikit-learn, FastAPI, PostgreSQL, RabbitMQ, Docker, Streamlit

GitHub: https://github.com/NRao0158/interceptiq-shipment-risk . Verified public prediction/replay demo: https://nihal-interceptiq.streamlit.app/ .

- Built an ML pipeline predicting movement before clearance within 60 simulated minutes from hold-time context, with chronological evaluation across 18,000 synthetic shipment snapshots and a 3,000-package shifted-facility stress test.
- Achieved 0.321 average precision versus a 0.153 prevalence baseline on 2,908 held-out synthetic packages; documented inspection-threshold tradeoffs and feature/label leakage safeguards.
- Implemented event-ingestion APIs, PostgreSQL stop detection and RabbitMQ delivery with a transactional outbox; verified 50 mock escape scenarios, duplicate suppression, late-event retractions, broker outage recovery and persistence, alongside 12 automated tests.

RabbitMQ publisher/consumer and PostgreSQL Docker integration have been verified locally. The prediction/replay demo is publicly deployed; the API and infrastructure are not publicly hosted. These results do not establish real carrier accuracy or prevented escapes. Delivery is at least once with consumer idempotency, not exactly once.

## Resume placement

Replace Cent after reviewing this project's results and understanding the implementation. Keep Web Manager experience. Preserve the FBLA first-place award in an Honors line if space permits. The open LaTeX resume is intentionally unchanged until the user requests the replacement.
