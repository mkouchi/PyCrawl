from urllib.parse import urlparse
from crawler.robots_sitemaps_parser import fetch_and_parse_robots_txt, fetch_and_parse_sitemaps
from crawler.scraper import crawl_website, scrape_url
from crawler.utils import setup_logging, create_directories, get_timestamp, save_json
import logging
import signal


start_url = "https://www.hra-news.org/"
# Signal handler for graceful exit on Ctrl+C
def signal_handler(sig, frame):
    print("\n\nCtrl+C detected. Stopping the crawl process...")
    logging.info(f"Total documents scraped: {len(articles_content)}")
    save_json(articles_content, start_url=start_url)
    exit(0)

# Register the signal handler for Ctrl+C (SIGINT)
signal.signal(signal.SIGINT, signal_handler)

def main():
    # setup logging
    setup_logging()

    # Create necessary directories
    create_directories()

    # Get current timestamp
    timestamp = get_timestamp()

        global crawl_count
    # Starting URL and depth for the crawler
    
    max_depth = 3  # Adjust the depth as needed

    parsed_start_url = urlparse(start_url)
    base_url = f"{parsed_start_url.scheme}://{parsed_start_url.netloc}"

    logging.info(f"Starting to crawl {base_url}")

    # Fetch and parse robots.txt
    rp, sitemap_urls = fetch_and_parse_robots_txt(base_url)

    if not sitemap_urls:
        # If no sitemap URLs found, you might decide to proceed with recursive crawling
        logging.info(f"No sitemap URLs found for {base_url}. Proceeding with recursive crawling.")
        crawl_website(start_url, 0, max_depth, headers, delay, rp)
        return

    # Fetch and parse sitemaps to get URLs to crawl
    urls_to_crawl = fetch_and_parse_sitemaps(sitemap_urls)

    # Crawl the URLs
    for url in urls_to_crawl:
        # Check if URL is allowed by robots.txt
        if rp is None or rp.can_fetch(DEFAULT_USER_AGENT, url) and (crawl_count <= MAX_CRAWL_COUNT or MAX_CRAWL_COUNT == -1):
            doc = scrape_url(url)
            crawl_count += 1
            articles_content.append(doc)

    logging.info(f"Total documents scraped: {len(articles_content)}")

    """ data_to_save = [
        {
            "content": doc.content,
            "url": doc.url
        }
        for doc in articles_content
    ] """

    

    save_json(articles_content, start_url)

    

    if not articles_content:
        logging.error("No articles were scraped. Exiting.")
        return



if __name__ == "__main__":
    main()