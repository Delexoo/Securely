import { loadGroqApiKeys, setGroqStickyKeyIndex, groqStickyKeyIndex } from '../lib/groqKeys.js';

/**
 * POST /api/analyze
 * Body: { text: string, imageBase64?: string }
 * Response: OpenAI-compatible JSON { choices: [{ message: { content: string } }] }
 */
export default async function analyze(req, res) {
  const keys = loadGroqApiKeys();
  if (keys.length === 0) {
    res.status(503).json({
      error: 'No Groq API keys configured',
      hint: 'Set GROQ_API_KEY and/or GROQ_API_KEY1–5 or SECURELY1–5',
    });
    return;
  }

  const { text = '' } = req.body || {};
  const model = process.env.GROQ_MODEL || 'llama-3.1-8b-instant';

  const userContent = `You are a cybersecurity expert analyzing screen OCR text for threats.
Respond with SAFE, SUSPICIOUS: (details), UNSURE: (details), LEGITIMATE_LOGIN, or LEGITIMATE_PAYMENT as appropriate.

OCR TEXT:
${String(text).slice(0, 100000)}`;

  const body = JSON.stringify({
    model,
    messages: [{ role: 'user', content: userContent }],
    temperature: 0.3,
    max_tokens: 2048,
  });

  let lastStatus = 0;
  let lastDetail = null;
  const n = keys.length;
  const start = groqStickyKeyIndex % n;

  for (let step = 0; step < n; step++) {
    const idx = (start + step) % n;
    const key = keys[idx];
    const r = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${key}`,
        'Content-Type': 'application/json',
      },
      body,
    });

    const j = await r.json().catch(() => ({}));
    if (r.ok) {
      const content = j?.choices?.[0]?.message?.content;
      if (content != null && String(content).trim().length > 0) {
        setGroqStickyKeyIndex(idx);
        res.status(200).json(j);
        return;
      }
      lastStatus = 200;
      lastDetail = j;
      continue;
    }

    lastStatus = r.status;
    lastDetail = j;
    if (r.status === 429 || r.status === 401 || r.status === 503) continue;
    break;
  }

  res.status(500).json({
    error: 'Groq request failed',
    status: lastStatus,
    detail: lastDetail,
    keysTried: keys.length,
  });
}

