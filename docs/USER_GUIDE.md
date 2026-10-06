# Using InterceptIQ, step by step

Live demo: https://nihal-interceptiq.streamlit.app/

Source code: https://github.com/NRao0158/interceptiq-shipment-risk

## What you built

InterceptIQ answers two questions. At the moment a package receives a HOLD or REJECT, a machine-learning model estimates whether it will move before clearance within the next 60 simulated minutes. After scan events arrive, deterministic rules detect whether movement actually violated an active stop condition.

Prediction helps prioritize inspection. It is an uncalibrated model score, not a guaranteed probability or permission to ignore a hold. Every active hold still requires normal enforcement. All package data is synthetic.

The public Streamlit app demonstrates predictions and replay. The local Docker stack separately demonstrates FastAPI ingestion, PostgreSQL storage, and RabbitMQ alert delivery. The public app does not read your local database.

## 1. Try a single prediction

1. Open the live demo and select **Risk studio**.
2. Pick a held-out synthetic shipment from the dropdown. Its context fills the controls.
3. Read **Movement before clearance / 60 min** and **Priority**. A score at or above 0.12 produces **Inspect now**.
4. Change facility queue load, staffing, scheduled departure, recent scans, or stop condition. The model recomputes automatically; there is no submit button.
5. Compare the score before and after your changes. Changing one control at a time makes the demonstration easier to understand. Changes are model associations, not proven causal effects.
6. Click **Download prediction JSON** to save the inputs and output.

Queue load ranges from 0 to 1. Staffing is actual staffing divided by planned staffing: 1 means fully staffed and 0.5 means half staffed. Departure and scan ages are minutes. Hour is UTC. Route hops and weight come from the selected shipment and are included in the downloaded input.

## 2. Watch a confirmed violation appear

1. Select **Event replay**, then **Movement after HOLD**.
2. Move **Events received** to 1 and advance it one step at a time.
3. Watch the package creation, stop condition, and subsequent movement arrive. The red confirmed-violation message appears when the rules have evidence of movement during an active stop.
4. Compare **Normal flow** and **Active HOLD without movement**. A hold alone is not a confirmed escape.
5. Download the full ingestion fixture if you want to inspect the event JSON.

This scripted fixture contains 1,000 packages, 2,050 events, 500 screening events, 300 brokerage events, and 50 escape scenarios. It is separate from the machine-learning evaluation data.

## 3. Understand the model results

Select **Model evidence**. Training uses earlier days, validation selects the model and threshold, and testing uses later days. Each package contributes one hold-time snapshot; future movement and release information are excluded from model inputs.

On 2,908 held-out synthetic packages, average precision is 0.321 versus a prevalence baseline of 0.153. Average precision summarizes precision across recall levels; 0.321 does not mean 32.1% accuracy. At the chosen threshold, recall is about 76.2% and precision about 23.8%, so many flagged packages are false positives. Explain this inspection-workload tradeoff in interviews. The separate 3,000-package stress set tests unseen facilities with shifted simulation conditions.

These results describe the simulator. Real deployment would require real shipment data, operational validation, calibration, and security controls.

## 4. Score a batch

1. Select **Batch predictions** and click **Download sample inputs**.
2. Upload that CSV unchanged first to confirm the workflow.
3. Edit some values in a spreadsheet while preserving the column names and categorical values.
4. Upload the edited CSV and click **Export scores**.

The limit is 5,000 rows. Required columns are shown in the app. Use information available at hold time; never add future movement or release times as input features.

## 5. Use your local backend

Your current Docker API runs at http://127.0.0.1:8001/docs . Keep Docker Desktop running. If the containers are stopped, open PowerShell and run:

```powershell
cd 'C:\Users\nihal\Documents\Codex\2026-10-05\i-want-to-build-teh-following\outputs\interceptiq'
docker compose up -d
docker compose ps
```

In the API documentation, expand an endpoint, select **Try it out**, fill the fields, and select **Execute**.

- `GET /alerts`: inspect confirmed, acknowledged, and retracted alerts.
- `GET /outbox`: inspect publication records. Published records show that the publisher completed broker delivery; the integration verifier also checks persisted consumer inbox records.
- `GET /packages/{id}/events`: use `DEMO-0000` to inspect a fixture package.
- `POST /predict`: submit a hold-time snapshot. Copy the `input` object from your downloaded prediction JSON, without the surrounding `input`/`prediction` wrapper.
- `POST /alerts/{id}/acknowledge`: use an alert ID returned by `GET /alerts` and fill the request body shown by the API.

Acknowledgement records human handling; it does not clear the package hold. Releases must come from the applicable stop source. A brokerage release cannot clear a screening hold.

The verified database already includes the fixture plus extra reliability scenarios: 2,055 events, 52 historical alerts (including a retraction), 54 published outbox messages, and 54 consumer inbox records. Further actions can change these counts. The fresh fixture alone produces 50 alerts.

To repeat the original fixture safely using the existing Python environment:

```powershell
..\..\work\venv\Scripts\python.exe -m scripts.replay --url http://127.0.0.1:8001
```

Duplicate event IDs do not create new alerts. RabbitMQ management is at http://127.0.0.1:15672 . The username is `interceptiq`; use the local `MQ_PASSWORD` in `.env`. Do not share that file. A consumed queue can show zero ready messages because the consumer has already processed them.

Stop the stack with `docker compose down`. Stored data remains in Docker volumes. Avoid `docker compose down -v`, which deletes those volumes. The free public prediction demo continues running independently.
