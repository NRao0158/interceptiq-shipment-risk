import hashlib
from .simulation import order

def detect(events):
    """One alert per active source-specific stop episode, derived in event time."""
    active={}; alerts={}
    for e in order(events):
        if e['kind'] in ['HOLD','REJECT']:
            active[e['source']]=e
        elif e['kind']=='RELEASE':
            active.pop(e['source'],None)
        elif e['kind'] in ['SCAN','DELIVERY']:
            for stop in active.values():
                key=hashlib.sha256(stop['event_id'].encode()).hexdigest()[:24]
                if key not in alerts:
                    alerts[key]=dict(alert_id=key,package_id=e['package_id'],stop_event_id=stop['event_id'],movement_event_id=e['event_id'],source=stop['source'],condition=stop['kind'],detected_at=e['occurred_at'],facility=e['facility'],reason='delivery_with_active_stop' if e['kind']=='DELIVERY' else 'movement_with_active_stop')
    return alerts
