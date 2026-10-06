"""Run inside publisher container against the isolated local Compose stack."""
import argparse,json,os,time
from urllib.request import Request,urlopen
from sqlalchemy import select,func
from sqlalchemy.orm import Session
import pika
from interceptiq.store import Store,EventRow,AlertRow,OutboxRow,InboxRow
from interceptiq.worker import connect,QUEUE
from interceptiq.simulation import ROOT,make_event,START
from datetime import timedelta

BASE='http://api:8000'
def request(path,payload=None):
    req=Request(BASE+path,data=json.dumps(payload).encode() if payload is not None else None,headers={'Content-Type':'application/json'},method='POST' if payload is not None else 'GET')
    with urlopen(req,timeout=20) as response: return json.load(response)

def counts(store):
    with Session(store.engine) as s:
        return dict(events=s.scalar(select(func.count()).select_from(EventRow)),alerts=s.scalar(select(func.count()).select_from(AlertRow)),outbox=s.scalar(select(func.count()).select_from(OutboxRow)),pending=s.scalar(select(func.count()).select_from(OutboxRow).where(OutboxRow.published==False)),inbox=s.scalar(select(func.count()).select_from(InboxRow)))

def settle(store,target,timeout=60):
    until=time.monotonic()+timeout
    while time.monotonic()<until:
        c=counts(store)
        if c['pending']==0 and c['inbox']==target: return c
        time.sleep(1)
    raise AssertionError(f'Delivery did not settle: {counts(store)}; expected inbox {target}')

def main():
    p=argparse.ArgumentParser(); p.add_argument('mode',choices=['full','outage','recovery','counts']); args=p.parse_args()
    store=Store(os.environ['DATABASE_URL'])
    if args.mode=='counts': print(json.dumps(counts(store))); return
    if args.mode=='outage':
        for i,kind,source in [(0,'HOLD','screening'),(1,'SCAN','shipment')]:
            e=make_event('VERIFY-OUTAGE',kind,source,START+timedelta(minutes=i),i,'TEST')
            request('/events',e)
        c=counts(store); assert c['pending']>=1,c
        print(json.dumps({'broker_offline_event_saved':True,'counts':c})); return
    if args.mode=='recovery':
        print(json.dumps({'recovered':True,'counts':settle(store,54)})); return
    events=json.loads((ROOT/'artifacts/demo_events.json').read_text())
    for e in events: request('/events',e)
    initial=settle(store,50)
    assert initial['events']==2050 and initial['alerts']==50 and initial['outbox']==50,initial
    for e in events: assert request('/events',e)['duplicate']
    assert counts(store)==initial
    # A true broker redelivery must not create a second inbox record.
    first=store.outbox()[0]; connection,channel=connect(); channel.confirm_delivery()
    channel.basic_publish(exchange='',routing_key=QUEUE,body=json.dumps(first['payload']),properties=pika.BasicProperties(delivery_mode=2,message_id=first['message_id']),mandatory=True)
    # Also verify malformed input reaches a durable dead-letter queue.
    channel.basic_publish(exchange='',routing_key=QUEUE,body='not-json',properties=pika.BasicProperties(delivery_mode=2,message_id='VERIFY-MALFORMED'),mandatory=True)
    until=time.monotonic()+30
    dead=0
    while time.monotonic()<until:
        dead=channel.queue_declare(queue='interceptiq.dead.alerts',passive=True).method.message_count
        ready=channel.queue_declare(queue=QUEUE,passive=True).method.message_count
        if dead>=1 and ready==0: break
        time.sleep(.5)
    connection.close(); assert dead>=1
    assert counts(store)['inbox']==50
    key=store.alerts()[0]['alert_id']; request('/alerts/'+key+'/acknowledge',{})
    settle(store,51)
    # A delayed release can retract a previously published confirmed violation.
    for i,kind,source,minute in [(0,'HOLD','screening',1),(1,'SCAN','shipment',3),(2,'RELEASE','screening',2)]:
        request('/events',make_event('VERIFY-LATE',kind,source,START+timedelta(minutes=minute),i,'TEST'))
    final=settle(store,53)
    alert=[a for a in store.alerts() if a['package_id']=='VERIFY-LATE'][0]
    assert alert['status']=='retracted'
    print(json.dumps({'fixture':initial,'duplicate_ingestion':'passed','broker_redelivery':'deduplicated','dead_letter_messages':dead,'acknowledgement':'delivered','late_release':'retracted_and_delivered','final':final},indent=2))
if __name__=='__main__': main()
