/** Vercel serverless: Stripe webhook with signature verification. */
import { createHmac, timingSafeEqual } from "crypto";

export const config = { api: { bodyParser: false } };

async function readRaw(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  return Buffer.concat(chunks);
}

function verifyStripeSignature(rawBody, header, secret) {
  if (!header || !secret) return false;
  const parts = Object.fromEntries(
    header.split(",").map((p) => {
      const [k, v] = p.split("=");
      return [k.trim(), v];
    })
  );
  const timestamp = parts.t;
  const signature = parts.v1;
  if (!timestamp || !signature) return false;
  const age = Math.abs(Date.now() / 1000 - Number(timestamp));
  if (!Number.isFinite(age) || age > 300) return false;
  const signed = `${timestamp}.${rawBody.toString("utf8")}`;
  const expected = createHmac("sha256", secret).update(signed, "utf8").digest("hex");
  try {
    return timingSafeEqual(Buffer.from(expected, "hex"), Buffer.from(signature, "hex"));
  } catch {
    return false;
  }
}

export default async function handler(req, res) {
  if (req.method !== "POST") {
    res.status(405).json({ error: "Method not allowed." });
    return;
  }
  const secret = process.env.STRIPE_WEBHOOK_SECRET || "";
  const raw = await readRaw(req);
  const header = req.headers["stripe-signature"];
  if (!verifyStripeSignature(raw, header, secret)) {
    res.status(400).json({ error: "Invalid signature." });
    return;
  }
  let event;
  try {
    event = JSON.parse(raw.toString("utf8"));
  } catch {
    res.status(400).json({ error: "Invalid JSON." });
    return;
  }
  // Idempotent fulfillment belongs in your database — stub acknowledges verified events only.
  if (event.type === "checkout.session.completed" || event.type === "invoice.paid") {
    // TODO: mark entitlement for customer/session id (server-side only).
  }
  res.status(200).json({ received: true, id: event.id || null });
}
