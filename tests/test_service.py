import json,random
import pytest
from fastapi.testclient import TestClient
from interceptiq.api import create_app
from interceptiq.store import Store
from interceptiq.simulation import demo_events,FEATURES,ROOT
from .test_rules import event

@pytest.fixture
def store(): return Store('sqlite:///:memory:')

def test_api_reject_duplicate_and_conflict(store):
    with TestClient(create_app(store)) as c:
        hold=event('HOLD','screening',1,1)
        assert c.post('/events',json=hold).status_code==201
        assert c.post('/events',json=hold).json()['duplicate']
        assert c.post('/events',json={**hold,'facility':'F1'}).status_code==409
        assert c.post('/sources/brokerage/events',json=hold).status_code==422
        assert c.post('/events',json={**hold,'occurred_at':'2026-01-01T00:00:00'}).status_code==422

def test_late_events_and_retraction(store):
    store.ingest(event('SCAN','shipment',3,3))
    store.ingest(event('HOLD','screening',1,1))
    assert len(store.alerts())==1
    store.ingest(event('RELEASE','screening',2,2))
    assert store.alerts()[0]['status']=='retracted'
    assert [r['payload']['type'] for r in store.outbox()]==['intercept.created','intercept.retracted']
    assert store.ingest(event('SCAN','shipment',3,3))['duplicate']

def test_ack_and_delivery_retry(store):
    store.ingest(event('HOLD','screening',1,1)); store.ingest(event('SCAN','shipment',3,3))
    key=store.alerts()[0]['alert_id']; store.acknowledge(key); store.acknowledge(key)
    assert len(store.outbox())==2
    def fail(key,payload): raise ConnectionError('test failure')
    assert store.dispatch(fail)==0
    assert not store.outbox()[0]['published']
    sent=[]; assert store.dispatch(lambda key,payload:sent.append(payload))==2
    assert store.dispatch(lambda key,payload:sent.append(payload))==0
    assert store.consume(sent[0]) and not store.consume(sent[0])

def test_full_demo_and_replay_idempotence(store):
    events=demo_events()
    for e in events: store.ingest(e)
    assert len(store.alerts())==50 and len(store.outbox())==50
    for e in events: assert store.ingest(e)['duplicate']
    assert len(store.outbox())==50

def test_persistence_and_prediction(tmp_path):
    url='sqlite:///'+str(tmp_path/'events.db'); s=Store(url)
    s.ingest(event('HOLD','screening',1,1)); s.ingest(event('SCAN','shipment',3,3))
    assert len(Store(url).alerts())==1
    import pandas as pd
    row=pd.read_csv(ROOT/'artifacts/demo_snapshots.csv').iloc[0][FEATURES].to_dict()
    with TestClient(create_app(s)) as c:
        r=c.post('/predict',json=row); assert r.status_code==200
        assert 0<=r.json()['risk']<=1
        assert c.post('/predict',json={**row,'escape':1}).status_code==422
