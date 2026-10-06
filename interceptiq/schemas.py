from datetime import datetime,timezone
from typing import Literal
from pydantic import BaseModel,Field,field_validator,model_validator,ConfigDict

class Event(BaseModel):
    model_config=ConfigDict(extra='forbid')
    event_id:str=Field(min_length=1,max_length=100,pattern=r'^[A-Za-z0-9_-]+$')
    package_id:str=Field(min_length=1,max_length=100,pattern=r'^[A-Za-z0-9_-]+$')
    kind:Literal['CREATED','SCAN','HOLD','REJECT','RELEASE','DELIVERY']
    source:Literal['shipment','screening','brokerage']
    occurred_at:datetime
    facility:str=Field(min_length=1,max_length=50)
    @field_validator('occurred_at')
    @classmethod
    def utc(cls,value):
        if value.tzinfo is None: raise ValueError('A timezone is required.')
        return value.astimezone(timezone.utc)
    @model_validator(mode='after')
    def source_kind(self):
        if self.kind in ['HOLD','REJECT','RELEASE'] and self.source=='shipment': raise ValueError('Stop conditions belong to screening or brokerage.')
        if self.kind in ['CREATED','SCAN','DELIVERY'] and self.source!='shipment': raise ValueError('Movement belongs to shipment.')
        return self
    def normalized(self):
        d=self.model_dump(); d['occurred_at']=self.occurred_at.isoformat(); return d

class Snapshot(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    queue_load:float=Field(ge=0,le=1)
    staff_ratio:float=Field(gt=0,le=3)
    scans_last30:int=Field(ge=0,le=100)
    minutes_since_scan:float=Field(ge=0,le=1440)
    minutes_to_departure:float=Field(ge=0,le=1440)
    route_hops:int=Field(ge=1,le=50)
    weight_kg:float=Field(gt=0,le=500)
    hour:int=Field(ge=0,le=23)
    source:Literal['screening','brokerage']
    condition:Literal['HOLD','REJECT']
    service:Literal['economy','priority','express']

class HoldContext(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    hold_event_id:str
    queue_load:float=Field(ge=0,le=1)
    staff_ratio:float=Field(gt=0,le=3)
    minutes_to_departure:float=Field(ge=0,le=1440)
    route_hops:int=Field(ge=1,le=50)
    weight_kg:float=Field(gt=0,le=500)
    service:Literal['economy','priority','express']
