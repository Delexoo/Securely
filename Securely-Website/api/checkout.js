/** Vercel serverless: Stripe Checkout for Securely ($3/month). Supports SECURELY-DEV 100% off. */
export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
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
      res.status(503).json({ error: "Billing is not configured yet (missing STRIPE_SECRET_KEY)." });
      return;
    }
    const body = typeof req.body === "object" && req.body ? req.body : {};
    const email = typeof body.email === "string" ? body.email.trim() : "";
    if (!email || email.length > 200 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      res.status(400).json({ error: "Enter a valid email for your receipt and app activation." });
      return;
    }
    const host = req.headers["x-forwarded-host"] || req.headers.host;
    const proto = req.headers["x-forwarded-proto"] || "https";
    const origin = `${proto}://${host}`;
    const priceId = process.env.STRIPE_PRICE_ID || "";
    const promoCode = process.env.SECURELY_PROMO_CODE || "SECURELY-DEV";
    const promoId = process.env.STRIPE_PROMO_ID || "";

    const params = new URLSearchParams();
    params.set("mode", "subscription");
    params.set("line_items[0][quantity]", "1");
    if (priceId) {
      params.set("line_items[0][price]", priceId);
    } else {
      params.set("line_items[0][price_data][currency]", "usd");
      params.set("line_items[0][price_data][unit_amount]", "300");
      params.set("line_items[0][price_data][recurring][interval]", "month");
      params.set("line_items[0][price_data][product_data][name]", "Securely");
      params.set(
        "line_items[0][price_data][product_data][description]",
        "Securely Windows app — $3/month. Cancel anytime.",
      );
    }
    params.set("success_url", `${origin}/billing-success.html?session_id={CHECKOUT_SESSION_ID}`);
    params.set("cancel_url", `${origin}/pricing.html?billing=cancel`);
    params.set("customer_email", email);
    params.set("billing_address_collection", "auto");
    params.set("client_reference_id", email.slice(0, 200));

    const typed = typeof body.promo === "string" ? body.promo.trim() : "";
    if (typed && (typed.length > 40 || !/^[A-Za-z0-9-]+$/.test(typed))) {
      res.status(400).json({ error: "Use letters, numbers, and hyphens in the promotional code." });
      return;
    }
    // Auto-apply known 100% off code when it matches; otherwise let Stripe collect codes.
    if (typed && promoId && typed.toUpperCase() === promoCode.toUpperCase()) {
      params.set("discounts[0][promotion_code]", promoId);
    } else {
      params.set("allow_promotion_codes", "true");
    }

    const response = await fetch("https://api.stripe.com/v1/checkout/sessions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${secret}`,
        "content-type": "application/x-www-form-urlencoded",
      },
      body: params,
    });
    const payload = await response.json();
    if (!response.ok || typeof payload.url !== "string") {
      const message = payload.error?.message || "Billing could not start.";
      res.status(400).json({ error: String(message).slice(0, 180) });
      return;
    }
    res.status(200).json({ url: payload.url });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Billing could not start.";
    res.status(400).json({ error: message.slice(0, 180) });
  }
}
