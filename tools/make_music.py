"""Compone las pistas de música de fondo de Mesifly (instrumentales alegres y motivadoras, 100% propias).

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


MAJ, MIN, MAJ7, SUS2, ADD9 = [0, 4, 7], [0, 3, 7], [0, 4, 7, 11], [0, 2, 7], [0, 4, 7, 14]

# Estilo alegre y motivador (pop acústico/upbeat): acordes mayores, groove ligero, sin estridencias.
TRACKS = {
    "buen-dia": dict(bpm=104, seed=11, prog=[("C", ADD9), ("G", MAJ), ("A", MIN), ("F", MAJ7)]),
    "paso-firme": dict(bpm=110, seed=12, prog=[("D", MAJ), ("A", SUS2), ("B", MIN), ("G", ADD9)]),
    "dia-soleado": dict(bpm=98, seed=13, prog=[("G", ADD9), ("D", MAJ), ("E", MIN), ("C", MAJ7)]),
}


def env(n, attack, release):
    e = np.ones(n)
    a, r = min(int(attack * SR), n // 2), min(int(release * SR), n // 2)
    e[:a] = np.linspace(0, 1, a)
    e[-r:] *= np.linspace(1, 0, r)
    return e


def lowpass(x, cutoff):
    return sosfilt(butter(2, cutoff, fs=SR, output="sos"), x)


def bandpass(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)


def add(buf, start, sig):
    end = min(len(buf), start + len(sig))
    if start < end:
        buf[start:end] += sig[:end - start]


def pluck(f, dur, bright=0.35):
    t = np.arange(int(dur * SR)) / SR
    tone = (np.sin(2 * np.pi * f * t) + bright * np.sin(4 * np.pi * f * t) * np.exp(-t * 8)
            + 0.12 * np.sin(6 * np.pi * f * t) * np.exp(-t * 14))
    return tone * np.exp(-t * 4.0) * np.minimum(1, t * 400)


def make_track(bpm, seed, prog, seconds=48):
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    music, drums = np.zeros(n), np.zeros(n)
    beat = 60.0 / bpm
    eighth = beat / 2
    bar_len = int(4 * beat * SR)
    # Sonidos de batería suaves
    kt = np.arange(int(0.25 * SR)) / SR
    kick = np.sin(2 * np.pi * (50 + 90 * np.exp(-kt * 30)) * kt) * np.exp(-kt * 14)
    cl = int(0.18 * SR)
    clap = bandpass(rng.standard_normal(cl), 900, 4000) * np.exp(-np.arange(cl) / SR * 22)
    hl = int(0.05 * SR)
    hat = bandpass(rng.standard_normal(hl), 6000, 12000) * np.exp(-np.arange(hl) / SR * 80)
    shaker = bandpass(rng.standard_normal(int(0.07 * SR)), 4000, 9000) * np.hanning(int(0.07 * SR))
    pos, i = 0, 0
    pattern = [0, 1, 2, 3, 2, 1, 3, 2]  # arpegio ascendente/descendente en corcheas
    while pos < n:
        root, ivs = prog[i % len(prog)]
        L = min(bar_len, n - pos)
        t = np.arange(L) / SR
        # Pad brillante de fondo
        pad = np.zeros(L)
        for f in chord(root, 4, ivs):
            for det in (-1.0, 1.0):
                pad += np.sin(2 * np.pi * (f + det) * t + rng.uniform(0, 6.28))
        add(music, pos, pad * env(L, 0.15, 0.3) * 0.022)
        # Arpegio tipo guitarra/marimba en corcheas, constante y con energía
        notes = chord(root, 4, ivs) + [chord(root, 5, ivs)[0]]
        for k in range(8):
            f = notes[pattern[k] % len(notes)]
            vel = 1.0 if k % 2 == 0 else 0.75
            add(music, pos + int(k * eighth * SR), pluck(f, 0.6) * 0.075 * vel)
        # Acorde rasgueado en el 1 y el "y" del 2 (empuje)
        for at in (0, 1.5, 2.5):
            for j, f in enumerate(chord(root, 3, ivs)):
                add(music, pos + int((at * beat + j * 0.012) * SR), pluck(f * 2, 0.5, 0.5) * 0.04)
        # Bajo saltarín: 1, y-del-2, 3, 4
        fb = hz(root, 2)
        for at, f in ((0, fb), (1.5, fb), (2, fb), (3, fb * 1.5)):
            bt = np.arange(int(0.45 * SR)) / SR
            b = (np.sin(2 * np.pi * f * bt) + 0.35 * np.sin(4 * np.pi * f * bt)) * np.exp(-bt * 5)
            add(music, pos + int(at * beat * SR), b * 0.17)
        # Groove: bombo 1 y 3 (+ y-del-3), palmada 2 y 4, hi-hat en corcheas, shaker en semicorcheas
        if i >= 1:  # la batería entra en el segundo compás
            for at in (0, 2, 2.5):
                add(drums, pos + int(at * beat * SR), kick * 0.5)
            for at in (1, 3):
                add(drums, pos + int(at * beat * SR), clap * 0.11)
            for k in range(8):
                add(drums, pos + int(k * eighth * SR), hat * (0.05 if k % 2 else 0.03))
            for k in range(16):
                add(drums, pos + int(k * beat / 4 * SR), shaker * 0.018)
        pos += L
        i += 1
    music = lowpass(music, 9000)
    ir_len = int(1.2 * SR)
    ir = rng.standard_normal(ir_len) * np.exp(-np.arange(ir_len) / SR * 4.5)
    wet = fftconvolve(music, lowpass(ir, 5000))[:n]
    wet /= np.max(np.abs(wet)) + 1e-9
    music = music / (np.max(np.abs(music)) + 1e-9)
    mix = music * 0.8 + wet * 0.18 + drums / (np.max(np.abs(drums)) + 1e-9) * 0.45
    mix = np.tanh(mix * 1.2)  # compresión suave
    mix *= env(n, 0.8, 3.0)
    mix = mix / np.max(np.abs(mix)) * 0.75
    return np.stack([mix, np.roll(mix, int(0.010 * SR))], axis=1)


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
