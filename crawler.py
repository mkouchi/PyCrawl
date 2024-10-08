import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from newspaper import Article
import time
import signal
import logging
from crawler_utils import is_allowed, get_sitemap_urls, parse_sitemap, parse_sitemap_index

DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
# Custom headers including a User-Agent
headers = {
    'User-Agent': DEFAULT_USER_AGENT
}

# Set up retry strategy
retry_strategy = Retry(
    total=5,  # Number of retries
    backoff_factor=1,  # Time between retries increases exponentially: 1, 2, 4, 8...
    status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

MAX_CRAWL_COUNT = 30  # Set the limit for the number of URLs to crawl
crawl_count = 0
visited = set()  # Keep track of visited URLs
articles_content = []  # Store crawled articles' content
delay = 2 # Initial delay in seconds

# Configure logging
logging.basicConfig(
    filename='scraper.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def make_request(url, headers=headers, max_retries=5):
    global delay
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


def get_clean_content(url):
    # Send a GET request to the URL
    response = http.get(url, headers=headers, timeout=15)
    
    # Check if the request was successful
    if response.status_code != 200:
        print(f"Failed to retrieve content from {url}")
        return None
    
    # Parse the HTML content of the page
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find the main content section
    main_content = soup.find('div', {'class': 'story-content-main'})  # Adjust this based on the page structure
    
    if not main_content:
        print(f"Could not find the main content on the page: {url}")
        return None
    
    # Extract text content and clean it
    clean_text = main_content.get_text(separator='\n', strip=True)
    
    return clean_text

def print_crawled_urls():
    # Print all visited URLs at the end
    print("\nCrawled URLs:")
    for idx, url in enumerate(visited):
        print(f"{idx + 1}: {url}")

def print_crawled_contents():

    # Print or process the collected articles' content
    for idx, article in enumerate(articles_content):
        print(f"Article {idx + 1}: {article['url']}\n")
        print(article['content'])
        print("\n" + "="*80 + "\n")

# Signal handler for graceful exit on Ctrl+C
def signal_handler(sig, frame):
    print("\n\nCtrl+C detected. Stopping the crawl process...")
    print_crawled_contents()
    exit(0)

# Register the signal handler for Ctrl+C (SIGINT)
signal.signal(signal.SIGINT, signal_handler)

def extract_main_content(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        print(f"Failed to extract content from {url}: {e}")
        return ""


def find_article_links(url):
    global delay
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
        delay = min(60, delay * 2)
        return []
    
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
        article_links.append(link)
    
    return article_links

def crawl_website(start_url, depth):
    max_depth = depth
    global crawl_count
    global delay

    def crawl(url, current_depth):
        global crawl_count
        global delay
        # Stop crawling if the counter has reached the maximum allowed crawls
        if current_depth > max_depth or url in visited or crawl_count >= MAX_CRAWL_COUNT:
            return
        
        if not is_allowed(url, DEFAULT_USER_AGENT):
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

def main():
    # Starting URL and depth for the crawler
    start_url =  "https://news.bahai.org/" #"https://www.radiozamaneh.com/" "https://universalhouseofjustice.bahai.org/" # "https://www.bahaisofiran.org/" # "https://news.persian-bahai.org/" #  "https://www.bahaisofiran.org/" "https://universalhouseofjustice.bahai.org/" # "https://bahaiworld.bahai.org/" # "https://www.bahaisofiran.org/" # "https://news.persian-bahai.org/" # "https://www.hra-news.org/" #  # "https://news.bahai.org/fa/"
    max_depth = 5  # Adjust the depth as needed

    # Check for sitemap at robots.txt URL
    sitemap_urls = get_sitemap_urls(start_url, DEFAULT_USER_AGENT)
    if sitemap_urls:
        logging.info(f"Using sitemap to get URLs for {start_url}")
        for sitemap_url in sitemap_urls:
            urls_to_crawl = parse_sitemap_index(sitemap_url)
            urls_to_crawl = parse_sitemap(sitemap_url)
            for url in urls_to_crawl:
                # Crawl each URL individually
                documents = scrape_url(
                    url=url,
                    headers=headers,
                    delay=config.delay
                )
                # Process documents...
    else:
        # Fall back to recursive crawling
        documents = scrape_website(
            url=start_url,
            depth=0,
            max_depth=config.max_depth,
            headers=headers,
            delay=config.delay
        )
    """ 
    def main():
    from crawler.utils import setup_logging, create_directories
    from crawler.config import DEFAULT_USER_AGENT
    import logging

    setup_logging()
    create_directories()

    headers = {'User-Agent': DEFAULT_USER_AGENT}

    # For each site in your Site enum
    for site in Site:
        config = site.value
        start_url = config.url
        delay = config.delay

        logging.info(f"Starting to scrape {start_url}")

        # Get sitemap URLs from robots.txt or use the provided sitemap URL
        sitemap_index_url = 'http://example.org/sitemap_index.xml'  # Replace with actual URL
        sitemap_urls = parse_sitemap_index(sitemap_index_url)

        all_urls_to_crawl = []
        for sitemap_url in sitemap_urls:
            urls = parse_sitemap(sitemap_url)
            all_urls_to_crawl.extend(urls)

        # Crawl the URLs
        for url in all_urls_to_crawl:
            if is_allowed(url, user_agent=DEFAULT_USER_AGENT):
                time.sleep(delay)
                documents = scrape_url(url, headers, delay)
                # Process documents...
            else:
                logging.info(f"Skipping disallowed URL: {url}")

    # Further processing...


     
       """

    crawl_website(start_url, max_depth)

    if not articles_content:
        logging.error("No articles were scraped. Exiting.")
        return

if __name__ == "__main__":
    main()