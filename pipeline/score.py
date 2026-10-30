"""Story score for Fridgeroo 3D story videos (no samples, all synthesized, all ours).

usage: python3 score.py marks.json out.wav
marks.json: {"total": s, "marks": {"sneak": t, "tension": t, "yuck": t, "hit": t, "app": t, "glow": t, "drop": t, "end": t}}
Sections:
  sneak   -> comedic sneaky pizzicato + woodblock (the clean-out)
  tension -> same groove + tremolo strings creeping up
  yuck    -> sad-trombone "wah-wah-waah"
  hit     -> music cuts, big orchestral DUN + heartbeat drone
  app     -> magic twinkles
  glow    -> riser lands on a huge major chord (minor -> major = payoff)
  drop    -> full epic groove: kick, clap, supersaw chords, arp
  end     -> final hit + sparkle tail
"""
import json, sys, wave
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

SR = 44100
M = json.load(open(sys.argv[1])); OUT = sys.argv[2]
T = M['total']; K = M['marks']; N = int(SR * (T + 1))
L = np.zeros(N); Rr = np.zeros(N)
rng = np.random.default_rng(3)
BPM = 104; B = 60 / BPM


def tt(d): return np.arange(int(SR * d)) / SR
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def flt(x, f, kind='low', o=2): return sosfilt(butter(o, f, kind, fs=SR, output='sos'), x)
def env(n, a, d, s=0.0, r=0.05):
    e = np.ones(n); na = max(1, int(a * SR)); e[:na] = np.linspace(0, 1, na)
    k = np.arange(n - na) / SR; e[na:] = s + (1 - s) * np.exp(-k / max(d, 1e-4))
    nr = min(n, int(r * SR)); e[-nr:] *= np.linspace(1, 0, nr); return e
def add(x, t0, g=1.0, pan=0.0):
    a = int(t0 * SR)
    if a >= N or a + len(x) <= 0: return
    if a < 0: x = x[-a:]; a = 0
    x = x[:N - a]; L[a:a + len(x)] += x * g * (1 - max(0, pan)); Rr[a:a + len(x)] += x * g * (1 + min(0, pan))

def saw(f, d, ph=0): t = tt(d); return 2 * ((t * f + ph) % 1) - 1
def pluck(m, d=0.35, bright=2500):  # pizzicato
    f = hz(m); t = tt(d); x = 0.7 * np.sin(2 * np.pi * f * t) + 0.3 * saw(f, d)
    return flt(x, bright) * env(len(t), 0.002, 0.09)
def wood(): t = tt(0.08); return (np.sin(2 * np.pi * 1600 * t) + 0.5 * np.sin(2 * np.pi * 2450 * t)) * env(len(t), 0.0005, 0.015)
def hat(): return flt(rng.normal(0, 1, int(SR * 0.05)), 7000, 'high') * env(int(SR * 0.05), 0.0005, 0.012)
def kick(): t = tt(0.4); return np.sin(2 * np.pi * (48 + 110 * np.exp(-t * 30)) * t) * env(len(t), 0.001, 0.12) * 1.2
def clap():
    x = flt(rng.normal(0, 1, int(SR * 0.22)), 1500, 'high'); e = env(len(x), 0.001, 0.06)
    for o in (0.008, 0.016): e[int(o * SR):] += 0.6 * env(len(x) - int(o * SR), 0.001, 0.02)
    return x * e * 0.5
def supersaw(ms, d, cut=4000, a=0.02, dec=0.8, s=0.7):
    x = np.zeros(int(SR * d))
    for m in ms:
        for v in range(7): x += saw(hz(m) * (1 + (v - 3) * 0.006), d, ph=v * 0.13)
    return flt(x / (len(ms) * 7), cut) * env(len(x), a, dec, s, 0.15)
def choir(ms, d):  # "aah" pad: saw through vowel formants
    x = np.zeros(int(SR * d))
    for m in ms:
        for v in range(3): x += saw(hz(m) * (1 + (v - 1) * 0.004), d, ph=v * 0.3)
    y = sum(sosfilt(butter(2, [f * 0.85, f * 1.15], 'band', fs=SR, output='sos'), x) * g for f, g in ((730, 1), (1090, .5), (2440, .25)))
    return y / len(ms) * env(len(y), 0.25, 2.0, 0.85, 0.4) * 2.2
def bell(m, d=1.2):
    f = hz(m); t = tt(d); return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) + 0.2 * np.sin(2 * np.pi * f * 5.4 * t)) * env(len(t), 0.001, 0.35)
def trombone(m0, m1, d):  # wah: bend down + wobble
    t = tt(d); f = hz(m0) * (hz(m1) / hz(m0)) ** (t / d); ph = np.cumsum(f) / SR
    x = flt(2 * (ph % 1) - 1, 1400) * (0.65 + 0.35 * np.sin(2 * np.pi * 5.5 * t))
    return x * env(len(t), 0.03, d, 0.8, 0.08) * 0.8
def boom(): t = tt(1.4); return np.sin(2 * np.pi * (40 + 30 * np.exp(-t * 8)) * t) * env(len(t), 0.002, 0.6) * 1.3
def hitchord(ms, d=1.4):
    x = supersaw(ms, d, cut=2500, a=0.003, dec=0.5, s=0.0) * 1.6
    return x + flt(rng.normal(0, 1, len(x)), 3000) * env(len(x), 0.001, 0.08) * 0.4
def riser(d): t = tt(d); return flt(rng.normal(0, 1, len(t)), 6000) * (t / d) ** 2.5 * 0.5 + np.sin(2 * np.pi * (200 + 900 * (t / d) ** 2) * t) * (t / d) ** 2 * 0.15
def tremolo(ms, d):
    x = supersaw(ms, d, cut=1800, a=0.4, dec=3, s=0.9); return x * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 9 * tt(d))))

# ---------------- A/B: sneaky groove in D minor (the clean-out + tension)
s0, s1 = K['sneak'], K['hit']
walk = [38, None, 41, None, 45, 44, 43, None, 38, None, 41, 43, 45, None, 46, 45]  # D2 ... sneaky
mel = [62, None, 65, None, 69, None, 68, 67, None, None, 62, None, 65, 64, 62, None]
t = s0; i = 0
while t < s1 - 0.05:
    n = walk[i % 16]
    if n: add(pluck(n, 0.4, 1800), t, 0.9, -0.1)
    if i % 2 == 1: add(wood(), t, 0.35, 0.4)
    if i % 4 == 2: add(hat(), t, 0.25, -0.3)
    m = mel[i % 16]
    if m and t > K['sneak'] + 4 * B: add(pluck(m + 12, 0.25, 4000), t, 0.35, 0.3)
    t += B / 2; i += 1
# tension strings creeping up chromatically
tt0 = K['tension']
for j, ms in enumerate([[50, 53, 57], [51, 54, 58], [52, 55, 59]]):
    a = tt0 + j * 1.2
    if a < s1: add(tremolo(ms, min(1.3, s1 - a)), a, 0.22, (-0.3, 0.3, 0)[j])
# yuck: sad trombone wah-wah-waaah
y = K['yuck']
for j, (m0, m1, d) in enumerate([(58, 57, 0.32), (57, 56, 0.32), (56, 53, 0.9)]):
    add(trombone(m0, m1, d), y + j * 0.36, 0.55)
# ---------------- C: the hit
h = K['hit']
add(riser(0.35) * 0.7, h - 0.35, 0.6)
add(hitchord([38, 45, 50, 53, 57], 0.9) * env(int(SR * 0.9), 0.001, 0.25), h, 0.75); add(boom() * env(int(SR * 1.4), 0.001, 0.25), h, 0.8)
for j in range(int((K['app'] - h - 0.3) / 0.75)):  # heartbeat
    add(boom()[:int(SR * 0.3)] * 0.5, h + 0.75 + j * 0.75, 0.3); add(boom()[:int(SR * 0.25)] * 0.35, h + 0.98 + j * 0.75, 0.3)
# ---------------- D: magic -> major payoff (D major)
ap, gl, dr, en = K['app'], K['glow'], K['drop'], K['end']
arp = [74, 78, 81, 86, 81, 78]
t = ap; i = 0
while t < en:
    add(bell(arp[i % 6] + (12 if t > dr else 0), 0.9), t, 0.18 if t < dr else 0.14, (i % 2) * 0.6 - 0.3); t += B / 2; i += 1
add(riser(gl - ap + 0.05), ap, 0.7)
add(choir([62, 66, 69, 74], dr - gl + 0.6), gl, 0.55); add(supersaw([50, 57, 62, 66], dr - gl + 0.3, 3000, 0.01, 1.2, 0.6), gl, 0.5); add(boom() * env(int(SR * 1.4), 0.001, 0.3), gl, 0.6)
add(hat() * 0, gl)
# drop: I - V - vi - IV, 1 bar each, kick 4 on the floor
prog = [[50, 57, 62, 66, 69], [45, 57, 61, 64, 69], [47, 59, 62, 66, 71], [43, 55, 59, 62, 67]]
t = dr; bar = 0
while t < en:
    ch = prog[bar % 4]
    dd = min(4 * B, en - t)
    add(supersaw(ch[1:], dd, 5000, 0.01, 1.5, 0.7), t, 0.5); add(choir(ch[1:], dd), t, 0.25)
    add(flt(saw(hz(ch[0] - 12), dd), 400) * env(int(SR * dd), 0.01, 2, 0.8), t, 0.5)
    for b in range(4):
        if t + b * B >= en: break
        add(kick(), t + b * B, 1.1)
        if b % 2: add(clap(), t + b * B, 0.6)
        add(hat(), t + b * B + B / 2, 0.3, 0.3)
    t += 4 * B; bar += 1
# ---------------- E: end hit + sparkle tail
# clean, warm ending: soft D-major chime chord + choir swell + one soft low note (no noise)
for j, m in enumerate([62, 66, 69, 74, 78, 81]): add(bell(m, 2.2) * env(int(SR * 2.2), 0.002, 0.9), en + 0.06 * j, 0.16, (j % 2) * 0.6 - 0.3)
add(choir([62, 66, 69, 74], 2.0), en, 0.3)
add(np.sin(2 * np.pi * hz(38) * tt(1.8)) * env(int(SR * 1.8), 0.01, 0.7), en, 0.45)

# ---------------- master: duck everything under the hit's silence, reverb, glue
mix = np.stack([L, Rr], 1)[:int(SR * T)]
ir = rng.normal(0, 1, int(SR * 1.2)) * np.exp(-np.arange(int(SR * 1.2)) / (SR * 0.35)); ir = flt(ir, 5000) * 0.03
for c in range(2): mix[:, c] += fftconvolve(mix[:, c], ir)[:len(mix)] * 0.6
fade = int(0.3 * SR); mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
mix = np.tanh(mix * 1.1) / np.tanh(1.1); mix *= 0.9 / (np.abs(mix).max() + 1e-9)
with wave.open(OUT, 'w') as o:
    o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR); o.writeframes((mix * 32767).astype(np.int16).tobytes())
print('score', OUT, f'{T:.1f}s')
