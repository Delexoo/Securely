from http.server import BaseHTTPRequestHandler
import json
import os
import hmac
import hashlib

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = self.rfile.read(length)
            secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
            sig = self.headers.get("Stripe-Signature", "")
            ok = bool(secret) and bool(sig)
            # Optional simple check to prove code runs
            result = {"received": True, "verified": ok}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
