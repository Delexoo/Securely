/** Vercel serverless: create Stripe Checkout for Securely Pro. */
export default async function handler(req, res) {
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
    if (email && (email.length > 200 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))) {
      res.status(400).json({ error: "Enter a valid email address." });
      return;
    }
    const host = req.headers["x-forwarded-host"] || req.headers.host;
    const proto = req.headers["x-forwarded-proto"] || "https";
    const origin = `${proto}://${host}`;
    const params = new URLSearchParams();
    params.set("mode", "subscription");
    params.set("line_items[0][quantity]", "1");
    params.set("line_items[0][price_data][currency]", "usd");
    params.set("line_items[0][price_data][unit_amount]", "2000");
    params.set("line_items[0][price_data][recurring][interval]", "month");
    params.set("line_items[0][price_data][product_data][name]", "Securely Pro");
    params.set("line_items[0][price_data][product_data][description]", "Monthly Securely Pro subscription.");
    params.set("success_url", `${origin}/billing-success.html?session_id={CHECKOUT_SESSION_ID}`);
    params.set("cancel_url", `${origin}/pricing.html?billing=cancel`);
    if (email) params.set("customer_email", email);
    params.set("allow_promotion_codes", "true");

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
