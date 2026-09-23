#!/usr/bin/env python3
"""Télécharge les photos d'une page produit (boutiques classiques, WooCommerce, Shopify).
Usage : python3 fetch_product.py <dossier_marque> <url> [<url2> …]   → <dossier>/product/
Si le site bloque (Etsy, Amazon : erreur 403), ouvre la page dans Chrome avec Claude in Chrome
et récupère les URL des images avec du JavaScript, ou enregistre les photos à la main dans product/."""
import re, sys, html
from pathlib import Path
import requests
root = Path(sys.argv[1]).expanduser().resolve(); out = root / "product"; out.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15"}
for url in sys.argv[2:]:
    r = requests.get(url, headers=UA, timeout=60)
    if r.status_code != 200:
        print(f"❌ {url} → {r.status_code} (site protégé : passer par le navigateur)"); continue
    s = r.text
    if "/products/" in url and "myshopify" in s or "Shopify" in s[:5000]:
        try:
            js = requests.get(url.split("?")[0] + ".json", headers=UA, timeout=30).json()["product"]
            urls = [i["src"] for i in js["images"]]; print(f"Shopify : {js['title']} · variantes : {[v['title'] for v in js['variants']]}")
        except Exception: urls = []
    else:
        urls = []
    urls += re.findall(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', s)
    urls += [u for u in re.findall(r'https?://[^"\'\s>]+?\.(?:jpe?g|png|webp)', s) if not re.search(r'-\d{2,4}x\d{2,4}\.|logo|icon|sprite|favicon', u, re.I)]
    seen = []; [seen.append(html.unescape(u)) for u in urls if html.unescape(u) not in seen]
    t = re.search(r"<title>(.*?)</title>", s, re.S); print(f"📦 {html.unescape(t.group(1)).strip() if t else url} · {len(seen)} images candidates")
    n = 0
    for u in seen[:16]:
        try:
            b = requests.get(u, headers=UA, timeout=60).content
            if len(b) < 30000: continue
            n += 1; (out / f"p{len(list(out.glob('p*')))+1:02d}{Path(u.split('?')[0]).suffix or '.jpg'}").write_bytes(b)
        except Exception: pass
    print(f"   {n} photos enregistrées dans {out}")
