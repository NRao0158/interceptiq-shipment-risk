import os
from fastapi import FastAPI,HTTPException,Query
from .schemas import Event,Snapshot,HoldContext
from .features import at_hold
from .store import Store
from .predict import score

def create_app(store=None):
    store=store or Store(os.getenv('DATABASE_URL','sqlite:///interceptiq.db'))
    app=FastAPI(title='InterceptIQ',version='1.0.0',description='Synthetic portfolio prototype. Local API; no production connections.')
    app.state.store=store
    @app.get('/health')
    def health(): return {'status':'ok','scope':'simulation'}
    @app.post('/events',status_code=201)
    def ingest(event:Event):
        try: return store.ingest(event.normalized())
        except ValueError as exc: raise HTTPException(409,str(exc))
    @app.post('/sources/{source}/events',status_code=201)
    def ingest_source(source:str,event:Event):
        if source!=event.source: raise HTTPException(422,'Path source and event source must match.')
        return ingest(event)
    @app.get('/packages/{package_id}/events')
    def events(package_id:str): return store.events(package_id)
    @app.get('/alerts')
    def alerts(limit:int=Query(default=1000,ge=1,le=10000)): return store.alerts()[:limit]
    @app.post('/alerts/{alert_id}/acknowledge')
    def acknowledge(alert_id:str):
        try: return store.acknowledge(alert_id)
        except KeyError: raise HTTPException(404,'Alert not found.')
        except ValueError as exc: raise HTTPException(409,str(exc))
    @app.get('/outbox')
    def outbox(limit:int=Query(default=1000,ge=1,le=10000)): return store.outbox()[:limit]
    @app.post('/predict')
    def predict(snapshot:Snapshot): return score(snapshot.model_dump())
    @app.post('/packages/{package_id}/predict')
    def predict_package(package_id:str,context:HoldContext):
        values=context.model_dump(); hold_id=values.pop('hold_event_id')
        try: snapshot=Snapshot.model_validate(at_hold(store.events(package_id),hold_id,values))
        except ValueError as exc: raise HTTPException(422,str(exc))
        return score(snapshot.model_dump())
    return app

app=create_app()
