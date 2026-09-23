#!/usr/bin/env python3
"""Page making-of : toutes les étapes, propositions, décisions et prompts exacts (lus dans les step.json).
Usage : python3 process.py <dossier_marque>   → <dossier>/web/process/index.html
Champs lus dans chaque <etape>/step.json : title, intro, jobs (prompts), decision. Films : <dossier>/film/film.json si présent."""
import html, json, sys
from pathlib import Path
E = html.escape
root = Path(sys.argv[1]).expanduser().resolve(); W = root / "web" / "process"; W.mkdir(parents=True, exist_ok=True)
brand = json.loads((root / "brand.json").read_text()) if (root / "brand.json").exists() else {"name": root.name}
secs = ""; nav = ""
for sj in sorted(root.glob("*/step.json")):
    s = json.loads(sj.read_text()); n = sj.parent.name
    figs = "".join(f'<figure><img src="../{n}/img/{j["id"]}.jpg" loading="lazy" alt=""><figcaption>{E(j.get("label", j["id"]))}</figcaption></figure>' for j in s["jobs"] if (root / "web" / n / "img" / f'{j["id"]}.jpg').exists())
    prompts = "".join(f'<details><summary>Prompt · {E(j.get("label", j["id"]))}</summary><pre>{E(j["prompt"])}</pre></details>' for j in s["jobs"])
    dec = f'<p class="out"><b>Décision :</b> {E(s["decision"])}</p>' if s.get("decision") else ""
    dec = f'<a class="go" href="../{n}/">Voir la page de choix de cette étape →</a>' + dec
    nav += f'<a href="#{n}">{E(s.get("title", n))}</a>'
    secs += f'<section id="{n}"><div class="num">{E(n)}</div><h2>{E(s.get("title", n))}</h2><p class="intro">{E(s.get("intro", ""))}</p><div class="g">{figs}</div>{prompts}{dec}</section>'
fj = root / "film" / "film.json"
if fj.exists():
    f = json.loads(fj.read_text())
    vids = "".join(f'<figure><video src="{E(v["url"])}" controls style="width:100%;border-radius:10px"></video><figcaption>{E(v.get("label", ""))}</figcaption></figure>' for v in f.get("videos", []))
    secs += f'<section id="film"><div class="num">film</div><h2>Le film</h2><div class="g">{vids}</div>' + "".join(f'<details><summary>{E(k)}</summary><pre>{E(v)}</pre></details>' for k, v in f.get("prompts", {}).items()) + "</section>"
    nav += '<a href="#film">Le film</a>'
sites = brand.get("sites", [])
if sites:
    for st in sites:
        shot = root / "web" / "process" / f"{st['slug']}.jpg"
        if not shot.exists():
            import subprocess
            ch = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            subprocess.run([ch, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1440,900", "--virtual-time-budget=8000", f"--screenshot={shot.with_suffix('.png')}", st["url"]], capture_output=True)
            if shot.with_suffix(".png").exists():
                from PIL import Image
                Image.open(shot.with_suffix(".png")).convert("RGB").save(shot, quality=86); shot.with_suffix(".png").unlink()
    cards = "".join(f'<div class="site"><a href="{E(st["url"])}" target="_blank"><img src="{E(st["slug"])}.jpg" alt=""></a><h3>{E(st["name"])}</h3><p>{E(st.get("pitch", ""))}</p><a class="bigbtn" href="{E(st["url"])}" target="_blank">Ouvrir le site {E(st["name"])} →</a></div>' for st in sites)
    secs += f'<section id="sites" class="final"><div class="num">Le résultat</div><h2>{"Les sites" if len(sites) > 1 else "Le site"}</h2><div class="sites">{cards}</div></section>'
    nav += '<a href="#sites" style="background:#1E2A44;color:#fff">Le résultat</a>'
(W / "index.html").write_text(f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex, nofollow"><title>{E(brand.get('name', ''))} · making-of</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:wght@300;500&family=Inter:wght@400;600&display=swap" rel="stylesheet"><style>*{{box-sizing:border-box}}body{{margin:0;background:#FBF7EF;color:#1E2A44;font-family:Inter,sans-serif;line-height:1.55}}.w{{max-width:1160px;margin:0 auto;padding:0 16px 60px}}h1{{font-family:Fraunces,serif;font-weight:300;font-size:clamp(32px,4.8vw,58px);margin:50px 0 12px}}nav a{{display:inline-block;margin:4px;padding:6px 12px;border:1px solid #E8E0D2;border-radius:999px;background:#fff;text-decoration:none;color:#1E2A44;font-size:13px;font-weight:600}}
section{{background:#fff;border:1px solid #E8E0D2;border-radius:24px;padding:22px;margin:22px 0}}.num{{font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:#F26A2E;font-weight:600}}h2{{font-family:Fraunces,serif;font-weight:500;font-size:28px;margin:4px 0 8px}}.intro{{color:#5A6275}}.g{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px;margin:12px 0}}figure{{margin:0}}figure img{{width:100%;border-radius:10px}}figcaption{{font-size:12px;color:#5A6275}}summary{{cursor:pointer;font-size:13px;font-weight:600;color:#5B2A86}}pre{{background:#F6F2EC;border-radius:10px;padding:10px;font:12px/1.5 ui-monospace,Menlo,monospace;white-space:pre-wrap;max-height:300px;overflow:auto}}.go{{display:inline-block;margin:8px 0;background:#F4EEFA;color:#5B2A86;border-radius:999px;padding:8px 14px;font-weight:600;font-size:14px;text-decoration:none}}.final{{background:#1E2A44;color:#fff}}.final h2{{color:#fff}}.sites{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:22px;margin-top:14px}}.site img{{width:100%;border-radius:16px;box-shadow:0 20px 50px rgba(0,0,0,.35)}}.site h3{{font-family:Fraunces,serif;font-size:26px;margin:14px 0 4px}}.site p{{color:#cfd3dc}}.bigbtn{{display:block;text-align:center;background:#F26A2E;color:#fff;text-decoration:none;font-weight:700;font-size:18px;padding:18px;border-radius:16px}}.out{{background:#F1ECFA;border-left:3px solid #5B2A86;padding:10px 12px;border-radius:10px}}</style></head>
<body><div class="w"><h1>Comment on a créé <i>{E(brand.get('name', ''))}</i>.</h1><nav>{nav}</nav>{secs}</div></body></html>""")
print(f"📄 {W / 'index.html'}")
