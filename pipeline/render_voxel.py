"""Fridgeroo 3D story videos (blocky voxel style, like the reels Tautvydas picked on 30 Oct 2026).
usage: python3 render_voxel.py ../voxelplans/<name>.json ../videos/<out>.mp4
Plan: {title, music, scenes:[{dur, cam, label, say, per, do:[actions], counter:{label,from,to,tone}, notif, chip, shake} ..., {type:'end',dur:3}], caption, hashtags}
cams: wide fridge face phone duo low | actions: walk_in open close rot shock sad phone scan fresh sunglasses happy eat
Text: one <b>keyword</b> per line (yellow); subtitles pop 3 words at a time.
"""
import asyncio, json, os, subprocess, sys, shutil
from pathlib import Path
from playwright.async_api import async_playwright
D = Path(__file__).resolve().parent
plan = json.load(open(sys.argv[1])); OUT = os.path.abspath(sys.argv[2]); FPS = 30
FR = D / 'frames_vox'; shutil.rmtree(FR, ignore_errors=True); FR.mkdir()
STAGE = (D / 'voxel_stage.html').read_text()

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
    only = os.environ.get('ONLY')  # e.g. ONLY=1,4.5,9 -> just these seconds (preview)
    async with async_playwright() as p:
        br = await p.chromium.launch(args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        pg = await br.new_page(viewport={'width': 1080, 'height': 1920})
        pg.on('console', lambda m: m.type == 'error' and print('JS:', m.text))
        pg.on('pageerror', lambda e: print('PAGEERR:', e))
        await pg.route('**/*', route)
        await pg.goto('https://stage.local/')
        await pg.wait_for_function('window.READY===true', timeout=30000)
        await pg.evaluate('document.fonts.ready'); await pg.wait_for_timeout(300)
        total = await pg.evaluate('window.TOTAL'); info = await pg.evaluate('({s:window.SCENES,t:window.TAPS,b:window.BEEPS,d:window.DINGS})')
        times = [float(x) for x in only.split(',')] if only else [i / FPS for i in range(int(round(total * FPS)))]
        for i, t in enumerate(times):
            await pg.evaluate('t=>render(t)', t)
            await pg.screenshot(path=str(FR / f'f{i:04d}.jpg'), type='jpeg', quality=92)
        await br.close()
    return total, info

TOTAL, I = asyncio.run(main())
if os.environ.get('ONLY'): print('preview frames in', FR); sys.exit()
starts = [s['start'] for s in I['s']]
tl = {'taps': I['t'], 'beeps': I['b'], 'dings': I['d'], 'scenes': starts, 'total': TOTAL, 'drop': starts[1]}
if plan.get('bpm'): tl['bpm'] = plan['bpm']
tlp = D / 'timelines'; tlp.mkdir(exist_ok=True)
tlf = tlp / (os.path.basename(OUT).rsplit('.', 1)[0] + '.json'); json.dump(tl, open(tlf, 'w'))
wav = str(D / 'music_vox.wav')
subprocess.run(['python3', str(D / 'music3.py'), plan.get('music', 'house'), wav, os.path.basename(OUT), str(tlf)], check=True, cwd=str(D))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', str(FR / 'f%04d.jpg'), '-i', wav, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
                '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-c:a', 'aac', '-b:a', '192k', '-shortest', OUT], check=True)
print('done', OUT, f'{TOTAL:.1f}s')
