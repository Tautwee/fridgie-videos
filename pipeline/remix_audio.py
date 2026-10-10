"""Swap the soundtrack of an already rendered video (keeps the picture).
usage: python3 remix_audio.py ../videos/<file>.mp4 [style|auto] [seed-extra]
Needs timelines/<file>.json, which render_plan.py saves for every render."""
import sys, os, subprocess, pathlib, tempfile
D = pathlib.Path(__file__).parent
vid = sys.argv[1]; style = sys.argv[2] if len(sys.argv) > 2 else 'auto'; extra = sys.argv[3] if len(sys.argv) > 3 else ''
name = os.path.basename(vid).rsplit('.', 1)[0]
tl = D / 'timelines' / f'{name}.json'
with tempfile.TemporaryDirectory() as td:
    wav = f'{td}/m.wav'; out = f'{td}/out.mp4'
    subprocess.run(['python3', str(D / 'music3.py'), style, wav, name + '.mp4' + extra, str(tl)], check=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', vid, '-i', wav, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                    '-shortest', '-movflags', '+faststart', out], check=True)
    os.replace(out, vid)
print('remixed', vid)
