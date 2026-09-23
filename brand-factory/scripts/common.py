"""Outils communs du kit Brand Factory : clés, config de marque, moteurs d'images/vidéo/son."""
import base64, json, os, sys, time
from pathlib import Path
import requests

sys.stdout.reconfigure(line_buffering=True)
KIT = Path(__file__).resolve().parent.parent


def load_keys():
    """Clé : variable d'environnement FAL_KEY, sinon ./keys.env, sinon ~/.brand_factory/keys.env."""
    for p in [Path.cwd() / "keys.env", Path.home() / ".brand_factory/keys.env"]:
        if p.exists():
            for line in p.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return os.environ


def key(name):
    load_keys()
    v = os.environ.get(name)
    if not v:
        sys.exit(f"❌ Clé manquante : {name}. Ajoute-la dans keys.env (voir keys.env.example).")
    return v


def load_brand(root):
    p = Path(root) / "brand.json"
    if not p.exists():
        sys.exit(f"❌ {p} introuvable. Copie examples/brand.example.json et remplis-le.")
    return json.loads(p.read_text())


def mime(p):
    s = str(p).lower()
    return "image/png" if s.endswith(".png") else "image/webp" if s.endswith(".webp") else "image/jpeg"


# ---------- fal.ai : file d'attente générique ----------
def fal_upload(path):
    h = {"Authorization": "Key " + key("FAL_KEY"), "Content-Type": "application/json"}
    p = Path(path)
    d = requests.post("https://rest.fal.ai/storage/upload/initiate?storage_type=fal-cdn-v3", headers=h,
                      json={"file_name": p.name, "content_type": mime(p)}, timeout=60).json()
    requests.put(d["upload_url"], data=p.read_bytes(), headers={"Content-Type": mime(p)}, timeout=300).raise_for_status()
    return d["file_url"]


def fal_run(endpoint, payload, poll=6, max_s=1200):
    h = {"Authorization": "Key " + key("FAL_KEY"), "Content-Type": "application/json"}
    sub = requests.post(f"https://queue.fal.run/{endpoint}", headers=h, json=payload, timeout=60).json()
    if "status_url" not in sub:
        raise RuntimeError(f"fal a refusé la requête : {sub}")
    t0 = time.time()
    while time.time() - t0 < max_s:
        time.sleep(poll)
        st = requests.get(sub["status_url"], headers=h, timeout=30).json().get("status")
        if st == "COMPLETED":
            break
        if st not in ("IN_QUEUE", "IN_PROGRESS"):
            raise RuntimeError(f"fal : statut {st}")
    for _ in range(5):
        r = requests.get(sub["response_url"], headers=h, timeout=60)
        if r.status_code == 200:
            return r.json()
        time.sleep(4)
    raise RuntimeError(f"fal : résultat introuvable ({r.status_code} {r.text[:200]})")


def nano_banana(prompt, refs=(), ratio="16:9", size="2K", model="pro", tries=3):
    """Nano Banana via fal. model = "pro" (Nano Banana Pro, ≈ 0,15 $) ou "flash" (Nano Banana 2, ≈ 0,08 $).
    refs = chemins d'images locales (≤ 14) : envoyées sur fal puis passées à la version /edit. Retourne les octets de l'image, ou None."""
    base = "fal-ai/nano-banana-pro" if model == "pro" else "fal-ai/nano-banana-2"
    for a in range(tries):
        try:
            payload = {"prompt": prompt, "aspect_ratio": ratio, "resolution": size, "output_format": "png", "safety_tolerance": "4" if a == 0 else "6"}
            if refs:
                payload["image_urls"] = [fal_upload(r) for r in refs]
            res = fal_run(base + ("/edit" if refs else ""), payload, poll=4)
            if res.get("images"):
                return requests.get(res["images"][0]["url"], timeout=180).content
            print(f"   ⚠ pas d'image ({str(res)[:160]}), essai {a + 1}")
        except Exception as e:
            print(f"   ⚠ {str(e)[:200]}, essai {a + 1}")
        time.sleep(5 * (a + 1))
    return None


def gpt_image(prompt, w=1536, h=1536):
    """GPT Image 2.5 Sunburst via fal (texte lisible : logos, étiquettes)."""
    res = fal_run("openai/gpt-image-2.5/sunburst/text-to-image", {"prompt": prompt, "image_size": {"width": w, "height": h}, "quality": "high", "output_format": "png"}, poll=5)
    return requests.get(res["images"][0]["url"], timeout=120).content


def kling(prompt, start, end=None, duration="10", negative=""):
    p = {"prompt": prompt, "start_image_url": fal_upload(start), "duration": duration, "negative_prompt": negative, "cfg_scale": 0.5, "generate_audio": False}
    if end:
        p["end_image_url"] = fal_upload(end)
    res = fal_run("fal-ai/kling-video/v3/pro/image-to-video", p, poll=10)
    return requests.get(res["video"]["url"], timeout=300).content


# ---------- Son (via fal) ----------
def music(prompt, out, seconds=40):
    """Musique instrumentale ElevenLabs Music via fal. Décrire l'ambiance, les instruments, le tempo (pas de nom d'artiste)."""
    res = fal_run("elevenlabs/music/v2.5", {"prompt": prompt, "force_instrumental": True, "music_length_ms": int(seconds * 1000), "output_format": "mp3_44100_128"}, poll=5)
    Path(out).write_bytes(requests.get(res["audio"]["url"], timeout=300).content); return out


def voice(text, out, voice_name="Charlotte", lang="fr"):
    """Voix off ElevenLabs via fal. Voix possibles : Charlotte, Alice, Matilda, Lily, George, Daniel, Brian…"""
    res = fal_run("fal-ai/elevenlabs/tts/turbo-v2.5", {"text": text, "voice": voice_name, "language_code": lang, "stability": 0.6, "similarity_boost": 0.8}, poll=2)
    Path(out).write_bytes(requests.get(res["audio"]["url"], timeout=120).content); return out
