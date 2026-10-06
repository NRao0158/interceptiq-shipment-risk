# Verification and limitations

Executed on Windows/Python 3.12: **12 automated tests passed**. Coverage: normal/released stops, source-specific clearance, REJECT/delivery, event order, overlapping holds, exact scripted fixture counts, seeded labels, future-event feature invariance, API schema/conflict rejection, late-event retraction, acknowledgement/delivery retry/inbox deduplication, durable SQLite restart, model inference and Streamlit interaction.

Live HTTP verification: ingested all 2,050 scripted events into the running SQLite API, yielding 50 alerts and 50 pending outbox messages. Replayed every event again: zero changes, still 50 alerts and 50 outbox messages. None are marked published because a live broker has not been started. Local Streamlit risk studio also rendered model scores successfully in the browser.

Public verification: https://nihal-interceptiq.streamlit.app/ loaded the trained model, displayed risk scores and rendered a confirmed stop violation in the event replay tab on October 6, 2026. Package-history prediction endpoint also returned a finite score with HTTP 200 using only pre-stop scan features.

ML: 12,048 fit packages; 3,044 validation; 2,908 future-day test; 3,000 shifted-facility stress test. Selected logistic regression. Test average precision=0.320509, ROC-AUC=0.715884, precision=0.238229 and recall=0.761798 at threshold=0.12. Confusion counts: 339 true positives, 1,084 false positives, 106 false negatives, 1,379 true negatives. Prevalence average precision=0.153026, departure heuristic=0.177668. Stress-set AP=0.415172, ROC-AUC=0.700917; higher AP partly reflects higher prevalence (0.241333), not better generalization. No real shipment metrics.

Transport reliability tests inject a publisher callback and simulate failure/retry; they do not run RabbitMQ. Docker/PostgreSQL integration is pending Docker installation. SQLite single-process workflow is verified. API tests produce one dependency deprecation warning from FastAPI/Starlette's HTTP test client; no test failures.

Simulator feature-history consistency was corrected during implementation and evaluation regenerated from final source. No test-set-based model hyperparameter tuning was performed. CI workflow is supplied; remote CI status must be verified separately before claiming it passed.
