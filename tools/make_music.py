"""Compone las pistas de música de fondo de Mesifly (instrumentales tranquilas, 100% propias).

Uso:  python3 tools/make_music.py      (genera tools/music/*.m4a)

Las pistas se crean por síntesis, sin samples de terceros, así que no tienen
problemas de derechos en TikTok, YouTube, Instagram ni Facebook.
make_social.py elige una de estas pistas para cada video.
"""
import os, subprocess, tempfile
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve, butter, sosfilt

SR = 44100
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music")

NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def hz(name, octave):
    return 440.0 * 2 ** ((NOTE[name] + 12 * (octave + 1) - 69) / 12)


def chord(root, octave, intervals):
    base = NOTE[root] + 12 * (octave + 1)
    return [440.0 * 2 ** ((base + i - 69) / 12) for i in intervals]


MAJ7, MIN7, DOM9, MAJ9, SIX = [0, 4, 7, 11], [0, 3, 7, 10], [0, 4, 10, 14], [0, 4, 7, 11, 14], [0, 4, 7, 9]

TRACKS = {
    "calma-cafe": dict(bpm=72, seed=1, hats=True, prog=[("C", MAJ7), ("A", MIN7), ("F", MAJ9), ("G", SIX)]),
    "tarde-tranquila": dict(bpm=66, seed=2, hats=False, prog=[("F", MAJ7), ("E", MIN7), ("D", MIN7), ("C", MAJ9)]),
    "mesa-lista": dict(bpm=78, seed=3, hats=True, prog=[("D", MAJ7), ("B", MIN7), ("G", MAJ7), ("A", SIX)]),
}


def env(n, attack, release):
    e = np.ones(n)
    a, r = min(int(attack * SR), n // 2), min(int(release * SR), n // 2)
    e[:a] = np.linspace(0, 1, a)
    e[-r:] *= np.linspace(1, 0, r)
    return e


def lowpass(x, cutoff):
    return sosfilt(butter(2, cutoff, fs=SR, output="sos"), x)


def make_track(bpm, seed, hats, prog, seconds=48):
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    out = np.zeros(n)
    beat = 60.0 / bpm
    bar = 4 * beat
    t_bar = np.arange(int(bar * SR)) / SR
    pos, i = 0, 0
    while pos < n:
        root, ivs = prog[i % len(prog)]
        L = min(len(t_bar), n - pos)
        t = t_bar[:L]
        # Pad suave: senos ligeramente desafinados
        pad = np.zeros(L)
        for f in chord(root, 3, ivs):
            for det in (-0.6, 0.6):
                pad += np.sin(2 * np.pi * (f + det) * t + rng.uniform(0, 6.28))
        pad *= env(L, 0.9, 0.9) * 0.05
        # Bajo
        fb = hz(root, 2)
        bass = (np.sin(2 * np.pi * fb * t) + 0.3 * np.sin(4 * np.pi * fb * t)) * np.exp(-t * 1.2) * 0.18
        # Piano eléctrico: arpegio en corcheas con algunas notas omitidas
        keys = np.zeros(L)
        notes = chord(root, 4, ivs)
        for k in range(8):
            if k and rng.random() < 0.3:
                continue
            start = int(k * beat / 2 * SR)
            if start >= L:
                break
            f = notes[rng.integers(len(notes))]
            tt = np.arange(L - start) / SR
            tone = np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(4 * np.pi * f * tt) * np.exp(-tt * 6)
            keys[start:] += tone * np.exp(-tt * 2.5) * 0.07 * rng.uniform(0.7, 1.0)
        seg = pad + bass + keys
        # Platillo suave tipo lo-fi en contratiempos
        if hats:
            for k in range(4):
                start = int((k + 0.5) * beat * SR)
                hl = int(0.08 * SR)
                if start + hl <= L:
                    noise = rng.standard_normal(hl) * np.exp(-np.arange(hl) / SR * 60)
                    seg[start:start + hl] += noise * 0.012
        out[pos:pos + L] += seg
        pos += L
        i += 1
    out = lowpass(out, 5000)
    # Reverb sencilla
    ir_len = int(1.8 * SR)
    ir = rng.standard_normal(ir_len) * np.exp(-np.arange(ir_len) / SR * 3.0)
    wet = fftconvolve(out, lowpass(ir, 3000))[:n]
    wet /= np.max(np.abs(wet)) + 1e-9
    mix = out / (np.max(np.abs(out)) + 1e-9) * 0.75 + wet * 0.3
    mix *= env(n, 1.5, 3.0)
    mix = mix / np.max(np.abs(mix)) * 0.7
    return np.stack([mix, np.roll(mix, int(0.012 * SR))], axis=1)


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, cfg in TRACKS.items():
        audio = make_track(**cfg)
        with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
            wavfile.write(tmp.name, SR, (audio * 32767).astype(np.int16))
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp.name, "-c:a", "aac",
                            "-b:a", "128k", os.path.join(OUT, name + ".m4a")], check=True)
        print("OK", name)


if __name__ == "__main__":
    main()
