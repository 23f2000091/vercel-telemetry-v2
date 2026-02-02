import json
import os
import numpy as np
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load telemetry data at startup
data_path = os.path.join(os.path.dirname(__file__), '../q-vercel-latency.json')
with open(data_path) as f:
    telemetry_data = json.load(f)

@app.after_request
def add_cors_headers(response):
    """Add CORS headers to all responses"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Accept'
    response.headers['Access-Control-Max-Age'] = '3600'
    # Remove Vary header if it conflicts
    if 'Vary' in response.headers:
        del response.headers['Vary']
    return response

@app.route('/api/telemetry', methods=['POST', 'OPTIONS'])
def telemetry():
    """Process telemetry metrics request"""
    if request.method == 'OPTIONS':
        response = make_response('', 200)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Accept'
        return response
    
    try:
        request_data = request.get_json()
        
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

        # Wrap in regions object for client compatibility
        response_data = {"regions": metrics}
        return jsonify(response_data), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


