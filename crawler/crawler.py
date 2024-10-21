import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from newspaper import Article
import nltk
import time
import signal
import logging
from crawler_utils import save_json, setup_logging, fetch_and_parse_robots_txt, fetch_and_parse_sitemaps, DEFAULT_USER_AGENT, headers

# Ensure NLTK's 'punkt' tokenizer is downloaded
# nltk.download('punkt', quiet=True)

start_url =   "https://www.hra-news.org/"# "https://www.radiozamaneh.com/" # "https://news.bahai.org/""https://universalhouseofjustice.bahai.org/" # "https://www.bahaisofiran.org/" # "https://news.persian-bahai.org/" #  "https://www.bahaisofiran.org/" "https://universalhouseofjustice.bahai.org/" # "https://bahaiworld.bahai.org/" # "https://www.bahaisofiran.org/" # "https://news.persian-bahai.org/" #  #  # "https://news.bahai.org/fa/"

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

MAX_CRAWL_COUNT = -1  # Set the limit for the number of URLs to crawl if = -1 don't set max
crawl_count = 0
visited = set()  # Keep track of visited URLs
articles_content = []  # Store crawled articles' content
delay = 1 # Initial delay in seconds

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
    logging.info(f"Total documents scraped: {len(articles_content)}")
    save_json(articles_content, start_url=start_url)
    exit(0)

# Register the signal handler for Ctrl+C (SIGINT)
signal.signal(signal.SIGINT, signal_handler)

def download_and_extract_main_content(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        logging.error(f"Failed to extract content from {url}: {e}")
        return ""
    
def extract_main_content(html_content, url):
    try:
        article = Article(url)
        article.set_html(html_content)
        article.parse()
        return article.text
    except Exception as e:
        logging.error(f"Failed to extract content from {url}: {e}")
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
        if link not in visited:
            article_links.append(link)
        
    
    return article_links

def crawl_website(start_url, depth, max_depth, headers, delay=1, robots_parser=None):
    global crawl_count


    def crawl(url, current_depth):
        global crawl_count

        # Stop crawling if the counter has reached the maximum allowed crawls
        if current_depth > max_depth or url in visited or (crawl_count >= MAX_CRAWL_COUNT and MAX_CRAWL_COUNT != -1):
            return
        
        if robots_parser and not robots_parser.can_fetch(DEFAULT_USER_AGENT, url):
            logging.info(f"Skipping {url} due to robots.txt restrictions.")
            return
    
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

            page_text = extract_main_content(html_content, url)
            if not page_text:
                logging.warning(f"No content extracted from {url}.")
                return
            
            if page_text:
                articles_content.append({'url': url, 'content': page_text})
            
            # Find links to other articles and crawl them
            links = find_article_links(url)
            for link in links:
                logging.info(f"Waiting for {delay} seconds before scraping {link}")
                time.sleep(delay)
                if crawl_count < MAX_CRAWL_COUNT:
                    crawl(link, current_depth + 1)
        except Exception as e:
            logging.error(f"Failed to retrieve {url}: {e}")
            return
            
    
    # Start crawling from the start URL
    crawl(start_url, depth)
    
    # After finishing the crawl, print all crawled URLs
    # print_crawled_contents()

def scrape_url(url, headers, delay):
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

class Document:  
    def __init__(self, content, url):  
        self.content = content  
        self.url = url

def main():
    global crawl_count
    # Starting URL and depth for the crawler
    
    max_depth = 3  # Adjust the depth as needed
    setup_logging()

    parsed_start_url = urlparse(start_url)
    base_url = f"{parsed_start_url.scheme}://{parsed_start_url.netloc}"

    logging.info(f"Starting to crawl {base_url}")

    # Fetch and parse robots.txt
    rp, sitemap_urls = fetch_and_parse_robots_txt(base_url, DEFAULT_USER_AGENT)

    if not sitemap_urls:
        # If no sitemap URLs found, you might decide to proceed with recursive crawling
        logging.info(f"No sitemap URLs found for {base_url}. Proceeding with recursive crawling.")
        crawl_website(start_url, 0, max_depth, headers, delay, rp)
        return

    # Fetch and parse sitemaps to get URLs to crawl
    urls_to_crawl = fetch_and_parse_sitemaps(sitemap_urls, DEFAULT_USER_AGENT)

    # Crawl the URLs
    for url in urls_to_crawl:
        # Check if URL is allowed by robots.txt
        if rp is None or rp.can_fetch(DEFAULT_USER_AGENT, url) and (crawl_count <= MAX_CRAWL_COUNT or MAX_CRAWL_COUNT == -1):
            doc = scrape_url(url, headers, delay)
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