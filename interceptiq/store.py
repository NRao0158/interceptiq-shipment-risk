import hashlib,threading
from datetime import datetime,timezone
from sqlalchemy import create_engine,Column,String,Integer,JSON,Boolean,select,text
from sqlalchemy.orm import declarative_base,Session
from sqlalchemy.pool import StaticPool
from .rules import detect

Base=declarative_base()
class EventRow(Base):
    __tablename__='events'
    id=Column(String(100),primary_key=True)
    package_id=Column(String(100),index=True,nullable=False)
    payload=Column(JSON,nullable=False)
class AlertRow(Base):
    __tablename__='alerts'
    id=Column(String(24),primary_key=True)
    package_id=Column(String(100),index=True,nullable=False)
    payload=Column(JSON,nullable=False)
    status=Column(String(20),nullable=False,default='open')
    revision=Column(Integer,nullable=False,default=1)
class OutboxRow(Base):
    __tablename__='outbox'
    id=Column(Integer,primary_key=True,autoincrement=True)
    message_id=Column(String(100),unique=True,nullable=False)
    payload=Column(JSON,nullable=False)
    published=Column(Boolean,nullable=False,default=False)
    attempts=Column(Integer,nullable=False,default=0)
    last_error=Column(String(100),nullable=True)
class InboxRow(Base):
    __tablename__='inbox'
    id=Column(String(100),primary_key=True)
    payload=Column(JSON,nullable=False)

class Store:
    def __init__(self,url='sqlite:///interceptiq.db'):
        options={}
        if url.startswith('sqlite'):
            options['connect_args']={'check_same_thread':False}
            if ':memory:' in url: options['poolclass']=StaticPool
        self.engine=create_engine(url,**options)
        Base.metadata.create_all(self.engine)
        self.lock=threading.RLock()
    def emit(self,session,alert,kind):
        message_id=f'{alert.id}-{alert.revision}-{kind}'
        session.add(OutboxRow(message_id=message_id,payload=dict(message_id=message_id,type=kind,revision=alert.revision,status=alert.status,alert=alert.payload,recorded_at=datetime.now(timezone.utc).isoformat())))
    def ingest(self,event):
        with self.lock,Session(self.engine) as session,session.begin():
            # PostgreSQL serializes recomputation per package across API processes.
            if self.engine.dialect.name=='postgresql':
                number=int.from_bytes(hashlib.sha256(event['package_id'].encode()).digest()[:8],signed=True)
                session.execute(text('SELECT pg_advisory_xact_lock(:key)'),{'key':number})
            existing=session.get(EventRow,event['event_id'])
            if existing:
                if existing.payload!=event: raise ValueError('Event ID already exists with different content.')
                return {'duplicate':True,'changes':[]}
            session.add(EventRow(id=event['event_id'],package_id=event['package_id'],payload=event)); session.flush()
            events=[r.payload for r in session.scalars(select(EventRow).where(EventRow.package_id==event['package_id']))]
            desired=detect(events); previous={r.id:r for r in session.scalars(select(AlertRow).where(AlertRow.package_id==event['package_id']))}
            changes=[]
            for key,payload in desired.items():
                old=previous.get(key)
                if old is None:
                    old=AlertRow(id=key,package_id=event['package_id'],payload=payload,status='open',revision=1)
                    session.add(old); self.emit(session,old,'intercept.created'); changes.append('created')
                elif old.status=='retracted' or old.payload!=payload:
                    old.payload=payload; old.revision+=1
                    if old.status=='retracted': old.status='open'
                    self.emit(session,old,'intercept.updated'); changes.append('updated')
            for key,old in previous.items():
                if key not in desired and old.status!='retracted':
                    old.status='retracted'; old.revision+=1; self.emit(session,old,'intercept.retracted'); changes.append('retracted')
            return {'duplicate':False,'changes':changes}
    def alerts(self):
        with Session(self.engine) as session:
            return [dict(**r.payload,status=r.status,revision=r.revision) for r in session.scalars(select(AlertRow).order_by(AlertRow.id))]
    def events(self,pid):
        with Session(self.engine) as session:
            return [r.payload for r in session.scalars(select(EventRow).where(EventRow.package_id==pid))]
    def acknowledge(self,key):
        with self.lock,Session(self.engine) as session,session.begin():
            row=session.get(AlertRow,key)
            if row is None: raise KeyError(key)
            if row.status=='retracted': raise ValueError('Cannot acknowledge a retracted alert.')
            if row.status!='acknowledged':
                row.status='acknowledged'; row.revision+=1; self.emit(session,row,'intercept.acknowledged')
            return {'alert_id':key,'status':row.status,'revision':row.revision}
    def outbox(self):
        with Session(self.engine) as session:
            return [dict(id=r.id,message_id=r.message_id,published=r.published,attempts=r.attempts,last_error=r.last_error,payload=r.payload) for r in session.scalars(select(OutboxRow).order_by(OutboxRow.id))]
    def consume(self,message):
        with self.lock,Session(self.engine) as session,session.begin():
            if session.get(InboxRow,message['message_id']): return False
            session.add(InboxRow(id=message['message_id'],payload=message)); return True
    def dispatch(self,publish,limit=100):
        sent=0
        with self.lock,Session(self.engine) as session,session.begin():
            rows=session.scalars(select(OutboxRow).where(OutboxRow.published==False).order_by(OutboxRow.id).limit(limit).with_for_update(skip_locked=True))
            for row in rows:
                row.attempts+=1
                try:
                    publish(row.message_id,row.payload)
                    row.published=True; row.last_error=None; sent+=1
                except Exception as exc:
                    row.last_error=type(exc).__name__
                    break # Preserve revision order while retrying on a later pass.
        return sent
