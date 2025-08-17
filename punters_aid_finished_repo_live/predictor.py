
import os, json, random
from datetime import date, timedelta, datetime

def load_raw_or_fallback(d: date):
    raw_path = f"data/raw_{d.isoformat()}.json"
    if os.path.exists(raw_path):
        with open(raw_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            if raw.get("tracks"): return raw
    preload = f"data/pred_{d.isoformat()}.json"
    if os.path.exists(preload):
        with open(preload, "r", encoding="utf-8") as f:
            pre = json.load(f)
            return {
                "date": d.isoformat(),
                "tracks": { t: { "races": { rn: [
                        {"trap": str(r["trap"]), "name": r["name"]}
                        for r in pre["runners"][t][rn]
                    ] for rn in pre["runners"][t].keys()
                }} for t in pre.get("runners", {}).keys()
                }
            }
    return {"date": d.isoformat(), "tracks": {}}

def mk_seed(day, track, raceNo):
    s = f"{day}-{track}-{raceNo}"
    return abs(hash(s)) % (2**32-1)

def predict_for_day(d: date):
    raw = load_raw_or_fallback(d)
    tracks = raw.get("tracks", {})
    schedule = {}
    runners_blob = {}
    for track, td in tracks.items():
        races = td.get("races", {})
        if not races: continue
        race_nos = sorted(map(int, races.keys()))
        schedule[track] = [{"raceNo": rn} for rn in race_nos]
        runners_blob.setdefault(track, {})
        for rn in race_nos:
            field = races[str(rn)]
            rloc = random.Random(mk_seed(d.isoformat(), track, rn))
            # Ensure 8 runners and unique boxes
            seen=set(); clean=[]
            for r in field[:]:
                t = str(r.get("trap",""))
                if t not in list("12345678") or t in seen: continue
                seen.add(t); clean.append({"trap": t, "name": r.get("name","Unnamed").title()})
            for i in range(1,9):
                if str(i) not in seen:
                    clean.append({"trap": str(i), "name": f"Runner {i}"})
                    seen.add(str(i))
                if len(clean)>=8: break
            # Rule-based: base time varies slightly by track hash
            base = 29.9 + (abs(hash(track)) % 50)/100.0  # 29.90–30.39
            perf = [rloc.random() for _ in range(8)]
            idx = list(range(8))
            idx.sort(key=lambda i: perf[i])
            rows=[]
            for rank, i in enumerate(idx):
                tsec = round(base + rank*0.10 + rloc.uniform(0.00,0.03), 3)
                rows.append({
                    "trap": clean[i]["trap"],
                    "name": clean[i]["name"],
                    "pred_time": tsec,
                    "pred_margin": 0.0,  # temp
                    "win_prob": 1.3**(8-rank)
                })
            # margins & probs
            winner_time = min(r["pred_time"] for r in rows)
            s = sum(r["win_prob"] for r in rows)
            for r in rows:
                r["pred_margin"] = round(r["pred_time"] - winner_time, 3)
                r["win_prob"] = round(r["win_prob"]/s, 4)
            rows = sorted(rows, key=lambda x: (x["pred_time"], -x["win_prob"]))
            runners_blob[track][str(rn)] = rows
    out = {
        "last_updated": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "schedule": schedule,
        "runners": runners_blob
    }
    out_path = f"data/pred_{d.isoformat()}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    return out_path

def main():
    today = date.today()
    tomorrow = today + timedelta(days=1)
    for d in [today, tomorrow]:
        print("Wrote", predict_for_day(d))

if __name__ == "__main__":
    main()
