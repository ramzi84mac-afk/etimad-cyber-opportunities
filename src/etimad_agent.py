import json, os, re, sys
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"

def tidy(v):
    if v is None: return ""
    if isinstance(v, dict): return str(v.get("name") or v.get("title") or "")
    return re.sub(r"\\s+", " ", str(v)).strip()

def pick(x, *keys):
    for k in keys:
        if x.get(k) not in (None, "", [], {}): return tidy(x[k])
    return ""

def items(payload):
    if isinstance(payload, list): return payload
    for key in ("data", "results", "items", "tenders"):
        value = payload.get(key) if isinstance(payload, dict) else None
        if isinstance(value, list): return value
        if isinstance(value, dict):
            for nested in ("data", "results", "items"):
                if isinstance(value.get(nested), list): return value[nested]
    raise ValueError("Tender records were not found in the API response")

def fetch():
    key = os.getenv("TENDERS_API_KEY", "").strip()
    if not key: raise RuntimeError("Missing GitHub secret TENDERS_API_KEY")
    url = os.getenv("TENDERS_API_URL") or "https://api.tendersalerts.com/integration/tenders"
    headers = {"Authorization": f"Bearer {key}", "X-API-Key": key, "Accept": "application/json"}
    all_rows = []
    for page in range(1, 101):
        r = requests.get(url, headers=headers, params={"page": page}, timeout=45)
        r.raise_for_status()
        batch = items(r.json())
        all_rows.extend(z for z in batch if isinstance(z, dict))
        if len(batch) < 10: break
    return all_rows

def main():
    OUT.mkdir(exist_ok=True)
    cfg = json.loads((ROOT / "config/keywords.json").read_text(encoding="utf-8"))
    result = []
    raw = fetch()
    for x in raw:
        row = {
            "id": pick(x, "id", "tender_id", "reference_number"),
            "tender_name": pick(x, "title", "name", "tender_name"),
            "agency": pick(x, "agency", "agency_name", "government_entity"),
            "description": pick(x, "description", "purpose", "summary", "scope"),
            "publish_date": pick(x, "publish_date", "published_at"),
            "submission_deadline": pick(x, "deadline", "submission_deadline", "last_offer_date"),
            "status": pick(x, "status", "tender_status"),
            "tender_type": pick(x, "type", "tender_type"),
            "url": pick(x, "url", "link", "tender_url")
        }
        text = " ".join(row.values()).lower()
        if any(k.lower() in text for k in cfg["exclude"]): continue
        hits, streams = [], []
        for stream, words in cfg["categories"].items():
            found = [w for w in words if w.lower() in text]
            if found: streams.append(stream); hits += found
        if hits:
            row.update(relevance_score=len(set(hits)), revenue_stream=" | ".join(streams), matched_keywords=", ".join(sorted(set(hits))))
            result.append(row)
    df = pd.DataFrame(result).drop_duplicates(subset=["id", "tender_name", "agency"])
    df.to_csv(OUT / "cyber_opportunities.csv", index=False, encoding="utf-8-sig")
    df.to_excel(OUT / "cyber_opportunities.xlsx", index=False)
    (OUT / "latest_run.json").write_text(json.dumps({"status":"success","received":len(raw),"saved":len(df),"time":datetime.now(timezone.utc).isoformat()}, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    try: main()
    except Exception as e:
        OUT.mkdir(exist_ok=True)
        (OUT / "latest_run.json").write_text(json.dumps({"status":"failed","error":str(e)}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(e, file=sys.stderr); raise
