#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path
root=Path(__file__).parent
out=root/'calculated-las-vegas.json'
subprocess.run([sys.executable,str(root/'update_nascar.py'),'--league',str(root/'test-data'/'kansas-baseline.json'),'--race',str(root/'test-data'/'race-input-las-vegas.json'),'--output',str(out)],check=True)
got=json.load(open(out)); exp=json.load(open(root/'test-data'/'expected-las-vegas.json'))
checks=[]
checks.append(('races_completed',got['races_completed'],exp['races_completed']))
checks.append(('current_race',got['current_race'],exp['current_race']))
checks.append(('weekly winner',got['weekly_winners'][-1],exp['weekly_winners'][-1]))
checks.append(('team breakdown',got['race_results']['Las Vegas Motor Speedway']['team_breakdown'],exp['race_results']['Las Vegas Motor Speedway']['team_breakdown']))
# Compare standings fields that calculation engine owns.
fields=['rank','team_id','team','weekly_points','segment_points','points','behind','behind_leader','weekly_wins']
gs=[{k:x[k] for k in fields} for x in got['standings']]
es=[{k:x[k] for k in fields} for x in exp['standings']]
checks.append(('standings',gs,es))
failed=[n for n,a,b in checks if a!=b]
if failed:
 print('FAIL:',', '.join(failed)); sys.exit(1)
print('PASS: Calculation engine reproduces the approved Las Vegas Race 7 team scores and standings exactly.')
