/** Server-side contact form validation (+ optional webhook delivery). */
import { setCors, rateLimit } from "./_limits.js";

export default async function handler(req, res) {
  setCors(req, res);
  if (req.method === "OPTIONS") {
    res.status(204).end();
    return;
  }
  if (req.method !== "POST") {
    res.status(405).json({ error: "Method not allowed." });
    return;
  }

  const limited = rateLimit(req, "contact", { limit: 8, windowMs: 60 * 60 * 1000 });
  if (limited) {
    res.setHeader("Retry-After", String(limited.retryAfterSec));
    res.status(429).json({ error: "Too many messages from this network. Try again later." });
    return;
  }

  try {
    const body = typeof req.body === "object" && req.body ? req.body : {};
    const name = String(body.name || "").trim().slice(0, 120);
    const email = String(body.email || "").trim().toLowerCase().slice(0, 200);
    const message = String(body.message || "").trim().slice(0, 4000);

    if (!name || name.length < 2) {
      res.status(400).json({ error: "Enter your name." });
      return;
    }
    if (!email || email.length > 200 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      res.status(400).json({ error: "Enter a valid email address." });
      return;
    }
    if (!message || message.length < 5) {
      res.status(400).json({ error: "Enter a short message (at least 5 characters)." });
      return;
    }

    const webhook = process.env.CONTACT_WEBHOOK_URL || "";
    let delivered = false;
    if (webhook) {
      const wr = await fetch(webhook, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          source: "securely-contact",
          name,
          email,
          message,
          at: new Date().toISOString(),
        }),
      });
      delivered = wr.ok;
    }

    res.status(200).json({
      ok: true,
      delivered,
      message: delivered
        ? "Thanks — your message was delivered."
        : "Thanks — your message was accepted. The team inbox will follow up at support@trysecurely.com.",
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Could not send message.";
    res.status(400).json({ error: message.slice(0, 180) });
  }
}
