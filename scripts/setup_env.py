from pathlib import Path
import secrets

p=Path(__file__).resolve().parents[1]/'.env'
if p.exists(): raise SystemExit('Existing .env preserved.')
p.write_text('DB_PASSWORD='+secrets.token_urlsafe(24)+'\nMQ_PASSWORD='+secrets.token_urlsafe(24)+'\n')
print('Created local .env with generated credentials. Do not commit or share it.')
