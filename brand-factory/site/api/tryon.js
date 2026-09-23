// Essayage virtuel : photo (selfie ou pièce) + produit choisi -> image générée (Nano Banana 2, relance puis Pro).
const CFG = require('./_brand.json');
const hits = new Map();
function limited(ip, max, ms) { const n = Date.now(); const a = (hits.get(ip) || []).filter(t => n - t < ms); a.push(n); hits.set(ip, a); return a.length > max; }
const MODES = {
  wear: 'The first photo shows the customer: use it as the casting reference for this person\'s look (face, hairstyle, glasses if any, skin tone, body type), faithful, not beautified. Create a realistic vertical photo of this same person',
  room: 'The first photo shows the customer\'s own room: keep this room exactly (walls, furniture, light, perspective). Create a realistic photo of this same room',
  hold: 'The first photo shows the customer: use it as the casting reference for this person\'s look, faithful, not beautified. Create a realistic vertical photo of this same person',
};
module.exports = async (req, res) => {
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST' });
  const ip = (req.headers['x-forwarded-for'] || '').split(',')[0] || 'x';
  if (limited(ip, 8, 600000)) return res.status(429).json({ error: 'Plusieurs essayages déjà faits, réessaie dans quelques minutes.' });
  const { photo, product } = req.body || {};
  const p = CFG.products.find(x => x.id === product);
  if (!p) return res.status(400).json({ error: 'Produit inconnu' });
  const m = /^data:image\/(jpeg|png|webp);base64,(.+)$/.exec(photo || '');
  if (!m || m[2].length > 2800000) return res.status(400).json({ error: 'Photo invalide ou trop lourde' });
  const pr = await fetch(`https://${req.headers.host}/${p.image}`);
  if (!pr.ok) return res.status(500).json({ error: 'Image produit introuvable' });
  const pb64 = Buffer.from(await pr.arrayBuffer()).toString('base64');
  const prompt = `Virtual try-on photograph for the brand ${CFG.name}. ${MODES[CFG.tryon_mode] || MODES.wear} ${CFG.tryon_scene}, with the product of the second photo: reproduce it exactly (shape, colours, materials, logo, proportions, true scale). How the product is used: ${CFG.usage}. Natural light, real photograph, no text, no extra logos.`;
  const t0 = Date.now(); let part = null, reason = null;
  for (const model of ['gemini-3.1-flash-image', 'gemini-3.1-flash-image', 'gemini-3-pro-image']) {
    const r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${process.env.GEMINI_API_KEY}`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ contents: [{ parts: [{ inline_data: { mime_type: 'image/' + m[1], data: m[2] } }, { inline_data: { mime_type: 'image/jpeg', data: pb64 } }, { text: prompt }] }], generationConfig: { responseModalities: ['IMAGE', 'TEXT'], imageConfig: { aspectRatio: CFG.tryon_mode === 'room' ? '4:3' : '4:5', imageSize: '1K' } } }) });
    const j = await r.json();
    part = (j.candidates?.[0]?.content?.parts || []).find(x => x.inlineData);
    if (part) break;
    reason = j.candidates?.[0]?.finishReason || j.error?.message;
    if (Date.now() - t0 > 40000) break;
  }
  if (!part) return res.status(422).json({ error: 'Le rendu n\'a pas abouti, essaie avec une autre photo (bien éclairée, sujet bien visible).', reason });
  res.json({ ms: Date.now() - t0, image: `data:${part.inlineData.mimeType};base64,${part.inlineData.data}` });
};
