"""Synthesize the small sound-design set used by the assemblers into tools/sfx/ (gitignored).
ring_break.wav is made elsewhere (episode 1 pass 3); this adds ambience, boom, whoosh and riser.
Usage: python scripts/make_sfx.py
"""
import os, subprocess

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, 'tools', 'sfx')
os.makedirs(OUT, exist_ok=True)
JOBS = {
    # low cellular hum: brown noise, heavily low-passed, very slow tremolo
    'ambience.wav': ('anoisesrc=color=brown:r=48000:d=150:seed=7', 'lowpass=f=140,lowpass=f=140,volume=0.9,tremolo=f=0.1:d=0.4'),
    # whoosh for the split-screen opening and segment changes
    'whoosh.wav': ('anoisesrc=color=pink:r=48000:d=1.0:seed=3', 'bandpass=f=900:w=600,afade=t=in:st=0:d=0.35:curve=exp,afade=t=out:st=0.45:d=0.55,volume=0.9'),
    # sub boom for the title card and the moment the paths part
    'boom.wav': ('sine=f=46:r=48000:d=1.8', 'aeval=val(0)*exp(-2.2*t)|val(0)*exp(-2.2*t),lowpass=f=120,volume=0.9'),
    # riser into the title
    'riser.wav': ('anoisesrc=color=white:r=48000:d=2.5:seed=11', 'bandpass=f=400:w=300,aeval=val(0)*(t/2.5)^2|val(1)*(t/2.5)^2,afade=t=out:st=2.3:d=0.2,volume=0.5'),
}
for name, (src, af) in JOBS.items():
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', src, '-af', af, '-ac', '2', os.path.join(OUT, name)], check=True)
    print('wrote', name)
