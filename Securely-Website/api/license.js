/** Verify an email has an active Securely Stripe subscription. No Securely account. */
async function stripeGet(secret, path) {
  const response = await fetch(`https://api.stripe.com/v1${path}`, {
    headers: { Authorization: `Bearer ${secret}` },
  });
  const payload = await response.json();
  return { ok: response.ok, status: response.status, payload };
}

function cors(res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
}

export default async function handler(req, res) {
  cors(res);
  if (req.method === "OPTIONS") {
    res.status(204).end();
    return;
  }
  if (req.method !== "POST") {
    res.status(405).json({ error: "Method not allowed." });
    return;
  }
  try {
    const secret = process.env.STRIPE_SECRET_KEY || "";
    if (!secret) {
      res.status(503).json({ error: "Billing is not configured yet." });
      return;
    }
    const body = typeof req.body === "object" && req.body ? req.body : {};
    const email = typeof body.email === "string" ? body.email.trim().toLowerCase() : "";
    if (!email || email.length > 200 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      res.status(400).json({ error: "Enter a valid email address." });
      return;
    }

    const customers = await stripeGet(
      secret,
      `/customers?email=${encodeURIComponent(email)}&limit=10`,
    );
    if (!customers.ok) {
      res.status(400).json({ error: "Could not look up that email in Stripe." });
      return;
    }
    const list = customers.payload.data || [];
    if (!list.length) {
      res.status(200).json({ active: false, status: "no_customer", email });
      return;
    }

    for (const customer of list) {
      const subs = await stripeGet(
        secret,
        `/subscriptions?customer=${encodeURIComponent(customer.id)}&status=all&limit=20`,
      );
      if (!subs.ok) continue;
      const active = (subs.payload.data || []).find((sub) =>
        ["active", "trialing"].includes(String(sub.status || "")),
      );
      if (active) {
        res.status(200).json({
          active: true,
          status: active.status,
          email,
          customerId: customer.id,
        });
        return;
      }
    }

    res.status(200).json({ active: false, status: "inactive", email });
  } catch (error) {
    const message = error instanceof Error ? error.message : "License check failed.";
    res.status(400).json({ error: message.slice(0, 180) });
  }
}
