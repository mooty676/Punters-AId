
# See detailed version in previous tool call; keeping identical here
import os, time, json, re
from datetime import date, timedelta, datetime
import requests
from bs4 import BeautifulSoup

BASE = "https://www.thedogs.com.au"
HEADERS = {"User-Agent":"Mozilla/5.0","Accept-Language":"en-AU,en;q=0.9"}
S = requests.Session(); S.headers.update(HEADERS)

def fetch(url, retries=3, sleep=1.5):
    for i in range(retries):
        try:
            r = S.get(url, timeout=20)
            if r.status_code==200 and len(r.text)>1000: return r.text
        except requests.RequestException: pass
        time.sleep(sleep*(i+1))
    return ""

def parse_meetings_for_day(day: date):
    url = f"{BASE}/racing/{day.isoformat()}"
    html = fetch(url) or fetch(f"{BASE}/racing")
    if not html: return []
    soup = BeautifulSoup(html, "lxml")
    meetings = []
    for a in soup.select('a[href*="/racing/"]'):
        href = a.get("href","")
        if re.match(r"^/racing/\d{4}-\d{2}-\d{2}/", href):
            track = a.get_text(strip=True)
            if track and len(track)<60:
                meetings.append({"track": track, "url": BASE+href})
    uniq = {}; [uniq.setdefault(m["url"], m) for m in meetings]
    return list(uniq.values())

def parse_meeting_fields(url: str):
    html = fetch(url)
    if not html: return {}
    soup = BeautifulSoup(html, "lxml")
    title = soup.find(["h1","h2"])
    track_name = title.get_text(strip=True) if title else "Unknown Track"
    races = {}
    for card in soup.select('a[href*="/race/"], div.race-card, section.race-card'):
        txt = card.get_text(" ", strip=True).lower()
        m = re.search(r"race\s*(\d+)", txt)
        if not m: continue
        rno = m.group(1)
        runners = []
        for row in card.select("tr"):
            cells = [c.get_text(" ", strip=True) for c in row.find_all(["td","th"])]
            if len(cells)<2: continue
            mbox = re.search(r"\b([1-8])\b", " ".join(cells))
            name = None
            for c in cells:
                if len(c)>=3 and not re.search(r"^\d+$", c) and "trainer" not in c.lower():
                    name = c.title(); break
            if mbox and name:
                runners.append({"trap": mbox.group(1), "name": name})
        if not runners:
            for li in card.select("li, div.runner"):
                t = li.get_text(" ", strip=True)
                mbox = re.search(r"\bBox\s*([1-8])\b|\b([1-8])\b", t, re.I)
                mname = re.search(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+", t)
                if mbox and mname:
                    boxnum = mbox.group(1) or mbox.group(2)
                    runners.append({"trap": boxnum, "name": mname.group(0)})
        if rno and runners:
            seen=set(); rr=[]
            for r in runners:
                t = str(r["trap"])
                if t in seen: continue
                seen.add(t); rr.append(r)
            races[str(int(rno))] = rr
    return {"track": track_name, "races": races}

def build_day_raw(day: date, out_path: str):
    meetings = parse_meetings_for_day(day)
    payload = {"date": day.isoformat(), "tracks": {}}
    for m in meetings:
        details = parse_meeting_fields(m["url"])
        track = details.get("track") or m["track"]
        races = details.get("races", {})
        if races:
            payload["tracks"][track] = {"races": races}
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    return payload

def main():
    today = date.today()
    tomorrow = today + timedelta(days=1)
    for d in [today, tomorrow]:
        out = f"data/raw_{d.isoformat()}.json"
        try:
            data = build_day_raw(d, out)
            print(f"Built raw for {d}: {len(data.get('tracks',{}))} tracks")
        except Exception as e:
            print(f"Error building raw for {d}: {e}")

if __name__ == "__main__":
    main()
