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

test("GEMINI_API_KEY", lambda k: (lambda r: (r.status_code == 200, "OK" if r.status_code == 200 else f"refusée ({r.status_code})"))(requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={k}", timeout=20)))
test("FAL_KEY", lambda k: (lambda r: (r.status_code in (200, 201), "OK" if r.status_code in (200, 201) else f"refusée ({r.status_code})"))(requests.post("https://rest.fal.ai/storage/upload/initiate?storage_type=fal-cdn-v3", headers={"Authorization": "Key " + k}, json={"file_name": "t.txt", "content_type": "text/plain"}, timeout=20)))
test("TYPESAFE_API_KEY", lambda k: (lambda r: (r.status_code == 200, "OK" if r.status_code == 200 else f"refusée ({r.status_code})"))(requests.post("https://api.typesafe.ai/v1/systemone", headers={"Authorization": "Bearer " + k}, json={"model": "jev-latest", "state": "test", "questions": {"q": {"type": "noul", "instructions": "Is this a test?"}}}, timeout=20)))
def suno(k):
    j = requests.get("https://api.sunoapi.org/api/v1/generate/credit", headers={"Authorization": "Bearer " + k, "User-Agent": "curl/8.7.1"}, timeout=20).json()
    return j.get("code") == 200, f"OK · {j.get('data')} crédits" if j.get("code") == 200 else f"refusée ({j.get('msg')})"
test("SUNO_API_KEY", suno)
test("ELEVENLABS_API_KEY", lambda k: (lambda r: (r.status_code == 200, "OK" if r.status_code == 200 else f"refusée ({r.status_code})"))(requests.get("https://api.elevenlabs.io/v1/voices", headers={"xi-api-key": k}, timeout=20)))

T = {}
for t in ("python3", "node", "ffmpeg", "vercel", "git"):
    T[t] = bool(shutil.which(t))
try:
    import PIL; T["Pillow"] = True
except ImportError: T["Pillow"] = False

ok = lambda k: R.get(k, ("", False))[1]
steps = [
    ("Récupérer le produit, pages de validation, making-of", T["python3"] and T["Pillow"], "python3 + Pillow"),
    ("Directions, master, déclinaisons, visuels (Nano Banana Pro)", ok("GEMINI_API_KEY"), "GEMINI_API_KEY"),
    ("Logos avec texte lisible (GPT Image 2.5)", ok("FAL_KEY"), "FAL_KEY"),
    ("Boutique en ligne", T["node"] and T["vercel"], "node + vercel (npm i -g vercel, puis vercel login)"),
    ("Essayage live : rendu (Nano Banana 2)", ok("GEMINI_API_KEY"), "GEMINI_API_KEY"),
    ("Essayage live : styliste Jev", ok("TYPESAFE_API_KEY"), "TYPESAFE_API_KEY (console.typesafe.ai, 5 $ offerts)"),
    ("Film à transitions (Kling 3.0)", ok("FAL_KEY") and T["ffmpeg"], "FAL_KEY + ffmpeg (brew install ffmpeg)"),
    ("Musique du film (Suno)", ok("SUNO_API_KEY"), "SUNO_API_KEY (sunoapi.org)"),
    ("Voix off (ElevenLabs)", ok("ELEVENLABS_API_KEY"), "ELEVENLABS_API_KEY"),
    ("Film plan-séquence (Seedance 2.5)", True, "compte Dreamina + Claude in Chrome (pas de clé)"),
]
print("\n🔑 CLÉS")
for k, (m, g) in R.items(): print(f"  {'✅' if g else '❌'} {k:20s} {m}")
print("\n🧰 OUTILS")
for k, g in T.items(): print(f"  {'✅' if g else '❌'} {k}")
print("\n🗺  ÉTAPES POSSIBLES")
for s, g, need in steps: print(f"  {'✅' if g else '⛔'} {s}" + ("" if g else f"  → il manque : {need}"))
if not ok("GEMINI_API_KEY"):
    print("\n⚠️  Sans GEMINI_API_KEY, rien ne peut être généré : c'est la seule clé indispensable (aistudio.google.com › Get API key).")
