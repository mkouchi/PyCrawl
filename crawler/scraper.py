from config import DEFAULT_USER_AGENT, MAX_DEPTH, MIN_DELAY, MAX_CRAWL_COUNT, headers
from requester import make_request, find_article_links
from extractor import extract_main_content 
import logging
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser


def is_allowed(url, user_agent='*'):
    """
    Checks if the URL is allowed to be scraped according to the website's robots.txt.

    Args:
        url (str): The URL to check.
        user_agent (str): The user agent to use for checking robots.txt.

    Returns:
        bool: True if scraping is allowed, False otherwise.
    """
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    robots_url = urljoin(base_url, '/robots.txt')
    rp = RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception as e:
        logging.warning(f"Could not read robots.txt for {base_url}: {e}")
        # If robots.txt cannot be fetched, assume allowed
        return True
    
def scrape_url(url, headers=headers, delay=MIN_DELAY):
    """
    Scrapes a single URL and extracts its main content.

    Args:
        url (str): The URL to scrape.
        headers (dict): HTTP headers to include in the request.

    Returns:
        Document: A Document object containing the scraped content, or None if extraction failed.
    """
    logging.info(f"Preparing to scrape URL: {url}")

    # Respect the delay between requests
    logging.debug(f"Sleeping for {delay} seconds before making the request to {url}")
    time.sleep(delay)

    try:
        response = make_request(url, headers=headers)
        logging.debug(f"Received response for {url} with status code {response.status_code}")
        
        # Decode content if necessary
        if response.encoding is None:
            response.encoding = 'utf-8' # Fallback encoding
        html_content = response.text

        # Parse and extract the main content using newspaper3k with the fetched HTML
        page_text = extract_main_content(html_content, url)
        if not page_text:
            logging.warning(f"No content extracted from {url}. Skipping.")
            return None
        logging.info(f"Successfully scraped URL: {url}")
        return {'url': url, 'content': page_text}

    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")
        return None

def crawl_website(start_url, visited, robots_parser=None, depth=0, max_depth=MAX_DEPTH, headers=headers, crawl_count=0, delay=MIN_DELAY):
    """
    Recursively scrapes a website starting from the given URL.

    Args:
        start_url (str): The URL to start scraping from.
        depth (int): The current depth of recursion.
        max_depth (int): The maximum depth to recurse.
        headers (dict): HTTP headers to include in requests.
        visited (set): Set of already visited URLs.
        delay (float): Delay between requests in seconds.

    Returns:
        list: A list of Document objects containing scraped content.
    """
    articles = []
    
    def crawl(url, current_depth, crawl_count, delay):

        # Stop crawling if the counter has reached the maximum allowed crawls
        if current_depth > max_depth or url in visited or (crawl_count >= MAX_CRAWL_COUNT and MAX_CRAWL_COUNT != -1):
            return articles
        
        if robots_parser and not robots_parser.can_fetch(DEFAULT_USER_AGENT, url):
            logging.info(f"Skipping {url} due to robots.txt restrictions.")
            return articles

        visited.add(url)
        crawl_count += 1
        logging.info(f"Scraping: {url} (Depth: {current_depth}) (crawl_count: {crawl_count})")
        
        
        try:
            response = make_request(url, headers=headers)
            logging.debug(f"Received response for {url} with status code {response.status_code}")
            # Decode content if necessary
            if response.encoding is None:
                response.encoding = 'utf-8' # Fallback encoding
            html_content = response.text

            # Get and store the main content of the article
            page_text = extract_main_content(html_content, url)
            if not page_text:
                logging.warning(f"No content extracted from {url}.")
                return articles
            
            if page_text:
                articles.append({'url': url, 'content': page_text})
            
            # Find links to other articles and crawl them
            links, delay = find_article_links(url, visited, delay)
            for link in links:
                logging.info(f"Waiting for {delay} seconds before scraping {link}")
                time.sleep(delay)
                if (crawl_count <= MAX_CRAWL_COUNT or MAX_CRAWL_COUNT == -1):
                    crawl(link, current_depth + 1, crawl_count, delay)
        except Exception as e:
            logging.error(f"Failed to retrieve {url}: {e}")
            return articles
            

    # Start crawling from the start URL
    crawl(start_url, depth, crawl_count, delay)

    return articles