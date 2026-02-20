from http.server import BaseHTTPRequestHandler
import os
import json
import stripe

# env needed
# STRIPE_WEBHOOK_SECRET
# STRIPE_SECRET_KEY optional if you later call Stripe API

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            payload = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            sig_header = self.headers.get("Stripe-Signature", "")

            if not WEBHOOK_SECRET:
                raise ValueError("Missing STRIPE_WEBHOOK_SECRET")

            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=sig_header,
                secret=WEBHOOK_SECRET,
            )

            if event["type"] == "checkout.session.completed":
                session = event["data"]["object"]
                # handle success here
                # example
                print("Checkout completed for", session.get("id"))

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"received": true}')
        except stripe.error.SignatureVerificationError as e:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Signature verification failed", "detail": str(e)}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_GET(self):
        self.send_response(405)
        self.send_header("Allow", "POST")
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"error":"Use POST"}')

