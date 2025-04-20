import requests
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from joblib import load
import numpy as np
import time
import threading
import logging
from datetime import datetime

# Initialize Flask
app = Flask(__name__)
socketio = SocketIO(app)

# Configuration
GNS3_SERVER = "http://localhost:3080"
ACTIVE_PROJECT = None
current_devices = []

# Load AI Model
try:
    model_data = load('model/network_ai.joblib')
    print("AI model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {str(e)}")
    model_data = None

# Alert System
class AlertSystem:
    def __init__(self):
        self.active_alerts = []
    
    def check_alerts(self, stats):
        alerts = []
        
        # High CPU
        if stats['cpu'] > 90:
            alerts.append({
                'type': 'high_cpu',
                'message': f'CPU usage critical ({stats["cpu"]:.1f}%)',
                'severity': 'critical'
            })
        
        # High Latency
        if stats['latency'] > 100:
            alerts.append({
                'type': 'high_latency',
                'message': f'High latency detected ({stats["latency"]:.1f}ms)',
                'severity': 'warning'
            })
        
        # Device Down
        for device in stats.get('devices', []):
            if device['status'] != 'started':
                alerts.append({
                    'type': 'device_down',
                    'message': f'Device {device["name"]} is offline',
                    'severity': 'critical',
                    'device': device['name']
                })
        
        return alerts
    
    def remediate(self, alert_type, device_name=None):
        if alert_type == 'high_cpu':
            return self._balance_load()
        elif alert_type == 'high_latency':
            return self._reroute_traffic()
        elif alert_type == 'device_down':
            return self._restart_device(device_name)
        return {"status": "no_action_available"}
    
    def _balance_load(self):
        print("Executing CPU load balancing...")
        return {"action": "load_balancing", "status": "initiated"}
    
    def _reroute_traffic(self):
        print("Rerouting network traffic...")
        return {"action": "traffic_reroute", "status": "initiated"}
    
    def _restart_device(self, device_name):
        print(f"Attempting to restart {device_name}...")
        return {"action": "device_restart", "device": device_name, "status": "attempted"}

alert_system = AlertSystem()

# GNS3 Project Management
@app.route('/get_projects', methods=['GET'])
def get_projects():
    try:
        response = requests.get(f"{GNS3_SERVER}/v2/projects")
        projects = [{"name": p["name"], "id": p["project_id"]} for p in response.json()]
        return jsonify({"success": True, "projects": projects})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/set_project', methods=['POST'])
def set_project():
    global ACTIVE_PROJECT, current_devices
    ACTIVE_PROJECT = request.json.get('project_id')
    current_devices = []
    return jsonify({"success": True})

@app.route('/remediate', methods=['POST'])
def handle_remediate():
    data = request.json
    result = alert_system.remediate(data['alert_type'], data.get('device'))
    return jsonify({"success": True, "result": result})

# Monitoring Thread
def background_monitor():
    global current_devices
    
    while True:
        if not ACTIVE_PROJECT:
            time.sleep(3)
            continue
            
        try:
            # Get project nodes
            response = requests.get(f"{GNS3_SERVER}/v2/projects/{ACTIVE_PROJECT}/nodes")
            nodes = response.json()
            current_devices = [{"name": n["name"], "status": n["status"]} for n in nodes]
            
            # Generate simulated metrics
            stats = {
                'cpu': np.random.uniform(0, 100),
                'memory': np.random.uniform(0, 100),
                'latency': np.random.uniform(1, 200),
                'packet_loss': np.random.uniform(0, 10),
                'errors': np.random.randint(0, 20),
                'devices': current_devices,
                'timestamp': datetime.now().isoformat()
            }
            
            # AI Prediction
            if model_data:
                try:
                    scaled = model_data['scaler'].transform([[
                        stats['cpu'],
                        stats['memory'],
                        500,  # Placeholder bandwidth
                        stats['latency'],
                        stats['packet_loss'],
                        stats['errors']
                    ]])
                    pred = model_data['model'].predict(scaled)
                    stats['status'] = model_data['classes'][np.argmax(pred)]
                except Exception as e:
                    print(f"Prediction error: {str(e)}")
                    stats['status'] = 'error'
            
            # Check alerts
            stats['alerts'] = alert_system.check_alerts(stats)
            
            socketio.emit('update', stats)
            
        except Exception as e:
            print(f"Monitoring error: {str(e)}")
        
        time.sleep(3)

# Routes
@app.route('/')
def dashboard():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    thread = threading.Thread(target=background_monitor)
    thread.daemon = True
    thread.start()

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000, host='127.0.0.1')