
# 🐕 Punters AId — AU Greyhound Predictor (Live)

Polished, sell-ready Streamlit app with:
- Splash screen (logo + spinner) that fades automatically.
- One-time-per-session disclaimer gate.
- Black & gold theme with sticky footer.
- Menus: **Date → Track → Race**.
- Predictions: **Winner, Top 4, win probability, predicted times & margins**.
- **Preloaded** predictions for **today & tomorrow** (instant demo).
- **Live** auto-refresh via GitHub Actions using free source (TheDogs.com.au).

## Deploy
1) Create a GitHub repo and upload all files to **root**.
2) Add secret: **Settings → Secrets → Actions → New repository secret**
   - Name: `GH_TOKEN`
   - Value: your classic token with `repo` scope.
3) On **Streamlit Cloud**, deploy with main file `app.py`.

## Live Refresh
- `scraper.py` → pulls meetings & fields for today + tomorrow from TheDogs (best-effort).
- `predictor.py` → rule-based predictions (times, margins, win %).
- GitHub Action runs at ~06:00 & ~18:00 AEST (UTC `20:00` & `08:00`) to rebuild `/data/pred_YYYY-MM-DD.json`.
- If scraping is blocked/changed, the app falls back to preloaded predictions.

> Later, you can upgrade `predictor.py` to a trained ML model without changing the UI.
