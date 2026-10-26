import os
import sys
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from typing import Dict, Any

# Ensure project root is accessible
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.config import RehabConfig
from viewer.parser import parse_session_csv


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Digital Goniometer - Rehabilitation Session Viewer</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --border: #334155;
      --primary: #38bdf8;
      --accent: #22c55e;
      --warning: #ef4444;
      --text: #f8fafc;
      --muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      padding: 24px;
      min-height: 100vh;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--border);
    }
    .title h1 {
      font-size: 1.6rem;
      font-weight: 700;
      color: var(--primary);
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .title p { color: var(--muted); font-size: 0.9rem; margin-top: 4px; }
    .selector {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    select {
      background: var(--card-bg);
      color: var(--text);
      border: 1px solid var(--border);
      padding: 10px 16px;
      border-radius: 8px;
      font-size: 0.95rem;
      cursor: pointer;
    }
    select:focus { outline: none; border-color: var(--primary); }
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .kpi-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      padding: 16px 20px;
      border-radius: 12px;
    }
    .kpi-label { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); margin-bottom: 6px; }
    .kpi-value { font-size: 1.8rem; font-weight: 700; color: var(--text); }
    .kpi-badge { font-size: 0.8rem; color: var(--muted); margin-top: 4px; }
    .chart-container {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 24px;
    }
    .chart-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }
    .chart-title { font-size: 1.1rem; font-weight: 600; color: var(--primary); }
    .canvas-box { position: relative; height: 360px; width: 100%; }
    .empty-state {
      text-align: center;
      padding: 60px;
      color: var(--muted);
      background: var(--card-bg);
      border-radius: 12px;
      border: 1px dashed var(--border);
    }
  </style>
</head>
<body>

  <div class="header">
    <div class="title">
      <h1>🦾 Digital Goniometer - Rehabilitation Session Viewer</h1>
      <p>Interactive kinematic dashboard & Range of Motion (ROM) clinical analytics</p>
    </div>
    <div class="selector">
      <label for="session-select" style="color: var(--muted); font-size: 0.9rem;">Session:</label>
      <select id="session-select" onchange="loadSession(this.value)">
        <option value="">Loading sessions...</option>
      </select>
    </div>
  </div>

  <div id="dashboard-content">
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Active Joint</div>
        <div class="kpi-value" id="kpi-joint">-</div>
        <div class="kpi-badge" id="kpi-samples">0 samples</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Range of Motion (ROM)</div>
        <div class="kpi-value" style="color: var(--primary);" id="kpi-rom">-</div>
        <div class="kpi-badge" id="kpi-minmax">Min: -° | Max: -°</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Session Duration</div>
        <div class="kpi-value" id="kpi-duration">-</div>
        <div class="kpi-badge">Recorded active tracking</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Cheat / Deviation Alert</div>
        <div class="kpi-value" style="color: var(--warning);" id="kpi-cheating">-</div>
        <div class="kpi-badge" id="kpi-cheating-frames">0 frames with wrist rotation</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Isometry Status</div>
        <div class="kpi-value" style="color: var(--accent);" id="kpi-isometry">-</div>
        <div class="kpi-badge">Hold >= 3.0s achieved</div>
      </div>
    </div>

    <div class="chart-container">
      <div class="chart-header">
        <div class="chart-title">📈 Joint Flexion Trajectory: Raw vs 1€ Filtered Angle</div>
      </div>
      <div class="canvas-box">
        <canvas id="romChart"></canvas>
      </div>
    </div>

    <div class="chart-container">
      <div class="chart-header">
        <div class="chart-title">🚨 Wrist Posture Compensation (Normal Vector Angular Deviation)</div>
      </div>
      <div class="canvas-box" style="height: 240px;">
        <canvas id="deviationChart"></canvas>
      </div>
    </div>
  </div>

  <div id="empty-state" class="empty-state" style="display: none;">
    <h2>No recorded data found in this session</h2>
    <p>Please perform an exercise session with the goniometer to generate CSV metrics.</p>
  </div>

  <script>
    let romChart = null;
    let deviationChart = null;

    async function init() {
      try {
        const res = await fetch('/api/sessions');
        const sessions = await res.json();
        const select = document.getElementById('session-select');
        select.innerHTML = '';
        if (sessions.length === 0) {
          select.innerHTML = '<option value="">No sessions found in exports/</option>';
          document.getElementById('dashboard-content').style.display = 'none';
          document.getElementById('empty-state').style.display = 'block';
          return;
        }
        sessions.forEach(s => {
          const opt = document.createElement('option');
          opt.value = s;
          opt.textContent = s;
          select.appendChild(opt);
        });
        loadSession(sessions[0]);
      } catch (err) {
        console.error("Error fetching sessions:", err);
      }
    }

    async function loadSession(filename) {
      if (!filename) return;
      try {
        const res = await fetch('/api/session?name=' + encodeURIComponent(filename));
        const data = await res.json();
        renderDashboard(data);
      } catch (err) {
        console.error("Error loading session:", err);
      }
    }

    function renderDashboard(data) {
      const joints = Object.keys(data.joints);
      if (joints.length === 0 || data.total_records === 0) {
        document.getElementById('dashboard-content').style.display = 'none';
        document.getElementById('empty-state').style.display = 'block';
        return;
      }

      document.getElementById('dashboard-content').style.display = 'block';
      document.getElementById('empty-state').style.display = 'none';

      const firstJointName = joints[0];
      const jointData = data.joints[firstJointName];

      // Update KPIs
      document.getElementById('kpi-joint').textContent = firstJointName;
      document.getElementById('kpi-samples').textContent = `${jointData.sample_count} samples recorded`;
      document.getElementById('kpi-rom').textContent = `${jointData.rom_deg}°`;
      document.getElementById('kpi-minmax').textContent = `Min: ${jointData.min_angle_deg}° | Max: ${jointData.max_angle_deg}°`;
      document.getElementById('kpi-duration').textContent = `${data.duration_s}s`;
      document.getElementById('kpi-cheating').textContent = `${data.global_metrics.cheating_percentage}%`;
      document.getElementById('kpi-cheating-frames').textContent = `${data.global_metrics.cheating_frames} frames flagged`;
      document.getElementById('kpi-isometry').textContent = data.global_metrics.isometry_frames > 0 ? "ACHIEVED" : "NONE";

      // Render ROM Chart
      const series = jointData.series;
      const labels = series.elapsed.map(e => e.toFixed(1) + 's');

      if (romChart) romChart.destroy();
      const ctxRom = document.getElementById('romChart').getContext('2d');
      romChart = new Chart(ctxRom, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            {
              label: 'Raw Angle (°)',
              data: series.raw_angles,
              borderColor: 'rgba(148, 163, 184, 0.4)',
              borderWidth: 1.5,
              pointRadius: 0,
              fill: false
            },
            {
              label: '1€ Smoothed Angle (°)',
              data: series.smoothed_angles,
              borderColor: '#38bdf8',
              backgroundColor: 'rgba(56, 189, 248, 0.08)',
              borderWidth: 2.5,
              pointRadius: 0,
              fill: true
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: 'index', intersect: false },
          scales: {
            x: { grid: { color: '#334155' }, ticks: { color: '#94a3b8' } },
            y: { grid: { color: '#334155' }, ticks: { color: '#94a3b8' }, title: { display: true, text: 'Angle (Degrees)', color: '#94a3b8' } }
          },
          plugins: {
            legend: { labels: { color: '#f8fafc' } }
          }
        }
      });

      // Render Deviation Chart
      if (deviationChart) deviationChart.destroy();
      const ctxDev = document.getElementById('deviationChart').getContext('2d');
      deviationChart = new Chart(ctxDev, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            {
              label: 'Palm Normal Deviation (°)',
              data: series.deviations,
              borderColor: '#ef4444',
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              borderWidth: 2,
              pointRadius: 0,
              fill: true
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: 'index', intersect: false },
          scales: {
            x: { grid: { color: '#334155' }, ticks: { color: '#94a3b8' } },
            y: {
              grid: { color: '#334155' },
              ticks: { color: '#94a3b8' },
              title: { display: true, text: 'Deviation (°)', color: '#94a3b8' },
              suggestedMax: 25
            }
          },
          plugins: {
            legend: { labels: { color: '#f8fafc' } }
          }
        }
      });
    }

    window.onload = init;
  </script>
</body>
</html>
"""

class GoniometerViewerHandler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        # Mute request access spam in terminal
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/dashboard":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode("utf-8"))

        elif path == "/api/sessions":
            export_dir = RehabConfig.EXPORT_DIR
            files = []
            if os.path.exists(export_dir):
                files = sorted(
                    [f for f in os.listdir(export_dir) if f.endswith(".csv")],
                    reverse=True
                )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(files).encode("utf-8"))

        elif path == "/api/session":
            query = urllib.parse.parse_qs(parsed.query)
            filename = query.get("name", [""])[0]
            if not filename or ".." in filename:
                self.send_error(400, "Invalid session filename")
                return

            file_path = os.path.join(RehabConfig.EXPORT_DIR, filename)
            if not os.path.exists(file_path):
                self.send_error(404, "Session file not found")
                return

            data = parse_session_csv(file_path)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))

        else:
            self.send_error(404, "Not Found")


def run_viewer(port: int = 8501, open_browser: bool = True):
    server = HTTPServer(("127.0.0.1", port), GoniometerViewerHandler)
    url = f"http://127.0.0.1:{port}"
    print(f"\n=======================================================")
    print(f"🦾 Digital Goniometer - Rehabilitation Session Viewer")
    print(f"Server listening at: {url}")
    print(f"Press Ctrl+C to terminate the server.")
    print(f"=======================================================\n")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Viewer server stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8501
    run_viewer(port=port)
