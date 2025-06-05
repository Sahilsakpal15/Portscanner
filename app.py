#!/usr/bin/env python3
"""
Port Scanner Pro - Fixed Version
Complete working port scanner with embedded HTML
"""

import socket
import threading
import time
import json
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os

# Flask app setup
app = Flask(__name__)
CORS(app)

# Global variables for tracking scans
active_scans = {}

def scan_port(ip, port):
    """
    Port scanning function that returns a dictionary
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((ip, port))
        sock.close()
        
        if result == 0:
            return {
                'port': port,
                'status': 'open',
                'message': f'Port {port} is open'
            }
        else:
            return {
                'port': port,
                'status': 'closed', 
                'message': f'Port {port} is closed'
            }
    except socket.error as err:
        return {
            'port': port,
            'status': 'error',
            'message': f"Couldn't connect to {ip}:{port} - {err}"
        }

# HTML Template (embedded to avoid file issues)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Port Scanner Pro</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
        }

        .header h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 600;
        }

        input[type="text"], input[type="number"] {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            background: #f8f9fa;
        }

        input:focus {
            outline: none;
            border-color: #667eea;
            background: white;
        }

        .port-range {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }

        .scan-button {
            width: 100%;
            padding: 18px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .scan-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }

        .scan-button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }

        .loading {
            display: none;
            margin-top: 20px;
            text-align: center;
            color: #667eea;
            font-weight: 600;
        }

        .results {
            margin-top: 30px;
            display: none;
        }

        .results h3 {
            color: #333;
            margin-bottom: 15px;
        }

        .results-container {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #e0e0e0;
        }

        .port-result {
            padding: 10px 15px;
            margin-bottom: 8px;
            border-radius: 8px;
            display: flex;
            align-items: center;
        }

        .port-result.open {
            background: #d4edda;
            border-left: 4px solid #28a745;
            color: #155724;
        }

        .port-result.closed {
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            color: #721c24;
        }

        .port-result.error {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            color: #856404;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 20px;
            display: none;
        }

        .stat-card {
            background: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }

        .stat-number {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .stat-number.open { color: #28a745; }
        .stat-number.closed { color: #dc3545; }
        .stat-number.total { color: #667eea; }

        .stat-label {
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Port Scanner Pro</h1>
            <p>Advanced network port scanning tool</p>
        </div>

        <div class="form-section">
            <form id="scanForm">
                <div class="form-group">
                    <label for="ipAddress">Target IP Address</label>
                    <input type="text" id="ipAddress" placeholder="127.0.0.1" value="127.0.0.1" required>
                </div>

                <div class="form-group">
                    <label>Port Range</label>
                    <div class="port-range">
                        <input type="number" id="startPort" placeholder="Start Port" min="1" max="65535" value="20">
                        <input type="number" id="endPort" placeholder="End Port" min="1" max="65535" value="100">
                    </div>
                </div>

                <button type="submit" class="scan-button" id="scanBtn">
                    🚀 Start Port Scan
                </button>
            </form>
        </div>

        <div class="loading" id="loading">
            ⏳ Scanning ports... Please wait
        </div>

        <div class="stats" id="stats">
            <div class="stat-card">
                <div class="stat-number open" id="openCount">0</div>
                <div class="stat-label">Open Ports</div>
            </div>
            <div class="stat-card">
                <div class="stat-number closed" id="closedCount">0</div>
                <div class="stat-label">Closed Ports</div>
            </div>
            <div class="stat-card">
                <div class="stat-number total" id="totalCount">0</div>
                <div class="stat-label">Total Scanned</div>
            </div>
        </div>

        <div class="results" id="results">
            <h3>Scan Results</h3>
            <div class="results-container" id="resultsContainer">
            </div>
        </div>
    </div>

    <script>
        let scanResults = { open: 0, closed: 0, errors: 0, total: 0 };
        let currentScanId = null;

        document.getElementById('scanForm').addEventListener('submit', function(e) {
            e.preventDefault();
            startScan();
        });

        function startScan() {
            const ip = document.getElementById('ipAddress').value.trim();
            const startPort = parseInt(document.getElementById('startPort').value) || 1;
            const endPort = parseInt(document.getElementById('endPort').value) || 1024;

            if (!ip) {
                alert('Please enter a valid IP address');
                return;
            }

            if (startPort > endPort) {
                alert('Start port must be less than or equal to end port');
                return;
            }

            resetScan();
            showLoading(true);
            
            // Call the backend API
            fetch('/api/scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ip: ip,
                    start_port: startPort,
                    end_port: endPort
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Error: ' + data.error);
                    showLoading(false);
                    return;
                }
                
                currentScanId = data.scan_id;
                console.log('Scan started:', data);
                
                // Start polling for progress
                pollScanProgress();
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to start scan: ' + error.message);
                showLoading(false);
            });
        }

        function pollScanProgress() {
            if (!currentScanId) return;

            fetch(`/api/scan/${currentScanId}/progress`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('Progress error:', data.error);
                        showLoading(false);
                        return;
                    }

                    // Update results in real-time
                    updateResults(data.results);
                    updateStats(data.stats);

                    if (data.completed) {
                        showLoading(false);
                        console.log('Scan completed');
                    } else {
                        // Continue polling
                        setTimeout(pollScanProgress, 500);
                    }
                })
                .catch(error => {
                    console.error('Polling error:', error);
                    showLoading(false);
                });
        }

        function updateResults(results) {
            const container = document.getElementById('resultsContainer');
            
            // Clear and rebuild (simple approach)
            container.innerHTML = '';
            
            results.forEach(result => {
                const div = document.createElement('div');
                div.className = `port-result ${result.status}`;
                
                const icon = result.status === 'open' ? '✅' : 
                           result.status === 'closed' ? '❌' : '⚠️';
                
                div.innerHTML = `<span style="margin-right: 10px;">${icon}</span>${result.message}`;
                container.appendChild(div);
            });

            // Show results section
            document.getElementById('results').style.display = 'block';
            document.getElementById('stats').style.display = 'grid';
        }

        function updateStats(stats) {
            document.getElementById('openCount').textContent = stats.open || 0;
            document.getElementById('closedCount').textContent = stats.closed || 0;
            document.getElementById('totalCount').textContent = stats.total_scanned || 0;
        }

        function resetScan() {
            scanResults = { open: 0, closed: 0, errors: 0, total: 0 };
            currentScanId = null;
            document.getElementById('resultsContainer').innerHTML = '';
            document.getElementById('results').style.display = 'none';
            document.getElementById('stats').style.display = 'none';
            updateStats({ open: 0, closed: 0, total_scanned: 0 });
        }

        function showLoading(show) {
            document.getElementById('loading').style.display = show ? 'block' : 'none';
            document.getElementById('scanBtn').disabled = show;
            document.getElementById('scanBtn').textContent = show ? '⏳ Scanning...' : '🚀 Start Port Scan';
        }
    </script>
</body>
</html>
'''

# Routes
@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/scan', methods=['POST'])
def start_scan():
    """Start a new port scan"""
    try:
        data = request.json
        ip = data.get('ip')
        start_port = int(data.get('start_port', 1))
        end_port = int(data.get('end_port', 1024))
        
        # Validate input
        if not ip:
            return jsonify({'error': 'IP address is required'}), 400
        
        if start_port > end_port:
            return jsonify({'error': 'Start port must be <= end port'}), 400
        
        if start_port < 1 or end_port > 65535:
            return jsonify({'error': 'Port range must be 1-65535'}), 400
        
        # Generate scan ID
        scan_id = f"{ip}_{start_port}_{end_port}_{int(time.time())}"
        
        # Initialize scan tracking
        active_scans[scan_id] = {
            'ip': ip,
            'start_port': start_port,
            'end_port': end_port,
            'results': [],
            'progress': 0,
            'total': end_port - start_port + 1,
            'completed': False,
            'started_at': time.time()
        }
        
        # Start scan in background thread
        def run_scan():
            for port in range(start_port, end_port + 1):
                if scan_id not in active_scans:
                    break  # Scan was cancelled
                    
                result = scan_port(ip, port)
                active_scans[scan_id]['results'].append(result)
                active_scans[scan_id]['progress'] = port - start_port + 1
                
                # Small delay to prevent overwhelming
                time.sleep(0.05)
            
            # Mark as complete
            if scan_id in active_scans:
                active_scans[scan_id]['completed'] = True
        
        thread = threading.Thread(target=run_scan)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'scan_id': scan_id,
            'message': f'Started scanning {ip} from port {start_port} to {end_port}',
            'status': 'started'
        })
        
    except Exception as e:
        print(f"Error in start_scan: {e}")  # Debug print
        return jsonify({'error': str(e)}), 500

@app.route('/api/scan/<scan_id>/progress', methods=['GET'])
def get_scan_progress(scan_id):
    """Get progress of a running scan"""
    if scan_id not in active_scans:
        return jsonify({'error': 'Scan not found'}), 404
    
    scan_data = active_scans[scan_id]
    
    # Count results by status
    open_ports = len([r for r in scan_data['results'] if r['status'] == 'open'])
    closed_ports = len([r for r in scan_data['results'] if r['status'] == 'closed'])
    error_ports = len([r for r in scan_data['results'] if r['status'] == 'error'])
    
    return jsonify({
        'scan_id': scan_id,
        'ip': scan_data['ip'],
        'progress': scan_data['progress'],
        'total': scan_data['total'],
        'completed': scan_data['completed'],
        'results': scan_data['results'],
        'stats': {
            'open': open_ports,
            'closed': closed_ports,
            'errors': error_ports,
            'total_scanned': len(scan_data['results'])
        }
    })

# Debug route to test if server is working
@app.route('/test')
def test():
    """Test route to verify server is working"""
    return jsonify({
        'status': 'working',
        'message': 'Port Scanner Pro is running!',
        'time': time.time()
    })

if __name__ == "__main__":
    print("🚀 Starting Port Scanner Pro...")
    print("📡 Open your browser and go to: http://localhost:5000")
    print("🔧 Test API at: http://localhost:5000/test")
    print("⏹️  Press Ctrl+C to stop")
    
    # Run with debug mode for better error messages
    app.run(debug=True, host='0.0.0.0', port=5000)