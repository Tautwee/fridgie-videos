"""Objective checks for a finished Fridgeroo video, used by the Judge before anything goes to Tautvydas.

usage: python3 judge_check.py ../videos/<file>.mp4 [out_dir]
Writes <out_dir>/<name>-sheet.jpg (4 frames per second, read it!) and <name>-keys.jpg (first frame,
1 s, middle, payoff, end card at full size) and prints a JSON report. "pass": false = do not send.
"""
import json, os, subprocess, sys
import numpy as np
from scipy.signal import butter, sosfilt

V = sys.argv[1]; OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(V))
name = os.path.basename(V).rsplit('.', 1)[0]; SR = 44100
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', V], capture_output=True, text=True).stdout)
rep = {'file': name, 'duration': round(dur, 2), 'problems': []}
P = rep['problems']
if not 13 <= dur <= 18: P.append(f'duration {dur:.1f}s (story videos must be 13-18 s)')

# ---------- audio
x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', V, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True).stdout, np.int16) / 32768
if len(x) == 0: P.append('no audio')
else:
    peak = float(np.abs(x).max()); clip = int(np.sum(np.abs(x) > 0.985))
    if clip > 20: P.append(f'clipping: {clip} samples at full scale')
    lo = sosfilt(butter(4, 90, 'low', fs=SR, output='sos'), x)
    hi = sosfilt(butter(4, 7000, 'high', fs=SR, output='sos'), x)
    win = int(0.5 * SR); rows = []
    for i in range(0, len(x) - win, win):
        s, l, h = x[i:i + win], lo[i:i + win], hi[i:i + win]
        r = np.sqrt(np.mean(s ** 2)) + 1e-9; rl = np.sqrt(np.mean(l ** 2)) + 1e-9; rh = np.sqrt(np.mean(h ** 2)) + 1e-9
        rows.append((i / SR, 20 * np.log10(r), 20 * np.log10(rl / r), 20 * np.log10(rh / r)))
        if r > 0.03 and 20 * np.log10(rl / r) > -10: P.append(f'{i / SR:.1f}s: too much deep bass (rattles on phone speakers)')
        if r > 0.03 and 20 * np.log10(rh / r) > -9: P.append(f'{i / SR:.1f}s: harsh/hissy highs (noise)')
    tail = [r for r in rows if r[0] >= dur - 1.0]
    if tail and tail[-1][1] > -30: P.append('ending does not fade out cleanly')
    silent = [r[0] for r in rows if r[1] < -45 and 0.5 < r[0] < dur - 1.5]
    if silent: P.append(f'dead silence at {silent}')
    rep['audio'] = {'peak': round(peak, 2), 'loudness_by_half_second_db': [round(r[1], 1) for r in rows]}

# ---------- picture: motion / cuts / static stretches / first frame
fps = 10; W, H = 108, 192
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', V, '-vf', f'fps={fps},scale={W}:{H},format=gray', '-f', 'rawvideo', '-'], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)
d = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))
cuts = [round((i + 1) / fps, 1) for i, v in enumerate(d) if v > 18]
static, run, longest = [], 0, (0, 0)
for i, v in enumerate(d):
    run = run + 1 if v < 0.6 else 0
    if run / fps > longest[0]: longest = (run / fps, (i + 1) / fps)
first = fr[0]; first_motion = float(d[:fps].mean()) if len(d) >= fps else 0
rep['picture'] = {'cuts_at': cuts, 'cuts_per_10s': round(len(cuts) / dur * 10, 1), 'longest_static_s': round(longest[0], 1),
                  'first_second_motion': round(first_motion, 2), 'first_frame_brightness': round(float(first.mean()), 1)}
if first.mean() < 25 or first.std() < 12: P.append('first frame is dark/empty (bad thumbnail and hook)')
if first_motion < 1.5: P.append('nothing moves in the first second (hook must be ACTION)')
if longest[0] > 1.6 and longest[1] < dur - 2.5: P.append(f'{longest[0]:.1f}s with almost no movement ending at {longest[1]:.1f}s')
if len(cuts) / dur * 10 < 4: P.append('too few shot changes (aim for a new shot or big action about every 1-2 s)')

# ---------- sheets for the Judge's eyes
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', V, '-vf', 'fps=4,scale=180:320,tile=10x8', '-frames:v', '1', os.path.join(OUT, f'{name}-sheet.jpg')])
ks = [0.0, 1.0, dur * 0.45, dur * 0.72, dur - 0.8]
sel = '+'.join(f'eq(n\\,{int(k * 30)})' for k in ks)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', V, '-vf', f"select='{sel}',scale=432:768,tile={len(ks)}x1", '-vsync', '0', '-frames:v', '1', os.path.join(OUT, f'{name}-keys.jpg')])
rep['pass'] = not P
rep['sheet'] = os.path.join(OUT, f'{name}-sheet.jpg'); rep['keys'] = os.path.join(OUT, f'{name}-keys.jpg')
print(json.dumps(rep, indent=1))
