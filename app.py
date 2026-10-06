import json
import pandas as pd
import streamlit as st
import altair as alt
from interceptiq.simulation import ROOT,FEATURES,order
from interceptiq.predict import bundle,score
from interceptiq.schemas import Snapshot
from interceptiq.rules import detect

st.set_page_config(page_title='InterceptIQ | Shipment Risk',page_icon='↗',layout='wide')
st.markdown('<style>h1{letter-spacing:-1.5px}[data-testid="stMetric"]{background:#172535;padding:18px;border-radius:12px;border:1px solid #2c4054}</style>',unsafe_allow_html=True)
st.caption('INTERCEPTIQ / SHIPMENT RISK LAB')
st.title('Prioritize the hold. Prevent the escape.')
st.write('Estimate movement-before-clearance risk over 60 simulated minutes. Confirm violations from event history.')
st.info('Independent portfolio simulation. Model metrics describe this simulator, not a carrier or brokerage operation. Public demo has no live API, database, or broker connection.')

@st.cache_data
def load():
    return pd.read_csv(ROOT/'artifacts/demo_snapshots.csv'),json.loads((ROOT/'artifacts/metrics.json').read_text()),json.loads((ROOT/'artifacts/demo_events.json').read_text())

df,report,events=load(); b=bundle()
one,two,three,four=st.tabs(['Risk studio','Event replay','Model evidence','Batch predictions'])
with one:
    st.subheader('Risk at the moment a stop is applied')
    chosen=st.selectbox('Start from a held-out synthetic shipment',df.package_id.tolist())
    sample=df[df.package_id==chosen].iloc[0]
    a,c,d=st.columns(3)
    with a:
        queue_load=st.slider('Facility queue load',0.,1.,float(sample.queue_load),step=.01)
        staff_ratio=st.slider('Staffing / planned staffing',.25,1.5,float(sample.staff_ratio),step=.01)
        departure=st.number_input('Scheduled departure in minutes',min_value=0.,max_value=1440.,value=float(sample.minutes_to_departure))
    with c:
        scans=st.number_input('Scans in the past 30 minutes',min_value=0,max_value=100,value=int(sample.scans_last30))
        since=st.number_input('Minutes since last scan',min_value=0.,max_value=1440.,value=float(sample.minutes_since_scan))
        service=st.selectbox('Service',['economy','priority','express'],index=['economy','priority','express'].index(sample.service))
    with d:
        source=st.selectbox('Stop source',['screening','brokerage'],index=['screening','brokerage'].index(sample.source))
        condition=st.selectbox('Stop condition',['HOLD','REJECT'],index=['HOLD','REJECT'].index(sample.condition))
        hour=st.number_input('Hour (UTC)',min_value=0,max_value=23,value=int(sample.hour))
    snapshot=Snapshot(queue_load=queue_load,staff_ratio=staff_ratio,scans_last30=scans,minutes_since_scan=since,minutes_to_departure=departure,route_hops=int(sample.route_hops),weight_kg=float(sample.weight_kg),hour=hour,source=source,condition=condition,service=service).model_dump()
    result=score(snapshot)
    left,right=st.columns(2)
    left.metric('Movement before clearance / 60 min',f"{result['risk']:.1%}")
    right.metric('Priority','Inspect now' if result['prioritize'] else 'Standard hold handling')
    st.caption(f"Uncalibrated model score. Validation-selected threshold: {result['threshold']:.2f}. Every active hold still requires normal enforcement regardless of score.")
    if result['out_of_range_features']: st.warning('Outside training ranges: '+', '.join(result['out_of_range_features']))
    st.write('Feature importance reflects validation ranking performance, not a causal maintenance recommendation.')
    st.bar_chart(pd.DataFrame(report['importance']).set_index('feature').head(7))
    st.download_button('Download prediction JSON',json.dumps({'input':snapshot,'prediction':result},indent=2),'prediction.json','application/json')

with two:
    st.subheader('Confirmed violations: deterministic rules')
    st.write('Scripted demo: 1,000 packages, 500 screening events, 300 brokerage events, exactly 50 escape scenarios. This scripted fixture is excluded from ML training and evaluation.')
    mode=st.radio('Replay scenario',['Movement after HOLD','Normal flow','Active HOLD without movement'],horizontal=True)
    pid={'Movement after HOLD':'DEMO-0000','Normal flow':'DEMO-0800','Active HOLD without movement':'DEMO-0050'}[mode]
    trajectory=order([e for e in events if e['package_id']==pid])
    step=st.slider('Events received',1,len(trajectory),len(trajectory))
    visible=trajectory[:step]; alerts=detect(visible)
    st.dataframe(pd.DataFrame(visible),hide_index=True)
    if alerts:
        st.error('Confirmed movement while a stop condition was active.')
        st.dataframe(pd.DataFrame(alerts.values()),hide_index=True)
    else: st.success('No confirmed intercept violation in the events received so far.')
    st.caption('Replay uses the same rule engine as the API. Durable storage and RabbitMQ publication run in the local service stack, not this public demo.')
    st.download_button('Download full ingestion fixture',json.dumps(events),'demo_events.json','application/json')

with three:
    st.subheader('Later days and unseen facilities')
    st.write('Earlier days 0–39 train; days 40–49 select model and thresholds; days 50–59 test. Each package contributes one snapshot. IDs, future events and labels are excluded from model inputs.')
    st.dataframe(pd.DataFrame(report['test']).T,width='stretch')
    st.write('Stress test: 3,000 packages at unseen facilities, with a hidden shift toward worse compliance. Facility identity is not a model input.')
    st.dataframe(pd.DataFrame(report['shifted_test']).T,width='stretch')
    st.caption('The future-day test uses the same synthetic process as training. It measures simulator generalization, not real-world validity. The departure heuristic checks scheduled departure <20 minutes.')
    st.write('Test average-precision bootstrap interval:',report['test_ap_bootstrap_95_interval'])
    st.download_button('Download experiment report',json.dumps(report,indent=2),'metrics.json','application/json')

with four:
    st.write('Upload numeric and categorical context available when the stop is applied. Never include future movement or clearance times as inputs.')
    st.code(','.join(FEATURES))
    st.download_button('Download sample inputs',df[FEATURES].head(20).to_csv(index=False),'sample_inputs.csv','text/csv')
    uploaded=st.file_uploader('Snapshot CSV',type=['csv'])
    if uploaded:
        try:
            batch=pd.read_csv(uploaded)
            if len(batch)>5000: raise ValueError('Limit batches to 5,000 packages.')
            output=[]
            for i,row in batch.iterrows():
                snap=Snapshot.model_validate(row.to_dict()).model_dump()
                output.append(dict(row=int(i),**score(snap)))
            result_df=pd.DataFrame(output)
            st.dataframe(result_df,hide_index=True)
            st.download_button('Export scores',result_df.to_csv(index=False),'scores.csv','text/csv')
        except (ValueError,TypeError) as exc: st.error(str(exc))
