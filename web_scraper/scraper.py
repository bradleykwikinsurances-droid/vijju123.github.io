import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import os
from flask import Flask, render_template, jsonify, request
from threading import Thread
import queue

class WebScraper:
    def __init__(self):
        self.results = []
        self.is_running = False
        self.status_queue = queue.Queue()
        
    def fetch_page(self, url, headers=None):
        try:
            response = requests.get(url, headers=headers or {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            return response.text
        except Exception as e:
            return {"error": str(e)}
    
    def extract_data(self, html, selectors):
        soup = BeautifulSoup(html, 'html.parser')
        data = {}
        
        for key, selector in selectors.items():
            elements = soup.select(selector)
            if elements:
                data[key] = [elem.get_text(strip=True) for elem in elements]
            else:
                data[key] = []
        
        return data
    
    def scrape_urls(self, urls, selectors):
        self.is_running = True
        self.results = []
        
        for i, url in enumerate(urls):
            if not self.is_running:
                break
                
            self.status_queue.put(f"Processing URL {i+1}/{len(urls)}: {url}")
            
            html = self.fetch_page(url)
            if isinstance(html, dict):  # Error occurred
                result = {"url": url, "error": html["error"], "timestamp": datetime.now().isoformat()}
            else:
                data = self.extract_data(html, selectors)
                result = {
                    "url": url,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }
            
            self.results.append(result)
            time.sleep(1)  # Rate limiting
        
        self.is_running = False
        self.status_queue.put("Scraping completed!")
        
        return self.results
    
    def stop_scraping(self):
        self.is_running = False

# Flask Web Interface
app = Flask(__name__)
scraper = WebScraper()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def start_scraping():
    data = request.json
    urls = data.get('urls', [])
    selectors = data.get('selectors', {})
    
    if not urls or not selectors:
        return jsonify({"error": "URLs and selectors are required"}), 400
    
    # Start scraping in background thread
    thread = Thread(target=scraper.scrape_urls, args=(urls, selectors))
    thread.daemon = True
    thread.start()
    
    return jsonify({"message": "Scraping started"})

@app.route('/api/stop', methods=['POST'])
def stop_scraping():
    scraper.stop_scraping()
    return jsonify({"message": "Scraping stopped"})

@app.route('/api/status')
def get_status():
    status_messages = []
    while not scraper.status_queue.empty():
        try:
            status_messages.append(scraper.status_queue.get_nowait())
        except queue.Empty:
            break
    
    return jsonify({
        "is_running": scraper.is_running,
        "results_count": len(scraper.results),
        "status_messages": status_messages
    })

@app.route('/api/results')
def get_results():
    return jsonify(scraper.results)

@app.route('/api/download')
def download_results():
    filename = f"scraping_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(scraper.results, f, indent=2, ensure_ascii=False)
    
    return jsonify({"message": f"Results saved to {filename}"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
