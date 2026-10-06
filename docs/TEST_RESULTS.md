# Verification and limitations

Executed on Windows/Python 3.12: **12 automated tests passed**. Coverage: normal/released stops, source-specific clearance, REJECT/delivery, event order, overlapping holds, exact scripted fixture counts, seeded labels, future-event feature invariance, API schema/conflict rejection, late-event retraction, acknowledgement/delivery retry/inbox deduplication, durable SQLite restart, model inference and Streamlit interaction.

ML: 12,048 fit packages; 3,044 validation; 2,908 future-day test; 3,000 shifted-facility stress test. Selected logistic regression. Test average precision=0.320509, ROC-AUC=0.715884, precision=0.238229 and recall=0.761798 at threshold=0.12. Confusion counts: 339 true positives, 1,084 false positives, 106 false negatives, 1,379 true negatives. Prevalence average precision=0.153026, departure heuristic=0.177668. Stress-set AP=0.415172, ROC-AUC=0.700917; higher AP partly reflects higher prevalence (0.241333), not better generalization. No real shipment metrics.

Transport reliability tests inject a publisher callback and simulate failure/retry; they do not run RabbitMQ. Docker/PostgreSQL integration is pending Docker installation. SQLite single-process workflow is verified. API tests produce one dependency deprecation warning from FastAPI/Starlette's HTTP test client; no test failures.

Simulator feature-history consistency was corrected during implementation and evaluation regenerated from final source. No test-set-based model hyperparameter tuning was performed. CI workflow is supplied; remote CI status must be verified separately before claiming it passed.
