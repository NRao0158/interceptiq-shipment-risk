from functools import lru_cache
import joblib,pandas as pd
from threadpoolctl import threadpool_limits
from .simulation import ROOT,FEATURES,NUMERIC

@lru_cache
def bundle():
    threadpool_limits(limits=2)
    return joblib.load(ROOT/'artifacts/model.joblib')

def score(snapshot):
    b=bundle(); frame=pd.DataFrame([snapshot])[FEATURES]
    risk=float(b['model'].predict_proba(frame)[0,1])
    unusual=[c for c in NUMERIC if snapshot[c]<b['bounds'][c][0] or snapshot[c]>b['bounds'][c][1]]
    return dict(risk=risk,threshold=b['threshold'],prioritize=risk>=b['threshold'],horizon_minutes=60,out_of_range_features=unusual,scope='Synthetic simulation only; uncalibrated risk score. No carrier validation.')
