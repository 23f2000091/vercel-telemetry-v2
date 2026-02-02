import json
import os
import numpy as np

# Load telemetry data at startup
data_path = os.path.join(os.path.dirname(__file__), '../q-vercel-latency.json')
with open(data_path) as f:
    telemetry_data = json.load(f)

def handler(request):
    """Handle POST requests for telemetry metrics"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        }
    
    try:
        # Parse JSON body
        request_data = json.loads(request.body)
        
        # Extract regions and threshold
        regions = request_data.get('regions', [])
        threshold_ms = request_data.get('threshold_ms', 180)

        # Calculate metrics per region
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

        # Return response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(metrics)
        }

    except Exception as e:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({"error": str(e)})
        }
