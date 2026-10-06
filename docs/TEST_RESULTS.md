# Verification and limitations

Executed on Windows/Python 3.12: **12 automated tests passed**. Coverage: normal/released stops, source-specific clearance, REJECT/delivery, event order, overlapping holds, exact scripted fixture counts, seeded labels, future-event feature invariance, API schema/conflict rejection, late-event retraction, acknowledgement/delivery retry/inbox deduplication, durable SQLite restart, model inference and Streamlit interaction.

SQLite HTTP verification: ingested all 2,050 scripted events, yielding 50 alerts and 50 pending outbox messages. Replayed every event again: zero changes, still 50 alerts and 50 outbox messages. This SQLite instance remains disconnected from the broker. Local Streamlit risk studio also rendered model scores successfully in the browser.

Public verification: https://nihal-interceptiq.streamlit.app/ loaded the trained model, displayed risk scores and rendered a confirmed stop violation in the event replay tab on October 6, 2026. Package-history prediction endpoint also returned a finite score with HTTP 200 using only pre-stop scan features.

ML: 12,048 fit packages; 3,044 validation; 2,908 future-day test; 3,000 shifted-facility stress test. Selected logistic regression. Test average precision=0.320509, ROC-AUC=0.715884, precision=0.238229 and recall=0.761798 at threshold=0.12. Confusion counts: 339 true positives, 1,084 false positives, 106 false negatives, 1,379 true negatives. Prevalence average precision=0.153026, departure heuristic=0.177668. Stress-set AP=0.415172, ROC-AUC=0.700917; higher AP partly reflects higher prevalence (0.241333), not better generalization. No real shipment metrics.

Live Docker integration: PostgreSQL 16 and RabbitMQ 4. The full fixture persisted 2,050 events, 50 alerts, 50 published outbox rows and 50 consumer inbox records. Repeated ingestion made no changes. Republishing an already consumed message did not increase inbox count. Malformed payload reached the dead-letter queue. Acknowledgement was delivered; a late release retracted the prior alert and delivered a correction. With the broker stopped, a new violation persisted and stayed pending; after restart it was delivered automatically. Consumer reconnect behavior was added and exercised. Recreating all containers without deleting volumes preserved the records.

Final integration database counts (including extra failure-mode fixtures): 2,055 events, 52 historical alerts (including a retraction), 54 published outbox rows, zero pending, 54 inbox records. These extra records are not additional escape predictions. Evidence summary: artifacts/integration_results.json. scripts/verify_stack.py can verify a fresh isolated stack; do not rerun its full mode against this already populated database.

Unit transport tests inject a publisher callback; live integration tests use actual RabbitMQ and PostgreSQL. SQLite remains single-process. API tests produce one dependency deprecation warning from FastAPI/Starlette's HTTP test client; no test failures.

Simulator feature-history consistency was corrected during implementation and evaluation regenerated from final source. No test-set-based model hyperparameter tuning was performed. CI workflow is supplied; remote CI status must be verified separately before claiming it passed.
