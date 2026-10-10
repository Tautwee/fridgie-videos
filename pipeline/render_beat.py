"""Short, beat-synced trend videos: every cut lands on a beat, the phone pulses with the kick,
build-up -> silence -> drop (flash + fast cuts) -> end card.

usage: python3 render_beat.py beatplan.json out.mp4
beatplan: {"title", "bpm", "music": "spookyhouse|phonk|house|...", "drop_beat": 8,
           "shots": [{"beats": 4, "kind": "text", "text": "POV: ... <b>word</b>", "bg": "#120a1f", "fx": "flicker|shake"},
                     {"beats": 2, "kind": "app", "screen": "home|freezer|cupboard|recipes|shopping", "focus": "Ham", "head": "...", "label": "auto", "bg": "#..."},
                     {"beats": 6, "kind": "add", "name": "Tosti ham", "head": "...", "bg": "#..."},
                     {"beats": 6, "kind": "end"}],
           "caption", "hashtags"}
"""
import shutil, os, asyncio, json, sys, subprocess, math, random
from playwright.async_api import async_playwright
from common import *

plan = json.load(open(sys.argv[1])); OUTMP4 = sys.argv[2]
FPS = 30; BPM = plan['bpm']; BEAT = 60 / BPM
FR = D / 'frames'; FR.mkdir(exist_ok=True)
for f in FR.glob('*.png'): f.unlink()
SX, SY, Z = 262, 626, 1.4256
random.seed(plan.get('title', 'x'))

# lay the shots on the beat grid
shots = []; b = 0
for s in plan['shots']:
    shots.append({**s, 't0': b * BEAT, 't1': (b + s['beats']) * BEAT, 'b0': b}); b += s['beats']
TOTAL = b * BEAT + 0.6
DROP = plan.get('drop_beat', 8) * BEAT
END_AT = next((s['t0'] for s in shots if s['kind'] == 'end'), TOTAL)
TAPS = []
def ease(x): x = max(0, min(1, x)); return x * x * (3 - 2 * x)

EXTRA_CSS = """
#big{position:absolute;left:130px;right:130px;top:0;bottom:0;display:flex;align-items:center;justify-content:center;text-align:center;color:#fff;
  font-family:Gabarito;font-weight:800;font-size:112px;line-height:1.05;letter-spacing:-1.5px;text-wrap:balance;opacity:0;z-index:25;text-shadow:0 8px 30px rgba(0,0,0,.35);padding-bottom:180px}
#big b{color:#ffc712}
#flash{position:absolute;inset:0;background:#fff;opacity:0;z-index:40;pointer-events:none}
#sticker{position:absolute;z-index:26;background:#ffc712;color:#11213e;font-family:Gabarito;font-weight:800;font-size:46px;padding:16px 30px;border-radius:60px;
  box-shadow:0 10px 0 #c99608,0 20px 40px rgba(0,0,0,.3);opacity:0;white-space:nowrap;transform-origin:50% 50%}
#vignette{position:absolute;inset:0;background:radial-gradient(ellipse 80% 70% at 50% 50%,rgba(0,0,0,0) 55%,rgba(0,0,0,.55));opacity:0;z-index:2;pointer-events:none}
"""

async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch()
        c0 = await br.new_context(); await c0.route('**/*', route)
        pg0 = await c0.new_page(); await pg0.goto('https://myfridgie.netlify.app/'); await pg0.wait_for_timeout(700)
        await pg0.evaluate(SEED2); state = await c0.storage_state(); await c0.close()
        ctx = await br.new_context(viewport={'width': 1080, 'height': 1920}, device_scale_factor=1, storage_state=state)
        await ctx.route('**/*', route)
        pg = await ctx.new_page(); await pg.goto('https://stage.local/'); await pg.wait_for_timeout(1500)
        await pg.evaluate("""css=>{const s=document.createElement('style');s.textContent=css;document.head.appendChild(s);
          for(const id of ['vignette','big','sticker','flash']){const d=document.createElement('div');d.id=id;document.body.appendChild(d)}
          document.getElementById('h2').style.display='none'}""", EXTRA_CSS)
        app = next(f for f in pg.frames if f.url.startswith('https://myfridgie'))
        await app.evaluate("""()=>{const s=document.createElement('style');s.textContent='*,*::before,*::after{transition:none!important;animation:none!important;scroll-behavior:auto!important} #localNote{display:none!important} ::-webkit-scrollbar{display:none}';document.head.appendChild(s);
          window.__byText=(re,sel)=>[...document.querySelectorAll(sel||'*')].filter(e=>e.offsetParent&&e.children.length<4&&new RegExp(re,'i').test(e.textContent.trim())).sort((a,b)=>a.textContent.length-b.textContent.length)[0]||null;
          window.__card=n=>{let e=__byText('^(❄\\s*)?'+n+'$','#fridgeView *');while(e&&e.offsetHeight<110)e=e.parentElement;return e};}""")
        logo = await app.evaluate("()=>document.querySelector('header.top svg.logo').outerHTML")
        await pg.evaluate("l=>{const d=document.createElement('div');d.innerHTML=l;const s=d.firstChild;s.setAttribute('id','logo');s.style.width='220px';s.style.height='220px';document.getElementById('logo').replaceWith(s)}", logo)
        await pg.wait_for_timeout(300)

        async def rect(js):
            r = await app.evaluate(f"()=>{{const e={js};if(!e)return null;const b=e.getBoundingClientRect();return [b.left,b.top,b.width,b.height]}}")
            return None if not r else [SX + r[0] * Z, SY + r[1] * Z, r[2] * Z, r[3] * Z]
        async def setup(s):
            await app.evaluate("()=>{try{closeSheet()}catch(e){};document.querySelector('[data-tab=fridge]')?.click();try{if(place!=='fridge')setPlace('fridge')}catch(e){}}")
            await pg.wait_for_timeout(80); await app.evaluate("()=>document.scrollingElement.scrollTop=0")
            scr = s.get('screen', 'home'); info = {}
            if scr in ('freezer', 'cupboard'): await app.evaluate(f"()=>setPlace('{'freezer' if scr == 'freezer' else 'pantry'}')")
            elif scr in ('recipes', 'shopping'):
                await app.evaluate(f"()=>document.querySelector('[data-tab={'recipes' if scr == 'recipes' else 'shop'}]')?.click()")
            await pg.wait_for_timeout(120); await app.evaluate("()=>document.scrollingElement.scrollTop=0")
            if s.get('focus'):
                n = s['focus']
                for pl in ('fridge', 'freezer', 'pantry'):  # find which space the item lives in
                    found = await app.evaluate(f"()=>!!__card({json.dumps(n)})")
                    if found: break
                    await app.evaluate(f"()=>setPlace('{pl if pl != 'fridge' else 'freezer'}')"); await pg.wait_for_timeout(100)
                await app.evaluate(f"()=>{{const e=__card({json.dumps(n)});if(e)e.scrollIntoView({{block:'center',inline:'center'}})}}")
                await pg.wait_for_timeout(100)
                await pg.evaluate("()=>{window.scrollTo(0,0);document.scrollingElement.scrollTop=0;document.scrollingElement.scrollLeft=0}")  # scrollIntoView also scrolls the stage
                info['rect'] = await rect(f"__card({json.dumps(n)})")
                if s.get('label', 'auto') == 'auto':
                    d = await app.evaluate(f"()=>{{const it=items.find(i=>i.name==={json.dumps(n)});return it?daysLeft(it.expires):null}}")
                    info['label'] = f"{n} · {'today' if d == 0 else 'tomorrow' if d == 1 else str(d) + ' days left'}" if d is not None else n
                else: info['label'] = s['label']
            if s['kind'] == 'add':
                await app.evaluate("()=>{openAdd()}"); await pg.wait_for_timeout(150)
            return info

        cur = -1; info = {}; typed = ''
        n = int(TOTAL * FPS)
        for fi in range(n):
            t = fi / FPS
            si = max(i for i, s in enumerate(shots) if t >= s['t0'] - 1e-6) if t < shots[-1]['t1'] else len(shots) - 1
            s = shots[si]
            if si != cur:
                cur = si; typed = ''; info = await setup(s) if s['kind'] in ('app', 'add') else {}
            lt = t - s['t0']; dur = s['t1'] - s['t0']
            bphase = (t % BEAT) / BEAT; since = (t % BEAT)
            post = t >= DROP
            bump = math.exp(-since * 10) * (0.045 if post else 0.02)
            st = {'bg': s.get('bg', '#11213e'), 'kind': s['kind'], 'big': '', 'bigo': 0, 'bigs': 1, 'head': '', 'heado': 0,
                  'phone': 1, 'ps': 1 + bump, 'px': 0, 'py': 0, 'flash': 0, 'stick': None, 'hl': None, 'tap': None, 'end': 0, 'vig': 0.6 if s.get('fx') else 0.25}
            if t >= DROP and t - DROP < 0.3: st['flash'] = 0.85 * (1 - (t - DROP) / 0.3)
            if s['kind'] == 'text':
                st['phone'] = 0; st['big'] = s['text']; st['bigo'] = 1; st['bigs'] = 1 + math.exp(-since * 9) * 0.05 + (0.06 * (1 - ease(lt / 0.18)))
                if s.get('fx') == 'flicker' and lt < 0.6: st['bigo'] = 1 if random.random() > 0.35 else 0.15
                if s.get('fx') == 'shake': st['px'] = random.uniform(-1, 1) * 14 * math.exp(-since * 6); st['py'] = random.uniform(-1, 1) * 14 * math.exp(-since * 6)
            elif s['kind'] in ('app', 'add'):
                st['head'] = s.get('head', ''); st['heado'] = ease(lt / 0.12)
                if s.get('fx') == 'shake': st['px'] = random.uniform(-1, 1) * 10 * math.exp(-since * 7)
                r = info.get('rect')
                if r:
                    st['hl'] = [r[0] - 12, r[1] - 12, r[2] + 24, r[3] + 24, ease(lt / 0.1)]
                    k = ease((lt - 0.05) / 0.15); x = min(max(r[0] + r[2] / 2, 330), 750); y = min(r[1] + r[3] + 70, 1500)
                    if y > 1480: y = r[1] - 70
                    st['stick'] = [x, y, info.get('label', ''), k, 1 + math.exp(-since * 9) * 0.06]
                if s['kind'] == 'add':
                    name = s['name']; nt = int(len(name) * ease(lt / (dur * 0.5)))
                    if name[:nt] != typed:
                        typed = name[:nt]
                        await app.evaluate(f"()=>{{const n=document.getElementById('aName');if(n){{n.value={json.dumps(typed)};n.oninput({{target:n}})}}}}")
                    if lt >= dur * 0.75 and not info.get('saved'):
                        r2 = await rect("document.getElementById('aSave')")
                        if r2: info['tap'] = (r2[0] + r2[2] / 2, r2[1] + r2[3] / 2, t); TAPS.append(round(t, 2))
                        await app.evaluate("()=>document.getElementById('aSave')?.click()"); await pg.wait_for_timeout(120)
                        info['saved'] = True
                tp = info.get('tap')
                if tp and 0 <= t - tp[2] <= 0.5: q = (t - tp[2]) / 0.5; st['tap'] = [tp[0], tp[1], 0.6 + 0.6 * q, 1 - q]
            elif s['kind'] == 'end':
                st['phone'] = 0; st['end'] = ease(lt / 0.25); st['endpop'] = ease((lt - 0.05) / 0.4)
            await pg.evaluate("""s=>{
              const g=id=>document.getElementById(id);
              g('bg').style.background=s.bg; g('vignette').style.opacity=s.vig;
              const big=g('big'); if(big.dataset.v!==s.big){big.innerHTML='<div>'+s.big+'</div>';big.dataset.v=s.big} big.style.opacity=s.bigo; big.style.transform=`translate(${s.px}px,${s.py}px) scale(${s.bigs})`;
              const h=g('h1'); if(h.dataset.v!==s.head){h.innerHTML=s.head;h.dataset.v=s.head} h.style.opacity=s.heado; h.style.transform=`translateY(${(1-s.heado)*25}px)`;
              const ph=g('phone'); ph.style.opacity=s.phone; ph.style.transform=`translate(${s.px}px,${s.py}px) scale(${s.ps})`;
              const hl=g('hl'); if(s.hl&&s.phone){Object.assign(hl.style,{left:s.hl[0]+'px',top:s.hl[1]+'px',width:s.hl[2]+'px',height:s.hl[3]+'px',opacity:s.hl[4]})}else hl.style.opacity=0;
              const st=g('sticker'); if(s.stick&&s.phone){if(st.dataset.v!==s.stick[2]){st.textContent=s.stick[2];st.dataset.v=s.stick[2]}
                 st.style.left=(s.stick[0]-st.offsetWidth/2)+'px'; st.style.top=(s.stick[1]-st.offsetHeight/2)+'px'; st.style.opacity=s.stick[3]; st.style.transform=`scale(${(0.7+0.3*s.stick[3])*s.stick[4]}) rotate(-3deg)`}else st.style.opacity=0;
              const tp=g('tap'); if(s.tap){tp.style.left=s.tap[0]+'px';tp.style.top=s.tap[1]+'px';tp.style.transform=`scale(${s.tap[2]})`;tp.style.opacity=s.tap[3]}else tp.style.opacity=0;
              g('flash').style.opacity=s.flash;
              const e=g('end'); e.style.opacity=s.end;
              [...e.children].forEach((c,i)=>{const k=Math.max(0,Math.min(1,(s.endpop||0)*1.6-i*0.15));c.style.opacity=k;c.style.transform=`translateY(${(1-k)*30}px) scale(${0.92+0.08*k})`});
            }""", st)
            await pg.evaluate("()=>{if(document.scrollingElement.scrollTop||document.scrollingElement.scrollLeft){window.scrollTo(0,0)}}")
            await pg.screenshot(path=str(FR / f'f{fi:04d}.png'))
        await br.close()
    tl = {'taps': TAPS, 'scenes': [0.0, DROP, END_AT], 'total': TOTAL, 'bpm': BPM, 'drop': DROP}
    json.dump(tl, open(D / 'timeline.json', 'w'))

asyncio.run(main())
TLD = D / 'timelines'; TLD.mkdir(exist_ok=True)
shutil.copy(D / 'timeline.json', TLD / (os.path.basename(OUTMP4).rsplit('.', 1)[0] + '.json'))
wav = str(D / 'music_tmp.wav')
subprocess.run(['python3', str(D / 'music3.py'), plan.get('music', 'house'), wav, os.path.basename(OUTMP4), str(D / 'timeline.json')], check=True, cwd=str(D))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', str(FR / 'f%04d.png'), '-i', wav, '-c:v', 'libx264', '-preset', 'slow', '-crf', '17',
                '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-movflags', '+faststart', '-c:a', 'aac', '-b:a', '192k', '-shortest', OUTMP4], check=True)
print('done', OUTMP4, f'{TOTAL:.1f}s')
