"""Fridgeroo 3D story videos with voices (blocky voxel style, picked by Tautvydas on 30 Oct 2026).

usage: python3 render_voxel.py ../voxelplans/<name>.json ../videos/<out>.mp4
       ONLY=1.0,5.5 python3 render_voxel.py ...   -> just those seconds as preview frames (frames_vox/)

Plan (see voxelplans/fridge-talks.json):
  voices: {name: path to wav}  (ElevenLabs lines; one take per character, lines separated by pauses)
  scenes: [{dur, cam | cams:[[cam,at]..], label, say ("a|b|c" = subtitle chunks), voice:{who:stu|fridge, src, a, b, at},
            do:[actions], counter:{label,from,to,tone,over}, notif, notifAt, poll:{q, opts:[[text,%]..]}, chip, chipAt,
            spit:[t..], scanAt:[t..], shadesAt, shakeAt} ..., {type:'end', dur}]
  cams: wide fridge face phone duo bin fface lean orbit
  actions: open_stink spit coins shock calm sad close dim phone scan fresh shades happy eat lean
Mouths move with the voice loudness; the fridge's main door is its mouth, its freezer door is its face.
Sound = music3.py bed (ducked under voices) + voices + synthesized effects (no samples, all ours).
"""
import asyncio, json, os, subprocess, sys, shutil, wave
from pathlib import Path
import numpy as np
from scipy.signal import butter, sosfilt
from playwright.async_api import async_playwright

D = Path(__file__).resolve().parent
PLAN = Path(sys.argv[1]).resolve()
plan = json.load(open(PLAN)); OUT = os.path.abspath(sys.argv[2]); FPS = 30; SR = 44100
FR = D / 'frames_vox'; shutil.rmtree(FR, ignore_errors=True); FR.mkdir()
STAGE = (D / 'voxel_stage.html').read_text()


def load(path):
    w = wave.open(str(path)); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    if w.getnchannels() == 2: x = x.reshape(-1, 2).mean(1)
    assert w.getframerate() == SR, 'convert voices to 44.1 kHz mono wav first'
    return x


VO = {k: load(PLAN.parent / v) for k, v in plan.get('voices', {}).items()}
clips = []  # (scene index, samples)
for i, s in enumerate(plan['scenes']):
    v = s.get('voice')
    if not v: continue
    x = VO[v['src']][int(v['a'] * SR):int(v['b'] * SR)].copy()
    fade = int(0.03 * SR); x[:fade] *= np.linspace(0, 1, fade); x[-fade:] *= np.linspace(1, 0, fade)
    rms = np.sqrt(np.mean(x[np.abs(x) > 0.005] ** 2) + 1e-9); x *= 0.16 / rms  # same loudness for every line
    x = np.clip(x, -0.98, 0.98)
    hop = SR // FPS; env = np.array([np.sqrt(np.mean(x[j:j + hop] ** 2)) for j in range(0, len(x), hop)])
    env = np.convolve(env, [0.25, 0.5, 0.25], 'same'); env = np.clip(env / (np.percentile(env, 95) + 1e-6), 0, 1)
    v['env'] = [round(float(e), 3) for e in env]
    clips.append((i, x))


async def route(r):
    u = r.request.url
    if u.startswith('https://stage.local'):
        return await r.fulfill(body=STAGE.replace('<script>', '<script>window.PLAN=' + json.dumps(plan) + ';', 1), content_type='text/html')
    if u.startswith('https://lib.local/'):
        return await r.fulfill(path=str(D / 'lib_three.module.min.js'), content_type='text/javascript')
    if u.startswith('https://fonts.local/'):
        f = u.split('/')[-1]
        return await r.fulfill(path=str(D / 'fonts' / f), content_type='font/ttf' if f.endswith('.ttf') else 'font/woff2')
    return await r.abort()


async def main():
    only = os.environ.get('ONLY')
    async with async_playwright() as p:
        br = await p.chromium.launch(args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        pg = await br.new_page(viewport={'width': 1080, 'height': 1920})
        pg.on('pageerror', lambda e: print('PAGEERR:', e))
        await pg.route('**/*', route)
        await pg.goto('https://stage.local/')
        await pg.wait_for_function('window.READY===true', timeout=30000)
        await pg.evaluate('document.fonts.ready'); await pg.wait_for_timeout(300)
        total = await pg.evaluate('window.TOTAL'); info = await pg.evaluate('({s:window.SCENES,x:window.SFX})')
        times = [float(x) for x in only.split(',')] if only else [i / FPS for i in range(int(round(total * FPS)))]
        for i, t in enumerate(times):
            await pg.evaluate('t=>render(t)', t)
            await pg.screenshot(path=str(FR / f'f{i:04d}.jpg'), type='jpeg', quality=92)
        await br.close()
    return total, info

TOTAL, I = asyncio.run(main())
if os.environ.get('ONLY'): print('preview frames in', FR); sys.exit()
starts = [s['start'] for s in I['s']]
N = int(TOTAL * SR) + SR

# ---------------- music bed (no built-in taps; our own effects below)
tl = {'taps': [], 'beeps': [], 'dings': [], 'scenes': starts, 'total': TOTAL, 'drop': starts[1]}
tlp = D / 'timelines'; tlp.mkdir(exist_ok=True)
tlf = tlp / (os.path.basename(OUT).rsplit('.', 1)[0] + '.json'); json.dump(tl, open(tlf, 'w'))
mw = str(D / 'music_vox.wav')
subprocess.run(['python3', str(D / 'music3.py'), plan.get('music', 'house'), mw, os.path.basename(OUT), str(tlf)], check=True, cwd=str(D), stdout=subprocess.DEVNULL)
w = wave.open(mw); mus = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
mus = mus.reshape(-1, w.getnchannels()).mean(1) if w.getnchannels() > 1 else mus
mus = np.pad(mus, (0, max(0, N - len(mus))))[:N]

voice = np.zeros(N, np.float32)
for i, x in clips:
    t0 = int((starts[i] + plan['scenes'][i]['voice'].get('at', 0)) * SR); voice[t0:t0 + len(x)] += x[:N - t0]
# duck the music under speech (smooth)
act = (np.abs(voice) > 0.01).astype(np.float32)
k = np.ones(int(0.25 * SR)) / int(0.25 * SR); act = np.clip(np.convolve(act, k, 'same') * 3, 0, 1)
mus *= (0.55 - 0.33 * act)

# ---------------- sound effects (synthesized)
rng = np.random.default_rng(7)
def tt(d): return np.arange(int(SR * d)) / SR
def flt(x, f, kind='low'): return sosfilt(butter(2, f, kind, fs=SR, output='sos'), x)
def env(n, a, d): e = np.exp(-np.arange(n) / (d * SR)); e[:int(a * SR)] *= np.linspace(0, 1, int(a * SR)); return e
def noise(d): return rng.normal(0, 1, int(SR * d))
FX = {
 'thunk': lambda: (np.sin(2 * np.pi * (70 + 90 * np.exp(-tt(.35) * 25)) * tt(.35)) * env(int(SR * .35), .002, .09) + flt(noise(.35), 900) * env(int(SR * .35), .001, .03) * .6) * .9,
 'whoosh': lambda: flt(noise(.4), 2500) * np.sin(np.linspace(0, np.pi, int(SR * .4))) ** 2 * .35,
 'swoosh': lambda: flt(flt(noise(.25), 1200, 'high'), 6000) * np.sin(np.linspace(0, np.pi, int(SR * .25))) ** 2 * .25,
 'coin': lambda: (np.sin(2 * np.pi * 2093 * tt(.25)) + .6 * np.sin(2 * np.pi * 3136 * tt(.25))) * env(int(SR * .25), .001, .06) * .22,
 'beep': lambda: np.sign(np.sin(2 * np.pi * 1760 * tt(.09))) * env(int(SR * .09), .002, .2) * .16,
 'buzz': lambda: np.sign(np.sin(2 * np.pi * 150 * tt(.5))) * (np.sin(2 * np.pi * 8 * tt(.5)) > 0) * .14 * flt(np.ones(int(SR * .5)), 30),
 'pop': lambda: np.sin(2 * np.pi * (500 + 900 * np.exp(-tt(.12) * 40)) * tt(.12)) * env(int(SR * .12), .001, .04) * .45,
 'tick': lambda: flt(noise(.04), 3000, 'high') * env(int(SR * .04), .001, .01) * .4,
 'door': lambda: (flt(noise(.25), 400) * env(int(SR * .25), .002, .05) + np.sin(2 * np.pi * 95 * tt(.25)) * env(int(SR * .25), .002, .06)) * .5,
 'stink': lambda: flt(noise(1.0), 600) * np.sin(np.linspace(0, np.pi, SR)) ** 1.5 * .45 + np.sin(2 * np.pi * (60 - 20 * tt(1.0)) * tt(1.0)) * np.sin(np.linspace(0, np.pi, SR)) * .3,
 'boing': lambda: np.sin(2 * np.pi * (220 + 60 * np.sin(2 * np.pi * 9 * tt(.45))) * tt(.45)) * env(int(SR * .45), .005, .2) * .3,
 'swish': lambda: flt(noise(.45), 3000) * np.linspace(0, 1, int(SR * .45)) ** 2 * .3,
 'click': lambda: (flt(noise(.05), 2000, 'high') * env(int(SR * .05), .001, .008) * .7 + np.sin(2 * np.pi * 1200 * tt(.05)) * env(int(SR * .05), .001, .01) * .3),
 'ding': lambda: (np.sin(2 * np.pi * 1318 * tt(.6)) + .5 * np.sin(2 * np.pi * 2637 * tt(.6))) * env(int(SR * .6), .002, .2) * .18,
}
sfx = np.zeros(N, np.float32)
for name, t in I['x']:
    if name not in FX: continue
    x = FX[name](); a = int(t * SR)
    if 0 <= a < N: sfx[a:a + len(x)] += x[:N - a]

mix = mus + voice + sfx
mix = mix[:int(TOTAL * SR)]
mix *= 0.95 / max(1e-6, np.abs(mix).max())
wav = str(D / 'mix_vox.wav')
with wave.open(wav, 'w') as o:
    o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR); o.writeframes((mix * 32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', str(FR / 'f%04d.jpg'), '-i', wav, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
                '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-c:a', 'aac', '-b:a', '192k', '-ac', '2', '-shortest', OUT], check=True)
print('done', OUT, f'{TOTAL:.1f}s')
