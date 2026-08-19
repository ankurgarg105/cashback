from pathlib import Path
from datetime import datetime,timezone
import pandas as pd
from collectors.public_source import fetch
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/"data/sources.csv"; df=pd.read_csv(p); now=datetime.now(timezone.utc).isoformat(); events=[]
for i,row in df.iterrows():
    try:
        _,digest=fetch(row.url); old=str(row.get("content_hash",""))
        changed=bool(old) and digest!=old
        df.loc[i,"last_checked"]=now; df.loc[i,"last_success"]=now; df.loc[i,"content_hash"]=digest
        df.loc[i,"status"]="changed" if changed else "unchanged"
        events.append({"source_id":row.source_id,"changed":changed,"status":"ok"})
    except Exception as e:
        df.loc[i,"last_checked"]=now; df.loc[i,"status"]="error"
        events.append({"source_id":row.source_id,"changed":False,"status":f"error: {e}"})
df.to_csv(p,index=False)
pd.DataFrame(events).to_csv(ROOT/"data/update_report.csv",index=False)
print(pd.DataFrame(events).to_string(index=False))
