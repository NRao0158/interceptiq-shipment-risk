from datetime import datetime

def at_hold(events,hold_id,context):
    """Build scan-history features using observations strictly before a stop."""
    hold=next((e for e in events if e['event_id']==hold_id),None)
    if hold is None or hold['kind'] not in ['HOLD','REJECT']: raise ValueError('Unknown stop event.')
    at=datetime.fromisoformat(hold['occurred_at'])
    previous=[datetime.fromisoformat(e['occurred_at']) for e in events if e['package_id']==hold['package_id'] and e['kind']=='SCAN' and datetime.fromisoformat(e['occurred_at'])<at]
    elapsed=[(at-t).total_seconds()/60 for t in previous]
    return dict(**context,scans_last30=sum(t<=30 for t in elapsed),minutes_since_scan=min(elapsed) if elapsed else 1440.,hour=at.hour,source=hold['source'],condition=hold['kind'])
