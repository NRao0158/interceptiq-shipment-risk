import json,hashlib
from datetime import datetime,timezone
import joblib,numpy as np,pandas as pd,sklearn
from threadpoolctl import threadpool_limits
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import average_precision_score,roc_auc_score,precision_score,recall_score,brier_score_loss
from sklearn.inspection import permutation_importance
from .simulation import ROOT,NUMERIC,CATEGORICAL,FEATURES

def metrics(y,p,t):
    z=p>=t
    return dict(average_precision=float(average_precision_score(y,p)),roc_auc=float(roc_auc_score(y,p)),precision=float(precision_score(y,z,zero_division=0)),recall=float(recall_score(y,z,zero_division=0)),brier=float(brier_score_loss(y,p)),true_positives=int(((y==1)&z).sum()),false_positives=int(((y==0)&z).sum()),false_negatives=int(((y==1)&~z).sum()),true_negatives=int(((y==0)&~z).sum()),positive_rate=float(np.mean(y)),packages=len(y))

def main():
    threadpool_limits(limits=2)
    df=pd.read_csv(ROOT/'data/snapshots.csv'); shifted=pd.read_csv(ROOT/'data/shifted.csv')
    fit=df.day<40; val=(df.day>=40)&(df.day<50); test=df.day>=50
    preprocess=lambda:ColumnTransformer([('numeric',StandardScaler(),NUMERIC),('categorical',OneHotEncoder(handle_unknown='ignore',sparse_output=False),CATEGORICAL)])
    models={'prevalence':make_pipeline(preprocess(),DummyClassifier(strategy='prior')),'logistic':make_pipeline(preprocess(),LogisticRegression(max_iter=1000)),'gradient_boosting':make_pipeline(preprocess(),HistGradientBoostingClassifier(max_iter=120,max_leaf_nodes=12,l2_regularization=8,random_state=42))}
    scores={}
    for name,m in models.items():
        m.fit(df.loc[fit,FEATURES],df.loc[fit,'escape'])
        scores[name]=float(average_precision_score(df.loc[val,'escape'],m.predict_proba(df.loc[val,FEATURES])[:,1]))
    selected=max(scores,key=scores.get); model=models[selected]
    p=model.predict_proba(df.loc[val,FEATURES])[:,1]; y=df.loc[val,'escape'].to_numpy()
    thresholds=np.linspace(.01,.99,99); costs=[int(((y==1)&(p<t)).sum())*8+int(((y==0)&(p>=t)).sum()) for t in thresholds]
    threshold=float(thresholds[np.argmin(costs)])
    report={'selected':selected,'threshold':threshold,'cost_assumption':{'false_negative':8,'false_positive':1},'validation_average_precision':scores,'test':{},'shifted_test':{},'split_counts':{'train':int(fit.sum()),'validation':int(val.sum()),'test':int(test.sum())},'features':FEATURES,'seed':42,'horizon_minutes':60,'timestamp':datetime.now(timezone.utc).isoformat(),'sklearn':sklearn.__version__}
    # All model thresholds tuned separately on validation for a fair policy comparison.
    report['thresholds']={}
    for name,m in models.items():
        vp=m.predict_proba(df.loc[val,FEATURES])[:,1]
        cs=[int(((y==1)&(vp<t)).sum())*8+int(((y==0)&(vp>=t)).sum()) for t in thresholds]
        t=float(thresholds[np.argmin(cs)]); report['thresholds'][name]=t
        report['test'][name]=metrics(df.loc[test,'escape'].to_numpy(),m.predict_proba(df.loc[test,FEATURES])[:,1],t)
        report['shifted_test'][name]=metrics(shifted.escape.to_numpy(),m.predict_proba(shifted[FEATURES])[:,1],t)
    # Operational rules are reactive and cannot predict future violations at hold time.
    rule_p=(df.loc[test,'minutes_to_departure']<20).astype(float).to_numpy()
    report['test']['departure_rule']=metrics(df.loc[test,'escape'].to_numpy(),rule_p,.5)
    importance=permutation_importance(model,df.loc[val,FEATURES],df.loc[val,'escape'],scoring='average_precision',n_repeats=3,random_state=42)
    report['importance']=sorted([{'feature':c,'ap_drop':float(v)} for c,v in zip(FEATURES,importance.importances_mean)],key=lambda z:z['ap_drop'],reverse=True)
    # Package bootstrap: one snapshot per package, avoiding repeated rows from one identity.
    rng=np.random.default_rng(73); tp=model.predict_proba(df.loc[test,FEATURES])[:,1]; ty=df.loc[test,'escape'].to_numpy(); boot=[]
    for _ in range(300):
        ix=rng.integers(0,len(ty),len(ty)); boot.append(average_precision_score(ty[ix],tp[ix]))
    report['test_ap_bootstrap_95_interval']=np.quantile(boot,[.025,.975]).tolist()
    report['sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'data').glob('*.csv')}
    art=ROOT/'artifacts'; art.mkdir(exist_ok=True)
    joblib.dump(dict(model=model,threshold=threshold,features=FEATURES,bounds={c:[float(df.loc[fit,c].min()),float(df.loc[fit,c].max())] for c in NUMERIC}),art/'model.joblib')
    (art/'metrics.json').write_text(json.dumps(report,indent=2))
    sample=df.loc[test].sample(150,random_state=42).copy(); sample['risk']=model.predict_proba(sample[FEATURES])[:,1]; sample.to_csv(art/'demo_snapshots.csv',index=False)
    (art/'demo_events.json').write_text((ROOT/'data/demo_events.json').read_text())
    print(json.dumps({k:report[k] for k in ['selected','threshold','split_counts','test','shifted_test']},indent=2))
if __name__=='__main__': main()
