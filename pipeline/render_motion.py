"""Animated ad-style renderer (stories AND feed videos) — the style Tautvydas picked on 13 Oct 2026.

python3 render_motion.py motionplans/<name>.json <out.mp4>

Plan:
{"title":"...", "bpm":120, "music":"house", "palette":"cobalt|grape|charcoal|forest|sunset|lagoon|berry|mint",
 "cta":"Free · no sign-up · link in bio",
 "scenes":[ {"type":..., "beats":N, ...}, ..., {"type":"end","beats":5} ],
 "caption":"...", "hashtags":[...]}            # caption/hashtags only for feed videos
Scene types (text fields allow ONE <b>keyword</b> = accent colour; emoji are fine, they render):
  hook      {text, sub?}                      big line slams in, sub pops in after ~1 beat, shakes into the drop
  countdown {emoji, from:3, stepBeats:2, unit:"days left", unit1:"day left ⚠️", notify, end}   ring + 3-2-1, bg green→amber→red, phone notification, check
  grid      {title, items:[4 emoji], loser:1, dead:"💀", verdict, stepBeats:0.5}   "what dies first" tiles pop, one dies
  scan      {title, items:[up to 9 emoji], label:"added", stepBeats:0.5}          items fly onto fridge shelves with BEEP + counter
  list      {title, items:[{emoji,text}], numbered?, stepBeats:1}                rows slide in (rankings, "things my housemate does")
  card      {title?, emoji, name, days, left:25, sticker}                         app-style item card, amount bar drains, sticker pops
  text      {text, pill?}                                                         statement + accent pill (e.g. "2 days before 🔔")
  punch     {text}                                                                one punchy word ("Saved. 😮‍💨")
  end       {}                                                                    logo animation, Fridgeroo, slogan, CTA pill (always last, 5 beats)
The scene after the first is the DROP (flash + music kicks in). Stories 8–10 s, feed videos 10–15 s.
"""
import asyncio, json, sys, subprocess, shutil, os, pathlib
from playwright.async_api import async_playwright
from common import D

FPS = 30
plan = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
FR = D / 'frames_motion'
shutil.rmtree(FR, ignore_errors=True); FR.mkdir()
STAGE = (D / 'motion_stage.html').read_text()


async def route(r):
    u = r.request.url
    if u.startswith('https://stage.local'):
        html = STAGE.replace('<script>', '<script>window.PLAN=' + json.dumps(plan) + ';', 1)
        return await r.fulfill(body=html, content_type='text/html')
    if u.startswith('https://fonts.local/'):
        f = u.split('/')[-1]
        return await r.fulfill(path=str(D / 'fonts' / f), content_type='font/ttf' if f.endswith('.ttf') else 'font/woff2')
    return await r.abort()


async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch()
        pg = await br.new_page(viewport={'width': 1080, 'height': 1920})
        await pg.route('**/*', route)
        await pg.goto('https://stage.local/')
        await pg.evaluate('document.fonts.ready')
        await pg.wait_for_timeout(400)
        total = await pg.evaluate('window.TOTAL')
        scenes = await pg.evaluate('window.SCENES')
        n = int(round((total + 0.25) * FPS))
        for fi in range(n):
            await pg.evaluate('t=>render(t)', fi / FPS)
            await pg.screenshot(path=str(FR / f'f{fi:04d}.jpg'), type='jpeg', quality=93)
        await br.close()
    return total + 0.25, scenes

TOTAL, SCN = asyncio.run(main())
beat = 60 / plan['bpm']
taps, beeps, dings = [], [], []
for s, sc in zip(plan['scenes'], SCN):
    t0, B = sc['start'], lambda x: sc['start'] + x * beat
    ty = s['type']
    if ty == 'hook' and s.get('sub'): taps.append(B(1.25))
    if ty == 'countdown':
        st, nn = s.get('stepBeats', 2), s.get('from', 3)
        taps += [B(k * st) for k in range(nn)]
        dings.append(B(nn * st) + 0.05); taps.append(B(nn * st) + 0.5)
    if ty == 'grid':
        st = s.get('stepBeats', 0.5); k = len(s['items'][:4])
        taps += [B(0.5 + i * st) for i in range(k)]; taps.append(B(0.5 + k * st + 1.4))
    if ty == 'scan':
        st = s.get('stepBeats', 0.5)
        beeps += [B(0.75 + i * st) for i in range(min(9, len(s['items'])))]
    if ty == 'list':
        taps += [B(0.75 + i * s.get('stepBeats', 1)) for i in range(min(5, len(s['items'])))]
    if ty == 'text' and s.get('pill'): taps.append(B(1))
    if ty == 'card': taps.append(B(2.5))
    if ty == 'end': taps.append(t0 + 0.75)
starts = [sc['start'] for sc in SCN]
tl = {'taps': taps, 'beeps': beeps, 'dings': dings, 'scenes': starts, 'total': TOTAL, 'bpm': plan['bpm'],
      'drop': starts[1] if len(starts) > 1 else 0}
tlp = D / 'timelines'; tlp.mkdir(exist_ok=True)
tlf = tlp / (os.path.basename(OUT).rsplit('.', 1)[0] + '.json')
json.dump(tl, open(tlf, 'w'))
wav = str(D / 'music_tmp.wav')
subprocess.run(['python3', str(D / 'music3.py'), plan.get('music', 'house'), wav, os.path.basename(OUT), str(tlf)], check=True, cwd=str(D))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', str(FR / 'f%04d.jpg'), '-i', wav, '-c:v', 'libx264', '-preset', 'slow', '-crf', '17',
                '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-movflags', '+faststart', '-c:a', 'aac', '-b:a', '192k', '-shortest', OUT], check=True)
print('done', OUT, f'{TOTAL:.1f}s')
