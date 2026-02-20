from http.server import BaseHTTPRequestHandler
import os, json, stripe

stripe.api_version = "2022-11-15"
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            payload = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            sig = self.headers.get("Stripe-Signature", "")
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=sig,
                secret=WEBHOOK_SECRET
            )
            # handle a common event
            if event["type"] == "checkout.session.completed":
                pass  # add your logic here

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"received": True}).encode())
        except stripe.error.SignatureVerificationError as e:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "invalid signature"}).encode())
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
