// Styliste Jev (TypeSafe) : choisit la variante (et la taille si le produit en a) à partir de ce que dit le client.
const CFG = require('./_brand.json');
const hits = new Map();
function limited(ip, max, ms) { const n = Date.now(); const a = (hits.get(ip) || []).filter(t => n - t < ms); a.push(n); hits.set(ip, a); return a.length > max; }
module.exports = async (req, res) => {
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST' });
  const ip = (req.headers['x-forwarded-for'] || '').split(',')[0] || 'x';
  if (limited(ip, 30, 600000)) return res.status(429).json({ error: 'Trop de demandes, réessaie dans quelques minutes.' });
  const { text } = req.body || {};
  if (!text || typeof text !== 'string' || text.length > 800) return res.status(400).json({ error: 'Requête invalide' });
  const criteria = {}; CFG.products.forEach(p => { criteria[p.id] = `${p.name} : ${p.variant}. ${p.desc}`; });
  const questions = { variante: { type: 'choice', instructions: `Tu conseilles les clients de la marque ${CFG.name} (${CFG.category}). Quelle variante correspond le mieux aux goûts, aux habitudes et à la situation décrits dans \`client\` ?`, criteria } };
  if (CFG.sizes && CFG.sizes.length) { const c = {}; CFG.sizes.forEach(s => { c[s.id] = s.label; }); questions.taille = { type: 'choice', instructions: CFG.size_question || 'Quelle taille ou quel format convient au client décrit dans `client` ?', criteria: c }; }
  if (CFG.trait_question) questions.trait = { type: 'noul', instructions: CFG.trait_question };
  const t0 = Date.now();
  const r = await fetch('https://api.typesafe.ai/v1/systemone', { method: 'POST', headers: { Authorization: 'Bearer ' + process.env.TYPESAFE_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ model: 'jev-latest', state: { client: text }, questions }) });
  const j = await r.json();
  if (!r.ok) return res.status(502).json({ error: 'Styliste indisponible', detail: j });
  res.json({ ms: Date.now() - t0, model: j.model, answers: j.answers });
};
