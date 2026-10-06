import argparse,json
from pathlib import Path
from urllib.request import Request,urlopen
from interceptiq.simulation import ROOT

def main():
    p=argparse.ArgumentParser(); p.add_argument('--url',default='http://127.0.0.1:8000'); p.add_argument('--file',type=Path,default=ROOT/'artifacts/demo_events.json'); args=p.parse_args()
    events=json.loads(args.file.read_text()); changes=0
    for e in events:
        req=Request(args.url+'/sources/'+e['source']+'/events',data=json.dumps(e).encode(),headers={'Content-Type':'application/json'},method='POST')
        with urlopen(req,timeout=20) as response: changes+=len(json.load(response)['changes'])
    with urlopen(args.url+'/alerts?limit=10000') as response: alerts=json.load(response)
    print(json.dumps({'events_submitted':len(events),'changes_this_run':changes,'active_alerts':sum(a['status']!='retracted' for a in alerts)},indent=2))
if __name__=='__main__': main()
