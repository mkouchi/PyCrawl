import logging
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser
import requests
from xml.etree import ElementTree
from crawler import DEFAULT_USER_AGENT


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

def is_sitemap_index(content):
    """
    Determines if the given sitemap content is a sitemap index.

    Args:
        content (bytes): The content of the sitemap in bytes.

    Returns:
        bool: True if it's a sitemap index, False otherwise.
    """
    from xml.etree import ElementTree as ET

    try:
        root = ET.fromstring(content)
        return root.tag.endswith('sitemapindex')
    except ET.ParseError:
        return False

def parse_sitemap_index(sitemap_index_content):
    """
    Parses a sitemap index and returns a list of sitemap URLs.

    Args:
        sitemap_index_content (bytes): The content of the sitemap index.

    Returns:
        list: A list of sitemap URLs.
    """
    from xml.etree import ElementTree as ET

    sitemap_urls = []
    try:
        root = ET.fromstring(sitemap_index_content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        for sitemap in root.findall('ns:sitemap', namespaces=namespace):
            loc = sitemap.find('ns:loc', namespaces=namespace)
            if loc is not None and loc.text:
                sitemap_urls.append(loc.text.strip())
    except ET.ParseError as e:
        logging.error(f"Failed to parse sitemap index: {e}")
    return sitemap_urls

def parse_sitemap(sitemap_content):
    """
    Parses a sitemap and returns a list of URLs.

    Args:
        sitemap_content (bytes): The content of the sitemap.

    Returns:
        list: A list of URLs to crawl.
    """
    from xml.etree import ElementTree as ET

    urls = []
    try:
        root = ET.fromstring(sitemap_content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        for url in root.findall('ns:url', namespaces=namespace):
            loc = url.find('ns:loc', namespaces=namespace)
            if loc is not None and loc.text:
                urls.append(loc.text.strip())
    except ET.ParseError as e:
        logging.error(f"Failed to parse sitemap: {e}")
    return urls

def fetch_and_parse_sitemaps(sitemap_urls, user_agent, max_depth=3, current_depth=0):
    """
    Recursively fetches and parses sitemaps and sitemap indexes.

    Args:
        sitemap_urls (list): A list of sitemap URLs to process.
        user_agent (str): The user agent string of your crawler.
        max_depth (int): The maximum depth to recurse when parsing sitemap indexes.
        current_depth (int): The current recursion depth.

    Returns:
        set: A set of URLs to crawl.
    """
    urls_to_crawl = set()
    if current_depth > max_depth:
        return urls_to_crawl

    for sitemap_url in sitemap_urls:
        try:
            response = requests.get(sitemap_url, headers={'User-Agent': user_agent}, timeout=10)
            response.raise_for_status()
            content = response.content

            if is_sitemap_index(content):
                logging.info(f"Found sitemap index: {sitemap_url}")
                # Parse sitemap index to get more sitemap URLs
                new_sitemap_urls = parse_sitemap_index(content)
                urls_to_crawl.update(fetch_and_parse_sitemaps(
                    new_sitemap_urls, user_agent, max_depth, current_depth + 1))
            else:
                logging.info(f"Parsing sitemap: {sitemap_url}")
                # Parse sitemap to get URLs
                urls = parse_sitemap(content)
                urls_to_crawl.update(urls)
        except requests.RequestException as e:
            logging.error(f"Failed to fetch sitemap {sitemap_url}: {e}")

    return urls_to_crawl
"""  
# old
def is_allowed(url, user_agent=DEFAULT_USER_AGENT):
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    robots_url = urljoin(base_url, '/robots.txt')
    rp = RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except:
        # If robots.txt cannot be fetched, assume allowed
        return True

def is_allowed(url, user_agent=DEFAULT_USER_AGENT):

    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    robots_url = urljoin(base_url, '/robots.txt')

    try:
        response = requests.get(robots_url, headers={'User-Agent': user_agent}, timeout=10)
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '')

        if 'text/plain' in content_type or 'text/plain' in response.headers.get('Content-Disposition', ''):
            # Assume it's a robots.txt file
            rp = RobotFileParser()
            rp.parse(response.text.splitlines())
            return rp.can_fetch(user_agent, url)
        elif 'application/xml' in content_type or 'text/xml' in content_type:
            # Assume it's an XML sitemap
            logging.info(f"Found XML sitemap at {robots_url}")
            # Optionally, parse the sitemap to get allowed URLs
            return True
        else:
            # Unknown content type, proceed cautiously
            logging.warning(f"Unknown content type at {robots_url}: {content_type}")
            return True
    except Exception as e:
        logging.warning(f"Could not read robots.txt for {base_url}: {e}")
        # If robots.txt cannot be fetched, proceed cautiously
        return True


def get_sitemap_urls(base_url, user_agent='*'):
    
    standard_sitemap_url = urljoin(base_url, '/sitemap.xml')
    urls = parse_sitemap(standard_sitemap_url)

    if len(urls) != 0:
        return urls
    else:
        # check other possibilites
        robots_url = urljoin(base_url, '/robots.txt')
        sitemap_urls = []

        try:
            response = requests.get(robots_url, headers={'User-Agent': user_agent}, timeout=10)
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '')

            if 'application/xml' in content_type or 'text/xml' in content_type:
                # The robots.txt URL is actually a sitemap
                sitemap_urls.append(robots_url)
            else:
                # Parse robots.txt to find Sitemap directives
                lines = response.text.splitlines()
                for line in lines:
                    if line.strip().lower().startswith('sitemap:'):
                        sitemap_url = line.split(':', 1)[1].strip()
                        sitemap_urls.append(sitemap_url)
        except Exception as e:
            logging.warning(f"Could not read robots.txt for {base_url}: {e}")

        return sitemap_urls

def parse_sitemap_index(sitemap_index_url):
    import requests
    from xml.etree import ElementTree

    try:
        response = requests.get(sitemap_index_url)
        response.raise_for_status()
        root = ElementTree.fromstring(response.content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        sitemap_urls = [elem.text for elem in root.findall('.//ns:sitemap/ns:loc', namespaces=namespace)]
        return sitemap_urls
    except Exception as e:
        logging.error(f"Failed to parse sitemap index {sitemap_index_url}: {e}")
        return []

def parse_sitemap(sitemap_url):
    import requests
    from xml.etree import ElementTree

    try:
        response = requests.get(sitemap_url, timeout=10)
        response.raise_for_status()
        root = ElementTree.fromstring(response.content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [elem.text for elem in root.findall('.//ns:url/ns:loc', namespaces=namespace)]
        return urls
    except Exception as e:
        logging.error(f"Failed to parse sitemap {sitemap_url}: {e}")
        return []
"""