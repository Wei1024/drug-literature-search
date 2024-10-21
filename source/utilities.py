import os
import requests
import shutil
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Function to download a PDF file
def download_pdf(url, destination_folder):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        filename = os.path.join(destination_folder, url.split("/")[-1])
        with open(filename, 'wb') as f:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)
        return filename
    else:
        return None

def download_from_cfm(url, destination_folder):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # Assuming that the PDF link is inside <a> tags
        pdf_links = soup.find_all('a', href=True)
        downloaded_files = []
        for link in pdf_links:
            href = link['href']
            if href.endswith(".pdf"):
                # Use urljoin to handle relative URLs correctly
                pdf_url = urljoin(url, href)
                pdf_filename = download_pdf(pdf_url, destination_folder)
                if pdf_filename:
                    downloaded_files.append(pdf_filename)
        return downloaded_files
    return None
