#!/usr/bin/env python3
"""
Simple HTTP Server for Web Scraper Dashboard
No external dependencies required - uses only Python standard library
"""

import http.server
import socketserver
import json
import urllib.request
import urllib.parse
import urllib.error
import re
import threading
import time
from datetime import datetime
import os
import html

class SimpleWebScraper:
    def __init__(self):
        self.results = []
        self.is_running = False
        self.status_messages = []
        
    def fetch_page(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read().decode('utf-8')
        except Exception as e:
            return {"error": str(e)}
    
    def extract_data(self, html_content, selectors):
        # Simple regex-based extraction (no BeautifulSoup)
        data = {}
        
        for key, selector in selectors.items():
            # Very basic CSS selector support
            if selector.startswith('.'):
                # Class selector
                class_name = selector[1:]
                pattern = f'class="[^"]*{class_name}[^"]*"[^>]*>([^<]+)'
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                data[key] = [match.strip() for match in matches if match.strip()]
            elif selector.startswith('#'):
                # ID selector
                id_name = selector[1:]
                pattern = f'id="{id_name}"[^>]*>([^<]+)'
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                data[key] = [match.strip() for match in matches if match.strip()]
            else:
                # Tag selector
                pattern = f'<{selector}[^>]*>([^<]+)</{selector}>'
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                data[key] = [match.strip() for match in matches if match.strip()]
        
        return data
    
    def scrape_urls(self, urls, selectors):
        self.is_running = True
        self.results = []
        
        for i, url in enumerate(urls):
            if not self.is_running:
                break
                
            status_msg = f"Processing URL {i+1}/{len(urls)}: {url}"
            self.status_messages.append({
                "message": status_msg,
                "timestamp": datetime.now().isoformat(),
                "type": "info"
            })
            
            html_content = self.fetch_page(url)
            if isinstance(html_content, dict):  # Error occurred
                result = {
                    "url": url,
                    "error": html_content["error"],
                    "timestamp": datetime.now().isoformat()
                }
            else:
                data = self.extract_data(html_content, selectors)
                result = {
                    "url": url,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }
            
            self.results.append(result)
            time.sleep(1)  # Rate limiting
        
        self.is_running = False
        self.status_messages.append({
            "message": "Scraping completed!",
            "timestamp": datetime.now().isoformat(),
            "type": "success"
        })
        
        return self.results
    
    def stop_scraping(self):
        self.is_running = False

# Global scraper instance
scraper = SimpleWebScraper()

class ScraperHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.serve_file('templates/index.html')
        elif self.path == '/api/status':
            self.serve_json({
                "is_running": scraper.is_running,
                "results_count": len(scraper.results),
                "status_messages": scraper.status_messages[-10:]  # Last 10 messages
            })
        elif self.path == '/api/results':
            self.serve_json(scraper.results)
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path == '/api/start':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            urls = data.get('urls', [])
            selectors = data.get('selectors', {})
            
            if not urls or not selectors:
                self.serve_json({"error": "URLs and selectors are required"}, 400)
                return
            
            # Start scraping in background thread
            thread = threading.Thread(target=scraper.scrape_urls, args=(urls, selectors))
            thread.daemon = True
            thread.start()
            
            self.serve_json({"message": "Scraping started"})
            
        elif self.path == '/api/stop':
            scraper.stop_scraping()
            self.serve_json({"message": "Scraping stopped"})
            
        elif self.path == '/api/download':
            filename = f"scraping_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(scraper.results, f, indent=2, ensure_ascii=False)
            self.serve_json({"message": f"Results saved to {filename}"})
        else:
            self.send_error(404)
    
    def serve_file(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except FileNotFoundError:
            self.send_error(404)
    
    def serve_json(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

def create_template():
    """Create the HTML template if it doesn't exist"""
    template_dir = 'templates'
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)
    
    template_file = os.path.join(template_dir, 'index.html')
    if not os.path.exists(template_file):
        html_content = '''<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Scraper - Live Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .header h1 { color: #333; display: flex; align-items: center; gap: 10px; }
        .status-indicator { display: flex; align-items: center; gap: 5px; font-size: 14px; }
        .status-dot { width: 12px; height: 12px; border-radius: 50%; }
        .status-ready { background: #6c757d; }
        .status-running { background: #28a745; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .grid { display: grid; grid-template-columns: 1fr 2fr; gap: 20px; }
        .panel { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .panel h2 { margin-bottom: 15px; color: #333; }
        textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-family: monospace; resize: vertical; }
        .buttons { display: flex; gap: 10px; margin-top: 15px; }
        button { padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; font-weight: 500; }
        button:disabled { opacity: 0.6; cursor: not-allowed; }
        .btn-primary { background: #007bff; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-success { background: #28a745; color: white; }
        .status-messages { max-height: 200px; overflow-y: auto; margin-top: 10px; }
        .status-message { padding: 8px; margin: 5px 0; border-radius: 4px; font-size: 14px; }
        .status-info { background: #d1ecf1; color: #0c5460; }
        .status-success { background: #d4edda; color: #155724; }
        .status-error { background: #f8d7da; color: #721c24; }
        .results { max-height: 400px; overflow-y: auto; }
        .result-item { border: 1px solid #ddd; border-radius: 4px; padding: 15px; margin-bottom: 10px; }
        .result-url { font-weight: bold; color: #007bff; margin-bottom: 10px; }
        .result-data { font-size: 14px; }
        .result-field { margin-bottom: 10px; }
        .result-field strong { color: #333; }
        .result-values { margin-left: 10px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🕷️ Web Scraper Dashboard</h1>
            <div class="status-indicator">
                <span class="status-dot status-ready" id="status-dot"></span>
                <span id="status-text">Ready</span>
            </div>
        </div>
        
        <div class="grid">
            <div>
                <div class="panel">
                    <h2>Configuration</h2>
                    <label style="display: block; margin-bottom: 5px; font-weight: 500;">URLs (one per line):</label>
                    <textarea id="urls" rows="4" placeholder="https://example.com&#10;https://example2.com">https://quotes.toscrape.com/
https://books.toscrape.com/</textarea>
                    
                    <label style="display: block; margin: 10px 0 5px; font-weight: 500;">CSS Selectors (JSON format):</label>
                    <textarea id="selectors" rows="6" placeholder='{"title": "h1", "links": "a"}'>{
  "titles": "h1, h2, h3",
  "quotes": "text",
  "authors": ".author",
  "links": "a"
}</textarea>
                    
                    <div class="buttons">
                        <button id="start-btn" class="btn-primary">▶️ Start</button>
                        <button id="stop-btn" class="btn-danger" disabled>⏹️ Stop</button>
                    </div>
                    
                    <button id="download-btn" class="btn-success" style="width: 100%; margin-top: 10px;">💾 Download Results</button>
                </div>
                
                <div class="panel" style="margin-top: 20px;">
                    <h2>Status</h2>
                    <div id="status-messages" class="status-messages">
                        <div class="status-message status-info">Ready to start scraping...</div>
                    </div>
                </div>
            </div>
            
            <div>
                <div class="panel">
                    <h2>Results <span id="results-count">(0)</span></h2>
                    <div id="results" class="results">
                        <div style="text-align: center; color: #666; padding: 40px;">
                            📋 No results yet. Start scraping to see results here.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let isScraping = false;
        
        const startBtn = document.getElementById('start-btn');
        const stopBtn = document.getElementById('stop-btn');
        const downloadBtn = document.getElementById('download-btn');
        const urlsTextarea = document.getElementById('urls');
        const selectorsTextarea = document.getElementById('selectors');
        const statusMessages = document.getElementById('status-messages');
        const resultsDiv = document.getElementById('results');
        const resultsCount = document.getElementById('results-count');
        const statusDot = document.getElementById('status-dot');
        const statusText = document.getElementById('status-text');
        
        startBtn.addEventListener('click', startScraping);
        stopBtn.addEventListener('click', stopScraping);
        downloadBtn.addEventListener('click', downloadResults);
        
        async function startScraping() {
            const urls = urlsTextarea.value.trim().split('\\n').filter(url => url.trim());
            const selectorsText = selectorsTextarea.value.trim();
            
            if (!urls.length) {
                addStatusMessage('Please enter at least one URL', 'error');
                return;
            }
            
            let selectors;
            try {
                selectors = JSON.parse(selectorsText);
            } catch (e) {
                addStatusMessage('Invalid JSON in selectors field', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ urls, selectors })
                });
                
                if (response.ok) {
                    isScraping = true;
                    updateUIState();
                    addStatusMessage('Scraping started...', 'success');
                } else {
                    const error = await response.json();
                    addStatusMessage('Error: ' + error.error, 'error');
                }
            } catch (error) {
                addStatusMessage('Network error: ' + error.message, 'error');
            }
        }
        
        async function stopScraping() {
            try {
                const response = await fetch('/api/stop', { method: 'POST' });
                if (response.ok) {
                    isScraping = false;
                    updateUIState();
                    addStatusMessage('Scraping stopped', 'info');
                }
            } catch (error) {
                addStatusMessage('Error stopping: ' + error.message, 'error');
            }
        }
        
        async function downloadResults() {
            try {
                const response = await fetch('/api/download');
                const result = await response.json();
                addStatusMessage(result.message, 'success');
            } catch (error) {
                addStatusMessage('Error downloading: ' + error.message, 'error');
            }
        }
        
        function updateUIState() {
            startBtn.disabled = isScraping;
            stopBtn.disabled = !isScraping;
            
            if (isScraping) {
                statusDot.className = 'status-dot status-running';
                statusText.textContent = 'Running';
            } else {
                statusDot.className = 'status-dot status-ready';
                statusText.textContent = 'Ready';
            }
        }
        
        function addStatusMessage(message, type = 'info') {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'status-message status-' + type;
            messageDiv.textContent = '[' + new Date().toLocaleTimeString() + '] ' + message;
            
            statusMessages.appendChild(messageDiv);
            statusMessages.scrollTop = statusMessages.scrollHeight;
            
            // Keep only last 20 messages
            while (statusMessages.children.length > 20) {
                statusMessages.removeChild(statusMessages.firstChild);
            }
        }
        
        function displayResults(results) {
            if (!results.length) {
                resultsDiv.innerHTML = '<div style="text-align: center; color: #666; padding: 40px;">📋 No results yet. Start scraping to see results here.</div>';
                resultsCount.textContent = '(0)';
                return;
            }
            
            resultsDiv.innerHTML = results.map((result, index) => `
                <div class="result-item">
                    <div class="result-url">
                        <a href="${result.url}" target="_blank">${result.url}</a>
                    </div>
                    ${result.error ? 
                        '<div style="color: #dc3545;">Error: ' + result.error + '</div>' :
                        '<div class="result-data">' +
                            Object.entries(result.data).map(([key, values]) => `
                                <div class="result-field">
                                    <strong>${key}:</strong>
                                    <div class="result-values">
                                        ${values.length > 0 ? 
                                            values.slice(0, 3).map(v => '• ' + v).join('<br>') +
                                            (values.length > 3 ? '<br>... and ' + (values.length - 3) + ' more' : '')
                                            : '<em>No items found</em>'
                                        }
                                    </div>
                                </div>
                            `).join('') +
                        '</div>'
                    }
                    <div style="font-size: 12px; color: #666; margin-top: 10px;">
                        ${new Date(result.timestamp).toLocaleString()}
                    </div>
                </div>
            `).join('');
            
            resultsCount.textContent = '(' + results.length + ')';
        }
        
        async function pollStatus() {
            try {
                const response = await fetch('/api/status');
                const status = await response.json();
                
                // Update status messages
                status.status_messages.forEach(msg => {
                    addStatusMessage(msg.message, msg.type);
                });
                
                // Update results
                if (status.results_count > 0) {
                    const resultsResponse = await fetch('/api/results');
                    const results = await resultsResponse.json();
                    displayResults(results);
                }
                
                // Update UI state
                if (status.is_running !== isScraping) {
                    isScraping = status.is_running;
                    updateUIState();
                }
            } catch (error) {
                console.error('Error polling status:', error);
            }
        }
        
        // Start polling
        setInterval(pollStatus, 2000);
        pollStatus();
    </script>
</body>
</html>'''
        
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

def main():
    create_template()
    
    PORT = 5000
    Handler = ScraperHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🚀 Web Scraper Dashboard is running!")
        print(f"📱 Open your browser and go to: http://localhost:{PORT}")
        print(f"🛑 Press Ctrl+C to stop the server")
        print()
        print("Features:")
        print("- ✅ Live scraping dashboard")
        print("- ✅ Real-time status updates")
        print("- ✅ Download results as JSON")
        print("- ✅ No external dependencies required")
        print()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped. Goodbye!")

if __name__ == "__main__":
    main()
