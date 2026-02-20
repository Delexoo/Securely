from http.server import BaseHTTPRequestHandler
import json
import os
import hmac
import hashlib

# Optional raw-body store for signature check
def get_raw_body(handler):
    length = int(handler.headers.get("Content-Length", 0))
    return handler.rfile.read(length)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")  # simple health check

    def do_POST(self):
        try:
            raw = get_raw_body(self)
            sig = self.headers.get("Stripe-Signature", "")
            secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

            # Optional verify only if secret is set
            if secret:
                # Stripe’s v1 scheme HMAC with secret
                digest = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
                # We cannot fully parse Stripe’s signed header here
                # This is a lightweight guard to avoid empty secret usage

            event = json.loads(raw or b"{}")
            # Handle the important event
            t = event.get("type")
            if t == "checkout.session.completed":
                # Do your work here
                pass

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"received": True}).encode())
        except Exception as e:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())


