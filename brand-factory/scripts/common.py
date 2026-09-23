"""Outils communs du kit Brand Factory : clés, config de marque, moteurs d'images/vidéo/son."""
import base64, json, os, sys, time
from pathlib import Path
import requests

sys.stdout.reconfigure(line_buffering=True)
KIT = Path(__file__).resolve().parent.parent


def load_keys():
    """Clés : variables d'environnement, sinon ./keys.env, sinon ~/.brand_factory/keys.env."""
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


# ---------- Images : Nano Banana Pro / Nano Banana 2 (Google) ----------
def nano_banana(prompt, refs=(), ratio="16:9", size="2K", model="gemini-3-pro-image", tries=3):
    """Retourne les octets PNG, ou None. refs = chemins d'images (≤ 14)."""
    k = key("GEMINI_API_KEY")
    parts = [{"inline_data": {"mime_type": mime(r), "data": base64.b64encode(Path(r).read_bytes()).decode()}} for r in refs]
    parts.append({"text": prompt})
    body = {"contents": [{"parts": parts}], "generationConfig": {"responseModalities": ["IMAGE", "TEXT"], "imageConfig": {"aspectRatio": ratio, "imageSize": size}}}
    for a in range(tries):
        try:
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={k}", json=body, timeout=300).json()
            c = (r.get("candidates") or [{}])[0]
            for p in (c.get("content") or {}).get("parts", []):
                if "inlineData" in p:
                    return base64.b64decode(p["inlineData"]["data"])
            print(f"   ⚠ pas d'image ({c.get('finishReason') or r.get('error', {}).get('message', '?')}), essai {a + 1}")
        except Exception as e:
            print(f"   ⚠ {e}")
        time.sleep(5 * (a + 1))
    return None


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


# ---------- Son ----------
def suno(style, prompt, title, out_dir, max_s=600):
    """Musique instrumentale Suno V5. ⚠ aucun nom d'artiste dans style (refus SENSITIVE_WORD_ERROR)."""
    k = key("SUNO_API_KEY"); B = "https://api.sunoapi.org"
    H = {"Authorization": f"Bearer {k}", "Content-Type": "application/json", "User-Agent": "curl/8.7.1"}
    t = requests.post(f"{B}/api/v1/generate", headers=H, json={"customMode": True, "instrumental": True, "model": "V5", "callBackUrl": "https://example.com/cb", "title": title, "style": style, "prompt": prompt}, timeout=60).json()["data"]["taskId"]
    t0 = time.time()
    while time.time() - t0 < max_s:
        time.sleep(15)
        d = requests.get(f"{B}/api/v1/generate/record-info?taskId={t}", headers=H, timeout=60).json().get("data", {})
        st = d.get("status") or ""
        if "ERROR" in st or "FAIL" in st:
            raise RuntimeError(f"Suno : {st} {d.get('errorMessage')}")
        songs = [s for s in ((d.get("response") or {}).get("sunoData") or []) if s.get("audioUrl")]
        if st == "SUCCESS" and songs:
            out = []
            for i, s in enumerate(songs, 1):
                p = Path(out_dir) / f"music_{i}.mp3"; p.write_bytes(requests.get(s["audioUrl"], headers={"User-Agent": "curl/8.7.1"}, timeout=300).content); out.append(p)
            return out
    raise RuntimeError("Suno : délai dépassé")


def elevenlabs(text, out, voice_id):
    r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128",
                      headers={"xi-api-key": key("ELEVENLABS_API_KEY"), "Content-Type": "application/json"},
                      json={"text": text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.6, "similarity_boost": 0.8, "style": 0.2, "use_speaker_boost": True}}, timeout=120)
    r.raise_for_status(); Path(out).write_bytes(r.content); return out
