/** Stripe Customer Portal — cancel / update payment without a Securely account. */
async function stripeForm(secret, path, params) {
  const response = await fetch(`https://api.stripe.com/v1${path}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${secret}`,
      "content-type": "application/x-www-form-urlencoded",
    },
    body: params,
  });
  const payload = await response.json();
  return { ok: response.ok, payload };
}

export default async function handler(req, res) {
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
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      res.status(400).json({ error: "Enter the email from your Stripe receipt." });
      return;
    }
    const host = req.headers["x-forwarded-host"] || req.headers.host;
    const proto = req.headers["x-forwarded-proto"] || "https";
    const origin = `${proto}://${host}`;

    const lookup = await fetch(
      `https://api.stripe.com/v1/customers?email=${encodeURIComponent(email)}&limit=1`,
      { headers: { Authorization: `Bearer ${secret}` } },
    );
    const customers = await lookup.json();
    const customer = customers.data?.[0];
    if (!customer?.id) {
      res.status(404).json({ error: "No Stripe customer found for that email." });
      return;
    }

    const params = new URLSearchParams();
    params.set("customer", customer.id);
    params.set("return_url", `${origin}/billing.html`);
    const session = await stripeForm(secret, "/billing_portal/sessions", params);
    if (!session.ok || typeof session.payload.url !== "string") {
      const message = session.payload.error?.message || "Could not open the billing portal.";
      res.status(400).json({ error: String(message).slice(0, 180) });
      return;
    }
    res.status(200).json({ url: session.payload.url });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Portal failed.";
    res.status(400).json({ error: message.slice(0, 180) });
  }
}
