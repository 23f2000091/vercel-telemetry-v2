import json
import os
import numpy as np
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Load telemetry data at startup
data_path = os.path.join(os.path.dirname(__file__), '../q-vercel-latency.json')
with open(data_path) as f:
    telemetry_data = json.load(f)

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            request_data = json.loads(body)

            regions = request_data.get('regions', [])
            threshold_ms = request_data.get('threshold_ms', 180)

            metrics = {}
            for region in regions:
                region_data = [r for r in telemetry_data if r['region'] == region]
                
                if not region_data:
                    continue

                latencies = [r['latency_ms'] for r in region_data]
                uptimes = [r['uptime_pct'] for r in region_data]
                breaches = len([r for r in region_data if r['latency_ms'] > threshold_ms])

                metrics[region] = {
                    "avg_latency": round(float(np.mean(latencies)), 2),
                    "p95_latency": round(float(np.percentile(latencies, 95)), 2),
                    "avg_uptime": round(float(np.mean(uptimes)), 2),
                    "breaches": breaches
                }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(metrics).encode())

        except Exception as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def log_message(self, format, *args):
        pass

