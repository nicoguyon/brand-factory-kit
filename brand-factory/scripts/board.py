#!/usr/bin/env python3
"""Construit la page de validation d'une étape (images, prompts exacts, regard critique, choix, sélection à copier)
et la page d'accueil qui liste toutes les étapes.

Usage : python3 board.py <dossier_marque> <etape>        ex. : python3 board.py ~/annabelle 01_directions
Champs optionnels dans step.json : "critique": {"id": "texte"}, "choose": "group" | "none", "decision": "texte après choix".
"""
import html, json, sys
from pathlib import Path
from PIL import Image

E = html.escape
root = Path(sys.argv[1]).expanduser().resolve(); name = sys.argv[2]
brand = json.loads((root / "brand.json").read_text()) if (root / "brand.json").exists() else {"name": root.name}
step = json.loads((root / name / "step.json").read_text())
web = root / "web"; W = web / name; (W / "img").mkdir(parents=True, exist_ok=True)
crit = step.get("critique", {})

def thumb(i):
    src = root / name / "img" / f"{i}.png"; dst = W / "img" / f"{i}.jpg"
    if src.exists() and (not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime):
        im = Image.open(src).convert("RGB"); im.thumbnail((1800, 1800)); im.save(dst, quality=85, optimize=True)
    return f"img/{i}.jpg" if src.exists() else None

groups = {}
for j in step["jobs"]:
    groups.setdefault(j.get("group", "Propositions"), []).append(j)
body = ""
for g, jobs in groups.items():
    cards = ""
    for j in jobs:
        t = thumb(j["id"])
        img = f'<img src="{t}" data-big="{t}" loading="lazy" alt="">' if t else '<div class="miss">image non générée</div>'
        c = f'<p class="crit"><b>Regard critique :</b> {E(crit[j["id"]])}</p>' if j["id"] in crit else ""
        btn = f'<button class="btn" data-g="{E(g)}" data-id="{E(j["id"])}">Je choisis</button>' if step.get("choose", "group") == "group" else ""
        cards += f'<article class="card">{img}<div class="b"><h4>{E(j.get("label", j["id"]))}</h4>{c}<details><summary>Prompt exact · {E(j.get("engine", "nano"))} · {E(j.get("ratio", ""))}</summary><pre>{E(j["prompt"])}</pre><p class="refs">Références : {E(", ".join(j.get("refs", [])) or "aucune")}</p></details>{btn}</div></article>'
    body += f'<section><h2>{E(g)}</h2><div class="grid">{cards}</div></section>'
dec = f'<div class="dec"><b>Décision :</b> {E(step["decision"])}</div>' if step.get("decision") else ""
CSS = """:root{--paper:#FBF7EF;--ink:#1E2A44;--ink2:#5A6275;--line:#E8E0D2;--acc:#F26A2E}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:Inter,-apple-system,sans-serif;line-height:1.55}
.wrap{max-width:1180px;margin:0 auto;padding:0 16px 120px}header{padding:48px 0 8px}.k{font-size:11px;letter-spacing:.18em;text-transform:uppercase;font-weight:600;color:var(--acc)}h1{font-family:Fraunces,Georgia,serif;font-weight:300;font-size:clamp(30px,4.4vw,54px);line-height:1.04;margin:8px 0 12px}.lead{color:var(--ink2);max-width:820px}
h2{font-family:Fraunces,Georgia,serif;font-weight:500;font-size:28px;margin:30px 0 10px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px}
.card{background:#fff;border:1px solid var(--line);border-radius:18px;overflow:hidden}.card img{width:100%;display:block;cursor:zoom-in}.miss{padding:40px;text-align:center;color:var(--ink2)}.b{padding:14px 16px 16px}h4{margin:0 0 6px;font-size:16px}
.crit{font-size:13.5px;color:var(--ink2)}.crit b{color:var(--acc)}summary{cursor:pointer;font-size:13px;font-weight:600;color:#5B2A86}pre{background:#F6F2EC;border-radius:10px;padding:10px;font:12px/1.5 ui-monospace,Menlo,monospace;white-space:pre-wrap;max-height:300px;overflow:auto}.refs{font-size:12px;color:var(--ink2)}
.btn{margin-top:8px;border:1px solid var(--ink);background:#fff;border-radius:999px;padding:8px 14px;font:600 13px Inter,sans-serif;cursor:pointer}.btn.on{background:var(--acc);border-color:var(--acc);color:#fff}
.dec{background:#F1ECFA;border-left:3px solid #5B2A86;padding:12px 14px;border-radius:10px;margin-top:14px}.bar{position:fixed;left:0;right:0;bottom:0;background:var(--ink);color:#fff;padding:12px 16px}.bar .in{max-width:1180px;margin:0 auto;display:flex;gap:12px;align-items:center}.bar code{flex:1;color:#ddd;font-size:12.5px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}.bar button{border:0;border-radius:999px;padding:9px 16px;background:var(--acc);color:#fff;font-weight:600;cursor:pointer}
#big{position:fixed;inset:0;background:rgba(15,18,28,.94);display:none;align-items:center;justify-content:center;z-index:9;cursor:zoom-out}#big img{max-width:95vw;max-height:94vh;border-radius:8px}a{color:var(--acc)}"""
page = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex, nofollow"><title>{E(brand.get('name', ''))} · {E(step.get('title', name))}</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:wght@300;500&family=Inter:wght@400;600&display=swap" rel="stylesheet"><style>{CSS}</style></head><body><div class="wrap">
<header><p class="k">{E(brand.get('name', ''))} · {E(name)} · <a href="../">toutes les étapes</a></p><h1>{E(step.get('title', name))}</h1><p class="lead">{E(step.get('intro', ''))}</p>{dec}</header>{body}</div>
<div class="bar"><div class="in"><b>Ma sélection</b><code id="sel">rien de choisi</code><button id="cp">Copier</button></div></div><div id="big" onclick="this.style.display='none'"><img id="bi" alt=""></div>
<script>const S={{}};document.querySelectorAll('[data-big]').forEach(e=>e.onclick=()=>{{bi.src=e.dataset.big;big.style.display='flex'}});
document.querySelectorAll('.btn[data-g]').forEach(b=>b.onclick=()=>{{const g=b.dataset.g;document.querySelectorAll('.btn[data-g="'+g+'"]').forEach(x=>x.classList.remove('on'));b.classList.add('on');S[g]=b.dataset.id;sel.textContent=Object.entries(S).map(([g,i])=>g+' : '+i).join(' ; ');}});
cp.onclick=()=>{{navigator.clipboard.writeText('{E(name)} → '+sel.textContent);cp.textContent='Copié ✓'}};</script></body></html>"""
(W / "index.html").write_text(page)
# page d'accueil : toutes les étapes
steps = sorted(p.parent.name for p in root.glob("*/step.json"))
links = "".join(f'<li><a href="{s}/">{E(json.loads((root / s / "step.json").read_text()).get("title", s))}</a> <span>{E(s)}</span></li>' for s in steps)
extra = '<li><a href="process/">Le making-of complet</a></li>' if (web / "process").exists() else ""
(web / "index.html").write_text(f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex, nofollow"><title>{E(brand.get('name', ''))} · étapes</title><style>{CSS} li{{margin:10px 0;font-size:18px}} li span{{color:var(--ink2);font-size:13px}}</style></head><body><div class="wrap"><header><p class="k">Brand Factory</p><h1>{E(brand.get('name', ''))}</h1><p class="lead">Chaque étape se valide sur sa page avant de lancer la suivante.</p></header><ol>{links}{extra}</ol></div></body></html>""")
(web / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
(web / "vercel.json").write_text(json.dumps({"headers": [{"source": "/(.*)", "headers": [{"key": "X-Robots-Tag", "value": "noindex, nofollow"}]}]}))
print(f"📄 {W / 'index.html'}")
