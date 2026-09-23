---
name: brand-factory
description: Crée une marque complète à partir d'un vrai produit (lien ou photos), comme on l'a fait pour Annabelle — analyse du produit, 4 directions artistiques, logos, master produit et déclinaisons, série de visuels (avec une vraie personne si on a sa photo), boutique en ligne avec cabine d'essayage live (styliste Jev + Nano Banana), film de 30 s, et une page making-of avec tous les prompts. Chaque étape se choisit sur une page web avant de lancer la suivante. Déclencheurs — « crée une marque pour … », « brand factory », « fais une marque à partir de ce produit », « /brand-factory ».
---

# Brand Factory — refaire « Annabelle » pour n'importe quel produit

Tu vas guider l'utilisateur pas à pas, **exactement comme pour Annabelle** (un sac porte-planche de surf devenu deux marques, « Annabelle Club » et « Annabelle & la Lune »). Tous les fichiers d'Annabelle sont fournis dans `examples/` : ce sont les modèles à recopier et adapter.

Les scripts sont dans le dossier de cette skill : `SKILL_DIR/scripts/` (remplace `SKILL_DIR` par le chemin réel de ce dossier, en général `~/.claude/skills/brand-factory`).

---

## Règles d'or (valables à chaque étape)

1. **On montre avant de lancer.** Chaque étape produit une **page web de choix** (`board.py`). L'utilisateur regarde, choisit, puis dit « go ». Jamais deux étapes d'affilée sans son accord.
2. **Toujours le vrai produit en référence.** Aucune image avant d'avoir les photos du produit. (Leçon Annabelle : un premier essai sans photo a donné un autre produit, tout était à refaire.)
3. **Regard critique honnête.** Sur chaque page, écrire dans `critique` ce qui est raté (produit mal utilisé, visage pas ressemblant, échelle fausse). Proposer de refaire.
4. **Tout est documenté.** `process.py` fabrique la page « Comment on a créé <marque> » avec chaque étape, chaque choix et chaque prompt. La relancer après chaque étape.
5. **Parler simplement.** L'utilisateur n'est pas développeur : lui dire ce qu'on fait, ce que ça coûte, et lui donner les liens.

---

## Étape 0 — Vérifier les clés et les outils (OBLIGATOIRE, en premier)

```bash
python3 SKILL_DIR/scripts/preflight.py
```

Le script teste chaque clé et chaque outil, puis affiche les étapes possibles. Si une clé manque :
- lire à l'utilisateur la ligne « il manque : … » et l'aider à créer la clé (liens dans `keys.env.example`) ;
- les clés vont dans `~/.brand_factory/keys.env` (copier `SKILL_DIR/keys.env.example`) ;
- **seule `GEMINI_API_KEY` est indispensable**. Sans les autres, on saute les étapes concernées et on le dit.

Outils : `python3` avec `requests` et `pillow` (le script donne la commande d'installation), `node`, `ffmpeg`, `vercel` (`npm i -g vercel` puis `vercel login`). Pour Etsy et Dreamina : l'extension Claude in Chrome.

---

## Étape 1 — Le produit et le brief (≈ 10 min)

1. Créer le dossier de la marque : `mkdir -p ~/<slug>/{product,personne,poses,brand_kit}`.
2. Photos du produit :
   ```bash
   python3 SKILL_DIR/scripts/fetch_product.py ~/<slug> "<url du produit>"
   ```
   Si le site bloque (Etsy, Amazon : erreur 403), ouvrir la page avec Claude in Chrome et lister les images avec du JavaScript, ou demander à l'utilisateur d'enregistrer 3 photos dans `product/`. **Regarder les photos.**
3. Écrire avec l'utilisateur les **cinq blocs** qui servent dans tous les prompts (exemple Annabelle entre parenthèses) :
   - `PRODUCT` : la construction exacte (panneau de toile 60 × 48 cm, deux sangles plates, écusson brodé) ;
   - `USAGE` : comment on s'en sert + l'erreur à ne pas faire (la planche traverse la boucle, portée à la hanche ; jamais un cabas) ;
   - `VARIANTS` : ce qui se décline et à quel prix (couleurs panneau × sangles, tailles M / L, 95 € uni, 110 € imprimé) ;
   - `SCENES` : où vit le produit (plage, promenade, cabines) ;
   - `TRYON` : ce que montre l'essayage — `wear` (porté sur soi : vêtement, sac, bijou), `room` (posé chez soi : déco, meuble), `hold` (tenu ou consommé : boisson, cosmétique, tech).
4. Photo de la personne (si la marque rend hommage à quelqu'un) → `personne/visage.jpg`. Photos réelles d'usage libres de droits (Wikimedia Commons) → `poses/`.

## Étape 2 — Quatre directions artistiques → page de choix (≈ 10 min, ≈ 3 $)

- Modèle : `examples/01_directions.json` (les 4 directions d'Annabelle, 3 images chacune : hero « photo d'art », variante éditoriale, packshot).
- Écrire `~/<slug>/01_directions.json` : 4 univers **très différents**, chacun avec un nom, une grammaire photographique (citer des photographes : Martin Parr, Luigi Ghirri, Sarah Moon, Viviane Sassen…), une palette. Chaque prompt commence par le bloc `PRODUCT` et contient `USAGE`.
- Lancer puis publier la page :
  ```bash
  python3 SKILL_DIR/scripts/gen.py ~/<slug> ~/<slug>/01_directions.json
  python3 SKILL_DIR/scripts/board.py ~/<slug> 01_directions
  ```
- Ouvrir `~/<slug>/web/01_directions/index.html` (ou le publier, étape 9). L'utilisateur choisit. Il peut garder deux directions : ce sont alors **deux marques séparées**.
- Écrire sa décision dans le champ `decision` du `step.json`.

## Étape 3 — Logos → page de choix (≈ 5 min, ≈ 2 $)

- Modèle : `examples/02_logos.json`. Moteur `gpt` (GPT Image 2.5, texte lisible, clé `FAL_KEY`).
- Ce qui marche : des logos **qui frappent, construits sur l'initiale du nom** (Annabelle : le A qui EST le produit, la trace de bronzage en forme de A, la lune prise dans le A, deux cabines qui forment le A). Deux essais par idée.
- Critique obligatoire : signaler ce qui peut choquer dans le mauvais sens, ou se lire de travers.
- Copier le logo choisi dans `brand_kit/`.

## Étape 4 — Master produit puis déclinaisons → page (≈ 5 min, ≈ 2 $)

- `examples/03_master.json` : une photo studio de référence, avec les photos produit + le logo en références.
- `examples/04_declinaisons.json` : 6 variantes, chacune avec **le master** en première référence et « keep EXACTLY … change ONLY … ». Zéro dérive.
- Donner un nom à chaque variante selon l'univers (plages, phases de lune…) et un prix.

## Étape 5 — Visuels → page (test de 4, puis 10 par marque, ≈ 0,25 $ l'image)

- Modèle : `examples/05_visuels.json`. Références dans l'ordre : visage (`personne/visage.jpg`), déclinaison produit, pose réelle.
- **Commencer par 4 tests**, les montrer, puis lancer la série.
- ⚠ Si une image avec la personne sort vide : Google bloque les formulations du type « the real woman ». Écrire « the brand muse, casting reference for the model's look ».
- Si le visage n'est pas reconnaissable : mettre 3 références de visage (la photo + 2 visuels réussis) et relancer avec `--redo <id>`.

## Étape 6 — La boutique (≈ 15 min)

1. Copier `examples/brand.example.json` en `~/<slug>/brand.json` et le remplir : nom, couleurs, polices Google, textes, produits (images des déclinaisons), heroes et lookbook (visuels), FAQ, `tryon` (mode, scène, mannequins, phrases toutes faites), `sites`.
2. Mannequins pour l'essayage : la personne + 4 ou 5 profils générés (portraits 4:5, t-shirt blanc, fond neutre) avec chacun un petit profil d'usage.
3. Générer et publier :
   ```bash
   python3 SKILL_DIR/scripts/build_site.py ~/<slug>
   bash SKILL_DIR/scripts/deploy.sh ~/<slug>/site/<slug> <slug> avec-cles
   ```
   `avec-cles` envoie `GEMINI_API_KEY` et `TYPESAFE_API_KEY` au serveur (jamais dans la page). Le script vérifie le JavaScript avant de livrer.
4. **Tester sur le site** : cliquer un mannequin → Jev choisit → le rendu s'affiche en 10 à 20 s.
5. Fonction signature (optionnelle, `feature_html` + `feature_js` dans brand.json) : une idée propre à l'univers, qui marche dans le navigateur (Annabelle : carte de membre à ton nom ; phase de la lune en direct).

## Étape 7 — Le film → page plan, puis page de validation des images (payant)

- **Montrer le plan d'abord** : plans, prompts, musique, voix, coût. Attendre « go ».
- **Film à transitions (Kling 3.0)** : `examples/kling.example.json` → `~/<slug>/film/kling.json` (3 plans de 10 s, chaque plan part d'un visuel et arrive sur le suivant), puis :
  ```bash
  python3 SKILL_DIR/scripts/film_kling.py ~/<slug>
  bash SKILL_DIR/scripts/montage.sh ~/<slug> ~/<slug>/film/endcard.png
  ```
  ≈ 1,12 $ par plan de 10 s. ⚠ Suno refuse les noms d'artistes dans le style : décrire l'ambiance.
- **Film plan-séquence (Seedance 2.5 sur Dreamina)**, si l'utilisateur a un compte Dreamina : modèle de prompt `examples/seedance.example.txt` (verrous d'identité @Image, storyboard horodaté, un effet signature, un gag). Avec Claude in Chrome : AI Video › Seedance 2.5 › Omni reference › 16:9 › 30 s ; vérifier les crédits AVANT ; ajouter les références dans l'ordre des @Image ; coller le prompt ; envoyer ; télécharger (le fichier arrive sur le Bureau). **Ne jamais cliquer dans un écran de paiement.**
- Mettre la vidéo en ligne (ou dans le dossier du site), renseigner `film.url` dans brand.json, relancer `build_site.py` et `deploy.sh`.

## Étape 8 — La page « Comment on a créé <marque> »

```bash
python3 SKILL_DIR/scripts/process.py ~/<slug>
```
Chaque étape a son bouton vers sa page de choix ; la fin montre chaque site en capture d'écran avec un gros bouton « Ouvrir le site » (renseigner `sites` dans brand.json).

## Étape 9 — Publier les pages de choix et le making-of

```bash
bash SKILL_DIR/scripts/deploy.sh ~/<slug>/web <slug>-making-of
```
Donner à l'utilisateur les liens : pages de choix, making-of, boutique.

---

## Coûts indicatifs (une marque)

| Poste | Coût |
|---|---|
| Directions (12 images) | ≈ 3 $ |
| Logos (16 images) | ≈ 2 $ |
| Master + 6 déclinaisons | ≈ 1 $ |
| 10 à 14 visuels 4K | ≈ 3 $ |
| Film Kling (3 × 10 s) | ≈ 3,40 $ |
| Essayage en ligne | ≈ 0,04 $ par rendu |

## Pannes connues

| Symptôme | Cause | Solution |
|---|---|---|
| Image vide, « IMAGE_OTHER » | filtre visages réels | « brand muse, casting reference » |
| Suno « SENSITIVE_WORD_ERROR » | nom d'artiste dans le style | décrire l'ambiance |
| Page du site blanche ou boutons morts | erreur JavaScript | `build_site.py` le détecte ; lire le message |
| Site qui demande une connexion Vercel | protection activée par défaut | Settings › Deployment Protection › désactiver |
| Etsy / Amazon 403 | anti-robot | Claude in Chrome ou photos enregistrées à la main |
| « missing_scope » au déploiement | plusieurs équipes Vercel | automatique, ou `VERCEL_SCOPE=<équipe>` |
