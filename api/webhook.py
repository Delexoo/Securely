from http.server import BaseHTTPRequestHandler
import json
import os
import stripe

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(405)
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            payload = self.rfile.read(length)
            sig = self.headers.get("Stripe-Signature", "")
            if WEBHOOK_SECRET:
                event = stripe.Webhook.construct_event(
                    payload=payload,
                    sig_header=sig,
                    secret=WEBHOOK_SECRET
                )
            else:
                event = json.loads(payload or b'{}')
            t = event.get("type", "unknown") if isinstance(event, dict) else getattr(event, "type", "unknown")
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"received": True, "type": t}).encode())
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-type','application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
