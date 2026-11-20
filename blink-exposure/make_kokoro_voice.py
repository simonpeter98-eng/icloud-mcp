#!/usr/bin/env python3
"""
Build Blink Exposure with a Kokoro neural voice built in.

Reads blink-exposure-standalone.html, speaks every sentence of its script with Kokoro
(kokoro-onnx, runs on CPU), and writes blink-exposure-kokoro.html: one file that plays
the same human-sounding voice on any phone or laptop, with no device voices needed.

Setup (once, Python 3.10-3.12):
    python -m pip install kokoro-onnx soundfile numpy
Run:
    python make_kokoro_voice.py blink-exposure-standalone.html
Options:
    --voice af_heart     warm US female (default). Others: af_bella, af_nicole, af_sarah,
                         bf_emma, bf_isabella (UK female), am_michael, am_fenrir (US male),
                         bm_george, bm_fable (UK male)
    --speed 0.9          speaking speed baked into the audio (the page's Pace setting adds pauses)
    --dry-run            list the sentences and exit
Model files (about 330 MB) download once into ./kokoro_models from the kokoro-onnx GitHub release.
"""
import argparse, base64, io, json, re, shutil, subprocess, sys, urllib.request
from pathlib import Path

RELEASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
MODEL, VOICES = "kokoro-v1.0.onnx", "voices-v1.0.bin"


def fetch(name, folder):
    dest = folder / name
    if dest.exists() and dest.stat().st_size > 1_000_000:
        return dest
    folder.mkdir(exist_ok=True)
    print(f"Downloading {name} ...")
    def hook(n, bs, total):
        if total > 0:
            print(f"\r  {min(100, n * bs * 100 // total)}%", end="", flush=True)
    urllib.request.urlretrieve(RELEASE + name, dest.with_suffix(".part"), hook)
    dest.with_suffix(".part").rename(dest)
    print()
    return dest


def sentences_from(html):
    block = re.search(r"const SCRIPT = \[(.*?)\n  \];", html, re.S)
    preview = re.search(r'const PREVIEW_TEXT = "((?:[^"\\]|\\.)*)"', html)
    if not block or not preview:
        sys.exit("Could not find the script in the HTML file. Use the latest blink-exposure file.")
    lines = re.findall(r'\[\s*\d\s*,\s*"((?:[^"\\]|\\.)*)"\s*\]', block.group(1))
    out = []
    for raw in lines + [preview.group(1)]:
        text = json.loads('"' + raw + '"')
        # must match the page's splitter: t.match(/[^.!?]+[.!?]*/g), trimmed
        for s in re.findall(r"[^.!?]+[.!?]*", text):
            s = s.strip()
            if s and s not in out:
                out.append(s)
    return out


def trim(x, sr, thr=0.006):
    import numpy as np
    idx = np.where(np.abs(x) > thr)[0]
    if not len(idx):
        return x
    a = max(0, idx[0] - int(0.05 * sr))
    b = min(len(x), idx[-1] + int(0.15 * sr))
    y = x[a:b].copy()
    fade = min(len(y) // 4, int(0.02 * sr))  # 20 ms fades, no clicks
    if fade:
        y[:fade] *= np.linspace(0, 1, fade)
        y[-fade:] *= np.linspace(1, 0, fade)
    return y


def encode(x, sr):
    import soundfile as sf
    buf = io.BytesIO()
    try:
        sf.write(buf, x, sr, format="MP3")
        return buf.getvalue(), "audio/mpeg"
    except Exception:
        pass
    wav = io.BytesIO()
    sf.write(wav, x, sr, format="WAV", subtype="PCM_16")
    if shutil.which("ffmpeg"):
        r = subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "wav", "-i", "pipe:0",
                            "-codec:a", "libmp3lame", "-q:a", "4", "-f", "mp3", "pipe:1"],
                           input=wav.getvalue(), capture_output=True)
        if r.returncode == 0 and r.stdout:
            return r.stdout, "audio/mpeg"
    print("  (MP3 encoding unavailable, using WAV; the file will be larger)")
    return wav.getvalue(), "audio/wav"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html", nargs="?", default="blink-exposure-standalone.html")
    ap.add_argument("--voice", default="af_heart")
    ap.add_argument("--speed", type=float, default=0.9)
    ap.add_argument("--out", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    src = Path(a.html)
    html = src.read_text(encoding="utf-8")
    if "<!--KOKORO_AUDIO-->" not in html:
        sys.exit("This HTML file has no audio slot. Use the latest blink-exposure file.")
    sents = sentences_from(html)
    if a.dry_run:
        print("\n".join(sents))
        print(f"\n{len(sents)} sentences")
        return

    from kokoro_onnx import Kokoro
    models = Path(__file__).resolve().parent / "kokoro_models"
    tts = Kokoro(str(fetch(MODEL, models)), str(fetch(VOICES, models)))
    lang = "en-gb" if a.voice.startswith("b") else "en-us"

    clips = {"__voice": a.voice}
    for n, s in enumerate(sents, 1):
        print(f"[{n}/{len(sents)}] {s}")
        samples, sr = tts.create(s, voice=a.voice, speed=a.speed, lang=lang)
        data, mime = encode(trim(samples, sr), sr)
        clips[s] = f"data:{mime};base64," + base64.b64encode(data).decode("ascii")

    out = Path(a.out) if a.out else src.with_name("blink-exposure-kokoro.html")
    tag = "<script>window.KOKORO_AUDIO=" + json.dumps(clips) + ";</script>"
    out.write_text(html.replace("<!--KOKORO_AUDIO-->", tag, 1), encoding="utf-8")
    print(f"\nWrote {out} ({out.stat().st_size / 1e6:.1f} MB). Open it in any browser.")


if __name__ == "__main__":
    main()
