#!/usr/bin/env python3
import json,re,sys
from pathlib import Path

class ValidationError(Exception): pass

def load_js(path):
    text=Path(path).read_text(encoding='utf-8')
    m=re.search(r'window\.LEAGUE_DATA\s*=\s*(\{.*\})\s*;?\s*$',text,re.S)
    if not m: raise ValidationError('Could not parse window.LEAGUE_DATA from league-data.js')
    return json.loads(m.group(1))

def need(ok,msg):
    if not ok: raise ValidationError(msg)

def main():
    path=sys.argv[1] if len(sys.argv)>1 else 'league-data.js'
    d=load_js(path)
    races=d.get('races',[]); teams=d.get('teams',[]); standings=d.get('standings',[])
    completed=[r for r in races if r.get('status')=='Completed']
    need(d.get('races_completed')==len(completed), f"races_completed={d.get('races_completed')} but {len(completed)} completed races found")
    need(len(teams)==10, f'Expected 10 teams, found {len(teams)}')
    need(len(standings)==10, f'Expected 10 standings rows, found {len(standings)}')
    race_names=[r['name'] for r in completed]
    need(len(set(race_names))==len(race_names),'Duplicate completed race names found')
    need(completed and d.get('current_race')==completed[-1]['name'],'current_race does not match last completed race')

    team_by_id={t['team_id']:t for t in teams}
    need(len(team_by_id)==10,'Duplicate team_id found')
    for t in teams:
        tid=t['team_id']; roster=t.get('roster',[])
        need(len(roster)==4,f'Team {tid} must have exactly 4 roster cars; found {len(roster)}')
        cars=[r.get('car_number',r.get('car')) for r in roster]
        need(all(c is not None for c in cars),f'Team {tid} has a roster entry without car number')
        need(len(set(cars))==4,f'Team {tid} has duplicate car numbers')
        ws=t.get('weekly_scores',{})
        need(set(ws)==set(race_names),f'Team {tid} weekly_scores race list does not match completed races')
        wp=t.get('weekly_points',[])
        wpmap={x['race']:x['points'] for x in wp}
        need(wpmap==ws,f'Team {tid} weekly_points does not match weekly_scores')
        total=sum(ws.values())
        for key in ('segment_points','segment_total','points'):
            need(t.get(key)==total,f'Team {tid} {key}={t.get(key)} but weekly scores sum to {total}')

    # Weekly team-score tables must reconcile with each team's weekly score.
    wts=d.get('weekly_team_scores',[])
    need(len(wts)==len(completed),f'Expected {len(completed)} weekly_team_scores blocks, found {len(wts)}')
    by_race={x['race']:x for x in wts}
    need(set(by_race)==set(race_names),'weekly_team_scores race list does not match completed races')
    computed_winners=[]
    for idx,r in enumerate(completed,1):
        block=by_race[r['name']]; scores=block.get('scores',[])
        need(len(scores)==10,f"{r['name']}: expected 10 team scores, found {len(scores)}")
        seen=set()
        for row in scores:
            tid=row['team_id']; need(tid in team_by_id,f"{r['name']}: unknown team {tid}")
            need(tid not in seen,f"{r['name']}: duplicate team {tid}"); seen.add(tid)
            pts=row.get('points'); need(row.get('weekly_total')==pts,f"{r['name']}: team {tid} weekly_total mismatch")
            need(team_by_id[tid]['weekly_scores'][r['name']]==pts,f"{r['name']}: team {tid} score disagrees with team weekly_scores")
            if 'qualifying_points' in row and 'race_points' in row:
                need(row['qualifying_points']+row['race_points']==pts,f"{r['name']}: team {tid} qualifying + race points mismatch")
        maxpts=max(x['points'] for x in scores); winners=sorted(x['team_id'] for x in scores if x['points']==maxpts)
        computed_winners.append((r['name'],maxpts,winners))
        need(r.get('winning_score')==maxpts,f"{r['name']}: race winning_score mismatch")

    # Weekly winners table must identify the same score and winner team IDs (supports ties).
    ww=d.get('weekly_winners',[]); need(len(ww)==len(completed),'weekly_winners count mismatch')
    for item,(race,maxpts,winners) in zip(ww,computed_winners):
        need(item.get('race')==race,f'weekly_winners race order mismatch at {race}')
        need(item.get('score')==maxpts,f'{race}: weekly_winners score mismatch')
        text=str(item.get('winner',''))
        for tid in winners: need(re.search(rf'(^|\D){tid}(\D|$)',text) is not None,f'{race}: weekly_winners missing Team {tid}')

    # Standings must be sorted by Segment Points and reconcile to team totals.
    ordered=sorted(teams,key=lambda t:(-t['segment_points'],t['team_id']))
    leader=ordered[0]['segment_points']
    for rank,(s,t) in enumerate(zip(standings,ordered),1):
        need(s['rank']==rank,f'Standings rank field mismatch at row {rank}')
        need(s['team_id']==t['team_id'],f'Standings row {rank} has wrong team')
        need(s['segment_points']==t['segment_points'] and s['points']==t['segment_points'],f"Team {t['team_id']} standings total mismatch")
        last=t['weekly_scores'][completed[-1]['name']]
        need(s.get('weekly_points')==last,f"Team {t['team_id']} standings weekly_points mismatch")
        gap=leader-t['segment_points']
        need(s.get('behind')==gap,f"Team {t['team_id']} behind mismatch")
        need(s.get('behind_leader')==-gap,f"Team {t['team_id']} behind_leader mismatch")

    # Race results should contain one block for every completed race when present.
    rr=d.get('race_results',[])
    need(len(rr)==len(completed),f'Expected {len(completed)} race_results blocks, found {len(rr)}')

    print('STEP 4A LIVE-DATA VALIDATION PASSED')
    print(f"Segment {d['segment']} | completed races: {len(completed)}")
    print(f"Current race: {d['current_race']} | next race: {d['next_race']}")
    print(f"Leader: Team {ordered[0]['team_id']} {ordered[0]['name']} — {leader} Segment Points")
    print('Validated: 10 teams, four-car rosters, weekly histories, weekly team tables, winners, Segment Points, standings, and race-results count.')

if __name__=='__main__':
    try: main()
    except (ValidationError,KeyError,TypeError,ValueError,json.JSONDecodeError) as e:
        print(f'STEP 4A VALIDATION FAILED: {e}',file=sys.stderr); sys.exit(1)
