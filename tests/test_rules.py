from datetime import timedelta
import random
from interceptiq.simulation import START,make_event,demo_events,generate,outcome,FEATURES
from interceptiq.rules import detect

def event(kind,source,minute,seq): return make_event('TEST',kind,source,START+timedelta(minutes=minute),seq,'F0')

def test_normal_and_source_specific_release():
    assert not detect([event('CREATED','shipment',0,0),event('SCAN','shipment',3,1)])
    stop=event('HOLD','screening',1,1)
    assert not detect([stop,event('RELEASE','screening',2,2),event('SCAN','shipment',3,3)])
    assert len(detect([stop,event('RELEASE','brokerage',2,2),event('SCAN','shipment',3,3)]))==1

def test_reject_delivery_dedup_and_order():
    seq=[event('REJECT','brokerage',1,1),event('SCAN','shipment',2,2),event('DELIVERY','shipment',3,3)]
    expected=detect(seq)
    assert len(expected)==1
    assert detect(list(reversed(seq)))==expected
    assert next(iter(detect([seq[0],seq[2]]).values()))['reason']=='delivery_with_active_stop'

def test_overlapping_holds():
    seq=[event('HOLD','screening',1,1),event('HOLD','brokerage',2,2),event('RELEASE','screening',3,3),event('SCAN','shipment',4,4)]
    alerts=detect(seq)
    assert len(alerts)==1 and next(iter(alerts.values()))['source']=='brokerage'

def test_target_and_demo_counts():
    seq=[event('HOLD','screening',1,1),event('SCAN','shipment',61,2)]
    assert outcome(seq,'TEST-1')==1
    seq[1]=event('SCAN','shipment',62,2)
    assert outcome(seq,'TEST-1')==0
    events=demo_events(); groups={}
    for e in events: groups.setdefault(e['package_id'],[]).append(e)
    assert len(groups)==1000
    assert sum(e['source']=='screening' for e in events)==500
    assert sum(e['source']=='brokerage' for e in events)==300
    assert sum(bool(detect(g)) for g in groups.values())==50

def test_simulation_reproducibility_and_labels():
    a,hist=generate(50); b,_=generate(50)
    assert a.equals(b)
    for _,row in a.iterrows(): assert outcome(hist[row.package_id],row.hold_id)==row.escape
    assert not {'escape','package_id','facility','day','hold_id','prediction_at'}&set(FEATURES)

def test_features_ignore_future():
    from interceptiq.features import at_hold
    context=dict(queue_load=.4,staff_ratio=1.,minutes_to_departure=10.,route_hops=2,weight_kg=4.,service='priority')
    before=[event('SCAN','shipment',0,0),event('HOLD','screening',2,2)]
    future=before+[event('SCAN','shipment',3,3),event('RELEASE','screening',4,4)]
    assert at_hold(before,'TEST-2',context)==at_hold(future,'TEST-2',context)
    assert at_hold(before,'TEST-2',context)['scans_last30']==1
