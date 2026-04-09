/**
 * Groq keys from Render / env:
 * - GROQ_API_KEY (single key)
 * - GROQ_API_KEY1 … GROQ_API_KEY5 (numbered keys; failover order)
 * - SECURELY1 … SECURELY5 or Securely1 … Securely5 (alias per slot)
 */
export function loadGroqApiKeys() {
  const keys = [];
  const single = process.env.GROQ_API_KEY?.trim();
  if (single) keys.push(single);
  for (let i = 1; i <= 5; i++) {
    const g = process.env[`GROQ_API_KEY${i}`]?.trim();
    const s = process.env[`SECURELY${i}`]?.trim();
    const camel = process.env[`Securely${i}`]?.trim();
    const k = g || s || camel;
    if (k) keys.push(k);
  }
  return [...new Set(keys)];
}

export let groqStickyKeyIndex = 0;
export function setGroqStickyKeyIndex(i) {
  if (Number.isFinite(i) && i >= 0) groqStickyKeyIndex = i;
}

