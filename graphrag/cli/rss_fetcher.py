"""RSS fetching and document processing functionality."""

import feedparser
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urlparse
import re

def get_safe_filename(url: str) -> str:
    """Extract and clean the last part of URL to use as filename."""
    path = urlparse(url).path
    filename = path.rstrip('/').split('/')[-1] or 'index'
    # Remove any non-alphanumeric chars except - and _
    filename = re.sub(r'[^\w\-_]', '_', filename)
    return filename

async def fetch_rss_documents(
    rss_url: str,
    max_links: int,
    dom_element: str,
    output_dir: Path
) -> None:
    """Fetch documents from RSS feed and save them.
    
    Args:
        rss_url: URL of the RSS feed
        max_links: Maximum number of links to process
        dom_element: DOM element to extract text from
        output_dir: Directory to save documents to
    """
    feed = feedparser.parse(rss_url)
    
    for i, entry in enumerate(feed.entries[:max_links]):
        if hasattr(entry, 'link'):
            try:
                response = requests.get(entry.link)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract text from specified DOM element
                if dom_element.upper() == "<HTML>":
                    content = soup.get_text()
                else:
                    elements = soup.select(dom_element)
                    content = "\n".join(elem.get_text() for elem in elements)
                
                # Save to file using URL's last segment as name
                safe_name = get_safe_filename(entry.link)
                output_file = output_dir / f"{safe_name}.txt"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(content)
                    
            except Exception as e:
                print(f"Error processing {entry.link}: {str(e)}")
