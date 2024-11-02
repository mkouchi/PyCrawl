from crawler.config import DEFAULT_USER_AGENT
import os
import logging
import json
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import requests
from xml.etree import ElementTree

def fetch_and_parse_robots_txt(base_url, user_agent=DEFAULT_USER_AGENT):
    """
    Fetches and parses the robots.txt file from the given base URL.
    
    Args:
        base_url (str): The base URL of the website (e.g., 'https://example.com').
        user_agent (str): The user agent string of your crawler.
    
    Returns:
        tuple: A RobotFileParser object and a list of sitemap URLs.
    """
    robots_url = urljoin(base_url, '/robots.txt')
    rp = RobotFileParser()
    sitemap_urls = []

    try:
        response = requests.get(robots_url, headers={'User-Agent': user_agent}, timeout=10)
        if response.status_code == 200:
            rp.parse(response.text.splitlines())
            # Extract sitemap URLs from robots.txt
            for line in response.text.splitlines():
                if line.strip().lower().startswith('sitemap:'):
                    sitemap_url = line.split(':', 1)[1].strip()
                    sitemap_urls.append(sitemap_url)
            logging.info(f"Parsed robots.txt from {robots_url}")
        else:
            logging.warning(f"robots.txt not found at {robots_url} (status code: {response.status_code})")
            rp = None  # robots.txt doesn't exist
    except requests.RequestException as e:
        logging.warning(f"Failed to fetch robots.txt from {robots_url}: {e}")
        rp = None  # robots.txt couldn't be fetched

    return rp, sitemap_urls

