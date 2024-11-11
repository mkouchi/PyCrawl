import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import logging
from config import MAX_RETRIES, TIMEOUT, MIN_DELAY, MAX_DELAY, headers
from requests.exceptions import RequestException, HTTPError
from email.utils import parsedate_to_datetime
from datetime import datetime


def make_request(url, headers=headers, max_retries=MAX_RETRIES):
    """
    Makes an HTTP GET request with error handling and retries.

    Args:
        url (str): The URL to request.
        headers (dict): HTTP headers to include in the request.
        max_retries (int): Maximum number of retries.

    Returns:
        requests.Response: The HTTP response object.

    Raises:
        HTTPError: If the request fails after the maximum number of retries.
    """
    delay = MIN_DELAY
    logging.info(f"make_request {url} delay { delay }.")
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            status_code = response.status_code
            if status_code == 200:
                return response
            elif status_code in [429, 503, 403]:
                # Handle Too Many Requests, Service Unavailable, Forbidden
                logging.warning(f"Received status code {status_code} for {url}")
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    try:
                        wait_time = int(retry_after)
                    except ValueError:
                        wait_time = delay * 2 ** (attempt - 1)
                    logging.info(f"Retry-After header found. Waiting for {wait_time} seconds.")
                    time.sleep(wait_time)
                else:
                    wait_time = delay * 2 ** (attempt - 1)
                    logging.info(f"No Retry-After header. Waiting for {wait_time} seconds before retrying.")
                    time.sleep(wait_time)
            else:
                # For other status codes, raise an error
                response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for {url}: {e}")
            wait_time = delay * 2 ** (attempt - 1)
            logging.info(f"Waiting for {wait_time} seconds before retrying.")
            time.sleep(wait_time)
    raise requests.exceptions.HTTPError(f"Failed to retrieve {url} after {max_retries} attempts")

def parse_retry_after(retry_after, delay, attempt):
    """
    Parses the Retry-After header to determine how long to wait before retrying.

    Args:
        retry_after (str): The value of the Retry-After header.
        delay (float): The base delay.
        attempt (int): The current attempt number.

    Returns:
        float: The number of seconds to wait before retrying.
    """
    try:
        # Try to parse as integer seconds
        wait_time = int(retry_after)
    except ValueError:
        # Parse HTTP-date
        retry_after_date = parsedate_to_datetime(retry_after)
        wait_time = (retry_after_date - datetime.now(datetime.timezone.utc)).total_seconds()
        if wait_time < 0:
            wait_time = delay * 2 ** (attempt - 1)
    return wait_time

def find_article_links(url, visited, delay):
    
    # Fetch page to extract links
    try:
        # Send a GET request to the URL 
        # The script will wait longer for responses (15 seconds) and can handle timeouts gracefully.
        response = make_request(url, headers=headers)
        # Reduce delay after successful request, minimum delay of 1 second
        delay = max(1, delay / 2)
    except requests.exceptions.HTTPError as e:
        logging.error(f"Failed to retrieve {url}: {e}")
        # Increase delay after failed request
        delay = min(MAX_DELAY, delay * 2)
        return [], delay
    
    # Parse the HTML content of the page
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all internal links
    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    # Find all article links on the page
    article_links = []
    for link_tag in soup.find_all('a', href=True):
        href = link_tag['href']
        if href.startswith('/'):
            link = urljoin(base_url, href)
        elif href.startswith(base_url):
            link = href
        else:
            continue # Skip external links
        # Avoid URL fragments and query parameters for simplicity
        link = link.split('#')[0].split('?')[0]
        if link not in visited:
            article_links.append(link)
        
    return article_links, delay