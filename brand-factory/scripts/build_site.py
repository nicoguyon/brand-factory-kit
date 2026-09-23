#!/usr/bin/env python3
"""Génère la boutique d'une marque à partir de brand.json : hero en diaporama, collection + fiche produit + panier,
histoire, lookbook, cabine d'essayage live (Jev + Nano Banana), FAQ, film, JSON-LD, llms.txt.

Usage : python3 build_site.py <dossier_marque>      → sortie : <dossier_marque>/site/<slug>/ (prêt pour Vercel)
"""
import html, json, shutil, subprocess, sys
from pathlib import Path
from PIL import Image

E = html.escape
KIT = Path(__file__).resolve().parent.parent
root = Path(sys.argv[1]).expanduser().resolve()
B = json.loads((root / "brand.json").read_text())
slug = B["slug"]; OUT = root / "site" / slug
for d in ("img/look", "img/prod", "img/models", "api"):
    (OUT / d).mkdir(parents=True, exist_ok=True)


def img(src, sub, w=2000, name=None):
    """Copie une image de la marque vers le site (JPEG web) et renvoie son chemin relatif."""
    s = root / src
    if not s.exists():
        sys.exit(f"❌ image introuvable : {s}")
    dst = OUT / "img" / sub / ((name or s.stem) + ".jpg")
    if not dst.exists() or dst.stat().st_mtime < s.stat().st_mtime:
        im = Image.open(s).convert("RGB"); im.thumbnail((w, w), Image.LANCZOS); im.save(dst, quality=84, optimize=True, progressive=True)
    return f"img/{sub}/{dst.name}"


C = B["colors"]; F = B["fonts"]
logo = img(B["logo"], "", 600, "logo")
heroes = [img(h, "look", 2400) for h in B["heroes"]]
look = [(img(l, "look", 1100, Path(l).stem + "-s"), img(l, "look", 2400)) for l in B.get("lookbook", [])]
prods = []
for p in B["products"]:
    prods.append({**{k: p[k] for k in ("id", "name", "variant", "desc", "price")}, "sw": p.get("colors", []), "badge": p.get("badge", ""), "image": img(p["image"], "prod", 1400, p["id"])})
T = B.get("tryon", {})
models = [{"id": m["id"], "name": m["name"], "profile": m["profile"], "img": img(m["image"], "models", 900, m["id"])} for m in T.get("models", [])]
story_img = img(B["story"]["image"], "look", 1400, Path(B["story"]["image"]).stem + "-story") if B.get("story") else ""
film = B.get("film") or {}
poster = img(film["poster"], "look", 1600, "film-poster") if film.get("poster") else ""

# ---------- API (fonctions serveur Vercel) ----------
for f in ("stylist.js", "tryon.js"):
    shutil.copy(KIT / "site" / "api" / f, OUT / "api" / f)
(OUT / "api" / "_brand.json").write_text(json.dumps({
    "name": B["name"], "category": B.get("category", ""), "usage": B.get("usage", ""),
    "tryon_mode": T.get("mode", "wear"), "tryon_scene": T.get("scene", ""),
    "sizes": B.get("sizes", []), "size_question": B.get("size_question", ""), "trait_question": T.get("trait_question", ""),
    "products": [{"id": p["id"], "name": p["name"], "variant": p["variant"], "desc": p["desc"], "image": p["image"]} for p in prods]}, ensure_ascii=False))

# ---------- SEO / GEO ----------
url = f"https://{B.get('domain') or slug + '.vercel.app'}/"
ld = [{"@context": "https://schema.org", "@type": "Organization", "name": B["name"], "url": url, "logo": url + logo, "description": B["tagline"]},
      {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in B.get("faq", [])]}]
ld += [{"@context": "https://schema.org", "@type": "Product", "name": p["name"], "image": url + p["image"], "description": p["desc"], "brand": {"@type": "Brand", "name": B["name"]},
        "offers": {"@type": "Offer", "price": p["price"], "priceCurrency": B.get("currency", "EUR"), "availability": "https://schema.org/PreOrder"}} for p in prods]
jsonld = "\n".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)

wt = lambda k, d: F.get(k, d)
CSS = f"""
:root{{--bg:{C['bg']};--ink:{C['ink']};--ink2:{C.get('ink2', '#5a6275')};--line:{C.get('line', '#e6e0d6')};--a1:{C['accent']};--a3:{C.get('accent2', C['accent'])};--card:#fff}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:'{F['body']}',-apple-system,sans-serif;line-height:1.55;-webkit-font-smoothing:antialiased}}a{{color:inherit}}img{{max-width:100%}}
.wrap{{max-width:1240px;margin:0 auto;padding:0 20px}}.demo{{background:var(--a3);text-align:center;font-size:13px;padding:7px 12px;font-weight:600}}
header.nav{{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--bg) 92%,transparent);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}}header.nav .wrap{{display:flex;align-items:center;justify-content:space-between;height:64px;gap:14px}}
.brand{{display:flex;align-items:center;gap:10px;text-decoration:none;font-family:'{F['head']}',serif;font-weight:700;font-size:19px}}.brand img{{height:44px;width:44px;object-fit:cover;border-radius:50%}}
nav.links{{display:flex;gap:20px;font-size:14px}}nav.links a{{text-decoration:none;opacity:.8}}.cartbtn{{border:1.5px solid var(--ink);background:transparent;border-radius:999px;padding:8px 14px;font:600 14px '{F['body']}';cursor:pointer;color:var(--ink)}}.cartbtn b{{background:var(--a1);color:#fff;border-radius:999px;margin-left:6px;font-size:12px;padding:1px 6px}}
.hero{{position:relative;height:calc(100svh - 64px);min-height:520px;overflow:hidden}}.hero img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0;transform:scale(1.06)}}.hero.go img{{transition:opacity 1.4s ease}}.hero img.on{{opacity:1!important;animation:kb 7s ease-out forwards}}@keyframes kb{{to{{transform:scale(1)}}}}
.hero .veil{{position:absolute;inset:0;z-index:2}}.hero.dark .veil{{background:linear-gradient(90deg,rgba(0,0,0,.5),rgba(0,0,0,.12) 42%,transparent 62%)}}.hero.light .veil{{background:linear-gradient(90deg,color-mix(in srgb,var(--bg) 95%,transparent),color-mix(in srgb,var(--bg) 70%,transparent) 30%,transparent 55%)}}
.hero .copy{{position:absolute;left:0;right:0;bottom:8vh;z-index:3;color:#fff}}.hero.light .copy{{color:var(--ink)}}.hero .copy .wrap>*{{max-width:min(560px,46vw)}}@media(max-width:760px){{.hero .copy .wrap>*{{max-width:none}}}}
.hero h1{{font-family:'{F['head']}',serif;font-weight:{wt('h1_weight', 700)};font-size:clamp(40px,6.2vw,92px);line-height:.98;margin:0 0 16px;letter-spacing:-.02em}}.hero p{{font-size:clamp(15px,1.5vw,19px);margin:0 0 24px}}
.dots{{position:absolute;right:20px;bottom:22px;z-index:3;display:flex;gap:8px}}.dots button{{width:10px;height:10px;border-radius:50%;border:0;background:rgba(255,255,255,.55);cursor:pointer;padding:0}}.dots button.on{{background:#fff;width:26px;border-radius:6px}}
.cta{{display:inline-block;background:var(--a1);color:#fff;border:0;border-radius:999px;padding:14px 26px;font:700 15px '{F['body']}';text-decoration:none;cursor:pointer}}
.marquee{{overflow:hidden;background:var(--ink);color:var(--bg);white-space:nowrap;padding:13px 0;font-family:'{F['head']}',serif;font-size:18px}}.marquee div{{display:inline-block;animation:mq 32s linear infinite}}.marquee span{{margin:0 26px}}.marquee span::after{{content:"✦";margin-left:52px;color:var(--a1)}}@keyframes mq{{to{{transform:translateX(-50%)}}}}
section{{padding:80px 0}}.eyebrow{{font-size:12px;letter-spacing:.18em;text-transform:uppercase;font-weight:700;color:var(--a1);margin:0 0 10px}}h2{{font-family:'{F['head']}',serif;font-weight:{wt('h2_weight', 600)};font-size:clamp(32px,4.4vw,58px);line-height:1.03;margin:0 0 14px}}.lead{{font-size:17px;color:var(--ink2);max-width:640px;margin:0}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:22px;margin-top:36px}}@media(max-width:900px){{.grid{{grid-template-columns:repeat(2,1fr)}}}}@media(max-width:560px){{.grid{{grid-template-columns:1fr}}}}
.p{{background:var(--card);border-radius:22px;overflow:hidden;cursor:pointer;border:1px solid var(--line);transition:transform .25s,box-shadow .25s}}.p:hover{{transform:translateY(-4px);box-shadow:0 18px 44px rgba(0,0,0,.1)}}.p .im{{aspect-ratio:4/5;overflow:hidden}}.p .im img{{width:100%;height:100%;object-fit:cover;display:block}}
.p .b{{padding:16px 18px;display:flex;justify-content:space-between;gap:10px}}.p h3{{font-family:'{F['head']}',serif;font-size:21px;margin:0}}.p .c{{font-size:13px;color:var(--ink2)}}.pr{{font-weight:700;font-size:17px;white-space:nowrap}}.sw{{display:flex;gap:5px;margin-top:8px}}.sw i{{width:16px;height:16px;border-radius:50%;border:1px solid rgba(0,0,0,.15)}}
.badge{{font-size:11px;font-weight:700;text-transform:uppercase;background:var(--a3);border-radius:999px;padding:3px 9px;margin-left:6px}}
.how{{display:grid;grid-template-columns:repeat(3,1fr);gap:22px;margin-top:34px}}@media(max-width:800px){{.how{{grid-template-columns:1fr}}}}.how div{{background:var(--card);border:1px solid var(--line);border-radius:20px;padding:24px}}.how b{{font-family:'{F['head']}',serif;font-size:44px;color:var(--a1)}}.how h4{{font-size:20px;margin:8px 0 6px}}.how p{{margin:0;color:var(--ink2)}}
.story{{display:grid;grid-template-columns:1.1fr 1fr;gap:50px;align-items:center}}@media(max-width:860px){{.story{{grid-template-columns:1fr}}}}.story img{{width:100%;border-radius:26px}}.story p{{font-size:17px;color:var(--ink2)}}
.look{{columns:3 300px;column-gap:16px;margin-top:34px}}.look img{{width:100%;border-radius:16px;margin-bottom:16px;cursor:zoom-in;break-inside:avoid}}
.tryon{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:30px}}@media(max-width:960px){{.tryon{{grid-template-columns:1fr}}}}.step{{background:var(--bg);border:1px solid var(--line);border-radius:22px;padding:20px}}.step>b{{font-family:'{F['head']}',serif;font-size:40px;color:var(--a1)}}.step h4{{font-size:20px;margin:4px 0 12px}}
.models{{display:grid;grid-template-columns:repeat(6,1fr);gap:6px;margin-bottom:10px}}.models button{{padding:0;border:2px solid transparent;border-radius:10px;overflow:hidden;cursor:pointer;background:none;aspect-ratio:4/5}}.models button.on{{border-color:var(--a1)}}.models img{{width:100%;height:100%;object-fit:cover}}
.shot{{position:relative;aspect-ratio:4/5;border-radius:16px;overflow:hidden;background:var(--line);display:flex;align-items:center;justify-content:center;color:var(--ink2);font-size:14px;text-align:center;padding:10px}}.shot video,.shot img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:none}}.shot .on{{display:block!important}}
.row{{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}}.opt{{border:1.5px solid var(--line);background:var(--card);border-radius:12px;padding:9px 12px;cursor:pointer;font:600 13px '{F['body']}';color:var(--ink)}}.opt.on{{background:var(--ink);color:var(--bg)}}
textarea{{width:100%;font:15px '{F['body']}';padding:12px;border-radius:14px;border:1.5px solid var(--line);background:var(--card);color:var(--ink)}}.chips{{display:flex;flex-direction:column;gap:6px;margin-bottom:8px}}.chips button{{text-align:left;border:1px solid var(--line);background:var(--card);border-radius:12px;padding:8px 10px;font:14px '{F['body']}';cursor:pointer;color:var(--ink)}}
.verdict{{margin-top:12px}}.big{{font-family:'{F['head']}',serif;font-size:24px;font-weight:700}}.bars div{{display:flex;align-items:center;gap:8px;font-size:12px;margin:3px 0}}.bars span{{width:120px;color:var(--ink2)}}.bars i{{height:8px;border-radius:4px;background:var(--a1);display:block;min-width:2px}}
.mini{{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}}.mini button{{width:46px;height:56px;border-radius:10px;overflow:hidden;border:2px solid transparent;padding:0;cursor:pointer}}.mini button.on{{border-color:var(--ink)}}.mini img{{width:100%;height:100%;object-fit:cover}}
.small,.note{{font-size:13px;color:var(--ink2)}}.jev{{background:var(--ink);color:var(--bg);border-radius:8px;padding:1px 8px}}.spin{{position:absolute;width:54px;height:54px;border:4px solid rgba(255,255,255,.4);border-top-color:var(--a1);border-radius:50%;animation:rot 1s linear infinite;display:none}}.spin.on{{display:block}}@keyframes rot{{to{{transform:rotate(360deg)}}}}
details.faq{{border-bottom:1px solid var(--line);padding:18px 0}}details.faq summary{{cursor:pointer;font-family:'{F['head']}',serif;font-size:20px;list-style:none}}details.faq p{{color:var(--ink2)}}
footer{{background:var(--ink);color:var(--bg);padding:50px 0 40px}}footer p{{opacity:.8;font-size:14px}}
.drawer{{position:fixed;inset:0;z-index:50;display:none}}.drawer.on{{display:block}}.drawer .bg{{position:absolute;inset:0;background:rgba(20,24,36,.5)}}.drawer .panel{{position:absolute;top:0;right:0;bottom:0;width:min(560px,100%);background:var(--bg);overflow:auto;padding:24px}}
.x{{position:absolute;top:14px;right:16px;border:0;background:var(--card);width:38px;height:38px;border-radius:50%;font-size:20px;cursor:pointer}}.pd img{{width:100%;border-radius:20px;aspect-ratio:4/5;object-fit:cover}}.pd h3{{font-family:'{F['head']}',serif;font-size:32px;margin:16px 0 2px}}
.thumbs{{display:flex;gap:8px;flex-wrap:wrap}}.thumbs button{{width:52px;height:52px;border-radius:12px;overflow:hidden;border:2px solid transparent;padding:0;cursor:pointer}}.thumbs button.on{{border-color:var(--ink)}}.thumbs img{{width:100%;height:100%;object-fit:cover}}
.cartline{{display:flex;gap:12px;align-items:center;border-bottom:1px solid var(--line);padding:12px 0}}.cartline img{{width:64px;height:80px;object-fit:cover;border-radius:10px}}.cartline div{{flex:1}}.total{{display:flex;justify-content:space-between;font-size:20px;font-weight:700;margin:18px 0}}
#big{{position:fixed;inset:0;background:rgba(15,18,28,.94);display:none;align-items:center;justify-content:center;z-index:60}}#big img{{max-width:95vw;max-height:94vh}}.toast{{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:var(--ink);color:var(--bg);padding:12px 18px;border-radius:999px;opacity:0;transition:.3s;z-index:70}}.toast.on{{opacity:1}}
@media(max-width:760px){{nav.links{{display:none}}section{{padding:56px 0}}}}
"""
DATA = {"products": prods, "models": models, "chips": T.get("chips", []), "sizes": B.get("sizes", []), "key": slug, "demo": B.get("demo_banner", True)}
JS = """
const D=__DATA__,P=D.products,$=s=>document.querySelector(s);let cart=[];try{cart=JSON.parse(localStorage.getItem(D.key+'cart')||'[]')}catch(e){}
function save(){try{localStorage.setItem(D.key+'cart',JSON.stringify(cart))}catch(e){}$('#cc').textContent=cart.reduce((a,l)=>a+l.q,0)}
function toast(m){const t=$('#toast');t.textContent=m;t.classList.add('on');setTimeout(()=>t.classList.remove('on'),1800)}
function openD(i){$('#'+i).classList.add('on')}function closeD(i){$('#'+i).classList.remove('on')}
$('#grid').innerHTML=P.map(p=>`<article class="p" data-id="${p.id}" id="${p.id}"><div class="im"><img src="${p.image}" alt="${p.name}" loading="lazy"></div><div class="b"><div><h3>${p.name}${p.badge?'<span class="badge">'+p.badge+'</span>':''}</h3><div class="c">${p.variant}</div><div class="sw">${p.sw.map(c=>`<i style="background:${c}"></i>`).join('')}</div></div><div class="pr">${p.price} €</div></div></article>`).join('');
document.querySelectorAll('.p').forEach(e=>e.onclick=()=>show(e.dataset.id));
let size=D.sizes.length?D.sizes[D.sizes.length-1].id:'';
function show(id){const p=P.find(x=>x.id===id);$('#pd').innerHTML=`<img src="${p.image}" alt=""><h3>${p.name}</h3><div class="small">${p.variant}</div><div class="pr" style="margin:8px 0">${p.price} €</div><p>${p.desc}</p>${D.sizes.length?'<div class="row">'+D.sizes.map(s=>`<button class="opt ${s.id===size?'on':''}" data-s="${s.id}">${s.label}</button>`).join('')+'</div>':''}<p class="small" style="margin-top:14px">Les autres variantes</p><div class="thumbs">${P.map(q=>`<button class="${q.id===id?'on':''}" data-o="${q.id}"><img src="${q.image}" alt=""></button>`).join('')}</div><button class="cta" id="add" style="width:100%;margin-top:18px">Ajouter au panier · ${p.price} €</button>`;
$('#pd').querySelectorAll('[data-s]').forEach(b=>b.onclick=()=>{size=b.dataset.s;show(id)});$('#pd').querySelectorAll('[data-o]').forEach(b=>b.onclick=()=>show(b.dataset.o));$('#add').onclick=()=>add(id);openD('prod')}
function add(id){const k=id+'-'+size,l=cart.find(x=>x.k===k);l?l.q++:cart.push({k,id,size,q:1});save();toast(P.find(p=>p.id===id).name+' ajouté')}
function renderCart(){$('#cl').innerHTML=cart.length?cart.map((l,i)=>{const p=P.find(x=>x.id===l.id);return `<div class="cartline"><img src="${p.image}" alt=""><div><b>${p.name}</b><br><span class="small">${l.size?'Taille '+l.size+' · ':''}${l.q} × ${p.price} €</span></div><button class="opt" data-r="${i}">Retirer</button></div>`}).join(''):'<p class="small">Ton panier est vide.</p>';$('#tot').textContent=cart.reduce((a,l)=>a+l.q*P.find(x=>x.id===l.id).price,0)+' €';$('#cl').querySelectorAll('[data-r]').forEach(b=>b.onclick=()=>{cart.splice(+b.dataset.r,1);save();renderCart()})}
$('#cartbtn').onclick=()=>{renderCart();openD('cart')};document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>closeD(b.dataset.close));$('#checkout').onclick=()=>toast(D.demo?'Boutique de démonstration : paiement non activé.':'Paiement à brancher (Stripe, Shopify…).');
document.querySelectorAll('.look img').forEach(i=>i.onclick=()=>{$('#bi').src=i.dataset.big;$('#big').style.display='flex'});$('#big').onclick=()=>$('#big').style.display='none';
(function(){const h=$('.hero');h.classList.add('go');const im=[...document.querySelectorAll('.hero img')],d=[...document.querySelectorAll('.dots button')];let i=0,t;function go(n){im[i].classList.remove('on');d[i]&&d[i].classList.remove('on');i=(n+im.length)%im.length;im[i].classList.add('on');d[i]&&d[i].classList.add('on');clearInterval(t);t=setInterval(()=>go(i+1),6000)}d.forEach((b,k)=>b.onclick=()=>go(k));if(im.length>1)t=setInterval(()=>go(i+1),6000)})();
save();
// ---- cabine d'essayage
if($('#tryon')){let photo=null,pick=P[0].id,stream=null;
function setPick(id){pick=id;document.querySelectorAll('#mini button').forEach(b=>b.classList.toggle('on',b.dataset.id===id));$('#go').disabled=!photo;$('#go').textContent='Essayer '+P.find(p=>p.id===id).name}
$('#mini').innerHTML=P.map(p=>`<button data-id="${p.id}" title="${p.name}"><img src="${p.image}" alt=""></button>`).join('');document.querySelectorAll('#mini button').forEach(b=>b.onclick=()=>setPick(b.dataset.id));
function useImage(src){const im=new Image();im.onload=()=>{const c=document.createElement('canvas'),s=Math.min(1,1024/Math.max(im.width,im.height));c.width=im.width*s;c.height=im.height*s;c.getContext('2d').drawImage(im,0,0,c.width,c.height);photo=c.toDataURL('image/jpeg',.88);$('#selfie').src=photo;$('#selfie').classList.add('on');$('#cam').classList.remove('on');$('#shotph').style.display='none';setPick(pick)};im.src=src}
$('#models').innerHTML=D.models.map(m=>`<button data-m="${m.id}" title="${m.name}"><img src="${m.img}" alt="${m.name}"></button>`).join('');
document.querySelectorAll('#models button').forEach(b=>b.onclick=async()=>{document.querySelectorAll('#models button').forEach(x=>x.classList.toggle('on',x===b));const m=D.models.find(x=>x.id===b.dataset.m);const r=new FileReader();r.onload=()=>{useImage(r.result);$('#talk').value=m.profile;setTimeout(ask,200)};r.readAsDataURL(await (await fetch(m.img)).blob())});
$('#chips').innerHTML=D.chips.map(c=>`<button>« ${c} »</button>`).join('');document.querySelectorAll('#chips button').forEach((b,i)=>b.onclick=()=>{$('#talk').value=D.chips[i];ask()});
$('#surprise').onclick=()=>{if(!D.chips.length)return;$('#talk').value=D.chips[Math.floor(Math.random()*D.chips.length)];ask()};
$('#camon').onclick=async()=>{const n=$('#camnote');if(!navigator.mediaDevices){n.textContent='Pas d\\'accès caméra : importe une photo.';return}n.textContent='Autorise la caméra dans la fenêtre du navigateur.';try{stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user',width:{ideal:1280}}});const v=$('#cam');v.srcObject=stream;await v.play();v.classList.add('on');$('#selfie').classList.remove('on');$('#shotph').style.display='none';$('#snap').disabled=false;n.textContent='Caméra active.'}catch(e){n.textContent=e.name==='NotAllowedError'?'Caméra refusée : autorise-la via l\\'icône de la barre d\\'adresse (et sur Mac : Réglages › Confidentialité › Caméra).':e.name==='NotReadableError'?'La caméra est utilisée par une autre application.':'Caméra indisponible ('+e.name+') : importe une photo.'}};
$('#snap').onclick=()=>{const v=$('#cam'),c=document.createElement('canvas');c.width=v.videoWidth;c.height=v.videoHeight;c.getContext('2d').drawImage(v,0,0);stream&&stream.getTracks().forEach(t=>t.stop());$('#snap').disabled=true;useImage(c.toDataURL('image/jpeg',.9))};
$('#file').onchange=e=>{const f=e.target.files[0];if(!f)return;const r=new FileReader();r.onload=()=>useImage(r.result);r.readAsDataURL(f)};
const SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR)$('#mic').style.display='none';else{const rec=new SR();rec.lang='fr-FR';rec.interimResults=true;rec.onresult=e=>{let t='';for(const r of e.results)t+=r[0].transcript;$('#talk').value=t};rec.onend=()=>{$('#mic').classList.remove('on');if($('#talk').value.trim())ask()};$('#mic').onclick=()=>{$('#mic').classList.add('on');rec.start()}}
async function ask(){const text=$('#talk').value.trim();if(!text)return toast('Décris ce que tu aimes et comment tu l\\'utiliserais.');$('#verdict').textContent='Jev décide…';try{const r=await fetch('/api/stylist',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})});const j=await r.json();if(!r.ok)throw new Error(j.error);const c=j.answers.variante,p=P.find(x=>x.id===c.choice);if(j.answers.taille)size=j.answers.taille.choice;setPick(p.id);
$('#verdict').innerHTML=`<div class="small">Jev a choisi :</div><div class="big">${p.name}${j.answers.taille?' · '+j.answers.taille.choice:''}</div><div class="small">Décidé en ${j.ms} ms par ${j.model}</div><div class="bars">${Object.entries(c.probabilities).sort((a,b)=>b[1]-a[1]).map(([k,v])=>`<div><span>${P.find(x=>x.id===k).name}</span><i style="width:${Math.round(v*140)}px"></i>${Math.round(v*100)} %</div>`).join('')}</div>`;if(photo)tryon()}catch(e){$('#verdict').textContent='Styliste indisponible : '+e.message}}
$('#ask').onclick=ask;
async function tryon(){if(!photo)return toast('Ajoute d\\'abord une photo.');$('#go').disabled=true;$('#spin').classList.add('on');$('#resph').textContent='Essayage en cours…';$('#res').classList.remove('on');const t0=Date.now();try{const r=await fetch('/api/tryon',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({photo,product:pick})});const j=await r.json();if(!r.ok)throw new Error(j.error);$('#res').src=j.image;$('#res').classList.add('on');$('#resph').textContent='';$('#tnote').innerHTML=`Rendu en ${((Date.now()-t0)/1000).toFixed(1)} s. <a href="#" id="addtry">Ajouter au panier</a>`;$('#addtry').onclick=e=>{e.preventDefault();add(pick)}}catch(e){$('#resph').textContent=e.message}$('#spin').classList.remove('on');$('#go').disabled=false}
$('#go').onclick=tryon;setPick(pick)}
"""
JS = JS.replace("__DATA__", json.dumps(DATA, ensure_ascii=False))
mode = T.get("mode", "wear")
who = {"wear": ("Qui essaie ?", "Choisis un mannequin, ou utilise ta photo"), "room": ("Ta pièce", "Choisis une pièce type, ou prends ta pièce en photo"), "hold": ("Qui essaie ?", "Choisis un profil, ou utilise ta photo")}[mode]
tryon_html = f"""<section id="essayage" style="background:var(--card)"><div class="wrap"><p class="eyebrow">Essayage · en direct</p><h2>{E(T.get('title', 'Essaie-le chez toi.'))}</h2><p class="lead">{E(T.get('intro', 'Choisis une photo, dis au styliste ce que tu aimes : il choisit pour toi, puis l’IA te montre le résultat en une dizaine de secondes.'))}</p>
<div class="tryon" id="tryon"><div class="step"><b>1</b><h4>{who[0]}</h4><div class="models" id="models"></div><div class="shot"><video id="cam" playsinline muted></video><img id="selfie" alt=""><span id="shotph">{who[1]}</span></div><div class="row"><button class="opt" id="camon">📷 Caméra</button><button class="opt" id="snap" disabled>Prendre la photo</button><label class="opt">Importer<input type="file" id="file" accept="image/*" hidden></label></div><div class="note" id="camnote"></div></div>
<div class="step"><b>2</b><h4>Ton styliste : <span class="jev">Jev</span></h4><p class="small">Un modèle de décision (TypeSafe) : il ne bavarde pas, il choisit.</p><div class="chips" id="chips"></div><textarea id="talk" rows="3" placeholder="Ou écris avec tes mots…"></textarea><div class="row"><button class="opt" id="mic">🎙 Dicter</button><button class="opt" id="ask">Demander à Jev</button><button class="opt" id="surprise">🎲 Surprends-moi</button></div><div class="verdict" id="verdict"></div><p class="small">Ou choisis toi-même :</p><div class="mini" id="mini"></div></div>
<div class="step"><b>3</b><h4>Le résultat</h4><div class="shot"><img id="res" alt=""><span id="resph">Le résultat apparaîtra ici</span><div class="spin" id="spin"></div></div><button class="cta" id="go" style="width:100%;margin-top:12px" disabled>Essayer</button><div class="note" id="tnote">Styliste : Jev (TypeSafe). Rendu : Nano Banana 2 (Google). La photo n'est pas conservée.</div></div></div></div></section>""" if T else ""
how = "".join(f"<div><b>{i + 1}</b><h4>{E(t)}</h4><p>{E(x)}</p></div>" for i, (t, x) in enumerate(B.get("how", [])))
faq = "".join(f'<details class="faq"><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in B.get("faq", []))
film_html = f"""<section id="film"><div class="wrap"><p class="eyebrow">Le film</p><h2>{E(film.get('title', ''))}</h2><div style="margin-top:26px;border-radius:24px;overflow:hidden;background:#000;aspect-ratio:16/9"><video src="{E(film['url'])}" {'poster="' + poster + '"' if poster else ''} controls playsinline preload="metadata" style="width:100%;height:100%"></video></div></div></section>""" if film.get("url") else ""
S = B.get("story") or {}
page = f"""<!doctype html><html lang="{B.get('lang', 'fr')}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{E(B['name'])} · {E(B['tagline'])}</title>
<meta name="description" content="{E(B['hero_sub'])}"><meta name="robots" content="{'noindex, nofollow' if B.get('noindex', True) else 'index, follow'}"><meta property="og:image" content="{url + heroes[0]}">
<link rel="icon" href="{logo}"><link href="https://fonts.googleapis.com/css2?{F['google']}&display=swap" rel="stylesheet"><style>{CSS}</style>{jsonld}</head><body>
{'<div class="demo">Boutique de démonstration · les commandes ne sont pas encore ouvertes</div>' if B.get('demo_banner', True) else ''}
<header class="nav"><div class="wrap"><a class="brand" href="#"><img src="{logo}" alt="">{E(B['name'])}</a><nav class="links"><a href="#collection">Collection</a>{'<a href="#histoire">Histoire</a>' if S else ''}{'<a href="#lookbook">Lookbook</a>' if look else ''}{'<a href="#essayage">Essayage</a>' if T else ''}{'<a href="#film">Film</a>' if film.get('url') else ''}</nav><button class="cartbtn" id="cartbtn">Panier<b id="cc">0</b></button></div></header>
<section class="hero {B.get('hero_style', 'dark')}" style="padding:0">{''.join(f'<img class="{"on" if i == 0 else ""}" src="{h}" alt="" {"" if i == 0 else "loading=lazy"}>' for i, h in enumerate(heroes))}<div class="veil"></div><div class="dots">{''.join(f'<button class="{"on" if i == 0 else ""}"></button>' for i in range(len(heroes))) if len(heroes) > 1 else ''}</div><div class="copy"><div class="wrap"><p class="eyebrow">{E(B.get('since', ''))}</p><h1>{B['hero_title']}</h1><p>{E(B['hero_sub'])}</p><a class="cta" href="#collection">Voir la collection</a></div></div></section>
{'<div class="marquee"><div>' + ''.join(f'<span>{E(t)}</span>' for t in B.get('marquee', []) * 2) + '</div></div>' if B.get('marquee') else ''}
<section id="collection"><div class="wrap"><p class="eyebrow">La collection</p><h2>{E(B.get('collection_title', 'La collection'))}</h2><p class="lead">{E(B.get('collection_sub', ''))}</p><div class="grid" id="grid"></div></div></section>
{'<section style="padding-top:0"><div class="wrap"><p class="eyebrow">Comment ça marche</p><div class="how">' + how + '</div></div></section>' if how else ''}
{f'<section id="histoire" style="background:var(--card)"><div class="wrap story"><img src="{story_img}" alt=""><div><p class="eyebrow">L’histoire</p><h2>{E(S["title"])}</h2>' + ''.join(f'<p>{E(x)}</p>' for x in S['paragraphs']) + '</div></div></section>' if S else ''}
{B.get('feature_html', '')}
{'<section id="lookbook"><div class="wrap"><p class="eyebrow">Lookbook</p><div class="look">' + ''.join(f'<img src="{s}" data-big="{b}" alt="" loading="lazy">' for s, b in look) + '</div></div></section>' if look else ''}
{tryon_html}
{'<section id="faq"><div class="wrap"><p class="eyebrow">Questions</p>' + faq + '</div></section>' if faq else ''}
{film_html}
<footer><div class="wrap"><h3 style="font-family:'{F['head']}',serif;font-size:26px;margin:0">{E(B['name'])}</h3><p>{E(B['tagline'])}</p></div></footer>
<div class="drawer" id="prod"><div class="bg" data-close="prod"></div><div class="panel"><button class="x" data-close="prod">×</button><div class="pd" id="pd"></div></div></div>
<div class="drawer" id="cart"><div class="bg" data-close="cart"></div><div class="panel"><button class="x" data-close="cart">×</button><h3>Panier</h3><div id="cl"></div><div class="total"><span>Total</span><span id="tot">0 €</span></div><button class="cta" id="checkout" style="width:100%">Commander</button></div></div>
<div id="big"><img id="bi" alt=""></div><div class="toast" id="toast"></div>
<script>{JS}{B.get('feature_js', '')}</script></body></html>"""
(OUT / "index.html").write_text(page)
(OUT / "robots.txt").write_text("User-agent: *\nDisallow: /\n" if B.get("noindex", True) else "User-agent: *\nAllow: /\n")
(OUT / "vercel.json").write_text(json.dumps({"functions": {"api/tryon.js": {"maxDuration": 60}, "api/stylist.js": {"maxDuration": 20}},
    "headers": [{"source": "/(.*)", "headers": [{"key": "X-Robots-Tag", "value": "noindex, nofollow"}]}] if B.get("noindex", True) else []}))
(OUT / "llms.txt").write_text(f"# {B['name']}\n\n> {B['tagline']} {B.get('usage', '')}\n\n## Produits\n" + "".join(f"- {p['name']} ({p['variant']}) : {p['price']} €. {p['desc']}\n" for p in prods) + "\n## FAQ\n" + "".join(f"- {q} {a}\n" for q, a in B.get("faq", [])))
# contrôle de syntaxe JS (évite qu'une erreur casse toute la page)
(OUT / ".check.js").write_text(JS + B.get("feature_js", ""))
r = subprocess.run(["node", "--check", str(OUT / ".check.js")], capture_output=True, text=True)
(OUT / ".check.js").unlink()
if r.returncode != 0:
    sys.exit("❌ Erreur JavaScript dans la page :\n" + r.stderr[:800])
print(f"✅ boutique générée : {OUT}  ({len(prods)} produits, essayage {'oui (' + mode + ')' if T else 'non'})")
