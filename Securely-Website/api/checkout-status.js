/** Confirm a Stripe Checkout session and return subscription status for immediate app unlock. */
async function stripeGet(secret, path) {
  const response = await fetch(`https://api.stripe.com/v1${path}`, {
    headers: { Authorization: `Bearer ${secret}` },
  });
  const payload = await response.json();
  return { ok: response.ok, status: response.status, payload };
}

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
  const limited = rateLimit(req, "checkout-status", { limit: 120, windowMs: 60 * 60 * 1000 });
  if (limited) {
    res.setHeader("Retry-After", String(limited.retryAfterSec));
    res.status(429).json({ error: "Too many status checks. Try again shortly." });
    return;
  }
  try {
    const secret = process.env.STRIPE_SECRET_KEY || "";
    if (!secret) {
      res.status(503).json({ error: "Billing is not configured yet." });
      return;
    }
    const body = typeof req.body === "object" && req.body ? req.body : {};
    const sessionId = typeof body.sessionId === "string" ? body.sessionId.trim() : "";
    if (!sessionId || !/^cs_[A-Za-z0-9_]+$/.test(sessionId) || sessionId.length > 200) {
      res.status(400).json({ error: "Missing or invalid checkout session." });
      return;
    }

    const session = await stripeGet(
      secret,
      `/checkout/sessions/${encodeURIComponent(sessionId)}?expand[]=subscription&expand[]=customer`,
    );
    if (!session.ok) {
      res.status(400).json({ error: "Could not load that checkout session." });
      return;
    }
    const s = session.payload;
    const email = String(
      s.customer_details?.email || s.customer_email || s.customer?.email || "",
    )
      .trim()
      .toLowerCase();

    const paymentOk = ["paid", "no_payment_required"].includes(String(s.payment_status || ""));
    const statusComplete = String(s.status || "") === "complete";
    let subStatus = "";
    let active = false;

    if (s.subscription) {
      const sub = typeof s.subscription === "object" ? s.subscription : null;
      if (sub) {
        subStatus = String(sub.status || "");
        active = ["active", "trialing"].includes(subStatus);
      } else if (typeof s.subscription === "string") {
        const subRes = await stripeGet(secret, `/subscriptions/${encodeURIComponent(s.subscription)}`);
        if (subRes.ok) {
          subStatus = String(subRes.payload.status || "");
          active = ["active", "trialing"].includes(subStatus);
        }
      }
    }

    // Fresh checkout / 100% promo: session complete + paid|no_payment_required
    // before subscription expand settles — unlock immediately.
    if (!active && statusComplete && paymentOk) {
      active = true;
      subStatus = subStatus || "active";
    }

    res.status(200).json({
      email,
      active,
      status: subStatus || s.status || (active ? "active" : "inactive"),
      paymentStatus: s.payment_status || "",
      sessionStatus: s.status || "",
      sessionId,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Checkout status failed.";
    res.status(400).json({ error: message.slice(0, 180) });
  }
}
