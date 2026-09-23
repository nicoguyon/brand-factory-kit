#!/bin/bash
# Publie un dossier sur Vercel (production). Usage : deploy.sh <dossier> <nom-du-projet> [avec-cles]
# « avec-cles » : ajoute FAL_KEY côté serveur (nécessaire pour l'essayage live et le styliste).
# Plusieurs équipes Vercel ? Mets VERCEL_SCOPE=<nom-équipe>, sinon la première équipe proposée est prise.
set -uo pipefail
cd "$1"; NAME="$2"; SC=()
[ -n "${VERCEL_SCOPE:-}" ] && SC=(--scope "$VERCEL_SCOPE")
OUT=$(vercel link --yes --project "$NAME" ${SC[@]+"${SC[@]}"} 2>&1)
if echo "$OUT" | grep -q "missing_scope"; then
  TEAM=$(echo "$OUT" | python3 -c "import sys,json,re;t=sys.stdin.read();j=json.loads(t[t.index('{'):t.rindex('}')+1]);print(j['choices'][0]['name'])")
  echo "ℹ️  Plusieurs équipes Vercel : j'utilise « $TEAM » (sinon : VERCEL_SCOPE=<équipe>)"; SC=(--scope "$TEAM")
  vercel link --yes --project "$NAME" ${SC[@]+"${SC[@]}"} >/dev/null 2>&1 || { echo "❌ vercel link a échoué"; exit 1; }
elif [ ! -f .vercel/project.json ]; then echo "$OUT" | tail -5; echo "❌ vercel link a échoué (as-tu fait « vercel login » ?)"; exit 1; fi
if [ "${3:-}" = "avec-cles" ]; then
  KF="${KEYS:-}"; [ -z "$KF" ] && for f in ./keys.env ../../keys.env "$HOME/.brand_factory/keys.env"; do [ -f "$f" ] && { KF="$f"; break; }; done
  for k in FAL_KEY; do v=$(grep "^$k=" "$KF" 2>/dev/null | cut -d= -f2-); if [ -n "$v" ]; then vercel env rm $k production --yes >/dev/null 2>&1; printf "%s" "$v" | vercel env add $k production >/dev/null 2>&1 && echo "🔑 $k ajoutée au serveur"; else echo "⚠️  $k absente de $KF : l'essayage ne marchera pas"; fi; done
fi
URL=$(vercel --prod --yes 2>&1 | grep -oE "https://[a-zA-Z0-9.-]+\.vercel\.app" | tail -1)
echo "✅ Déployé : https://$NAME.vercel.app  (déploiement : $URL)"
echo "ℹ️  Si la page demande une connexion Vercel : projet › Settings › Deployment Protection › désactive « Vercel Authentication »."
