#!/usr/bin/env python3
"""Film « transformations » : N plans Kling 3.0 Pro avec image de début et image de fin imposées + musique + voix off.
Usage : python3 film_kling.py <dossier_marque>      (lit <dossier>/film/kling.json, voir examples/kling.example.json)"""
import json, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from common import kling, music as make_music, voice as make_voice
root = Path(sys.argv[1]).expanduser().resolve(); F = root / "film"; (F / "clips").mkdir(parents=True, exist_ok=True)
cfg = json.loads((F / "kling.json").read_text())
def clip(c):
    out = F / "clips" / f"{c['id']}.mp4"
    if out.exists(): print("⏭️", c["id"]); return
    print("🎬", c["id"], "en cours (≈ 5 min)")
    out.write_bytes(kling(c["prompt"], root / c["start"], root / c["end"] if c.get("end") else None, c.get("duration", "10"), cfg.get("negative", ""))); print("✅", c["id"])
def music():
    if list(F.glob("music_*.mp3")): return
    make_music(cfg["music"]["prompt"], F / "music_1.mp3", cfg["music"].get("seconds", 40)); print("🎵 musique ok")
def voice():
    if (F / "vo.mp3").exists() or not cfg.get("voiceover"): return
    make_voice(cfg["voiceover"]["text"], F / "vo.mp3", cfg["voiceover"].get("voice", "Charlotte"), cfg["voiceover"].get("lang", "fr")); print("🎙 voix off ok")
with ThreadPoolExecutor(6) as ex:
    fs = [ex.submit(clip, c) for c in cfg["clips"]] + [ex.submit(music), ex.submit(voice)]
    for f in fs: f.result()
print("=== tout est prêt : lance montage.sh ===")
