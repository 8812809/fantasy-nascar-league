#!/usr/bin/env python3
"""Step 5B Jayski access test and race-page discovery."""
import argparse, json, re, sys
from html import unescape
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

BASE="https://www.jayski.com"
INDEX=f"{BASE}/nascar-cup-series/2026-nascar-cup-series-race-results/"

def die(s):
    print("ERROR:",s,file=sys.stderr); raise SystemExit(1)

def get(url):
    req=Request(url,headers={
      "User-Agent":"Mozilla/5.0 (compatible; FantasyNASCARLeague/1.0; GitHub-Actions)",
      "Accept":"text/html,application/xhtml+xml"
    })
    try:
        with urlopen(req,timeout=30) as r:
            return r.geturl(), r.read().decode("utf-8","replace")
    except Exception as e: die(f"Unable to fetch Jayski: {e}")

def textify(h):
    h=re.sub(r"<script\b[^>]*>.*?</script>"," ",h,flags=re.I|re.S)
    h=re.sub(r"<style\b[^>]*>.*?</style>"," ",h,flags=re.I|re.S)
    h=re.sub(r"<[^>]+>"," | ",h)
    return re.sub(r"\s+"," ",unescape(h).replace("\xa0"," "))

def links(h,base):
    out=[]
    for m in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',h,flags=re.I|re.S):
        label=re.sub(r"<[^>]+>"," ",m.group(2))
        label=re.sub(r"\s+"," ",unescape(label)).strip()
        out.append((label,urljoin(base,m.group(1))))
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--race-number",type=int,default=31)
    p.add_argument("--track",default="Las Vegas Motor Speedway")
    p.add_argument("--output",default="automation/test-data/jayski-las-vegas-discovery.json")
    a=p.parse_args()

    final,index=get(INDEX)
    t=textify(index)
    if f"Race #{a.race_number} of 36".lower() not in t.lower(): die("Jayski index does not show expected Cup race number")
    if a.track.lower() not in t.lower(): die("Jayski index does not show expected track")
    if "South Point 400".lower() not in t.lower(): die("Jayski index does not show South Point 400")

    # Discover Las Vegas fall race page from index links.
    all_links=links(index,final)
    race_pages=[u for label,u in all_links if "las-vegas" in u.lower() and "fall" in u.lower() and "race-page" in u.lower()]
    race_page=race_pages[-1] if race_pages else f"{BASE}/nascar-cup-series/2026-nascar-cup-series-fall-las-vegas-race-page/"
    rp_url,rp=get(race_page)
    rpt=textify(rp)
    for needle in ["Sunday, October 4, 2026",a.track,"South Point 400"]:
        if needle.lower() not in rpt.lower(): die(f"Race page identity check failed: {needle}")

    rp_links=links(rp,rp_url)
    result_links=[u for label,u in rp_links if label.strip().lower()=="race results"]
    lineup_links=[u for label,u in rp_links if label.strip().lower()=="starting lineup"]
    qual_links=[u for label,u in rp_links if label.strip().lower()=="qualifying results"]

    # It is okay if Jayski renders a link through dynamic markup; record page access
    # and require at least result/lineup words to be present.
    if "Race Results".lower() not in rpt.lower(): die("Race Results resource not advertised on Jayski race page")
    if "Starting Lineup".lower() not in rpt.lower(): die("Starting Lineup resource not advertised on Jayski race page")

    data={
      "source":"Jayski",
      "indexUrl":final,
      "racePageUrl":rp_url,
      "raceNumber":a.race_number,
      "raceName":"South Point 400",
      "track":a.track,
      "date":"2026-10-04",
      "raceResultsLinks":result_links,
      "startingLineupLinks":lineup_links,
      "qualifyingResultsLinks":qual_links,
      "accessPassed":True
    }
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    print("PASS: GitHub-access-style request reached Jayski.")
    print("PASS: Jayski index identifies Race #31, South Point 400, Las Vegas.")
    print("PASS: Jayski race page advertises Race Results and Starting Lineup.")
    print("Race results links discovered:",len(result_links))
    print("Starting lineup links discovered:",len(lineup_links))
    print("Wrote",out)

if __name__=="__main__": main()
