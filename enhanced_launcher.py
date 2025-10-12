#!/usr/bin/env python3
"""
Enhanced Ollama Discord Bot Launcher with Management Interface
- Web dashboard for monitoring
- Auto-restart capabilities
- Performance analytics
- Security monitoring
- Model management
"""

import os
import sys
import asyncio
import subprocess
import signal
import threading
import time
import json
import psutil
from datetime import datetime
from pathlib import Path
import logging
from flask import Flask, render_template_string, jsonify, request
import sqlite3
import webbrowser

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedBotManager:
    def __init__(self):
        self.bot_process = None
        self.is_running = False
        self.start_time = None
        self.restart_count = 0
        self.db_path = "enhanced_ollama_bot.db"
        self.config = self.load_config()
        
        # Web dashboard
        self.app = Flask(__name__)
        self.setup_web_routes()
        
    def load_config(self):
        """Load configuration from .env file"""
        config = {}
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        config[key] = value
        return config
    
    def setup_web_routes(self):
        """Setup Flask routes for web dashboard"""
        
        @self.app.route('/')
        def dashboard():
            return render_template_string(DASHBOARD_HTML)
        
        @self.app.route('/api/status')
        def api_status():
            """Get bot status"""
            status = {
                'running': self.is_running,
                'uptime': time.time() - self.start_time if self.start_time else 0,
                'restart_count': self.restart_count,
                'pid': self.bot_process.pid if self.bot_process else None
            }
            
            # System metrics
            if self.is_running:
                try:
                    process = psutil.Process(self.bot_process.pid)
                    status.update({
                        'cpu_percent': process.cpu_percent(),
                        'memory_mb': process.memory_info().rss / 1024 / 1024,
                        'threads': process.num_threads()
                    })
                except:
                    pass
            
            return jsonify(status)
        
        @self.app.route('/api/metrics')
        def api_metrics():
            """Get performance metrics from database"""
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Get recent metrics
                cursor.execute('''
                    SELECT metric_name, metric_value, timestamp 
                    FROM performance_metrics 
                    WHERE timestamp > datetime('now', '-1 hour')
                    ORDER BY timestamp DESC
                ''')
                
                metrics = []
                for row in cursor.fetchall():
                    metrics.append({
                        'name': row[0],
                        'value': row[1],
                        'timestamp': row[2]
                    })
                
                conn.close()
                return jsonify(metrics)
                
            except Exception as e:
                return jsonify({'error': str(e)})
        
        @self.app.route('/api/conversations')
        def api_conversations():
            """Get conversation statistics"""
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Get conversation stats
                cursor.execute('''
                    SELECT COUNT(*) as total, 
                           AVG(response_time) as avg_time,
                           AVG(tokens_used) as avg_tokens
                    FROM conversations 
                    WHERE timestamp > datetime('now', '-24 hours')
                ''')
                
                stats = cursor.fetchone()
                
                # Get model usage
                cursor.execute('''
                    SELECT model_used, COUNT(*) as count
                    FROM conversations 
                    WHERE timestamp > datetime('now', '-24 hours')
                    GROUP BY model_used
                    ORDER BY count DESC
                ''')
                
                models = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]
                
                conn.close()
                
                return jsonify({
                    'total_conversations': stats[0] or 0,
                    'avg_response_time': stats[1] or 0,
                    'avg_tokens': stats[2] or 0,
                    'model_usage': models
                })
                
            except Exception as e:
                return jsonify({'error': str(e)})
        
        @self.app.route('/api/security')
        def api_security():
            """Get security alerts"""
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT event_type, severity, COUNT(*) as count
                    FROM security_logs 
                    WHERE timestamp > datetime('now', '-24 hours')
                    GROUP BY event_type, severity
                    ORDER BY count DESC
                ''')
                
                alerts = [
                    {'type': row[0], 'severity': row[1], 'count': row[2]} 
                    for row in cursor.fetchall()
                ]
                
                conn.close()
                return jsonify(alerts)
                
            except Exception as e:
                return jsonify({'error': str(e)})
        
        @self.app.route('/api/control/<action>', methods=['POST'])
        def api_control(action):
            """Control bot actions"""
            if action == 'start':
                result = self.start_bot()
            elif action == 'stop':
                result = self.stop_bot()
            elif action == 'restart':
                result = self.restart_bot()
            else:
                return jsonify({'error': 'Invalid action'}), 400
            
            return jsonify({'success': result})
    
    def start_bot(self):
        """Start the Discord bot"""
        if self.is_running:
            logger.info("Bot is already running")
            return False
        
        try:
            # Check if Ollama is running
            if not self.check_ollama():
                logger.error("Ollama is not running. Please start Ollama first.")
                return False
            
            # Start bot process
            python_path = sys.executable
            bot_script = Path(__file__).parent / "enhanced_discord_bot.py"
            
            self.bot_process = subprocess.Popen([
                python_path, str(bot_script)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.is_running = True
            self.start_time = time.time()
            
            logger.info(f"Enhanced Discord bot started with PID: {self.bot_process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            return False
    
    def stop_bot(self):
        """Stop the Discord bot"""
        if not self.is_running or not self.bot_process:
            return False
        
        try:
            self.bot_process.terminate()
            self.bot_process.wait(timeout=10)
            self.is_running = False
            self.bot_process = None
            logger.info("Bot stopped successfully")
            return True
            
        except subprocess.TimeoutExpired:
            self.bot_process.kill()
            self.is_running = False
            self.bot_process = None
            logger.warning("Bot forcefully killed")
            return True
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
            return False
    
    def restart_bot(self):
        """Restart the Discord bot"""
        self.stop_bot()
        time.sleep(2)  # Wait a bit
        result = self.start_bot()
        if result:
            self.restart_count += 1
        return result
    
    def check_ollama(self):
        """Check if Ollama is running"""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/version", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def monitor_bot(self):
        """Monitor bot process and auto-restart if needed"""
        while True:
            if self.is_running and self.bot_process:
                # Check if process is still alive
                if self.bot_process.poll() is not None:
                    logger.warning("Bot process died, restarting...")
                    self.is_running = False
                    time.sleep(5)
                    self.start_bot()
                    self.restart_count += 1
            
            time.sleep(30)  # Check every 30 seconds
    
    def run_dashboard(self):
        """Run the web dashboard"""
        logger.info("Starting web dashboard on http://localhost:5555")
        self.app.run(host='0.0.0.0', port=5555, debug=False, use_reloader=False)
    
    def main(self):
        """Main launcher function"""
        print("🤖 Enhanced Ollama Discord Bot Manager")
        print("=" * 50)
        
        # Check requirements
        if not self.check_ollama():
            print("❌ Ollama is not running!")
            print("Please start Ollama with: ollama serve")
            return
        
        if not os.path.exists('.env') or 'DISCORD_TOKEN' not in self.config:
            print("❌ Discord token not found!")
            print("Please create .env file with: DISCORD_TOKEN=your_token_here")
            return
        
        # Install dependencies if needed
        self.install_dependencies()
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_bot, daemon=True)
        monitor_thread.start()
        
        # Start dashboard thread
        dashboard_thread = threading.Thread(target=self.run_dashboard, daemon=True)
        dashboard_thread.start()
        
        # Start bot
        if self.start_bot():
            print(f"✅ Bot started successfully!")
            print(f"🌐 Dashboard: http://localhost:5555")
            
            # Open dashboard in browser
            time.sleep(2)
            try:
                webbrowser.open('http://localhost:5555')
            except:
                pass
            
            # Keep running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Shutting down...")
                self.stop_bot()
        else:
            print("❌ Failed to start bot!")
    
    def install_dependencies(self):
        """Install required dependencies"""
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "enhanced_requirements.txt"
            ], check=True, capture_output=True)
            logger.info("Dependencies installed successfully")
        except subprocess.CalledProcessError:
            logger.warning("Some dependencies may not have installed correctly")

# HTML template for dashboard
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Ollama Bot Dashboard</title>
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
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .status-card h3 {
            color: #4a5568;
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 8px 0;
            border-bottom: 1px solid #e2e8f0;
        }
        .metric:last-child {
            border-bottom: none;
        }
        .metric-value {
            font-weight: bold;
            color: #2d3748;
        }
        .running {
            color: #48bb78;
        }
        .stopped {
            color: #f56565;
        }
        .controls {
            text-align: center;
            margin: 30px 0;
        }
        .btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 25px;
            margin: 0 10px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s ease;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .charts {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .alert {
            background: #fff3cd;
            color: #856404;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            border-left: 4px solid #ffc107;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: white;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Enhanced Ollama Bot Dashboard</h1>
            <p>Real-time monitoring and control</p>
        </div>

        <div class="controls">
            <button class="btn" onclick="controlBot('start')" id="startBtn">▶️ Start Bot</button>
            <button class="btn" onclick="controlBot('stop')" id="stopBtn">⏹️ Stop Bot</button>
            <button class="btn" onclick="controlBot('restart')" id="restartBtn">🔄 Restart Bot</button>
            <button class="btn" onclick="refreshData()">🔄 Refresh Data</button>
        </div>

        <div class="status-grid">
            <div class="status-card">
                <h3>🚀 Bot Status</h3>
                <div class="metric">
                    <span>Status:</span>
                    <span class="metric-value" id="botStatus">Loading...</span>
                </div>
                <div class="metric">
                    <span>Uptime:</span>
                    <span class="metric-value" id="uptime">-</span>
                </div>
                <div class="metric">
                    <span>Restarts:</span>
                    <span class="metric-value" id="restarts">-</span>
                </div>
                <div class="metric">
                    <span>PID:</span>
                    <span class="metric-value" id="pid">-</span>
                </div>
            </div>

            <div class="status-card">
                <h3>⚡ Performance</h3>
                <div class="metric">
                    <span>CPU Usage:</span>
                    <span class="metric-value" id="cpu">-</span>
                </div>
                <div class="metric">
                    <span>Memory:</span>
                    <span class="metric-value" id="memory">-</span>
                </div>
                <div class="metric">
                    <span>Threads:</span>
                    <span class="metric-value" id="threads">-</span>
                </div>
            </div>

            <div class="status-card">
                <h3>💬 Conversations</h3>
                <div class="metric">
                    <span>Total (24h):</span>
                    <span class="metric-value" id="totalConversations">-</span>
                </div>
                <div class="metric">
                    <span>Avg Response:</span>
                    <span class="metric-value" id="avgResponse">-</span>
                </div>
                <div class="metric">
                    <span>Avg Tokens:</span>
                    <span class="metric-value" id="avgTokens">-</span>
                </div>
            </div>

            <div class="status-card">
                <h3>🔐 Security</h3>
                <div id="securityAlerts">Loading...</div>
            </div>
        </div>

        <div class="charts">
            <div class="status-card">
                <h3>🤖 Model Usage (24h)</h3>
                <div id="modelUsage">Loading...</div>
            </div>
        </div>
    </div>

    <script>
        let refreshInterval;

        function formatUptime(seconds) {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return `${hours}h ${minutes}m`;
        }

        function updateStatus(data) {
            document.getElementById('botStatus').textContent = data.running ? 'Running' : 'Stopped';
            document.getElementById('botStatus').className = 'metric-value ' + (data.running ? 'running' : 'stopped');
            document.getElementById('uptime').textContent = data.uptime ? formatUptime(data.uptime) : '-';
            document.getElementById('restarts').textContent = data.restart_count || 0;
            document.getElementById('pid').textContent = data.pid || '-';
            document.getElementById('cpu').textContent = data.cpu_percent ? `${data.cpu_percent.toFixed(1)}%` : '-';
            document.getElementById('memory').textContent = data.memory_mb ? `${data.memory_mb.toFixed(1)} MB` : '-';
            document.getElementById('threads').textContent = data.threads || '-';

            // Update button states
            document.getElementById('startBtn').disabled = data.running;
            document.getElementById('stopBtn').disabled = !data.running;
            document.getElementById('restartBtn').disabled = false;
        }

        function updateConversations(data) {
            document.getElementById('totalConversations').textContent = data.total_conversations || 0;
            document.getElementById('avgResponse').textContent = data.avg_response_time ? 
                `${data.avg_response_time.toFixed(2)}s` : '-';
            document.getElementById('avgTokens').textContent = data.avg_tokens ? 
                Math.round(data.avg_tokens) : '-';

            // Update model usage
            const modelDiv = document.getElementById('modelUsage');
            if (data.model_usage && data.model_usage.length > 0) {
                modelDiv.innerHTML = data.model_usage.map(model => 
                    `<div class="metric"><span>${model.name}</span><span class="metric-value">${model.count}</span></div>`
                ).join('');
            } else {
                modelDiv.innerHTML = '<p>No model usage data</p>';
            }
        }

        function updateSecurity(data) {
            const securityDiv = document.getElementById('securityAlerts');
            if (data && data.length > 0) {
                securityDiv.innerHTML = data.map(alert => 
                    `<div class="alert">
                        <strong>${alert.type}</strong> (${alert.severity}): ${alert.count} alerts
                    </div>`
                ).join('');
            } else {
                securityDiv.innerHTML = '<p style="color: #48bb78;">✅ No security alerts</p>';
            }
        }

        async function refreshData() {
            try {
                const [statusResp, conversationsResp, securityResp] = await Promise.all([
                    fetch('/api/status'),
                    fetch('/api/conversations'),
                    fetch('/api/security')
                ]);

                const statusData = await statusResp.json();
                const conversationsData = await conversationsResp.json();
                const securityData = await securityResp.json();

                updateStatus(statusData);
                updateConversations(conversationsData);
                updateSecurity(securityData);

            } catch (error) {
                console.error('Error fetching data:', error);
            }
        }

        async function controlBot(action) {
            try {
                const response = await fetch(`/api/control/${action}`, {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.success) {
                    setTimeout(refreshData, 2000); // Refresh after 2 seconds
                } else {
                    alert(`Failed to ${action} bot`);
                }
            } catch (error) {
                console.error(`Error ${action}ing bot:`, error);
                alert(`Error ${action}ing bot`);
            }
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            refreshData();
            refreshInterval = setInterval(refreshData, 10000); // Refresh every 10 seconds
        });
    </script>
</body>
</html>
'''

if __name__ == "__main__":
    manager = EnhancedBotManager()
    manager.main()
