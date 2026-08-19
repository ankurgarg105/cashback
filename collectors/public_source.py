from hashlib import sha256
from datetime import datetime, timezone
import requests
HEADERS={"User-Agent":"CardOptimizerIndiaDataBot/0.1 (GitHub Actions public-source monitor)"}
def fetch(url):
    r=requests.get(url,headers=HEADERS,timeout=30)
    r.raise_for_status()
    text=r.text
    return text,sha256(text.encode("utf-8",errors="ignore")).hexdigest()
def utc_now(): return datetime.now(timezone.utc).isoformat()
