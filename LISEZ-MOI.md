# Brand Factory — le kit

Créer une marque complète à partir d'un vrai produit, avec Claude Code, en suivant exactement la méthode utilisée pour **Annabelle** : https://annabelle.comptoiria.com/process/

## Installation (5 minutes)

Le plus simple : dans Claude Code, demande « Installe la skill brand-factory depuis https://github.com/nicoguyon/brand-factory-kit ». Sinon, à la main :

1. **Copier la skill** dans Claude Code :
   ```bash
   mkdir -p ~/.claude/skills && cp -R brand-factory ~/.claude/skills/
   ```
2. **Les clés** :
   ```bash
   mkdir -p ~/.brand_factory && cp brand-factory/keys.env.example ~/.brand_factory/keys.env
   open -e ~/.brand_factory/keys.env
   ```
   Remplis `FAL_KEY` (fal.ai › Dashboard › API Keys). C'est la seule clé : elle sert aux images, aux logos, à l'essayage, au styliste, au film, à la musique et à la voix off. Prévois une vingtaine de dollars de crédit fal pour une marque complète.
3. **Les outils** (Mac) :
   ```bash
   brew install ffmpeg node && npm i -g vercel && vercel login
   python3 -m pip install requests pillow
   ```
4. **Vérifier** :
   ```bash
   python3 ~/.claude/skills/brand-factory/scripts/preflight.py
   ```
   Le script dit si la clé marche et quelles étapes sont possibles.

## Utilisation

Dans Claude Code, écris par exemple :

```
/brand-factory
Produit : <lien du produit>
Pour qui : <prénom de la personne ou nom de la marque>, photo : <chemin de la photo>
Envie : <3-4 mots : osé, décalé, poétique…>
Fais-moi valider chaque étape sur une page avant de lancer la suivante.
```

Claude déroule les étapes, te montre une page de choix à chaque fois, et termine par la boutique en ligne, le film et la page « Comment on a créé ta marque ».

## Contenu

| Dossier | Rôle |
|---|---|
| `SKILL.md` | la méthode, étape par étape |
| `scripts/` | vérification des clés, génération d'images, pages de choix, boutique, film, making-of, publication |
| `site/api/` | le styliste Jev et l'essayage (fonctions serveur Vercel) |
| `examples/` | tous les fichiers du cas Annabelle, à recopier et adapter |
| `keys.env.example` | la liste des clés, avec où les créer |
