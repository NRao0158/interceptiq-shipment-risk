# InterceptIQ — Shipment Escape Risk Prediction

Predict which packages under HOLD or REJECT may move before clearance within **60 simulated minutes**, then detect confirmed stop violations from shipment, screening and brokerage events.

Independent ML/backend portfolio project. **All shipments, facilities, labels and results are synthetic.** No production connections, carrier validation, live operational savings or guaranteed prevention claims.

## Two runnable parts

1. **Prediction demo:** Streamlit risk studio, event replay, evidence and batch inference. Loads bundled models; no Docker or training required.
2. **Event service:** FastAPI + SQLite by default. Durable event storage, source-specific hold rules, idempotent ingestion, late-event recomputation, alert acknowledgement and transactional outbox. Docker Compose adds PostgreSQL and RabbitMQ with publisher confirms and an idempotent consumer.

## Run on Windows without Docker

From this repository, with Python 3.12:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

In a second terminal, start the local service:

```powershell
.\.venv\Scripts\python.exe -m uvicorn interceptiq.api:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs for interactive API documentation. Replay the complete ingestion fixture:

```powershell
.\.venv\Scripts\python.exe -m scripts.replay
```

Expected on a fresh database: **2,050 events, 1,000 packages, 500 screening events, 300 brokerage events, 50 alerts and 50 outbox messages**. Replaying again adds no duplicate messages. SQLite outbox messages are pending until a RabbitMQ publisher runs; the no-Docker mode does not simulate successful queue delivery.

## Reproduce ML and tests

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m interceptiq.simulation
.\.venv\Scripts\python.exe -m interceptiq.train
.\.venv\Scripts\python.exe -m pytest -q
```

18,000 packages: earlier days 0–39 fit, 40–49 validation, 50–59 test. A separate 3,000-package stress set uses unseen facilities and a hidden compliance shift. One prediction snapshot per package at hold time. IDs, future movement, releases and labels never enter the feature matrix. [Model card](docs/MODEL_CARD.md) explains the simulation assumptions and limitations.

## Optional PostgreSQL + RabbitMQ

Install and start Docker Desktop first. Generate ignored local credentials and start the stack:

```powershell
python scripts/setup_env.py
docker compose up --build -d
python -m scripts.replay
docker compose logs publisher consumer
```

Open API docs at http://127.0.0.1:8000/docs and RabbitMQ management at http://127.0.0.1:15672. Management user: `interceptiq`; password is local `MQ_PASSWORD` from `.env`. Do not share or commit `.env`. Stop with `docker compose down` (volumes retained). This stack is a local test configuration, not a production deployment.

## API

| Endpoint | Purpose |
|---|---|
| `POST /events` | Ingest a validated event |
| `POST /sources/{source}/events` | Source-specific ingestion |
| `GET /packages/{id}/events` | Inspect stored history |
| `POST /packages/{id}/predict` | Build causal scan context for a known stop and predict |
| `POST /predict` | Score an explicit hold-time snapshot |
| `GET /alerts` | Inspect confirmed/retracted/acknowledged alerts |
| `POST /alerts/{id}/acknowledge` | Record acknowledgement |
| `GET /outbox` | Inspect queued publication status |

## Repository

- `interceptiq/simulation.py`: seeded event/snapshot generator and scripted demo.
- `interceptiq/features.py`: scan features strictly before the hold timestamp.
- `interceptiq/train.py`: chronological splits, baselines, selection, threshold, stress test.
- `interceptiq/rules.py`: deterministic event-time stop detection.
- `interceptiq/store.py`: transactions, deduplication, revisions, outbox/inbox.
- `interceptiq/api.py`: validated ingestion and prediction endpoints.
- `interceptiq/worker.py`: RabbitMQ publication/consumption.
- `app.py`: public prediction/replay demo, disconnected from the service database.
- `tests/`: causality, rule edge cases, API behavior, persistence, retries and UI.
- `docs/`: architecture, evaluation, deployment, learning guide and resume wording.

Original code is MIT licensed. No third-party shipment dataset is used. Public demo deployment is documented separately and must be verified before claiming it is deployed.
