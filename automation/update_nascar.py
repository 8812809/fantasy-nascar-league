#!/usr/bin/env python3
import argparse, json, copy, sys
from pathlib import Path

def qpts(start):
    if not 1 <= start <= 40: raise ValueError(f'Invalid start: {start}')
    return 41-start

def rpts(finish):
    if not 1 <= finish <= 40: raise ValueError(f'Invalid finish: {finish}')
    return 123-(3*finish)

def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,obj): Path(p).write_text(json.dumps(obj,indent=2)+"\n",encoding='utf-8')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--league',required=True)
    ap.add_argument('--race',required=True)
    ap.add_argument('--output',required=True)
    a=ap.parse_args()
    d=load(a.league); race=load(a.race)
    if len(d.get('teams',[])) != 10: raise SystemExit('ERROR: expected 10 teams')
    bycar={int(x['car']):x for x in race['results']}
    if len(bycar)!=len(race['results']): raise SystemExit('ERROR: duplicate car in race input')
    breakdown=[]
    for t in d['teams']:
        roster=t.get('roster',[])
        if len(roster)!=4: raise SystemExit(f"ERROR: Team {t['id']} does not have 4 cars")
        drivers=[]; q=rp=0
        for r in roster:
            car=int(r.get('car_number',r.get('car')))
            if car not in bycar: raise SystemExit(f"ERROR: missing race result for car #{car} on Team {t['id']}")
            x=bycar[car]; qp=qpts(int(x['start'])); rr=rpts(int(x['finish']))
            drivers.append({'car':car,'driver':x['driver'],'start':int(x['start']),'qualifying_points':qp,'finish':int(x['finish']),'race_points':rr,'total':qp+rr})
            q+=qp; rp+=rr
        total=q+rp
        breakdown.append({'team_id':t['id'],'team':t['name'],'display_name':f"Team {t['id']} {t['name']}",'qualifying_points':q,'race_points':rp,'points':total,'weekly_total':total,'drivers':drivers})
    breakdown.sort(key=lambda x:(-x['points'],x['team_id']))
    for i,x in enumerate(breakdown,1): x['rank']=i
    win=breakdown[0]['points']; winners=[x for x in breakdown if x['points']==win]
    winner_text=' & '.join(f"{x['team_id']} {x['team']}" for x in winners)
    winner_card=' & '.join(f"Team {x['team_id']} {x['team']}" for x in winners)
    name=race['name']
    for t in d['teams']:
        b=next(x for x in breakdown if x['team_id']==t['id'])
        t.setdefault('weekly_scores',{})[name]=b['points']
        t.setdefault('weekly_points',[]).append({'race':name,'points':b['points']})
        t['segment_points']=t.get('segment_points',0)+b['points']; t['segment_total']=t['segment_points']; t['points']=t['segment_points']
    d['races'].append({'race_number':race['race_number'],'name':name,'date':race['date'],'status':'Completed','weekly_winner':winner_card,'winning_score':win})
    d['races_completed']=race['race_number']; d['current_race']=name; d['next_race']=race.get('next_race','TBD'); d['last_updated']=race['date']
    d.setdefault('weekly_winners',[]).append({'race_number':race['race_number'],'race':name,'winner':winner_text,'score':win})
    
    wts=d.setdefault('weekly_team_scores',[])
    entry={'race_number':race['race_number'],'race':name,'scores':[{k:x[k] for k in ('team_id','team','display_name','qualifying_points','race_points','points','weekly_total','rank')} for x in breakdown]}
    if isinstance(wts,list): wts.append(entry)
    else: wts[name]=entry['scores']
    d.setdefault('race_results',{})[name]={'team_breakdown':breakdown}
    for s in d.get('schedule',[]):
        if s.get('race_number')==race['race_number']: s['status']='Completed'
    oldwins={s['team_id']:s.get('weekly_wins',0) for s in d.get('standings',[])}
    share=1/len(winners)
    for w in winners: oldwins[w['team_id']]=oldwins.get(w['team_id'],0)+share
    standings=[]
    for t in d['teams']:
        b=next(x for x in breakdown if x['team_id']==t['id'])
        row={'team_id':t['id'],'team':t['name'],'display_name':f"Team {t['id']} {t['name']}",'weekly_points':b['points'],'segment_points':t['segment_points'],'points':t['segment_points'],'weekly_wins':oldwins.get(t['id'],0)}
        slug=name.lower().replace(' motor speedway','').replace(' speedway','').replace(' ','_').replace('-','_')
        row[slug]=b['points']
        standings.append(row)
    standings.sort(key=lambda x:(-x['segment_points'],x['team_id'])); leader=standings[0]['segment_points']
    for i,s in enumerate(standings,1):
        s['rank']=i; s['behind']=leader-s['segment_points']; s['behind_leader']=s['segment_points']-leader
    d['standings']=standings
    dump(a.output,d)
    print(f"PASS: {name} calculated. Winner: {winner_card}, {win} points. Leader: Team {standings[0]['team_id']} {standings[0]['team']}, {leader} points.")
if __name__=='__main__': main()
