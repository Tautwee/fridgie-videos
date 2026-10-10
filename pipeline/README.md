# Fridgeroo video pipeline (formerly Fridgie)

Turns a locked plan from the **Fridgie Bot Room** into a 9:16 video in the house style (real app screens in a phone, coloured scene backgrounds, white headline with one yellow keyword, navy end card, music + tap sounds).

## Files
- `render_plan.py` – the engine. `python3 render_plan.py plan.json out.mp4 [energy|upbeat|chill]`
- `common.py` – routes the app, fonts and stage page offline; seeds demo fridge / freezer / cupboard data.
- `stage.html` – the 1080×1920 stage (background, headline, phone frame, end card).
- `music2.py` – generates the soundtrack (default style: **energy**, the founder's pick).
- `fonts/` – Gabarito + Atkinson Hyperlegible (SIL Open Font License, from Google Fonts).

## Inputs
- `FRIDGIE_APP_HTML` env var: path to a saved copy of `https://myfridgie.netlify.app/` (single HTML file).
  - Fresh copy: built-in browser → open https://fridgeroo.netlify.app (or the old https://myfridgie.netlify.app) and run `fetch(location.href).then(r=>r.text())`. If the fetched app still says "Fridgie", replace "Fridgie"→"Fridgeroo" and "myfridgie.netlify.app"→"fridgeroo.netlify.app" (never touch lowercase "fridgie-" storage keys).
  - Fallback snapshot: Bot Room artifact asset `46005a49372e6e7f222167a7b6fe65de` (`fridgeroo-app-snapshot.txt`, already renamed to Fridgeroo).
- `plan.json`: `{"title", "scenes":[{"bg","headline","keyword","sub","screen","action"}×3], "caption", "hashtags"}`.
  Screens: `home`, `freezer`, `cupboard`, `item`, `freeze_it`, `recipes`, `shopping`, `unpack`.

## Publishing
Finished videos go in `videos/` (this repo is public) and are scheduled through Metricool
(brand `7328598`, TikTok + Instagram Reel + YouTube Short) using the raw link
`https://raw.githubusercontent.com/Tautwee/fridgie-videos/main/videos/<file>.mp4`.
Never schedule without the founder's explicit yes.
