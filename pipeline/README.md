# Fridgie video pipeline

Turns a locked plan from the **Fridgie Bot Room** into a 9:16 video in the house style (real app screens in a phone, coloured scene backgrounds, white headline with one yellow keyword, navy end card, music + tap sounds).

## Files
- `render_plan.py` – the engine. `python3 render_plan.py plan.json out.mp4 [energy|upbeat|chill]`
- `common.py` – routes the app, fonts and stage page offline; seeds demo fridge / freezer / cupboard data.
- `stage.html` – the 1080×1920 stage (background, headline, phone frame, end card).
- `music2.py` – generates the soundtrack (default style: **energy**, the founder's pick).
- `fonts/` – Gabarito + Atkinson Hyperlegible (SIL Open Font License, from Google Fonts).

## Inputs
- `FRIDGIE_APP_HTML` env var: path to a saved copy of `https://myfridgie.netlify.app/` (single HTML file).
  - Fresh copy: built-in browser → `fetch(location.href).then(r=>r.text())` on the app page.
  - Fallback snapshot: Bot Room artifact asset `a8dd5fb787c9b468e6f41b85552fddc5` (`fridgie-app-snapshot.txt`).
- `plan.json`: `{"title", "scenes":[{"bg","headline","keyword","sub","screen","action"}×3], "caption", "hashtags"}`.
  Screens: `home`, `freezer`, `cupboard`, `item`, `freeze_it`, `recipes`, `shopping`, `unpack`.

## Publishing
Finished videos go in `videos/` (this repo is public) and are scheduled through Metricool
(brand `7328598`, TikTok + Instagram Reel + YouTube Short) using the raw link
`https://raw.githubusercontent.com/Tautwee/fridgie-videos/main/videos/<file>.mp4`.
Never schedule without the founder's explicit yes.
