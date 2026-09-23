# Brand Factory — une skill Claude Code pour créer une marque de A à Z

À partir d'un **vrai produit** (un lien ou des photos), Claude Code crée une marque complète en suivant la méthode utilisée pour **Annabelle** : directions artistiques, logos, master produit et déclinaisons, visuels éditoriaux, boutique en ligne avec cabine d'essayage live et styliste IA, film de 30 s, et une page « Comment on a créé la marque » avec tous les prompts.

➡ Le cas complet, étape par étape : **https://annabelle.comptoiria.com/process/**

## Installer (le plus simple : le demander à Claude Code)

Ouvre Claude Code et colle :

```
Installe la skill brand-factory depuis https://github.com/nicoguyon/brand-factory-kit :
clone le dépôt, copie le dossier brand-factory dans ~/.claude/skills/,
crée ~/.brand_factory/keys.env à partir de keys.env.example,
installe ce qui manque (python3 requests pillow, ffmpeg, node, vercel),
puis lance scripts/preflight.py et dis-moi ce qu'il manque.
```

Ou à la main, dans un terminal :

```bash
git clone https://github.com/nicoguyon/brand-factory-kit.git
mkdir -p ~/.claude/skills && cp -R brand-factory-kit/brand-factory ~/.claude/skills/
mkdir -p ~/.brand_factory && cp ~/.claude/skills/brand-factory/keys.env.example ~/.brand_factory/keys.env
open -e ~/.brand_factory/keys.env        # mets ta FAL_KEY
python3 ~/.claude/skills/brand-factory/scripts/preflight.py
```

## Une seule clé : fal

`FAL_KEY` (fal.ai › Dashboard › API Keys). Elle sert à tout : images (Nano Banana Pro et 2), logos (GPT Image 2.5), essayage et styliste IA, film (Kling 3.0), musique et voix off (ElevenLabs). Compte une vingtaine de dollars de crédit fal pour une marque complète. Pour publier la boutique : un compte Vercel gratuit (`npm i -g vercel` puis `vercel login`).

## Lancer ta propre marque

Dans Claude Code :

```
/brand-factory
Produit : <lien du produit, ou dossier de photos>
Pour qui : <prénom ou nom de la marque> — photo : <chemin, si la marque rend hommage à quelqu'un>
Envie : <3-4 mots : osé, décalé, poétique…>
Fais-moi valider chaque étape sur une page avant de lancer la suivante.
```

Claude vérifie d'abord ta clé, puis déroule les étapes en te montrant une page de choix à chaque fois.

## Contenu

| Dossier | Rôle |
|---|---|
| `brand-factory/SKILL.md` | la méthode, étape par étape |
| `brand-factory/scripts/` | vérification de la clé, images, pages de choix, boutique, film, making-of, publication |
| `brand-factory/site/api/` | l'essayage et le styliste (fonctions serveur Vercel) |
| `brand-factory/examples/` | tous les fichiers du cas Annabelle, à recopier et adapter |

Créé par Comptoir IA.
