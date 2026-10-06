# Deployment and setup

Public demo: https://nihal-interceptiq.streamlit.app/ . Verified on October 6, 2026: saved model inference and confirmed HOLD-to-movement replay render successfully on Streamlit Community Cloud with Python 3.12. GitHub repository: https://github.com/NRao0158/interceptiq-shipment-risk . The API/broker stack remains local.

## Local quick start

Use README instructions to run the Streamlit demo and SQLite API separately. Neither requires Docker. API startup creates `interceptiq.db`; restarting preserves events/alerts. A clean dedicated database is needed for the exact 50-alert fixture count. Override `DATABASE_URL` to use another file or approved PostgreSQL instance. Never reuse production data.

## Docker test stack

1. Install/start Docker Desktop using WSL 2.
2. Run `python scripts/setup_env.py` once to generate local ignored secrets.
3. Run `docker compose up --build -d`.
4. Run `python -m scripts.replay` against loopback port 8000.
5. Inspect `docker compose logs publisher consumer` and API `/outbox`.
6. Pending rows should become published; consumer should store message identifiers once.

The live PostgreSQL/RabbitMQ stack was verified on Docker Desktop: complete fixture delivery, ingestion and transport deduplication, acknowledgements, late-event retractions, dead-letter routing, broker outage recovery and persistence across container recreation. Unit tests still use injected transport; `scripts/verify_stack.py` checks the actual broker and database. Its `full` mode expects a fresh dedicated test database, not the existing workspace database containing prior verification events. Do not erase persistent volumes just to rerun it.

This workspace uses `API_PORT=8001` in ignored `.env`, preserving SQLite on port 8000. Use http://127.0.0.1:8001/docs and `python -m scripts.replay --url http://127.0.0.1:8001`. `docker compose up -d` uses the saved port automatically. `docker compose down` stops/removes containers but preserves volumes; do not add `-v` unless you intend to delete test data.

## Free public prediction demo

Publish this folder's contents as GitHub repository root. In Streamlit Community Cloud, select repo, branch `main`, entrypoint `app.py` and Python 3.12. Bundled artifacts eliminate startup training. This deployment is prediction/event replay only; the full PostgreSQL/RabbitMQ service stack runs locally. Do not claim publicly hosted APIs or message queues.

Official references:

- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://fastapi.tiangolo.com/tutorial/testing/
- https://www.rabbitmq.com/docs/reliability
- https://docs.docker.com/desktop/setup/install/windows-install/
