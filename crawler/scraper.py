from crawler.config import MIN_DELAY, MAX_CRAWL_COUNT
import logging
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
    
def crawl_website(start_url, depth, max_depth, headers, visited=None, delay=MIN_DELAY):
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
    crawl_count = 0

    def crawl(url, current_depth):
        global crawl_count
        global delay
        # Stop crawling if the counter has reached the maximum allowed crawls
        if current_depth > max_depth or url in visited or crawl_count >= MAX_CRAWL_COUNT:
            return
        
        if not is_allowed(url):
            logging.info(f"Skipping {url} due to robots.txt restrictions.")
            return

        visited.add(url)
        crawl_count += 1
        logging.info(f"Scraping: {url} (Depth: {current_depth}) (crawl_count: {crawl_count})")
        
        # Get and store the main content of the article
        content = extract_main_content(url)
        if not content:
            logging.warning(f"No content extracted from {url}.")
            return
        
        if content:
            articles_content.append({'url': url, 'content': content})
        
        # Find links to other articles and crawl them
        links = find_article_links(url)
        for link in links:
            logging.info(f"Waiting for {delay} seconds before scraping {link}")
            time.sleep(delay)
            if crawl_count < MAX_CRAWL_COUNT:
                crawl(link, current_depth + 1)

        logging.info(f"Total documents scraped: {len(articles_content)}")
            

    # Start crawling from the start URL
    crawl(start_url, 0)

    # After finishing the crawl, print all crawled URLs
    print_crawled_contents()