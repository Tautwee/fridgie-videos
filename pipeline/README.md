# Fridgeroo video pipeline (formerly Fridgie)

Turns a locked plan from the **Fridgeroo Bot Room** into a 9:16 video in the house style (real app screens in a phone, coloured scene backgrounds, white headline with one yellow keyword, navy end card, music + tap sounds).

## Files
- `render_plan.py` – the engine. `python3 render_plan.py plan.json out.mp4 [auto|house|futurebass|lofi|disco|afro|synthwave|trap|tropical]` (default auto)
- `common.py` – routes the app, fonts and stage page offline; seeds demo fridge / freezer / cupboard data.
- `stage.html` – the 1080×1920 stage (background, headline, phone frame, end card).
- `music3.py` – generates a fresh soundtrack per video: 8 genres, rotated by posting slot so back-to-back posts never share a genre; key, tempo, chords and melody come from the file name. Mixed for phone speakers.
- `remix_audio.py` – swap the music on a finished video: `python3 remix_audio.py ../videos/<file>.mp4 [style]` (uses `timelines/<file>.json`, saved by every render).
- `music2.py` – old single-track generator (kept for reference).
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

## Covers
Every render's first frame is a complete picture (headline + phone), so it works as the cover.
When booking, also make `covers/<file>.jpg` (`ffmpeg -ss 2.0 -i videos/<file>.mp4 -frames:v 1 -q:v 2 covers/<file>.jpg`; for beat videos use `-ss 0.5`), push it, and pass it to Metricool as `videoThumbnailUrl`.

## Stories and ad-style videos (13 Oct 2026, the style Tautvydas picked)
Every Instagram story is a VIDEO (no more photos), made with `render_motion.py` from `motionplans/<name>.json`:
`cd pipeline && python3 render_motion.py ../motionplans/<name>.json ../stories/<name>.mp4`
Look at `examples/` (his 4 reference ads; `fridgeroo-story-countdown-SOUND.mp4` is the one with music he liked):
fast, bouncy, eye-catching motion, cuts and pops on the beat, music genre matching the energy, starry gradient
background, logo outro. Rotate palettes so two days in a row never look the same.
`render_story.py` (still images) is retired.

## 3D story videos (the format Tautvydas loved, 31 Oct 2026) — every 2 days at 18:30
Blocky (voxel) 3D mini-stories: the **fridge is the character** and roasts the viewer (POV). Gold example: `voxelplans/fridge-roast.json` → `videos/fridgeroo-3d-roast-v7.mp4`.
`cd pipeline && python3 render_voxel.py ../voxelplans/<name>.json ../videos/<out>.mp4` (~12–15 min; `ONLY=1.0,5.5` renders preview frames only into frames_vox/; `REUSE_FRAMES=1` re-encodes sound only).
- Stage `voxel_stage2.html` (set `"stage":"voxel_stage2.html"` in the plan). Music = `score.py` (story score) when the plan has `"score"` marks `{name:[sceneIndex, secondsIntoScene]}` for sneak, tension, yuck, hit, app, glow, drop, end.
- Voices: ElevenLabs, fridge voice **"Grampa Werthers – Old & Cranky"** (his account). Bots cannot make voices: he pastes the text, downloads the mp3 and uploads it to the Bot Room. Convert with `ffmpeg -i in.mp3 -ac 1 -ar 44100 -af atempo=1.12 out.wav`, find lines with `silencedetect=noise=-40dB:d=0.15`, cut long pauses, set each scene's `voice:{who:'fridge',src:'fridge',a,b,at}` (seconds in the wav). The fridge's mouth syncs automatically.
- Scene actions: `cold` (open mid clean-out: bin open, food flying from frame 1 — always start like this), `cleanout` (walks in with bin), `yogurt` (pulls the `reveal` item from the back: sniff, gag, fly on nose), `stare` (fridge stares at the camera), `phone` + `shades` + `magic` (app zoom, glow, sky of fridges). Items: pizza takeaway sandwich yogurt milk cheese pasta apple carrot banana tomato eggs broccoli; `toss:[...]`, `reveal:'<item>'`. App screen rows: plan `appRows`. Cameras: front three side hero yog fmed fwide ftalk fside fside2 fstare phone phonezoom sky pullout binTop.
- Rules he gave: open on ACTION in frame 1; max ~4 short fridge lines (≈9 s talking); show the fridge's face whenever it talks; no polls in the video (the question goes in the caption); the app on screen ≥1.5 s; big text; end card slogan **"Use it or lose it."**; 14–17 s total; clean, warm ending (no noise).
