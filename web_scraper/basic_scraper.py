import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
from urllib.parse import urljoin, urlparse

class WebScraper:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.data = []
        
    def fetch_page(self, url):
        """Fetch a single page and return BeautifulSoup object"""
        try:
            time.sleep(1)  # Respect website, avoid hitting too fast
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_links(self, soup, domain):
        """Extract all links from a page"""
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(self.base_url, href)
            if domain in full_url and full_url not in links:
                links.append(full_url)
        return links
    
    def extract_data(self, soup):
        """Override this method for specific website extraction"""
        # Basic extraction - gets all text from common tags
        page_data = {
            'url': '',
            'title': '',
            'headings': [],
            'paragraphs': [],
            'links': []
        }
        
        # Get title
        title_tag = soup.find('title')
        if title_tag:
            page_data['title'] = title_tag.get_text(strip=True)
        
        # Get all headings (h1, h2, h3)
        for h_tag in ['h1', 'h2', 'h3']:
            for heading in soup.find_all(h_tag):
                page_data['headings'].append(heading.get_text(strip=True))
        
        # Get all paragraphs
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if text:
                page_data['paragraphs'].append(text)
        
        return page_data
    
    def scrape_site(self, max_pages=50):
        """Main scraping function"""
        visited = set()
        to_visit = [self.base_url]
        scraped_data = []
        
        while to_visit and len(visited) < max_pages:
            current_url = to_visit.pop(0)
            
            if current_url in visited:
                continue
                
            print(f"Scraping: {current_url}")
            soup = self.fetch_page(current_url)
            
            if soup:
                # Extract data from current page
                page_data = self.extract_data(soup)
                page_data['url'] = current_url
                scraped_data.append(page_data)
                
                # Find more links to scrape
                domain = urlparse(self.base_url).netloc
                new_links = self.extract_links(soup, domain)
                
                for link in new_links:
                    if link not in visited and link not in to_visit:
                        to_visit.append(link)
            
            visited.add(current_url)
            
        return scraped_data

# Example usage
if __name__ == "__main__":
    # Aap yahan apni website ka URL denge
    website_url = input("Enter website URL to scrape: ")
    scraper = WebScraper(website_url)
    data = scraper.scrape_site(max_pages=20)
    
    # Save data
    with open('scraped_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Scraped {len(data)} pages")
    print("Data saved to scraped_data.json")