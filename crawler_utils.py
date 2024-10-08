import logging
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import requests
from xml.etree import ElementTree
from crawler import DEFAULT_USER_AGENT


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
