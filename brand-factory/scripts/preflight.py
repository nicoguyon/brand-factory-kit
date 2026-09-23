#!/usr/bin/env python3
"""ÉTAPE 0 : vérifie les clés API et les outils, puis dit quelles étapes sont possibles.
Usage : python3 preflight.py        (lit les variables d'environnement, ./keys.env ou ~/.brand_factory/keys.env)"""
import os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
missing = []
for mod, pkg in (("requests", "requests"), ("PIL", "pillow")):
    try: __import__(mod)
    except ImportError: missing.append(pkg)
if missing:
    print(f"❌ Bibliothèques Python manquantes : {', '.join(missing)}\n   Installe-les avec :  {sys.executable} -m pip install {' '.join(missing)}\n   puis relance ce script.")
    sys.exit(1)
import requests
from common import load_keys
load_keys(); E = os.environ; R = {}

def test(name, fn):
    v = E.get(name)
    if not v: R[name] = ("absente", False); return
    try: ok, msg = fn(v)
    except Exception as e: ok, msg = False, str(e)[:120]
    R[name] = (msg, ok)

def fal(k):
    h = {"Authorization": "Key " + k, "Content-Type": "application/json"}
    r = requests.post("https://rest.fal.ai/storage/upload/initiate?storage_type=fal-cdn-v3", headers=h, json={"file_name": "t.txt", "content_type": "text/plain"}, timeout=20)
    if r.status_code not in (200, 201): return False, f"refusée ({r.status_code})"
    t = requests.post("https://fal.run/openrouter/router", headers=h, json={"model": "google/gemini-2.5-flash", "prompt": "Réponds OK", "max_tokens": 5}, timeout=40)
    return (t.status_code == 200, "OK (images, vidéo, son, styliste)" if t.status_code == 200 else f"clé valide mais appel refusé ({t.status_code}) : crédit fal épuisé ?")
test("FAL_KEY", fal)

T = {}
for t in ("python3", "node", "ffmpeg", "vercel", "git"):
    T[t] = bool(shutil.which(t))
try:
    import PIL; T["Pillow"] = True
except ImportError: T["Pillow"] = False

ok = lambda k: R.get(k, ("", False))[1]
f = ok("FAL_KEY")
steps = [
    ("Récupérer le produit, pages de choix, making-of", T["python3"] and T["Pillow"], "python3 + Pillow"),
    ("Directions, master, déclinaisons, visuels (Nano Banana Pro)", f, "FAL_KEY"),
    ("Logos avec texte lisible (GPT Image 2.5)", f, "FAL_KEY"),
    ("Boutique en ligne", T["node"] and T["vercel"], "node + vercel (npm i -g vercel, puis vercel login)"),
    ("Essayage live + styliste IA", f, "FAL_KEY"),
    ("Film à transitions (Kling 3.0) + musique + voix off", f and T["ffmpeg"], "FAL_KEY + ffmpeg (brew install ffmpeg)"),
    ("Film plan-séquence (Seedance 2.5)", True, "compte Dreamina + Claude in Chrome (optionnel, pas de clé)"),
]
print("\n🔑 CLÉS")
for k, (m, g) in R.items(): print(f"  {'✅' if g else '❌'} {k:20s} {m}")
print("\n🧰 OUTILS")
for k, g in T.items(): print(f"  {'✅' if g else '❌'} {k}")
print("\n🗺  ÉTAPES POSSIBLES")
for s, g, need in steps: print(f"  {'✅' if g else '⛔'} {s}" + ("" if g else f"  → il manque : {need}"))
if not f:
    print("\n⚠️  Sans FAL_KEY valide, rien ne peut être généré : c'est la seule clé nécessaire (fal.ai › Dashboard › API Keys, avec un peu de crédit).")
