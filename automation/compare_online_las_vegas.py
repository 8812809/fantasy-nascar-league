#!/usr/bin/env python3
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parent
f=json.loads((R/'generated'/'race-input-las-vegas-online.json').read_text())
e=json.loads((R/'test-data'/'race-input-las-vegas.json').read_text())
def norm(d): return sorted((int(x['car']),int(x['start']),int(x['finish'])) for x in d['results'])
if norm(f)!=norm(e):
    a=set(norm(f)); b=set(norm(e))
    print('ERROR: online NASCAR data did not match approved Las Vegas input')
    print('Only online:',sorted(a-b)[:10]); print('Only approved:',sorted(b-a)[:10]); sys.exit(1)
print(f'PASS: online NASCAR data matches approved Las Vegas input for {len(e["results"])} cars.')
