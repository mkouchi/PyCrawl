from urllib.parse import urlparse
from config import DEFAULT_USER_AGENT, MAX_CRAWL_COUNT
from robots_sitemaps_parser import fetch_and_parse_robots_txt, fetch_and_parse_sitemaps
from scraper import crawl_website, scrape_url
from utils import setup_logging, create_directories, get_timestamp, save_json
import logging
import signal

visited = set()  # Keep track of visited URLs
articles = []  # Store crawled articles' content

start_url = "https://www.zeitoons.com/"

# Signal handler for graceful exit on Ctrl+C
def signal_handler(sig, frame):
    print("\n\nCtrl+C detected. Stopping the crawl process...")
    logging.info(f"Total documents scraped: {len(articles)}")
    save_json(articles, start_url=start_url)
    exit(0)

# Register the signal handler for Ctrl+C (SIGINT)
signal.signal(signal.SIGINT, signal_handler)

def main():
    global articles
    # setup logging
    setup_logging()

    # Create necessary directories
    create_directories()

    # Get current timestamp
    # timestamp = get_timestamp()

    crawl_count = 0
    # Starting URL and depth for the crawler
    
    parsed_start_url = urlparse(start_url)
    base_url = f"{parsed_start_url.scheme}://{parsed_start_url.netloc}"

    logging.info(f"Starting to crawl {base_url}")

    # Fetch and parse robots.txt
    rp, sitemap_urls = fetch_and_parse_robots_txt(base_url)

    if not sitemap_urls:
        # If no sitemap URLs found, you might decide to proceed with recursive crawling
        logging.info(f"No sitemap URLs found for {base_url}. Proceeding with recursive crawling.")
        articles = crawl_website(start_url, visited, rp)
        return finalProcessing(articles)

    # Fetch and parse sitemaps to get URLs to crawl
    urls_to_crawl = fetch_and_parse_sitemaps(sitemap_urls)

    # Crawl the URLs
    for url in urls_to_crawl:
        # Check if URL is allowed by robots.txt
        if rp is None or rp.can_fetch(DEFAULT_USER_AGENT, url) and url not in visited and (crawl_count <= MAX_CRAWL_COUNT or MAX_CRAWL_COUNT == -1):
            doc = scrape_url(url)
            visited.add(url)
            crawl_count += 1
            articles.append(doc)

    logging.info(f"Total documents scraped: {len(articles)}")

    return finalProcessing(articles)

def finalProcessing(articles):
    
    if not articles:
        logging.error("No articles were scraped. Exiting.")
        return
    
    save_json(articles, start_url)

    

if __name__ == "__main__":
    main()