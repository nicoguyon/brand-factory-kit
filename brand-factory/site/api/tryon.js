// Essayage virtuel : photo (selfie ou pièce) + produit choisi -> image générée par Nano Banana 2 via fal (relance puis Nano Banana Pro).
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
  if (!/^data:image\/(jpeg|png|webp);base64,/.test(photo || '') || photo.length > 2900000) return res.status(400).json({ error: 'Photo invalide ou trop lourde' });
  const prompt = `Virtual try-on photograph for the brand ${CFG.name}. ${MODES[CFG.tryon_mode] || MODES.wear} ${CFG.tryon_scene}, with the product of the second photo: reproduce it exactly (shape, colours, materials, logo, proportions, true scale). How the product is used: ${CFG.usage}. Natural light, real photograph, no text, no extra logos.`;
  // Le filtre de contenu de fal refuse parfois au hasard : on alterne deux formulations, puis on passe sur Nano Banana Pro.
  const alt = `Virtual try-on for a fashion brand: the person of the first photo (same look, glasses kept) ${CFG.tryon_scene}, with the exact product of the second photo. How it is used: ${CFG.usage}. Real photograph, natural light, no text.`;
  const imgs = [photo, `https://${req.headers.host}/${p.image}`];
  const tries = [['fal-ai/nano-banana-2/edit', prompt], ['fal-ai/nano-banana-2/edit', alt], ['fal-ai/nano-banana-pro/edit', prompt], ['fal-ai/nano-banana-2/edit', prompt]];
  const t0 = Date.now(); let url = null, reason = null;
  for (const [ep, pr] of tries) {
    try {
      const body = { prompt: pr, image_urls: imgs, aspect_ratio: CFG.tryon_mode === 'room' ? '4:3' : '4:5', resolution: '1K', output_format: 'jpeg', safety_tolerance: '6' };
      const r = await fetch('https://fal.run/' + ep, { method: 'POST', headers: { Authorization: 'Key ' + process.env.FAL_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      const j = await r.json();
      url = j.images?.[0]?.url; if (url) break;
      reason = j.detail || j.error || r.status;
    } catch (e) { reason = String(e); }
    if (Date.now() - t0 > 48000) break;
  }
  if (!url) return res.status(422).json({ error: 'Le rendu n\'a pas abouti, essaie avec une autre photo (bien éclairée, sujet bien visible).', reason });
  res.json({ ms: Date.now() - t0, image: url });
};
