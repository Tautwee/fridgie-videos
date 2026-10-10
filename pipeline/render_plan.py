"""Render a Fridgie video from a Bot Room plan.

Usage: python3 render_plan.py plan.json out.mp4 [upbeat|chill|energy]
Needs: FRIDGIE_APP_HTML=<path to a saved copy of myfridgie.netlify.app index.html>
"""
import asyncio, json, sys, subprocess, re, html
from playwright.async_api import async_playwright
from common import *

plan = json.load(open(sys.argv[1])); OUTMP4 = sys.argv[2]; STYLE = sys.argv[3] if len(sys.argv) > 3 else 'energy'
FPS = 30
FR = D / 'frames'; FR.mkdir(exist_ok=True)
for f in FR.glob('*.png'): f.unlink()

COL = {'navy': (17, 33, 62), 'green': (24, 92, 60), 'orange': (169, 99, 0), 'blue': (28, 92, 157), 'brown': (121, 72, 32)}
SCENE_LEN, END_LEN = 5.2, 3.8
scenes = plan['scenes'][:3]

def headline_html(s):
    h = html.escape(s.get('headline', '')); k = html.escape(s.get('keyword', '') or '')
    if k and k in h: h = h.replace(k, f'<b>{k}</b>', 1)
    sub = html.escape(s.get('sub', '') or '')
    size = '' if len(s.get('headline', '')) <= 22 else " style='font-size:76px'"
    return f"<span{size}>{h}</span>" + (f"<span class='sub'>{sub}</span>" if sub else '')

SCENES = [(i * SCENE_LEN, COL.get(s.get('bg'), COL['navy']), headline_html(s)) for i, s in enumerate(scenes)]
END_AT = len(scenes) * SCENE_LEN; TOTAL = END_AT + END_LEN
SX, SY, Z = 224, 458, 1.6205
TAPS = []
NAMES = ['Chicken','Lettuce','Greek yogurt','Milk','Eggs','Cheddar','Butter','Salmon','Ham','Tomatoes','Peppers','Carrots','Cucumber','Strawberries','Apples','Bananas','Orange juice','Cola','Ketchup','Pesto','Hummus','Tortilla wraps','Bread','Leftover pasta',
         'Ice cream','Burgers','Frozen peas','Fries','Pizza','Dumplings','Fish fingers','Frozen berries','Chicken nuggets','Spinach',
         'Crisps','Pasta','Rice','Tinned tomatoes','Honey','Peanut butter','Cereal','Nuts','Popcorn','Olive oil','Chocolate','Oats','Tuna tins','Noodles','Soy sauce','Biscuits']
def item_for(s, default='Chicken'):
    txt = (s.get('action', '') + ' ' + s.get('headline', '') + ' ' + s.get('sub', '')).lower()
    for n in sorted(NAMES, key=len, reverse=True):
        if n.lower() in txt: return n
    return default
def ease(x): x = max(0, min(1, x)); return x * x * (3 - 2 * x)
def mix(a, b, k): return tuple(round(a[i] + (b[i] - a[i]) * k) for i in range(3))

async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch()
        c0 = await br.new_context(); await c0.route('**/*', route)
        pg0 = await c0.new_page(); await pg0.goto('https://myfridgie.netlify.app/'); await pg0.wait_for_timeout(700)
        await pg0.evaluate(SEED2); state = await c0.storage_state(); await c0.close()
        ctx = await br.new_context(viewport={'width': 1080, 'height': 1920}, device_scale_factor=1, storage_state=state)
        await ctx.route('**/*', route)
        pg = await ctx.new_page(); await pg.goto('https://stage.local/'); await pg.wait_for_timeout(1500)
        app = next(f for f in pg.frames if f.url.startswith('https://myfridgie'))
        await app.evaluate("""()=>{const s=document.createElement('style');s.textContent='*,*::before,*::after{transition:none!important;animation:none!important;scroll-behavior:auto!important} #localNote{display:none!important} ::-webkit-scrollbar{display:none}';document.head.appendChild(s);
          [...document.querySelectorAll('#fridgeView *')].filter(e=>e.children.length<3&&/still good\\?/.test(e.textContent)).forEach(e=>{let c=e;while(c.parentElement&&c.parentElement.id!=='fridgeView'&&c.offsetWidth<330)c=c.parentElement;c.style.display='none'});
          window.__byText=(re,sel)=>[...document.querySelectorAll(sel||'*')].filter(e=>e.offsetParent&&e.children.length<4&&new RegExp(re,'i').test(e.textContent.trim())).sort((a,b)=>a.textContent.length-b.textContent.length)[0]||null;}""")
        logo = await app.evaluate("()=>document.querySelector('header.top svg.logo').outerHTML")
        await pg.evaluate("l=>{const d=document.createElement('div');d.innerHTML=l;const s=d.firstChild;s.setAttribute('id','logo');s.style.width='220px';s.style.height='220px';document.getElementById('logo').replaceWith(s)}", logo)
        await pg.wait_for_timeout(400)

        async def rect(js):
            r = await app.evaluate(f"()=>{{const e={js};if(!e)return null;const b=e.getBoundingClientRect();return [b.left,b.top,b.width,b.height]}}")
            return None if not r else [SX + r[0] * Z, SY + r[1] * Z, r[2] * Z, r[3] * Z]
        async def maxscroll(): return await app.evaluate("()=>document.scrollingElement.scrollHeight-innerHeight")
        async def reset():
            await app.evaluate("()=>{try{closeSheet()}catch(e){};document.querySelector('[data-tab=fridge]')?.click();try{if(place!=='fridge')setPlace('fridge')}catch(e){}}")
            await pg.wait_for_timeout(120)
            await app.evaluate("()=>document.scrollingElement.scrollTop=0")

        # build an event list: (time, kind, payload)
        EV = []
        def tapjs(t, js): EV.append((t, 'tap', js))
        def clickjs(t, js): EV.append((t, 'click', js))
        def hl(t0, t1, js): EV.append((t0, 'hl', (js, t0, t1)))
        def scroll(t0, t1, to=1400): EV.append((t0, 'scroll', (t0, t1, to)))
        def run(t, js): EV.append((t, 'js', js))
        for i, s in enumerate(scenes):
            t = i * SCENE_LEN; scr = s.get('screen', 'home')
            EV.append((t + 0.02, 'reset', None))
            if scr == 'home':
                hl(t + 0.6, t + 1.7, "[...document.querySelectorAll('#fridgeView *')].find(e=>/need eating soon/.test(e.textContent)&&e.offsetWidth>300&&e.offsetHeight>100&&e.offsetHeight<300)")
                scroll(t + 1.9, t + 4.9)
            elif scr in ('freezer', 'cupboard'):
                k = 'freezer' if scr == 'freezer' else 'pantry'; sel = f"document.querySelector('[data-place={k}]')"
                hl(t + 0.15, t + 0.9, sel); tapjs(t + 0.8, sel); clickjs(t + 1.05, sel); scroll(t + 2.0, t + 4.9, 1300)
            elif scr in ('item', 'freeze_it'):
                name = item_for(s, 'Chicken' if scr == 'freeze_it' else 'Pasta')
                place = 'freezer' if name in NAMES[24:34] else 'pantry' if name in NAMES[34:] else None
                if place: clickjs(t + 0.1, f"document.querySelector('[data-place={place}]')")
                run(t + 0.15, f"(()=>{{const e=__byText('^{name}$','#fridgeView *');if(e)e.scrollIntoView({{block:'center'}})}})()")
                open_js = f"(()=>{{const it=items.find(i=>i.name==='{name}');openDetail(it.id)}})()"
                tapjs(t + 0.7, f"__byText('^{name}$','#fridgeView *')"); run(t + 0.95, open_js)
                if scr == 'item':
                    EV.append((t + 2.0, 'slider', (t + 2.0, t + 3.6, 100, 50)))
                else:
                    sel = "(document.querySelector('#dSpace [data-sp=freezer]')||[...document.querySelectorAll('button')].find(b=>/Freeze it/.test(b.textContent)&&b.offsetParent))"
                    hl(t + 1.5, t + 2.4, sel); tapjs(t + 2.3, sel); clickjs(t + 2.55, sel)
                    tapjs(t + 3.7, "document.querySelector('[data-place=freezer]')"); clickjs(t + 3.95, "document.querySelector('[data-place=freezer]')")
                    EV.append((t + 4.1, 'scroll_to', (t + 4.1, t + 4.9, f"__byText('^{name}$','#fridgeView *')")))
                    hl(t + 4.5, t + 5.15, f"__byText('^{name}$','#fridgeView *')")
            elif scr == 'recipes':
                sel = "document.querySelector('[data-tab=recipes]')"; tapjs(t + 0.6, sel); clickjs(t + 0.85, sel)
                EV.append((t + 1.8, 'scroll_to', (t + 1.8, t + 3.3, "[...document.querySelectorAll('#recipeView h3')].find(e=>/Ready to cook/.test(e.textContent))")))
                hl(t + 3.6, t + 4.9, "(()=>{let e=document.querySelectorAll('#recipeView h3')[1];while(e&&e.offsetHeight<200)e=e.parentElement;return e})()")
            elif scr in ('shopping', 'unpack'):
                tab = 'shop' if scr == 'shopping' else 'unpack'
                sel = f"document.querySelector('[data-tab={tab}]')||__byText('^{'Shopping' if scr=='shopping' else 'Unpack'}$','nav *')"
                tapjs(t + 0.6, sel); clickjs(t + 0.85, sel)
        EV.sort(key=lambda e: e[0])

        tap = None; hlc = None; scr_anim = None; sld = None; ei = 0
        n = int(TOTAL * FPS)
        for fi in range(n):
            t = fi / FPS
            while ei < len(EV) and EV[ei][0] <= t:
                _, kind, pl = EV[ei]; ei += 1
                if kind == 'reset': await reset(); scr_anim = None; sld = None
                elif kind == 'tap':
                    r = await rect(pl)
                    if r: tap = (r[0] + r[2] / 2, r[1] + r[3] / 2, t); TAPS.append(round(t, 2))
                elif kind == 'click':
                    await app.evaluate(f"()=>{{const e={pl};if(e)e.click()}}"); await pg.wait_for_timeout(150)
                    await app.evaluate("()=>document.scrollingElement.scrollTop=0")
                elif kind == 'js': await app.evaluate(f"()=>{pl}"); await pg.wait_for_timeout(150)
                elif kind == 'hl': hlc = (await rect(pl[0]), pl[1], pl[2])
                elif kind == 'scroll':
                    m = await maxscroll(); y0 = await app.evaluate("()=>document.scrollingElement.scrollTop"); scr_anim = (y0, min(m, pl[2]), pl[0], pl[1])
                elif kind == 'scroll_to':
                    top = await app.evaluate(f"()=>{{const e={pl[2]};return e?e.getBoundingClientRect().top+document.scrollingElement.scrollTop-60:0}}")
                    y0 = await app.evaluate("()=>document.scrollingElement.scrollTop"); scr_anim = (y0, top, pl[0], pl[1])
                elif kind == 'slider': sld = pl
            if scr_anim and scr_anim[2] <= t <= scr_anim[3] + 0.1:
                y0, y1, a, b = scr_anim
                await app.evaluate(f"()=>document.scrollingElement.scrollTop={y0 + (y1 - y0) * ease((t - a) / (b - a))}")
            if sld and sld[0] <= t <= sld[1] + 0.1:
                v = round(sld[2] + (sld[3] - sld[2]) * ease((t - sld[0]) / (sld[1] - sld[0])))
                await app.evaluate(f"()=>{{const r=document.getElementById('dRange');if(r){{r.value={v};r.dispatchEvent(new Event('input',{{bubbles:true}}))}}}}")
            si = max(k for k, s in enumerate(SCENES) if t >= s[0]); s0 = SCENES[si]; prev = SCENES[si - 1] if si else s0
            k = ease((t - s0[0]) / 0.45) if si else 1; hk = ease((t - s0[0]) / 0.4) if si else ease(t / 0.4)
            st = {'bg': 'rgb(%d,%d,%d)' % mix(prev[1], s0[1], k), 'cur': s0[2], 'prev': prev[2] if si else '', 'ci': hk,
                  'endk': ease((t - END_AT) / 0.4), 'popk': ease((t - END_AT - 0.15) / 0.5), 'phone': ease(t / 0.5), 'tap': None, 'hl': None}
            if tap and 0 <= t - tap[2] <= 0.6:
                q = (t - tap[2]) / 0.6; st['tap'] = [tap[0], tap[1], 0.6 + 0.6 * q, 1 - q]
            if hlc and hlc[0] and hlc[1] <= t <= hlc[2]:
                q = min((t - hlc[1]) / 0.25, (hlc[2] - t) / 0.25, 1); r = hlc[0]; st['hl'] = [r[0] - 12, r[1] - 12, r[2] + 24, r[3] + 24, q]
            await pg.evaluate("""s=>{
              document.getElementById('bg').style.background=s.bg;
              const h1=document.getElementById('h1'),h2=document.getElementById('h2');
              if(h1.dataset.v!==s.cur){h1.innerHTML=s.cur;h1.dataset.v=s.cur} if(h2.dataset.v!==s.prev){h2.innerHTML=s.prev;h2.dataset.v=s.prev}
              h1.style.opacity=s.ci; h1.style.transform=`translateY(${(1-s.ci)*40}px)`;
              h2.style.opacity=s.prev?1-s.ci:0; h2.style.transform=`translateY(${-s.ci*40}px)`;
              const ph=document.getElementById('phone'); ph.style.transform=`translateY(${(1-s.phone)*120}px)`; ph.style.opacity=s.phone;
              const tp=document.getElementById('tap'); if(s.tap){tp.style.left=s.tap[0]+'px';tp.style.top=s.tap[1]+'px';tp.style.transform=`scale(${s.tap[2]})`;tp.style.opacity=s.tap[3]}else tp.style.opacity=0;
              const hl=document.getElementById('hl'); if(s.hl){Object.assign(hl.style,{left:s.hl[0]+'px',top:s.hl[1]+'px',width:s.hl[2]+'px',height:s.hl[3]+'px',opacity:s.hl[4]})}else hl.style.opacity=0;
              const e=document.getElementById('end'); e.style.opacity=s.endk;
              [...e.children].forEach((c,i)=>{const k=Math.max(0,Math.min(1,s.popk*1.6-i*0.15));c.style.opacity=k;c.style.transform=`translateY(${(1-k)*30}px) scale(${0.92+0.08*k})`});
            }""", st)
            await pg.screenshot(path=str(FR / f'f{fi:04d}.png'))
        json.dump({'taps': TAPS, 'scenes': [s[0] for s in SCENES] + [END_AT], 'total': TOTAL}, open(D / 'timeline.json', 'w'))
        await br.close()

asyncio.run(main())
wav = str(D / f'music_{STYLE}.wav')
subprocess.run(['python3', str(D / 'music2.py'), STYLE, wav], check=True, cwd=str(D))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', str(FR / 'f%04d.png'), '-i', wav, '-c:v', 'libx264', '-preset', 'slow', '-crf', '17',
                '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-movflags', '+faststart', '-c:a', 'aac', '-b:a', '192k', '-shortest', OUTMP4], check=True)
print('done', OUTMP4)
