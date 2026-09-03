import os
import sys
import socket
import platform
import subprocess
import threading
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

# System Network Functions
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def ping_ip(ip):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    cmd = ["ping", param, "1", "-w", "500", ip]
    try:
        output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=1)
        return output.returncode == 0
    except Exception:
        return False

def get_mac_address(ip):
    try:
        if platform.system().lower() == "windows":
            cmd = ["arp", "-a", ip]
            output = subprocess.check_output(cmd, text=True)
            for line in output.splitlines():
                if ip in line:
                    parts = line.split()
                    for part in parts:
                        if "-" in part and len(part) == 17:
                            return part.upper()
        else:
            cmd = ["arp", "-n", ip]
            output = subprocess.check_output(cmd, text=True)
            for line in output.splitlines():
                if ip in line:
                    parts = line.split()
                    return parts[2].upper()
    except Exception:
        pass
    return "N/A"

def ip_to_tuple(ip):
    try:
        return tuple(map(int, ip.split('.')))
    except Exception:
        return (0, 0, 0, 0)

# Embedded Single-File HTML/CSS/JS Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>S.B. INFOTECH - CCTV Network Diagnostic Tool</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: #121212; color: #e0e0e0; padding: 15px; }
        .header { background: linear-gradient(135deg, #1e3c72, #2a5298); padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
        .header h1 { font-size: 22px; color: #ffffff; letter-spacing: 1px; }
        .header p { font-size: 13px; color: #00d2ff; font-weight: bold; margin-top: 4px; }
        .ad-banner { background-color: #1e1e1e; border: 1px solid #333; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 15px; font-size: 12px; color: #aaa; }
        .ad-banner span { color: #ff9800; font-weight: bold; }
        .controls { display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap; }
        input[type="text"] { flex: 1; padding: 10px; border-radius: 5px; border: 1px solid #444; background: #222; color: #fff; min-width: 180px; }
        button { padding: 10px 18px; border: none; border-radius: 5px; background-color: #008cba; color: white; cursor: pointer; font-weight: bold; transition: 0.2s; }
        button:hover { background-color: #005f73; }
        .summary { display: flex; gap: 10px; margin-bottom: 15px; }
        .card { flex: 1; background: #1e1e1e; padding: 10px; border-radius: 6px; text-align: center; border-left: 4px solid #008cba; }
        .card.active { border-color: #4caf50; }
        .card.conflict { border-color: #f44336; }
        .card h3 { font-size: 12px; color: #888; }
        .card p { font-size: 18px; font-weight: bold; margin-top: 5px; }
        table { width: 100%; border-collapse: collapse; background: #1e1e1e; border-radius: 8px; overflow: hidden; }
        th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #2c2c2c; font-size: 13px; }
        th { background-color: #252525; color: #00d2ff; }
        tr:hover { background-color: #2a2a2a; }
        .status-online { color: #4caf50; font-weight: bold; }
        .status-offline { color: #f44336; }
        .conflict-tag { background: #f44336; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; }
        .btn-web { background: #2196f3; padding: 4px 8px; font-size: 11px; text-decoration: none; color: white; border-radius: 3px; }
        select { background: #222; color: white; border: 1px solid #444; padding: 4px; border-radius: 4px; }
    </style>
</head>
<body>

    <div class="header">
        <h1>S.B. INFOTECH</h1>
        <p>CCTV & Network Diagnostic Tool | Contact: +91 9924757111</p>
    </div>

    <div class="ad-banner">
        <span>Wholesale Deals:</span> IP Cameras, NVRs, Network Switches, Fiber Accessories & IT Instruments. Best prices guaranteed for field engineers!
    </div>

    <div class="controls">
        <input type="text" id="subnetInput" placeholder="Subnet (e.g. 192.168.1)">
        <button onclick="startScan()">Start Network Scan</button>
    </div>

    <div class="summary">
        <div class="card active">
            <h3>Active Devices</h3>
            <p id="activeCount">0</p>
        </div>
        <div class="card conflict">
            <h3>IP Conflicts</h3>
            <p id="conflictCount">0</p>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>IP Address</th>
                <th>Status</th>
                <th>MAC Address</th>
                <th>Category</th>
                <th>Action</th>
            </tr>
        </thead>
        <tbody id="resultTable">
            <tr><td colspan="5" style="text-align:center; color:#666;">Enter subnet and click 'Start Network Scan'</td></tr>
        </tbody>
    </table>

    <script>
        async function fetchLocalIP() {
            let res = await fetch('/api/local-ip');
            let data = await res.json();
            document.getElementById('subnetInput').value = data.subnet;
        }
        fetchLocalIP();

        async function startScan() {
            let subnet = document.getElementById('subnetInput').value.trim();
            if(!subnet) return alert("Please enter a valid subnet!");

            let tbody = document.getElementById('resultTable');
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:#00d2ff;">Scanning network, please wait...</td></tr>';

            let res = await fetch('/api/scan', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ subnet: subnet })
            });
            let devices = await res.json();
            renderTable(devices);
        }

        function renderTable(devices) {
            let tbody = document.getElementById('resultTable');
            tbody.innerHTML = '';

            let active = 0;
            let conflicts = 0;
            let macMap = {};

            devices.forEach(d => {
                if(d.status === 'Online') {
                    active++;
                    if(d.mac !== 'N/A') {
                        macMap[d.mac] = (macMap[d.mac] || 0) + 1;
                    }
                }
            });

            devices.forEach(d => {
                let isConflict = d.mac !== 'N/A' && macMap[d.mac] > 1;
                if(isConflict) conflicts++;

                let row = `<tr>
                    <td>${d.ip} ${isConflict ? '<span class="conflict-tag">CONFLICT</span>' : ''}</td>
                    <td class="${d.status === 'Online' ? 'status-online' : 'status-offline'}">${d.status}</td>
                    <td>${d.mac}</td>
                    <td>
                        <select>
                            <option>Camera</option>
                            <option>NVR / DVR</option>
                            <option>Router / Switch</option>
                            <option>PC / Laptop</option>
                            <option>Other</option>
                        </select>
                    </td>
                    <td>
                        ${d.status === 'Online' ? `<a href="http://${d.ip}" target="_blank" class="btn-web">1-Click Web Access</a>` : '-'}
                    </td>
                </tr>`;
                tbody.innerHTML += row;
            });

            document.getElementById('activeCount').innerText = active;
            document.getElementById('conflictCount').innerText = conflicts;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/local-ip', methods=['GET'])
def api_local_ip():
    ip = get_local_ip()
    subnet = ".".join(ip.split(".")[:3])
    return jsonify({"ip": ip, "subnet": subnet})

@app.route('/api/scan', methods=['POST'])
def api_scan():
    data = request.get_json()
    subnet = data.get('subnet', '192.168.1')
    
    results = []
    
    def scan_target(ip):
        is_up = ping_ip(ip)
        if is_up:
            mac = get_mac_address(ip)
            results.append({"ip": ip, "status": "Online", "mac": mac})

    with ThreadPoolExecutor(max_workers=50) as executor:
        for i in range(1, 255):
            executor.submit(scan_target, f"{subnet}.{i}")

    # Numeric IP Sorting
    results.sort(key=lambda x: ip_to_tuple(x["ip"]))
    return jsonify(results)

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    threading.Timer(1.5, open_browser).start()
    app.run(host='0.0.0.0', port=5000, debug=False)
