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

Broker/consumer operation must be verified on this stack before claiming real RabbitMQ integration was tested. Provided publisher tests use an injected transport, not a running broker. PostgreSQL-specific behavior likewise requires integration verification. Do not run local SQLite API concurrently on the same port as Docker API.

## Free public prediction demo

Publish this folder's contents as GitHub repository root. In Streamlit Community Cloud, select repo, branch `main`, entrypoint `app.py` and Python 3.12. Bundled artifacts eliminate startup training. This deployment is prediction/event replay only; the full PostgreSQL/RabbitMQ service stack runs locally. Do not claim publicly hosted APIs or message queues.

Official references:

- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://fastapi.tiangolo.com/tutorial/testing/
- https://www.rabbitmq.com/docs/reliability
- https://docs.docker.com/desktop/setup/install/windows-install/
