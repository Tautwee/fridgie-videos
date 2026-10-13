"""Render a 1080x1920 Instagram story image from a story plan.

python3 render_story.py storyplans/<name>.json  -> stories/<name>.png

Plan fields:
  template: poll | tip | teaser | question
  kicker:   small line on top (e.g. "Quick poll")
  title:    big line, wrap ONE keyword in <b>..</b> (shown in mint)
  body:     optional short line under the title
  options:  poll only, 2 short answers
  shot:     optional image: a file path, or "videos/<name>.mp4@1.5" (frame at 1.5 s)
  theme:    charcoal (default) | mint | cream
Keep text inside the safe area: nothing important in the top 250 px or bottom 340 px.
Instagram's API can't add real poll stickers, so polls ask people to reply.
"""
import asyncio, json, sys, subprocess, base64, pathlib, html
from playwright.async_api import async_playwright
from common import route, D

ROOT = D.parent
THEMES = {
    'charcoal': ('#1b1d22', '#ffffff', '#3fbf8f', '#2a2d34'),
    'mint':     ('#249a6e', '#ffffff', '#1b1d22', '#2fae7f'),
    'cream':    ('#f4f1e8', '#1b1d22', '#249a6e', '#e8e3d4'),
}
LOGO = '<svg viewBox="0 0 96 96" width="88" height="88"><rect width="96" height="96" rx="24" fill="#3fbf8f"/><rect x="26" y="12" width="44" height="72" rx="11" fill="#fff" stroke="#1b1d22" stroke-width="3"/><path d="M26 36 h44" stroke="#1b1d22" stroke-width="3"/><path d="M29 47 h38 l-2 8 q-1 4 -6 4 h-5 q-4 0 -5 -4 l-1 -3 l-1 3 q-1 4 -5 4 h-5 q-5 0 -6 -4z" fill="#1b1d22"/><path d="M42 66 q7 5 14 -1" fill="none" stroke="#1b1d22" stroke-width="3" stroke-linecap="round"/></svg>'


def shot_uri(spec):
    if not spec:
        return ''
    if '@' in spec and spec.split('@')[0].endswith('.mp4'):
        vid, t = spec.split('@')
        out = ROOT / 'stories' / '_frame.jpg'
        out.parent.mkdir(exist_ok=True)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', t, '-i', str(ROOT / vid), '-frames:v', '1', '-q:v', '2', str(out)], check=True)
        p = out
    else:
        p = ROOT / spec
    return 'data:image/jpeg;base64,' + base64.b64encode(p.read_bytes()).decode()


def safe(s):
    # allow only <b>, escape everything else
    return html.escape(s or '').replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')


def page(plan):
    bg, fg, acc, soft = THEMES.get(plan.get('theme', 'charcoal'), THEMES['charcoal'])
    t = plan.get('template', 'tip')
    img = shot_uri(plan.get('shot'))
    opts = ''
    if t == 'poll':
        o = plan.get('options', ['Yes', 'No'])[:2]
        opts = '<div class="opts">' + ''.join(f'<div class="opt"><span>{"AB"[i]}</span>{safe(x)}</div>' for i, x in enumerate(o)) + '</div><div class="reply">Reply A or B 👇</div>'
    if t == 'question':
        opts = '<div class="ask">Type your answer…</div>'
    shot = f'<div class="shot"><img src="{img}"></div>' if img else ''
    return f"""<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gabarito"><style>
*{{box-sizing:border-box;margin:0}}
body{{width:1080px;height:1920px;background:{bg};color:{fg};font-family:'Atkinson Hyperlegible';overflow:hidden;position:relative}}
.glow{{position:absolute;width:1400px;height:1400px;border-radius:50%;background:radial-gradient(circle,{acc}33,transparent 62%);left:-160px;top:-260px}}
.wrap{{position:absolute;inset:250px 90px 340px;display:flex;flex-direction:column;gap:44px;justify-content:center}}
.kick{{font-family:Gabarito;font-weight:600;font-size:40px;letter-spacing:4px;text-transform:uppercase;color:{acc}}}
h1{{font-family:Gabarito;font-weight:800;font-size:{118 if len(plan.get('title',''))<40 else 96}px;line-height:1.03;letter-spacing:-2px;text-wrap:balance}}
h1 b{{color:{acc}}}
p{{font-size:44px;line-height:1.3;opacity:.85;max-width:860px}}
.opts{{display:flex;flex-direction:column;gap:24px}}
.opt{{display:flex;align-items:center;gap:28px;background:{soft};border-radius:34px;padding:34px 38px;font-family:Gabarito;font-weight:600;font-size:54px}}
.opt span{{width:84px;height:84px;border-radius:50%;background:{acc};color:{bg};display:grid;place-items:center;font-weight:800;flex:none}}
.reply,.ask{{font-size:38px;opacity:.75}}
.ask{{background:{soft};border-radius:30px;padding:34px 38px;opacity:.9}}
.shot{{border-radius:44px;overflow:hidden;height:820px;aspect-ratio:9/16;align-self:flex-start;box-shadow:0 30px 80px rgba(0,0,0,.35)}}
.shot img{{width:100%;height:100%;object-fit:cover}}
.foot{{position:absolute;left:90px;right:90px;bottom:250px;display:flex;align-items:center;gap:24px;font-family:Gabarito;font-weight:600;font-size:38px}}
.foot small{{display:block;font-family:'Atkinson Hyperlegible';font-weight:400;font-size:30px;opacity:.7}}
</style></head><body><div class="glow"></div><div class="wrap">
<div class="kick">{safe(plan.get('kicker',''))}</div><h1>{safe(plan.get('title',''))}</h1>
{f'<p>{safe(plan["body"])}</p>' if plan.get('body') else ''}{shot}{opts}</div>
<div class="foot">{LOGO}<div>Fridgeroo<small>fridgeroo.netlify.app · Know before it goes.</small></div></div></body></html>"""


async def main(path):
    plan = json.loads(pathlib.Path(path).read_text())
    name = pathlib.Path(path).stem
    out = ROOT / 'stories' / f'{name}.png'
    out.parent.mkdir(exist_ok=True)
    body = page(plan)
    async with async_playwright() as p:
        br = await p.chromium.launch()
        pg = await br.new_page(viewport={'width': 1080, 'height': 1920})
        await pg.route('**/*', route)

        await pg.route('https://story.local/', lambda r: r.fulfill(body=body, content_type='text/html'))
        await pg.goto('https://story.local/')
        await pg.evaluate('document.fonts.ready')
        await pg.wait_for_timeout(300)
        await pg.screenshot(path=str(out))
        await br.close()
    print(out)

if __name__ == '__main__':
    asyncio.run(main(sys.argv[1]))
