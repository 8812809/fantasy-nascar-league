#!/usr/bin/env python3
"""Fetch official NASCAR Cup race data and normalize it for the fantasy engine.

Primary source: NASCAR's public CDN Weekend_Race.json.
Fails closed on incomplete/duplicate/invalid fields.
"""
import argparse, json, re, sys, urllib.request
from pathlib import Path

UA='Fantasy-NASCAR-League-Automation/1.0'

def get_json(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=30) as r:
        return json.load(r)

def walk(obj):
    if isinstance(obj,dict):
        yield obj
        for v in obj.values(): yield from walk(v)
    elif isinstance(obj,list):
        for v in obj: yield from walk(v)

def pick(d,*keys):
    for k in keys:
        if k in d and d[k] not in (None,''): return d[k]

def as_int(x):
    try: return int(str(x).strip())
    except: return None

def extract_rows(payload):
    candidates=[]
    for d in walk(payload):
        if not isinstance(d,dict): continue
        car=pick(d,'vehicle_number','car_number','car','number')
        name=pick(d,'driver_fullname','driver_full_name','full_name','driver_name','driver')
        start=pick(d,'starting_position','start_position','starting_pos','start')
        finish=pick(d,'finishing_position','finish_position','finishing_pos','finish','position')
        ci=as_int(car); si=as_int(start); fi=as_int(finish)
        if ci is not None and name and si and fi and 1<=si<=40 and 1<=fi<=40:
            candidates.append({'car':ci,'driver':str(name).strip(),'start':si,'finish':fi})
    # Deduplicate repeated nested representations by car/start/finish/name.
    uniq={}
    for x in candidates:
        uniq[(x['car'],x['start'],x['finish'])]=x
    rows=list(uniq.values())
    # If same car appears in multiple records, choose only if one consistent tuple exists.
    bycar={}
    for x in rows: bycar.setdefault(x['car'],[]).append(x)
    out=[]
    for car,xs in bycar.items():
        sig={(x['start'],x['finish'],x['driver']) for x in xs}
        if len(sig)==1: out.append(xs[0])
    out.sort(key=lambda x:x['finish'])
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--year',type=int,required=True)
    ap.add_argument('--cup-race-number',type=int,required=True,help='NASCAR Cup season race number, e.g. 31 for 2026 Las Vegas fall race')
    ap.add_argument('--fantasy-race-number',type=int,required=True)
    ap.add_argument('--name',required=True)
    ap.add_argument('--date',required=True)
    ap.add_argument('--next-race',required=True)
    ap.add_argument('--output',required=True)
    ap.add_argument('--source-url')
    a=ap.parse_args()
    url=a.source_url or f'https://cf.nascar.com/cacher/{a.year}/1/{a.year}-{a.cup_race_number:02d}/Weekend_Race.json'
    print('Fetching official NASCAR race data:',url)
    try: payload=get_json(url)
    except Exception as e: raise SystemExit(f'ERROR: unable to fetch NASCAR data: {e}')
    rows=extract_rows(payload)
    if not (30 <= len(rows) <= 40):
        raise SystemExit(f'ERROR: expected a complete Cup field (30-40 cars); extracted {len(rows)}')
    starts=[x['start'] for x in rows]; finishes=[x['finish'] for x in rows]; cars=[x['car'] for x in rows]
    if len(set(cars))!=len(cars): raise SystemExit('ERROR: duplicate car numbers')
    if len(set(starts))!=len(starts): raise SystemExit('ERROR: duplicate starting positions')
    if len(set(finishes))!=len(finishes): raise SystemExit('ERROR: duplicate finishing positions')
    if sorted(finishes)!=list(range(1,len(rows)+1)): raise SystemExit('ERROR: finishing positions are not contiguous')
    if sorted(starts)!=list(range(1,len(rows)+1)): raise SystemExit('ERROR: starting positions are not contiguous')
    out={'race_number':a.fantasy_race_number,'name':a.name,'date':a.date,'next_race':a.next_race,
         'source':{'provider':'NASCAR','url':url,'cup_race_number':a.cup_race_number},'results':rows}
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(f'PASS: fetched {len(rows)} official NASCAR results. Winner: #{rows[0]["car"]} {rows[0]["driver"]}, started {rows[0]["start"]}.')
if __name__=='__main__': main()
