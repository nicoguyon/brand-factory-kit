#!/usr/bin/env python3
"""Génère toutes les images d'une étape décrite dans un fichier JSON.

Usage : python3 gen.py <dossier_marque> <etape.json> [--only id1 id2] [--workers 4] [--redo id]

Format de l'étape (voir examples/step.example.json) :
{ "step": "01_directions", "title": "...", "intro": "...",
  "jobs": [ {"id": "A-hero", "group": "Direction A", "engine": "nano" | "nano-flash" | "gpt",
             "ratio": "16:9", "size": "4K", "refs": ["product/p1.jpg"], "prompt": "...", "label": "..."} ] }
Les chemins de refs sont relatifs au dossier de la marque. Une ref peut viser une image déjà générée : "01_directions/img/A-hero.png".
"""
import argparse, json, subprocess, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from common import nano_banana, gpt_image

ap = argparse.ArgumentParser()
ap.add_argument("root"); ap.add_argument("step"); ap.add_argument("--only", nargs="*"); ap.add_argument("--redo", nargs="*", default=[])
ap.add_argument("--workers", type=int, default=4); ap.add_argument("--no-open", action="store_true")
a = ap.parse_args()
root = Path(a.root).expanduser().resolve()
step = json.loads(Path(a.step).read_text())
out_dir = root / step["step"] / "img"; out_dir.mkdir(parents=True, exist_ok=True)
(root / step["step"] / "step.json").write_text(json.dumps(step, ensure_ascii=False, indent=1))


def run(j):
    out = out_dir / f"{j['id']}.png"
    if out.exists() and j["id"] not in a.redo:
        print(f"⏭️  {j['id']}"); return j["id"], True
    refs = [root / r for r in j.get("refs", [])]
    missing = [str(r) for r in refs if not r.exists()]
    if missing:
        print(f"❌ {j['id']} référence introuvable : {missing}"); return j["id"], False
    t0 = time.time(); eng = j.get("engine", "nano")
    if eng == "gpt":
        data = gpt_image(j["prompt"])
    else:
        data = nano_banana(j["prompt"], refs, j.get("ratio", "16:9"), j.get("size", "2K"),
                           "gemini-3.1-flash-image" if eng == "nano-flash" else "gemini-3-pro-image")
    if not data:
        print(f"❌ {j['id']} aucune image (filtre ou erreur). Astuce visages : « the brand muse, casting reference », jamais « the real person »."); return j["id"], False
    out.write_bytes(data); print(f"✅ {j['id']} {time.time() - t0:.0f}s")
    if not a.no_open: subprocess.run(["open", str(out)], check=False)
    return j["id"], True


jobs = [j for j in step["jobs"] if not a.only or j["id"] in a.only]
with ThreadPoolExecutor(a.workers) as ex:
    res = list(ex.map(run, jobs))
ok = sum(r[1] for r in res)
print(f"=== {ok}/{len(jobs)} images · {out_dir} ===")
