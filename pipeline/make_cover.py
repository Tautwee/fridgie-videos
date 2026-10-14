"""Designed 1080x1920 covers and photo stories in the Fridgeroo look.

python3 make_cover.py cover ../motionplans/<slug>.json ../covers/<video-file-without-.mp4>.jpg
python3 make_cover.py story ../storyplans/<name>.json ../stories/<name>.jpg

cover: uses plan["cover"] = {words, emoji} + plan["palette"]. Hook words huge and centred in the middle third,
       one big emoji, starry gradient in the video's palette, small Fridgeroo badge — same frame on every cover.
story: {palette, emoji, headline (one <b>keyword</b>), chips:[2], kicker, url} — everything inside the
       Instagram safe area (y 250..1580).
Rendered with Chromium (same fonts as the videos), saved as JPEG with PIL.
"""
import asyncio, json, sys, io, re
from playwright.async_api import async_playwright
from PIL import Image
from common import D

PAL = {
    'cobalt': ('#2f5cf0', '#0b1a5c', '#ffc93c', '#13223F'),
    'grape': ('#7b5cff', '#1d0f5e', '#ffd23f', '#1d0f5e'),
    'charcoal': ('#3a3f4b', '#121418', '#3fdc9c', '#0f1a15'),
    'forest': ('#1f9a68', '#0a2e20', '#fff07a', '#0a2e20'),
    'sunset': ('#ff6b4a', '#5c1236', '#ffe9a8', '#5c1236'),
    'lagoon': ('#12a3b4', '#06303a', '#ffcf4a', '#06303a'),
    'berry': ('#e0367a', '#3d0a2a', '#ffe066', '#3d0a2a'),
    'mint': ('#3fdc9c', '#0e5e43', '#1b1d22', '#ffffff'),
}
mode, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
plan = json.load(open(src))
a, b, acc, accInk = PAL.get(plan.get('palette'), PAL['cobalt'])


def fmt(s):
    s = re.sub(r'[&<>]', lambda m: {'&': '&amp;', '<': '&lt;', '>': '&gt;'}[m.group()], s or '')
    return re.sub(r'&lt;b&gt;(.*?)&lt;/b&gt;', r'<b>\1</b>', s)


LOGO = ('<svg viewBox="0 0 96 96"><rect width="96" height="96" rx="24" fill="#1b1d22"/><rect x="26" y="12" width="44" height="72" rx="11" '
        'fill="#fff"/><path d="M26 36 h44" stroke="#1b1d22" stroke-width="3"/><path d="M33 19 v10" stroke="#3fbf8f" stroke-width="4" '
        'stroke-linecap="round"/><path d="M29 47 h38 l-2 8 q-1 4 -6 4 h-5 q-4 0 -5 -4 l-1 -3 l-1 3 q-1 4 -5 4 h-5 q-5 0 -6 -4z" '
        'fill="#1b1d22"/><path d="M42 66 q7 5 14 -1" fill="none" stroke="#1b1d22" stroke-width="3" stroke-linecap="round"/></svg>')
stars = ''.join(f'<i style="left:{(i*137)%1080}px;top:{(i*251)%1920}px;opacity:{0.25+((i*7)%10)/20}"></i>' for i in range(70))
CSS = f"""@font-face{{font-family:G;src:url(https://fonts.local/Gabarito-800.woff2)}}
@font-face{{font-family:A;src:url(https://fonts.local/AtkinsonHyperlegible-700.woff2)}}
*{{margin:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;overflow:hidden;position:relative;color:#fff;font-family:G;font-weight:800;
background:radial-gradient(circle at 50% 42%,{a} 0%,{b} 78%)}}
.st i{{position:absolute;width:5px;height:5px;border-radius:50%;background:#fff}}
.frame{{position:absolute;inset:34px;border:10px solid rgba(255,255,255,.9);border-radius:64px}}
b{{color:{acc};font-weight:800}}
.badge{{position:absolute;left:0;right:0;display:flex;justify-content:center;align-items:center;gap:18px;font-size:50px}}
.badge svg{{width:76px;height:76px}}
.c{{position:absolute;left:90px;right:90px;text-align:center}}
.e{{font-family:'Noto Color Emoji';line-height:1}}
"""
if mode == 'cover':
    words = plan['cover']['words'].upper().split()
    lines, cur = [], ''
    for w in words:  # max ~11 chars per line keeps letters huge
        if cur and len(cur) + 1 + len(w) > 11: lines.append(cur); cur = w
        else: cur = (cur + ' ' + w).strip()
    lines.append(cur)
    longest = max(len(l) for l in lines)
    fs = min(220, int(880 / (max(longest, 4) * 0.66)))
    # one keyword in the accent colour: the longest word
    kw = max(words, key=len)
    html_lines = '<br>'.join(l.replace(kw, f'<b>{kw}</b>', 1) if kw in l.split() else l for l in lines)
    body = f"""<div class="st">{stars}</div><div class="frame"></div>
<div class="c e" style="top:420px;font-size:250px">{plan['cover']['emoji']}</div>
<div class="c" style="top:{760 if len(lines) < 3 else 720}px;font-size:{fs}px;line-height:.95;letter-spacing:-2px;text-shadow:0 10px 0 rgba(0,0,0,.25)">{html_lines}</div>
<div class="badge" style="top:1500px">{LOGO}<span>Fridgeroo</span></div>"""
else:
    chips = ''.join(f'<span style="display:inline-block;margin:0 14px;padding:26px 46px;border-radius:70px;background:#fff;color:{b};font-size:64px">{fmt(c)}</span>' for c in plan.get('chips', []))
    body = f"""<div class="st">{stars}</div>
<div class="badge" style="top:300px">{LOGO}<span>Fridgeroo</span></div>
<div class="c e" style="top:470px;font-size:300px">{plan['emoji']}</div>
<div class="c" style="top:850px;font-size:118px;line-height:1.02;letter-spacing:-1px">{fmt(plan['headline'])}</div>
<div class="c" style="top:1180px">{chips}</div>
<div class="c" style="top:1390px;font-family:A;font-size:46px;opacity:.95">{fmt(plan.get('kicker',''))}</div>
<div class="c" style="top:1470px;font-family:A;font-size:38px;color:{acc}">{fmt(plan.get('url',''))}</div>"""
HTML = f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{body}</body></html>'


async def route(r):
    u = r.request.url
    if u.startswith('https://stage.local'):
        return await r.fulfill(body=HTML, content_type='text/html')
    if u.startswith('https://fonts.local/'):
        return await r.fulfill(path=str(D / 'fonts' / u.split('/')[-1]), content_type='font/woff2')
    return await r.abort()


async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch()
        pg = await br.new_page(viewport={'width': 1080, 'height': 1920})
        await pg.route('**/*', route)
        await pg.goto('https://stage.local/')
        await pg.evaluate('document.fonts.ready')
        await pg.wait_for_timeout(300)
        png = await pg.screenshot(type='png')
        await br.close()
    Image.open(io.BytesIO(png)).convert('RGB').save(out, 'JPEG', quality=92)
    print('done', out)

asyncio.run(main())
