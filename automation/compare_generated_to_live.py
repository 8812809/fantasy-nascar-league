#!/usr/bin/env python3
import json,re,sys
from pathlib import Path

def load_js(p):
 t=Path(p).read_text(encoding='utf-8'); m=re.search(r'window\.LEAGUE_DATA\s*=\s*(\{.*\})\s*;?\s*$',t,re.S)
 if not m: raise SystemExit(f'Could not parse {p}')
 return json.loads(m.group(1))

g=load_js(sys.argv[1] if len(sys.argv)>1 else 'automation/generated-league-data.js')
l=load_js(sys.argv[2] if len(sys.argv)>2 else 'league-data.js')
r='Las Vegas Motor Speedway'
checks=[]
for k in ('races_completed','current_race','next_race'):
 checks.append((k,g.get(k),l.get(k)))
checks.append(('Las Vegas race card',g['races'][-1],l['races'][-1]))
checks.append(('Las Vegas weekly winner',g['weekly_winners'][-1],l['weekly_winners'][-1]))
checks.append(('Las Vegas team table',g['weekly_team_scores'][-1],l['weekly_team_scores'][-1]))
checks.append(('Las Vegas race breakdown',g['race_results'][r],l['race_results'][r]))
team_fields=('team_id','name','weekly_scores','weekly_points','segment_points','segment_total','points','locked','change_status')
gt=[{k:t.get(k) for k in team_fields} for t in sorted(g['teams'],key=lambda x:x['team_id'])]
lt=[{k:t.get(k) for k in team_fields} for t in sorted(l['teams'],key=lambda x:x['team_id'])]
checks.append(('team totals/history',gt,lt))
stand_fields=('rank','team_id','team','display_name','weekly_points','las_vegas','segment_points','points','weekly_wins','behind','behind_leader')
gs=[{k:s.get(k) for k in stand_fields} for s in g['standings']]
ls=[{k:s.get(k) for k in stand_fields} for s in l['standings']]
checks.append(('standings',gs,ls))
failed=[]
for name,a,b in checks:
 if a!=b: failed.append(name)
if failed:
 print('STEP 4B COMPARISON FAILED: '+', '.join(failed),file=sys.stderr); sys.exit(1)
print('STEP 4B GENERATED DATA MATCHES THE APPROVED LIVE LAS VEGAS DATA.')
print('No live file was changed.')
