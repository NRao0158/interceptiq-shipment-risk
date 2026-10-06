"""Seeded simulator. Outcomes come from future events, never exported risk formulas."""
from pathlib import Path
from datetime import datetime, timedelta, timezone
import json
import numpy as np
import pandas as pd
from .features import at_hold

ROOT=Path(__file__).resolve().parents[1]
NUMERIC=['queue_load','staff_ratio','scans_last30','minutes_since_scan','minutes_to_departure','route_hops','weight_kg','hour']
CATEGORICAL=['source','condition','service']
FEATURES=NUMERIC+CATEGORICAL
START=datetime(2026,1,1,tzinfo=timezone.utc)

def order(events):
    rank={'CREATED':0,'RELEASE':1,'HOLD':2,'REJECT':2,'SCAN':3,'DELIVERY':3}
    return sorted(events,key=lambda e:(e['occurred_at'],rank[e['kind']],e['event_id']))

def make_event(pid,kind,source,at,sequence,facility):
    return dict(event_id=f'{pid}-{sequence}',package_id=pid,kind=kind,source=source,occurred_at=at.isoformat(),facility=facility)

def outcome(events,hold_id):
    active=False; start=None; source=None
    for e in order(events):
        if e['event_id']==hold_id:
            active=True; start=datetime.fromisoformat(e['occurred_at']); source=e['source']
        elif active:
            elapsed=(datetime.fromisoformat(e['occurred_at'])-start).total_seconds()/60
            if elapsed>60: return 0
            if e['source']==source and e['kind']=='RELEASE': return 0
            if e['kind'] in ['SCAN','DELIVERY']: return 1
    return 0

def generate(n=18000,seed=42,shift=False):
    rng=np.random.default_rng(seed); rows=[]; trajectories={}
    for i in range(n):
        day=int(rng.integers(50,60) if shift else rng.integers(0,60))
        facility=f'F{int(rng.integers(8,10) if shift else rng.integers(0,8))}'
        hour=int(rng.integers(0,24)); at=START+timedelta(days=day,hours=hour,minutes=int(rng.integers(0,60)))
        source=str(rng.choice(['screening','brokerage'])); condition=str(rng.choice(['HOLD','REJECT'],p=[.8,.2]))
        service=str(rng.choice(['economy','priority','express']))
        load=float(rng.beta(2,2)); staff=float(rng.uniform(.25,1.5)); scans=int(rng.poisson(2)); since=float(rng.uniform(1,29) if scans else rng.uniform(31,45)); departure=float(rng.uniform(5,100)); hops=int(rng.integers(1,7)); weight=float(rng.lognormal(1,.8))
        pid=f'{"OOD" if shift else "PKG"}-{seed}-{i:06d}'
        # Noisy latent bypass behavior; the hidden driver is intentionally unavailable.
        z=-3.1+2.6*load-1.6*staff+.38*scans+1.3*(departure<20)+.45*(service=='express')+.5*(source=='brokerage')+.35*(condition=='REJECT')+rng.normal(0,.8)
        if shift: z+=.8 # unseen facilities have worse compliance, not just new IDs
        bypass=rng.random()<1/(1+np.exp(-z))
        move_minutes=float(rng.uniform(2,58) if bypass else rng.uniform(65,160))
        release_minutes=float(rng.uniform(3,100))
        events=[make_event(pid,'CREATED','shipment',at-timedelta(minutes=90),0,facility),make_event(pid,'SCAN','shipment',at-timedelta(minutes=since),1,facility),make_event(pid,condition,source,at,2,facility),make_event(pid,'RELEASE',source,at+timedelta(minutes=release_minutes),3,facility),make_event(pid,'SCAN','shipment',at+timedelta(minutes=move_minutes),4,facility),make_event(pid,'DELIVERY','shipment',at+timedelta(minutes=max(move_minutes,release_minutes)+120),5,facility)]
        for j,minutes in enumerate(np.linspace(since,29.9,scans)[1:]):
            events.append(make_event(pid,'SCAN','shipment',at-timedelta(minutes=float(minutes)),6+j,facility))
        context=dict(queue_load=load,staff_ratio=staff,minutes_to_departure=departure,route_hops=hops,weight_kg=weight,service=service)
        snapshot=at_hold(events,events[2]['event_id'],context)
        rows.append(dict(package_id=pid,day=day,facility=facility,hold_id=events[2]['event_id'],prediction_at=at.isoformat(),**snapshot,escape=outcome(events,events[2]['event_id'])))
        if i<50: trajectories[pid]=order(events)
    return pd.DataFrame(rows),trajectories

def demo_events():
    # Exactly 1,000 packages, 500 screening events, 300 brokerage events, 50 escapes.
    # Separate scripted demonstration: never used for training or reported ML metrics.
    events=[]
    for i in range(1000):
        pid=f'DEMO-{i:04d}'; at=START+timedelta(minutes=i); facility=f'F{i%8}'
        events.append(make_event(pid,'CREATED','shipment',at,0,facility))
        if i<800:
            source='screening' if i<500 else 'brokerage'
            events.append(make_event(pid,'HOLD',source,at+timedelta(minutes=1),1,facility))
            if i<50: events.append(make_event(pid,'SCAN','shipment',at+timedelta(minutes=10),2,facility))
        else:
            events.append(make_event(pid,'SCAN','shipment',at+timedelta(minutes=10),1,facility))
    return order(events)

def main():
    data=ROOT/'data'; data.mkdir(exist_ok=True)
    df,hist=generate(); df.to_csv(data/'snapshots.csv',index=False)
    ood,_=generate(3000,99,shift=True); ood.to_csv(data/'shifted.csv',index=False)
    (data/'example_histories.json').write_text(json.dumps(hist,indent=2))
    (data/'demo_events.json').write_text(json.dumps(demo_events(),indent=2))
    print(f'Generated {len(df)} training/evaluation snapshots and {len(ood)} shifted snapshots.')
if __name__=='__main__': main()
