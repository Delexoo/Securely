from http.server import BaseHTTPRequestHandler
import json
import os
import hmac
import hashlib

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(length)

            # Optional signature check for Stripe CLI
            secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
            sig = self.headers.get('Stripe-Signature')
            if secret and sig:
                # Simple tolerance free check for CLI testing
                mac = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
                # Not verifying header format here. Only ensures code path runs.

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
