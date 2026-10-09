import numpy as np, json, wave, sys
SR = 44100
style = sys.argv[1]; out = sys.argv[2]
tl = json.load(open('timeline.json'))
T = tl['total']; N = int(SR * T)
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(11)

def note(m): return 440 * 2 ** ((m - 69) / 12)
def add(sig, t0, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N or i < 0: return
    s = sig[: N - i] * gain
    L[i:i + len(s)] += s * (1 - max(pan, 0)); R[i:i + len(s)] += s * (1 + min(pan, 0))
def env(n, a=0.005, d=0.3):
    t = np.arange(n) / SR
    return np.minimum(t / max(a, 1e-4), 1) * np.exp(-t / d)
def lp(x, k):  # one-pole lowpass, vectorised enough for short buffers
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)): acc += k * (x[i] - acc); y[i] = acc
    return y
def tone(f, dur, shape='sine', a=0.005, d=0.4):
    n = int(SR * dur); t = np.arange(n) / SR
    if shape == 'sine': s = np.sin(2*np.pi*f*t)
    elif shape == 'epiano': s = np.sin(2*np.pi*f*t + 1.2*np.exp(-t*6)*np.sin(2*np.pi*f*t)) + 0.15*np.sin(4*np.pi*f*t)
    elif shape == 'saw':
        s = sum(np.sin(2*np.pi*f*k*t)/k for k in range(1, 9)) * 0.6
    elif shape == 'square':
        s = sum(np.sin(2*np.pi*f*k*t)/k for k in range(1, 10, 2)) * 0.8
    return s * env(n, a, d)
def kick(punch=1.0, dec=9):
    n = int(SR*0.4); t = np.arange(n)/SR; f = 45 + 100*punch*np.exp(-t*30)
    return np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t*dec)
def noise_hit(dur, k_hp, dec):
    n = int(SR*dur); x = rng.normal(0, 1, n); x = x - lp(x, k_hp); return x * env(n, 0.0008, dec)
def clap(): return noise_hit(0.22, 0.25, 0.07)
def hat(): return noise_hit(0.05, 0.6, 0.014)
def rim(): n=int(SR*0.08); t=np.arange(n)/SR; return (np.sin(2*np.pi*1700*t)*0.6+rng.normal(0,0.3,n))*env(n,0.0005,0.012)

P = dict(
    upbeat=dict(bpm=116, prog=[[60,64,67,71],[57,60,64,67],[53,57,60,64],[55,59,62,67]], keys='epiano', arp=True, drums='pop', bass='sine', swing=0, crackle=0),
    chill=dict(bpm=86, prog=[[62,65,69,72],[60,64,67,71],[57,60,64,67],[58,62,65,69]], keys='epiano', arp=False, drums='lofi', bass='sine', swing=0.18, crackle=1),
    energy=dict(bpm=124, prog=[[57,60,64],[53,57,60],[60,64,67],[55,59,62]], keys='saw', arp=True, drums='house', bass='square', swing=0, crackle=0),
)[style]
beat = 60 / P['bpm']; bar = beat * 4
nbars = int(T / bar) + 1
for b in range(nbars):
    t0 = b * bar; ch = P['prog'][b % 4]
    # chords
    if P['keys'] == 'epiano':
        hits = [0, 2.5] if style == 'chill' else [0, 1.5, 2.5]
        for h in hits:
            for m in ch: add(tone(note(m), beat*1.6, 'epiano', 0.004, 0.55 if style=='chill' else 0.35), t0 + h*beat, 0.07, pan=(m%3-1)*0.25)
    else:  # energy: offbeat saw stabs
        for k in range(4):
            for m in ch: add(lp(tone(note(m+12), beat*0.45, 'saw', 0.003, 0.12), 0.35), t0 + (k+0.5)*beat, 0.05, pan=(m%3-1)*0.3)
    # bass
    root = ch[0] - 24
    if style == 'energy':
        for k in range(8): add(lp(tone(note(root + (12 if k%2 else 0)), beat*0.45, 'square', 0.003, 0.15), 0.2), t0 + k*beat/2, 0.22)
    else:
        add(tone(note(root), bar*0.95, 'sine', 0.01, 1.2), t0, 0.32)
        if style == 'upbeat': add(tone(note(root+7), beat, 'sine', 0.01, 0.3), t0 + 2.5*beat, 0.2)
    # arp
    if P['arp'] and b > 0:
        seq = [0,2,1,3,2,1,3,2]
        for k in range(8):
            m = ch[seq[k] % len(ch)] + 12
            add(tone(note(m), beat*0.5, 'sine' if style=='upbeat' else 'saw', 0.002, 0.12), t0 + k*beat/2, 0.09 if style=='upbeat' else 0.04, pan=0.35 if k%2 else -0.35)
    if style == 'chill':  # little melody
        mel = [ch[-1]+12, ch[-2]+12, ch[-1]+12+2, ch[-2]+12]
        for k, m in enumerate(mel): add(tone(note(m), beat, 'sine', 0.02, 0.5), t0 + k*beat + 0.5*beat, 0.06, pan=0.2)

# drums
nb = int(T / beat)
for k in range(nb):
    tt = k * beat
    if tt > T - 1.0: break
    sw = P['swing'] * beat
    if P['drums'] == 'pop':
        if k >= 4 or k % 2 == 0: add(kick(), tt, 0.7)
        if k >= 4 and k % 2 == 1: add(clap(), tt, 0.16)
        add(hat(), tt + beat/2, 0.06, 0.2)
    elif P['drums'] == 'lofi':
        if k % 4 in (0,) or (k % 4 == 2 and k % 8 == 6): add(kick(0.6, 7), tt, 0.55)
        if k % 2 == 1: add(rim(), tt, 0.22)
        add(hat(), tt, 0.03, -0.2); add(hat(), tt + beat/2 + sw, 0.04, 0.2)
    else:
        add(kick(1.2, 10), tt, 0.8)
        if k % 2 == 1: add(clap(), tt, 0.2)
        add(noise_hit(0.08, 0.5, 0.03), tt + beat/2, 0.07, 0.15)
        add(hat(), tt + beat/4, 0.03, -0.2); add(hat(), tt + 3*beat/4, 0.03, -0.2)
if P['crackle']:
    c = np.zeros(N); idx = rng.integers(0, N, int(T*25)); c[idx] = rng.normal(0, 0.25, len(idx)); c = c - lp(c, 0.5)
    L += c*0.15; R += c*0.15
    hiss = rng.normal(0, 1, N); hiss = lp(hiss, 0.05) * 0.01; L += hiss; R += hiss

# sidechain feel on non-chill
if style != 'chill':
    duck = np.ones(N)
    for k in range(nb):
        i = int(k*beat*SR); n = int(0.18*SR); seg = duck[i:i+n]; duck[i:i+n] = np.minimum(seg, 0.55 + 0.45*np.linspace(0,1,len(seg)))
    L *= duck; R *= duck

# SFX: taps, whooshes, end ding
def pop():
    n = int(SR*0.12); t = np.arange(n)/SR; return np.sin(2*np.pi*(1100-3000*t)*t) * env(n, 0.001, 0.035)
def whoosh(d=0.45):
    n = int(SR*d); x = rng.normal(0,1,n); t = np.arange(n)/SR; y = np.empty(n); acc = 0.0
    for i in range(n):
        k = 0.02 + 0.35*np.sin(np.pi*t[i]/d); acc += k*(x[i]-acc); y[i] = acc
    return y * np.sin(np.pi*t/d)**2
def ding():
    n = int(SR*1.4); t = np.arange(n)/SR
    return (np.sin(2*np.pi*1318.5*t) + 0.5*np.sin(2*np.pi*1975.5*t)) * env(n, 0.002, 0.45)
for tp in tl['taps']: add(pop(), tp, 0.45)
for sc in tl['scenes'][1:]: add(whoosh(), sc - 0.2, 0.4)
add(ding(), tl['scenes'][-1] + 0.15, 0.2)

fade = np.ones(N); fo = int(1.4*SR); fade[-fo:] = np.linspace(1, 0, fo); fade[:int(0.04*SR)] = np.linspace(0, 1, int(0.04*SR))
st = np.stack([L*fade, R*fade], 1); st = np.tanh(st*1.1); st = st/np.max(np.abs(st))*0.89
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st*32767).astype('<i2').tobytes())
print(style, 'ok')
