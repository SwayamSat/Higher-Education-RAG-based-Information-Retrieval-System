import os
import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from config import DATA_DIR

# List of target URLs for scraping
TARGET_URLS = {
    "MoE": "https://www.education.gov.in/en/schemes",
    "UGC": "https://www.ugc.ac.in/", # Note: UGC home page might not have all PDFs directly
    "AICTE": "https://www.aicte-india.org/schemes/students-development-schemes",
    "MSDE": "https://www.msde.gov.in/en/reports-documents/schemes" # Updated more direct URL if known
}

# Add MSDE schemes specifically if reports-documents is too broad
# "MSDE": "https://www.msde.gov.in/en/schemes" 

def download_pdf(pdf_url, folder_name, base_url):
    try:
        full_pdf_url = urllib.parse.urljoin(base_url, pdf_url)
        pdf_name = full_pdf_url.split('/')[-1]
        
        if '?' in pdf_name:
            pdf_name = pdf_name.split('?')[0]
            
        if not pdf_name.lower().endswith('.pdf'):
            pdf_name += ".pdf"

        folder_path = os.path.join(DATA_DIR, folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        local_filename = os.path.join(folder_path, pdf_name)
        if os.path.exists(local_filename):
            logger.info(f"Skipping existing: {pdf_name}")
            return True

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        logger.info(f"Downloading: {pdf_name}")
        pdf_response = requests.get(full_pdf_url, headers=headers, timeout=30)
        pdf_response.raise_for_status()

        with open(local_filename, 'wb') as f:
            f.write(pdf_response.content)
        return True
        
    except Exception as e:
        logger.error(f"Error downloading {pdf_url}: {e}")
        return False

def scrape_site(folder_name, url):
    try:
        logger.info(f"Scraping {folder_name} from {url}...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        pdf_links = set()
        
        # General link search
        for link in soup.find_all(['a', 'iframe'], href=True):
            href = link.get('href') or link.get('src')
            if href and ('.pdf' in href.lower() or 'download' in href.lower()):
                pdf_links.add(href)

        # Text-based search
        for link in soup.find_all('a', string=True):
            if any(term in link.string.lower() for term in ['pdf', 'download', 'guidelines', 'scheme']):
                 href = link.get('href')
                 if href:
                     pdf_links.add(href)

        logger.info(f"Found {len(pdf_links)} potential documents.")
        
        success_count = 0
        for i, pdf_link in enumerate(list(pdf_links)):
            if download_pdf(pdf_link, folder_name, url):
                success_count += 1
            time.sleep(0.5)
            
        logger.info(f"Finished {folder_name}: {success_count} documents downloaded/saved.")

    except Exception as e:
        logger.error(f"Error scraping {folder_name}: {e}")

if __name__ == "__main__":
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    for folder_name, url in TARGET_URLS.items():
        scrape_site(folder_name, url)
