"""Fridgeroo soundtrack generator v3 — a different track for every video.

usage: python3 music3.py <style|auto> <out.wav> [seed-text] [timeline.json]
styles: house, futurebass, lofi, disco, afro, synthwave, trap, tropical  (auto = picked from seed-text)
Everything is synthesised here (no samples), so every track is ours to use.
"""
import numpy as np, json, wave, sys, hashlib
from scipy.signal import butter, sosfilt, fftconvolve

SR = 44100
STYLES = ['house', 'futurebass', 'lofi', 'disco', 'afro', 'synthwave', 'trap', 'tropical']
style = sys.argv[1]; out = sys.argv[2]
seedtxt = sys.argv[3] if len(sys.argv) > 3 else out
tlpath = sys.argv[4] if len(sys.argv) > 4 else 'timeline.json'
H = int(hashlib.md5(seedtxt.encode()).hexdigest(), 16)
import re, datetime
if style in ('auto', 'energy', 'upbeat', 'chill'):
    style = {'upbeat': 'tropical', 'chill': 'lofi'}.get(style)
    m = re.search(r'(20\d{6})-(\d{2})(\d{2})', seedtxt)
    if not style and m:  # rotate by posting slot, so two posts in a row never share a genre
        day = datetime.date(int(m[1][:4]), int(m[1][4:6]), int(m[1][6:])).toordinal()
        style = STYLES[(day * 2 + (int(m[2]) >= 15)) % len(STYLES)]
    style = style or STYLES[H % len(STYLES)]
rng = np.random.default_rng(H % (2**32))

tl = json.load(open(tlpath))
T = tl['total']; N = int(SR * T)
END = tl['scenes'][-1]

# ---------------------------------------------------------------- buses
bus = {k: np.zeros((N, 2)) for k in ('drums', 'bass', 'music', 'lead', 'send', 'sfx')}
def add(name, sig, t0, gain=1.0, pan=0.0):
    i = int(round(t0 * SR))
    if i >= N or len(sig) == 0: return
    if i < 0: sig = sig[-i:]; i = 0
    s = sig[: N - i] * gain
    if s.ndim == 1:
        l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
        s = np.stack([s * l * 1.414, s * r * 1.414], 1)
    bus[name][i:i + len(s)] += s

# ---------------------------------------------------------------- dsp helpers
def filt(x, f, kind='low', order=2):
    f = min(max(f, 20), SR / 2 * 0.95)
    return sosfilt(butter(order, f, kind, fs=SR, output='sos'), x, axis=0)
def env(n, a=0.005, d=0.3, s=0.0, r=None):
    t = np.arange(n) / SR
    e = np.minimum(t / max(a, 1e-4), 1) * (s + (1 - s) * np.exp(-t / max(d, 1e-4)))
    k = int(min(n, max(r or 0, 0.006) * SR))  # always fade out: no clicks
    if k: e[-k:] *= np.linspace(1, 0, k)
    return e
def E(x, *a):  # apply an envelope sized to the sound itself
    return x * env(len(x), *a)
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def tt(dur): return np.arange(int(SR * dur)) / SR

def saw(f, dur, ph=0.0): t = tt(dur); return 2 * ((t * f + ph) % 1) - 1
def sq(f, dur, pw=0.5): t = tt(dur); return np.where((t * f) % 1 < pw, 1.0, -1.0)
def tri(f, dur): return 2 * np.abs(saw(f, dur)) - 1
def sine(f, dur): return np.sin(2 * np.pi * f * tt(dur))

def supersaw(f, dur, voices=7, detune=0.18, cut=5000, a=0.01, d=0.6, s=0.6, r=0.08):
    n = int(SR * dur); L = np.zeros(n); R = np.zeros(n)
    for v in range(voices):
        dt = (v - (voices - 1) / 2) / ((voices - 1) / 2) * detune
        x = saw(f * 2 ** (dt / 12), dur, rng.random())
        p = (v / (voices - 1)) * 2 - 1
        L += x * (1 - p) / 2; R += x * (1 + p) / 2
    st = np.stack([L, R], 1) / voices * 1.6
    return filt(st, cut) * env(n, a, d, s, r)[:, None]

def pluck(f, dur, bright=0.6, decay=0.996):
    n = int(SR * dur); P = max(2, int(SR / f)); y = np.zeros(n + P + 1)
    y[:P] = filt(rng.uniform(-1, 1, P), 1500 + 9000 * bright)
    i = P
    while i < n + P:  # Karplus-Strong, one period at a time
        k = min(P, n + P - i)
        y[i:i + k] = decay * 0.5 * (y[i - P:i - P + k] + y[i - P + 1:i - P + k + 1])
        i += k
    return y[P:P + n] * env(n, 0.001, dur, 1, 0.02)

def epiano(f, dur, d=0.9):
    t = tt(dur); n = len(t)
    m = np.sin(2 * np.pi * f * 14 * t) * np.exp(-t * 9) * 0.25
    s = np.sin(2 * np.pi * f * t + 1.6 * np.exp(-t * 4) * np.sin(2 * np.pi * f * t) + m)
    return (s + 0.12 * np.sin(4 * np.pi * f * t)) * env(n, 0.003, d, 0.0, 0.05)

def marimba(f, dur):
    t = tt(dur); n = len(t)
    return (np.sin(2 * np.pi * f * t) * np.exp(-t * 7) + 0.35 * np.sin(2 * np.pi * f * 3.93 * t) * np.exp(-t * 28)) * env(n, 0.001, 9, 1, 0.01)

def bell(f, dur):
    t = tt(dur); n = len(t)
    return np.sin(2 * np.pi * f * t + 2.2 * np.exp(-t * 3) * np.sin(2 * np.pi * f * 3.5 * t)) * np.exp(-t * 3.2) * env(n, 0.002, 9, 1, 0.03)

def organ_stab(f, dur):
    return sum(np.sin(2 * np.pi * f * k * tt(dur)) / k for k in (1, 2, 3, 4)) * env(int(SR * (dur)), 0.004, 0.12, 0.0, 0.03)

# drums
def kick(punch=1.0, dec=8.0, low=56):
    t = tt(0.45); f = low + 120 * punch * np.exp(-t * 32)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * dec)
    click = rng.normal(0, 1, len(t)) * np.exp(-t * 400) * 0.25
    return np.tanh((x + click) * 1.4)
def k808(m, dur, glide_to=None):
    t = tt(dur); f0 = hz(m); f1 = hz(glide_to) if glide_to else f0
    f = f0 + (f1 - f0) * np.clip(t / 0.12, 0, 1) + 90 * np.exp(-t * 40)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return np.tanh(x * 2.2) * env(len(t), 0.002, dur * 0.9, 0.2, 0.05)
def noise(dur): return rng.normal(0, 1, int(SR * dur))
def snare(tone=190, dec=0.12, bright=1.0):
    t = tt(0.3)
    n = filt(noise(0.3), 1800 * bright, 'high') * np.exp(-t / dec)
    b = np.sin(2 * np.pi * tone * t) * np.exp(-t * 25)
    return n * 0.7 + b * 0.6
def clap():
    x = np.zeros(int(SR * 0.3))
    for k, o in enumerate((0, 0.011, 0.022)):
        b = filt(noise(0.3), 1200, 'high') * env(int(SR * 0.3), 0.0005, 0.012 if k < 2 else 0.11)
        i = int(o * SR); x[i:] += b[:len(x) - i]
    return filt(x, 900, 'high') * 0.8
def hat(open_=False):
    d = 0.32 if open_ else 0.045
    return filt(noise(d), 7500, 'high', 3) * env(int(SR * d), 0.0005, d / 3.5 if open_ else 0.012)
def shaker(): return filt(noise(0.09), 5000, 'high') * env(int(SR * 0.09), 0.02, 0.02)
def tom(f): t = tt(0.4); return np.sin(2 * np.pi * (f + f * 0.6 * np.exp(-t * 30)) * t) * np.exp(-t * 9)
def crash(): return filt(noise(1.8), 4000, 'high') * env(int(SR * 1.8), 0.001, 0.5)
def riser(dur):
    n = int(SR * dur); x = noise(dur); out = np.zeros(n); seg = int(SR * 0.05)
    for i in range(0, n, seg):
        k = i / n; out[i:i + seg] = filt(x[i:i + seg], 400 + 9000 * k ** 2, 'band' if False else 'low')
    return out * np.linspace(0, 1, n) ** 2

# ---------------------------------------------------------------- music theory
MAJ = [0, 2, 4, 5, 7, 9, 11]; MIN = [0, 2, 3, 5, 7, 8, 10]
PROGS = {'maj': [[0, 4, 5, 3], [5, 3, 0, 4], [0, 5, 3, 4], [3, 4, 2, 5], [0, 3, 5, 4], [3, 0, 4, 5]],
         'min': [[0, 5, 2, 6], [0, 3, 5, 4], [0, 6, 5, 6], [5, 6, 0, 0], [0, 5, 3, 4], [0, 2, 6, 5]]}
CFG = {  # bpm range, mode, swing
    'house': ((120, 126), 'min', 0.0), 'futurebass': ((144, 152), 'maj', 0.0), 'lofi': ((78, 90), 'maj', 0.16),
    'disco': ((112, 120), 'min', 0.0), 'afro': ((108, 116), 'min', 0.06), 'synthwave': ((96, 106), 'min', 0.0),
    'trap': ((136, 146), 'min', 0.0), 'tropical': ((100, 110), 'maj', 0.0),
    'spookyhouse': ((122, 126), 'min', 0.0), 'phonk': ((128, 132), 'min', 0.0)}
(b0, b1), mode, SWING = CFG[style]
if style in ('house', 'disco', 'afro') and rng.random() < 0.35: mode = 'maj'
bpm = tl.get('bpm') or int(rng.integers(b0, b1 + 1)); beat = 60 / bpm; bar = beat * 4  # beat videos lock the tempo
key = 52 + int(rng.integers(0, 10))  # E3..C#4 root
scale = MAJ if mode == 'maj' else MIN
prog = PROGS[mode][int(rng.integers(0, len(PROGS[mode])))]
def deg(d, octv=0): return key + 12 * (octv + d // 7) + scale[d % 7]
def chord(d, sev=False, octv=0):
    ns = [deg(d, octv), deg(d + 2, octv), deg(d + 4, octv)]
    if sev: ns.append(deg(d + 6, octv))
    return ns
nbars = int(np.ceil(T / bar)) + 1
def sw(k16):  # swing 16ths
    return k16 * beat / 4 + (SWING * beat / 4 if k16 % 2 else 0)

# melody: a 2-bar hook, chord tones on strong steps, repeated with a twist
def make_hook():
    rhythms = {'house': '1.1.1..1.1.11..1', 'futurebass': '1..1..1.1..1.1..', 'lofi': '1...1.1.....1...', 'disco': '1.11.1.1.11.1...',
               'afro': '1..1..1...1.1...', 'synthwave': '1...1...1.1.1...', 'trap': '1..1..1.....1.1.', 'tropical': '1..1..1.1..1..1.', 'spookyhouse': '1.1.1...1.1.1...', 'phonk': '1.11.1.11.1.1.1.'}
    r = rhythms[style]; notes = []
    for half in range(2):
        cd = prog[half % len(prog)]; tones = [cd, cd + 2, cd + 4]; prev = cd + 7
        for k, c in enumerate(r):
            if c != '1': continue
            if k % 4 == 0: d = tones[int(rng.integers(0, 3))] + 7
            else: d = prev + int(rng.choice([-2, -1, 1, 2, 0]))
            d = int(np.clip(d, cd + 3, cd + 12)); prev = d
            notes.append((half * 16 + k, d))
    return notes
HOOK = make_hook()
def hook_events(rep):
    ev = list(HOOK)
    if rep % 2 == 1 and len(ev) > 3:  # answer phrase: last notes resolve to the root
        ev[-1] = (ev[-1][0], prog[0] + 7); ev[-2] = (ev[-2][0], ev[-2][1] + int(rng.choice([-1, 1])))
    return ev

# ---------------------------------------------------------------- arrangement
scenes = tl['scenes']
intro_end = tl['drop'] if 'drop' in tl else (bar if T > 10 else 0)
kicks = []
melody_start = tl['drop'] if 'drop' in tl else (scenes[1] if len(scenes) > 2 else bar * 2)

for b in range(nbars):
    t0 = b * bar
    if t0 > T: break
    cd = prog[b % len(prog)]
    full = t0 >= intro_end
    ending = t0 >= END - 0.01
    # ---------------- chords / pads
    if style in ('house',):
        for h in ([0.5, 1.5, 2.75, 3.5] if b % 2 else [0.5, 1.5, 2.5, 3.25]):
            for m in chord(cd, True, 1): add('music', organ_stab(hz(m), beat * 0.5), t0 + h * beat, 0.085, pan=(m % 5 - 2) * 0.15)
    elif style == 'futurebass':
        for k in range(8):
            for m in chord(cd, True, 1): add('music', supersaw(hz(m), beat * 0.5, cut=4500, d=0.3, s=0.5), t0 + k * beat / 2, 0.028)
    elif style == 'lofi':
        for h in (0, 2.5):
            for j, m in enumerate(chord(cd, True, 0)): add('music', epiano(hz(m), beat * 2.2, 1.2), t0 + h * beat + j * 0.012, 0.075, pan=(j - 1.5) * 0.25)
    elif style == 'disco':
        for k in range(16):
            if k % 4 in (1, 3) or k % 8 == 6:
                for m in chord(cd, False, 1): add('music', pluck(hz(m), beat * 0.22, 0.8), t0 + k * beat / 4, 0.1, pan=0.4)
        if b % 2 == 0:
            for m in chord(cd, True, 1): add('music', supersaw(hz(m), bar * 0.9, 5, 0.12, 2600, 0.15, 1.5, 0.7, 0.3), t0, 0.02)
    elif style == 'afro':
        for m in chord(cd, True, 0): add('music', supersaw(hz(m), bar, 3, 0.08, 1400, 0.3, 2, 0.8, 0.4), t0, 0.022)
        for k, h in enumerate([0, 0.75, 1.5, 2.5, 3, 3.5]):
            m = chord(cd, True, 1)[k % 4]; add('lead', marimba(hz(m + 12), 0.5), t0 + h * beat, 0.07, pan=(k % 3 - 1) * 0.4)
    elif style == 'synthwave':
        for m in chord(cd, True, 0): add('music', supersaw(hz(m), bar, 5, 0.2, 2200, 0.25, 2, 0.8, 0.3), t0, 0.022)
        arp = chord(cd, True, 1)
        for k in range(16):
            m = arp[[0, 1, 2, 3, 2, 1, 0, 2][k % 8]]
            add('music', filt(saw(hz(m), beat / 4 * 0.9), 1300 + 700 * np.sin(b + k / 8)) * env(int(SR * (beat / 4 * 0.9)), 0.002, 0.08), t0 + k * beat / 4, 0.045, pan=0.3 if k % 2 else -0.3)
    elif style == 'trap':
        for m in chord(cd, False, 1): add('music', supersaw(hz(m), bar, 3, 0.1, 1100, 0.4, 2, 0.8, 0.5), t0, 0.018)
    elif style == 'spookyhouse':
        arp = chord(cd, False, 2)
        for k in range(8):  # music-box arpeggio
            add('music', bell(hz(arp[[0, 2, 1, 2][k % 4]]), beat * 0.9), t0 + k * beat / 2, 0.05, pan=0.35 if k % 2 else -0.35)
        for h in (0.5, 1.5, 2.5, 3.5):
            for m in chord(cd, False, 1): add('music', organ_stab(hz(m), beat * 0.35), t0 + h * beat, 0.07, pan=(m % 3 - 1) * 0.2)
        if t0 < intro_end:  # eerie theremin in the build
            th = deg(cd + 4, 2); tq = tt(bar); x = np.sin(2 * np.pi * hz(th) * tq + 0.6 * np.sin(2 * np.pi * 5.5 * tq) * 6)
            add('music', E(x, 0.4, 3, 0.8, 0.4), t0, 0.03)
    elif style == 'phonk':
        for m in chord(cd, False, 0): add('music', supersaw(hz(m), bar, 3, 0.15, 900, 0.3, 2, 0.8, 0.4), t0, 0.02)
    elif style == 'tropical':
        for h in (0, 0.75, 1.5, 2.5, 3.25):
            for m in chord(cd, False, 1): add('music', marimba(hz(m), 0.45) * 0.8 + pluck(hz(m), 0.45, 0.5) * 0.5, t0 + h * beat, 0.085, pan=(m % 3 - 1) * 0.3)

    # ---------------- bass
    root = deg(cd, -2)
    if style == 'spookyhouse':
        for k in range(1, 8, 2):
            add('bass', E(filt(saw(hz(root), beat * 0.42), 800), 0.003, 0.15, 0.3, 0.03), t0 + k * beat / 2, 0.3)
    elif style == 'phonk' and t0 >= intro_end:
        for k16, gl in ((0, None), (3, None), (6, None), (10, root + 3)):
            add('bass', np.tanh(k808(root, beat * 0.7, gl) * 1.8), t0 + k16 * beat / 4, 0.42)
    if style in ('house', 'disco'):
        for k in range(8):
            m = root + (12 if (style == 'disco' and k % 2) else 0)
            if style == 'house' and k % 2 == 0: continue
            add('bass', E(filt(saw(hz(m), beat * 0.42), 900), 0.003, 0.15, 0.3, 0.03), t0 + k * beat / 2, 0.3)
    elif style == 'futurebass':
        add('bass', E(sine(hz(root), bar * 0.95), 0.01, 2, 0.8, 0.1), t0, 0.25)
    elif style == 'lofi':
        for h, l in ((0, 1.6), (2.5, 1.2)):
            add('bass', filt(tri(hz(root + (7 if h else 0)), beat * l), 500) * env(int(SR * (beat * l)), 0.01, 0.6, 0.4, 0.05), t0 + h * beat, 0.4)
    elif style == 'afro':
        for h in (0, 1.5, 2.5, 3.25):
            add('bass', sine(hz(root + (12 if h == 3.25 else 0)), beat * 0.6) * env(int(SR * (beat * 0.6)), 0.005, 0.3, 0.3, 0.05), t0 + h * beat, 0.42)
    elif style == 'synthwave':
        for k in range(8):
            add('bass', filt(saw(hz(root + (12 if k % 4 == 3 else 0)), beat * 0.45), 700) * env(int(SR * (beat * 0.45)), 0.003, 0.2, 0.4, 0.03), t0 + k * beat / 2, 0.3)
    elif style == 'trap':
        nxt = deg(prog[(b + 1) % len(prog)], -2)
        add('bass', k808(root, beat * 1.4), t0, 0.5)
        add('bass', k808(root, beat * 1.1, nxt if b % 2 else None), t0 + 2.5 * beat, 0.45)
    elif style == 'tropical':
        for h in (0, 1.5, 2, 3.5):
            add('bass', E(sine(hz(root), beat * 0.5), 0.005, 0.25, 0.3, 0.04), t0 + h * beat, 0.3)

    # ---------------- drums
    if not full: continue
    for q in range(4):
        tb = t0 + q * beat
        if tb > T - 0.8: break
        if style in ('house', 'disco', 'synthwave', 'tropical', 'spookyhouse'):
            add('drums', kick(1.1, 8 if style != 'synthwave' else 6), tb, 0.85); kicks.append(tb)
        elif style == 'afro':
            if q in (0, 2): add('drums', kick(0.9, 9), tb, 0.8); kicks.append(tb)
            if q == 1: add('drums', kick(0.9, 9), tb + beat * 0.5, 0.6); kicks.append(tb + beat * 0.5)
        elif style == 'lofi':
            if q == 0 or (q == 2 and b % 2): add('drums', filt(kick(0.6, 7), 3000), tb + (0.5 * beat if q == 2 else 0), 0.7); kicks.append(tb)
        elif style in ('futurebass', 'trap'):
            if q == 0: add('drums', kick(1.2, 7), tb, 0.85); kicks.append(tb)
            if style == 'futurebass' and q == 1: add('drums', kick(1.0, 9), tb + beat * 0.5, 0.6); kicks.append(tb + beat * 0.5)
        # backbeat
        if style in ('house', 'disco', 'tropical', 'afro', 'spookyhouse') and q in (1, 3): add('drums', clap(), tb, 0.45, 0.05)
        if style == 'lofi' and q in (1, 3): add('drums', filt(snare(200, 0.09, 0.6), 4000), tb + SWING * beat / 2, 0.5)
        if style == 'synthwave' and q in (1, 3):
            s = snare(180, 0.18); add('drums', s, tb, 0.55); add('send', s, tb, 0.6)
        if style in ('futurebass', 'trap') and q == 2:
            add('drums', snare(210, 0.14) * 0.6 + clap() * 0.7, tb, 0.6); add('send', clap(), tb, 0.3)
    # hats & percussion
    for k16 in range(16):
        tk = t0 + sw(k16)
        if tk > T - 0.8: break
        if style == 'house':
            if k16 % 4 == 2: add('drums', hat(True), tk, 0.12, 0.2)
            elif k16 % 2 == 1: add('drums', hat(), tk, 0.06, -0.2)
        elif style == 'disco': add('drums', hat(k16 % 4 == 2), tk, 0.1 if k16 % 4 == 2 else 0.05, 0.25)
        elif style == 'afro':
            add('drums', shaker(), tk, 0.07 if k16 % 2 else 0.04, -0.3)
            if k16 in (3, 6, 10, 14): add('drums', tom(220 if k16 in (3, 10) else 330), tk, 0.18, 0.4)
        elif style == 'lofi':
            if k16 % 2 == 0: add('drums', hat(), tk, 0.04 + 0.02 * (k16 % 4 == 0), 0.2)
        elif style == 'synthwave':
            if k16 % 2 == 0: add('drums', hat(), tk, 0.05, 0.3)
        elif style == 'futurebass':
            if k16 % 2 == 0: add('drums', hat(), tk, 0.05, 0.25)
        elif style == 'trap':
            if b % 2 == 1 and k16 >= 12:
                for r in range(3): add('drums', hat(), tk + r * beat / 12, 0.05, 0.3)
            elif k16 % 2 == 0: add('drums', hat(), tk, 0.06, 0.3)
        elif style == 'tropical':
            if k16 % 2 == 1: add('drums', shaker(), tk, 0.06, 0.3)
        elif style == 'spookyhouse':
            if k16 % 4 == 2: add('drums', hat(True), tk, 0.12, 0.2)
            elif k16 % 2 == 1: add('drums', hat(), tk, 0.06, -0.2)
        elif style == 'phonk':  # brega-funk / tamborzao style groove
            if k16 in (0, 3, 6, 10): add('drums', kick(1.3, 7), tk, 0.85); kicks.append(tk)
            if k16 in (4, 12): add('drums', snare(220, 0.1) * 0.7 + clap() * 0.8, tk, 0.6); add('send', clap(), tk, 0.2)
            if k16 in (7, 13, 15): add('drums', tom(160 if k16 == 7 else 240), tk, 0.25, 0.3)
            if k16 % 2 == 0: add('drums', hat(k16 == 14), tk, 0.06, 0.3)

# ---------------- lead hook (from scene 2, and loud on the end card)
rep = 0; t = melody_start - (melody_start % (bar * 2)) if melody_start > bar * 2 else melody_start
t = max(t, intro_end)
LEADV = {'house': 'pluck', 'futurebass': 'saw', 'lofi': 'sine', 'disco': 'saw', 'afro': 'bell', 'synthwave': 'saw', 'trap': 'bell', 'tropical': 'pluck',
         'spookyhouse': 'pluck', 'phonk': 'cowbell'}[style]
def cowbell(f, dur):  # phonk cowbell: two clangy square partials
    x = sq(f, dur) * 0.6 + sq(f * 1.48, dur) * 0.4
    return E(filt(np.tanh(x * 1.5), 5000), 0.001, 0.12, 0.0, 0.02)
while t < T - 1.2:
    for k16, d in hook_events(rep):
        tn = t + sw(k16)
        if tn > T - 1.0: break
        m = deg(d, 1 if style not in ('trap', 'afro') else 1); f = hz(m); du = beat * 0.45
        if LEADV == 'pluck': x = pluck(f, du * 1.6, 0.9, 0.994)
        elif LEADV == 'bell': x = bell(f, du * 2)
        elif LEADV == 'cowbell': x = cowbell(f * 2, du * 1.2)
        elif LEADV == 'sine': x = E((sine(f, du * 1.5) + 0.2 * sine(2 * f, du * 1.5)), 0.01, 0.4, 0.3, 0.1)
        else: x = filt(supersaw(f, du, 3, 0.1, 3500, 0.005, 0.25, 0.5, 0.05).mean(1), 4000)
        g = 0.11 if tn >= END - 0.2 else 0.08
        add('lead', x, tn, g, pan=0.1); add('send', x, tn, g * 0.5)
        add('lead', x, tn + beat * 0.75, g * 0.3, pan=-0.4)  # dotted-8th echo
    t += bar * 2; rep += 1

# ---------------- build-up into the drop (beat videos)
if 'drop' in tl and tl['drop'] > bar:
    D0 = tl['drop']
    for k in range(16):
        tk = D0 - bar + k * beat / 4
        if tk < D0 - beat / 2: add('drums', snare(230, 0.07), tk, 0.08 + 0.4 * (k / 16) ** 2, 0.1)
# ---------------- transitions
for i, sc in enumerate(scenes[1:]):
    add('sfx', riser(min(1.2, bar / 2)), sc - min(1.2, bar / 2), 0.08)
    add('drums', crash(), sc, 0.18 if i == len(scenes) - 2 else 0.1, 0.1)
    add('send', crash(), sc, 0.06)

# ---------------- UI sound effects
def pop():
    n = int(SR * 0.12); t = np.arange(n) / SR; return np.sin(2 * np.pi * (1100 - 3000 * t) * t) * env(n, 0.001, 0.035)
def whoosh(d=0.45):
    n = int(SR * d); t = np.arange(n) / SR
    return filt(noise(d), 1800, 'low') * np.sin(np.pi * t / d) ** 2
def ding():
    n = int(SR * 1.4); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1318.5 * t) + 0.5 * np.sin(2 * np.pi * 1975.5 * t)) * env(n, 0.002, 0.45)
for tp in tl['taps']: add('sfx', pop(), tp, 0.35)
for sc in scenes[1:]: add('sfx', whoosh(), sc - 0.2, 0.3)
add('sfx', ding(), END + 0.15, 0.16)

# ---------------- mix
def duck_curve(times, depth=0.5, rel=0.22):
    d = np.ones(N)
    for k in times:
        i = int(k * SR); n = int(rel * SR); seg = d[i:i + n]
        d[i:i + n] = np.minimum(seg, (1 - depth) + depth * np.linspace(0, 1, len(seg)) ** 1.5)
    return d[:, None]
sc_depth = {'spookyhouse': 0.5, 'phonk': 0.3, 'futurebass': 0.7, 'house': 0.5, 'disco': 0.4, 'synthwave': 0.35, 'tropical': 0.45, 'afro': 0.35, 'trap': 0.2, 'lofi': 0.15}[style]
dk = duck_curve(kicks, sc_depth)
ir_n = int(SR * (2.2 if style in ('synthwave', 'lofi') else 1.5)); it = np.arange(ir_n) / SR
ir = np.stack([rng.normal(0, 1, ir_n), rng.normal(0, 1, ir_n)], 1) * np.exp(-it / (0.45 if style != 'synthwave' else 0.7))[:, None]
ir = filt(ir, 6000) * 0.06
send = filt(bus['send'] + bus['music'] * 0.25 + bus['lead'] * 0.2, 250, 'high')
rev = np.stack([fftconvolve(send[:, 0], ir[:, 0])[:N], fftconvolve(send[:, 1], ir[:, 1])[:N]], 1)
# phone speakers can't play deep bass: give the bass audible overtones and keep the sub in check
bass = filt(bus['bass'], 35, 'high')
bass = bass * 0.75 + filt(filt(np.tanh(bass * 4), 180, 'high'), 1600) * 0.35
mix = (bus['drums'] * 0.9 + bass * dk + bus['music'] * 1.8 * dk + bus['lead'] * 1.7 * (0.6 + 0.4 * dk) + rev * dk * 1.1)
sub = filt(mix, 110); mix = mix - sub * 0.5          # about -6 dB below 110 Hz
mix = mix + filt(mix, 2500, 'high') * 0.25           # a little sparkle for small speakers
mix = filt(mix, 30, 'high')
if style == 'lofi':
    mix = filt(mix, 6500)
    c = np.zeros(N); idx = rng.integers(0, N, int(T * 30)); c[idx] = rng.normal(0, 0.3, len(idx)); c = filt(c, 1500, 'high')
    mix += (c * 0.12 + filt(rng.normal(0, 1, N), 3000) * 0.006)[:, None]
# intro filter sweep: first bar opens up
k = int(min(intro_end, T) * SR)
if k:
    lowv = filt(mix[:k], 700); ramp = np.linspace(0, 1, k)[:, None] ** 2
    mix[:k] = lowv * (1 - ramp) + mix[:k] * ramp
if 'drop' in tl:  # a breath of silence right before the drop
    g0, g1 = int((tl['drop'] - beat / 2) * SR), int(tl['drop'] * SR)
    mix[g0:g1] *= np.linspace(0.25, 0.02, g1 - g0)[:, None]
mix += bus['sfx']
# master: gentle glue + limiter + fades
fade = np.ones(N); fo = int(1.4 * SR); fade[-fo:] = np.linspace(1, 0, fo) ** 1.5; fade[:int(0.03 * SR)] = np.linspace(0, 1, int(0.03 * SR))
mix *= fade[:, None]
rms = np.sqrt(np.mean(mix ** 2)) + 1e-9
mix *= 0.2 / rms
mix = np.tanh(mix * 1.15) / np.tanh(1.15)
mix = mix / np.max(np.abs(mix)) * 0.93
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype('<i2').tobytes())
print(f'{style} {bpm}bpm key={key} {mode} prog={prog}')
