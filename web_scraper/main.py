#!/usr/bin/env python3
"""
Web Scraper Pro - Complete Web Scraping Tool
Usage: python main.py [url]
"""

import sys
import json
from data_extractor import DataExtractor
from basic_scraper import WebScraper

def main():
    print("=" * 60)
    print("WEB SCRAPER PRO - Complete Data Extraction Tool")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter website URL to scrape: ").strip()
    
    if not url:
        print("No URL provided. Exiting.")
        return
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        print(f"Using URL: {url}")
    
    print("\nChoose scraping method:")
    print("1. Basic Scraping (Fast, for static websites)")
    print("2. Advanced Scraping (For dynamic content, more comprehensive)")
    print("3. Full Data Extraction (Recommended)")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == '1':
        print("\nStarting basic scraper...")
        scraper = WebScraper(url)
        data = scraper.scrape_site(max_pages=20)
        
        output_file = 'basic_scraped_data.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Scraping completed! Saved {len(data)} pages to {output_file}")
    
    elif choice == '2':
        print("\nStarting advanced scraper with dynamic content support...")
        from advanced_scraper import DynamicScraper
        
        scraper = DynamicScraper(headless=True)
        data = scraper.scrape_page(url)
        scraper.close()
        
        output_file = 'advanced_scraped_data.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Scraping completed! Data saved to {output_file}")
    
    else:
        print("\nStarting full data extraction...")
        extractor = DataExtractor()
        data = extractor.extract_all_data(url)
        
        if data:
            # Save in multiple formats
            extractor.save_data(data, 'full_extraction', 'json')
            extractor.save_data(data, 'full_extraction', 'txt')
            
            print("\n✅ Extraction completed!")
            print(f"\nSummary:")
            print(f"- Page Title: {data['page_info']['title']}")
            print(f"- Headings: {len(data['content']['headings'])}")
            print(f"- Paragraphs: {len(data['content']['paragraphs'])}")
            print(f"- Links: {len(data['links'])}")
            print(f"- Images: {len(data['images'])}")
            print(f"- Tables: {len(data['tables'])}")
        else:
            print("\n❌ Failed to extract data from the website.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check if the website URL is correct")
        print("2. Ensure you have internet connection")
        print("3. Some websites may block automated scraping")
        print("4. Try using a VPN if the website is geo-restricted")