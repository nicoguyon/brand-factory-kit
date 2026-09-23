// Styliste IA : un modèle de langage (via fal, clé FAL_KEY) choisit la variante et la taille, avec une phrase d'explication.
const CFG = require('./_brand.json');
const hits = new Map();
function limited(ip, max, ms) { const n = Date.now(); const a = (hits.get(ip) || []).filter(t => n - t < ms); a.push(n); hits.set(ip, a); return a.length > max; }
module.exports = async (req, res) => {
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST' });
  const ip = (req.headers['x-forwarded-for'] || '').split(',')[0] || 'x';
  if (limited(ip, 30, 600000)) return res.status(429).json({ error: 'Trop de demandes, réessaie dans quelques minutes.' });
  const { text } = req.body || {};
  if (!text || typeof text !== 'string' || text.length > 800) return res.status(400).json({ error: 'Requête invalide' });
  const variants = {}; CFG.products.forEach(p => { variants[p.id] = `${p.name} : ${p.variant}. ${p.desc}`; });
  const sizes = {}; (CFG.sizes || []).forEach(s => { sizes[s.id] = s.label; });
  const prompt = `Marque : ${CFG.name} (${CFG.category}).\nVariantes (id : description) : ${JSON.stringify(variants)}\n${Object.keys(sizes).length ? 'Tailles (id : description) : ' + JSON.stringify(sizes) + '\n' + (CFG.size_question || '') + '\n' : ''}Ce que dit le client : « ${text.replace(/[«»]/g, '')} »\n\nRéponds UNIQUEMENT par un objet JSON : {"variante": "<id>", ${Object.keys(sizes).length ? '"taille": "<id>", ' : ''}"probabilites": {"<id>": <0 à 1>, … pour chaque variante, somme = 1}, "raison": "<une phrase courte, chaleureuse, en tutoyant>"}`;
  const t0 = Date.now();
  const r = await fetch('https://fal.run/openrouter/router', { method: 'POST', headers: { Authorization: 'Key ' + process.env.FAL_KEY, 'Content-Type': 'application/json' },
    body: JSON.stringify({ model: CFG.stylist_model || 'google/gemini-2.5-flash', temperature: 0.2, system_prompt: 'Tu es le styliste de la marque. Tu choisis pour le client la variante qui lui correspond le mieux. Tu réponds uniquement en JSON valide.', prompt }) });
  const j = await r.json();
  if (!r.ok || !j.output) return res.status(502).json({ error: 'Styliste indisponible', detail: j });
  let d; try { d = JSON.parse(j.output.replace(/```json|```/g, '').trim()); } catch (e) { return res.status(502).json({ error: 'Réponse illisible du styliste' }); }
  if (!variants[d.variante]) d.variante = CFG.products[0].id;
  if (Object.keys(sizes).length && !sizes[d.taille]) d.taille = CFG.sizes[CFG.sizes.length - 1].id;
  res.json({ ms: Date.now() - t0, model: CFG.stylist_model || 'google/gemini-2.5-flash', ...d });
};
