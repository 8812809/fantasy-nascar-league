#!/usr/bin/env python3
import json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUTDIR=ROOT/'generated'
OUTDIR.mkdir(parents=True, exist_ok=True)
OUT=OUTDIR/'league-data.js'
TMP=OUTDIR/'league-data.json'
subprocess.run([sys.executable,str(ROOT/'update_nascar.py'),'--league',str(ROOT/'test-data/kansas-baseline.json'),'--race',str(ROOT/'test-data/race-input-las-vegas.json'),'--output',str(TMP)],check=True)
d=json.loads(TMP.read_text(encoding='utf-8'))
OUT.write_text('window.LEAGUE_DATA = '+json.dumps(d,indent=2)+';\n',encoding='utf-8')
print(f'Generated dry-run file: {OUT}')
