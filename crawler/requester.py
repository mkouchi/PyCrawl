import requests
import time
import logging
from crawler.config import MAX_RETRIES, TIMEOUT, MIN_DELAY, MAX_DELAY
from requests.exceptions import RequestException, HTTPError
from email.utils import parsedate_to_datetime
from datetime import datetime

# Custom headers including a User-Agent
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
}

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
            response = requests.get(url, headers=headers, timeout=TIMEOUT)
            status_code = response.status_code
            if status_code == 200:
                return response
            elif status_code in [429, 503, 403]:
                # Handle Too Many Requests, Service Unavailable, Forbidden
                logging.warning(f"Received status code {status_code} for {url}")
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    wait_time = parse_retry_after(retry_after, delay, attempt)
                    logging.info(f"Retry-After header found. Waiting for {wait_time} seconds.")
                    time.sleep(wait_time)
                else:
                    wait_time = min(MAX_DELAY, delay * 2 ** (attempt - 1))
                    logging.info(f"No Retry-After header. Waiting for {wait_time} seconds before retrying.")
                    time.sleep(wait_time)
            else:
                # For other status codes, raise an error
                response.raise_for_status()
        except RequestException as e:
            logging.error(f"Request failed for {url}: {e}")
            wait_time = min(MAX_DELAY, delay * 2 ** (attempt - 1))
            logging.info(f"Waiting for {wait_time} seconds before retrying.")
            time.sleep(wait_time)
    raise HTTPError(f"Failed to retrieve {url} after {max_retries} attempts")

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