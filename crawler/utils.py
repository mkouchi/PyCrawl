import logging
import json
import os
from urllib.parse import quote, urlparse
from config import LOG_FILE, LOG_LEVEL, LOG_FORMAT, LOG_DATE_FORMAT, OUTPUT_DIR

DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
# Custom headers including a User-Agent
headers = {
    'User-Agent': DEFAULT_USER_AGENT
}

def get_scraped_filename(start_url):
    parsed_start_url = urlparse(start_url)
    filename = f"{parsed_start_url.netloc}_scraped_data.json"
    return filename

def setup_logging():
    """
    Sets up the logging configuration for the crawler.
    Logs to both a file and the console.
    """
    # Create log directory if it doesn't exist
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create a custom logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    
    # Prevent adding multiple handlers if setup_logging is called multiple times
    if not logger.handlers:
        # File handler
        file_handler = logging.FileHandler(LOG_FILE, mode='a')
        file_handler.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
        file_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
        console_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

def create_directories():
    """
    Creates necessary directories if they do not exist.
    """
    from config import LOG_DIR, OUTPUT_DIR, DATA_DIR

    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

def sanitize_filename(filename):
    """
    Sanitizes a string to be used as a safe filename.

    Args:
        filename (str): The original filename.

    Returns:
        str: A sanitized filename.
    """
    import re
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def save_content_to_file(content, filepath):
    """
    Saves the given content to a file at the specified filepath.

    Args:
        content (str): The content to save.
        filepath (str): The path to the file where content will be saved.
    """
    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(content)

def load_json(filepath):
    """
    Loads JSON data from a file.

    Args:
        filepath (str): The path to the JSON file.

    Returns:
        dict: The loaded JSON data.
    """
    
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)


def save_json(data, start_url):
    """
    Saves the given data to a JSON file at the specified filepath.
    
    Args:
        data (dict or list): The data to save.
        filepath (str): The path to the file where data will be saved.
    """
    filename = get_scraped_filename(start_url)
    # Ensure the parent directories exist
    filepath = os.path.join(OUTPUT_DIR, filename)
    parent_dir = os.path.dirname(filepath)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    logging.info(f"Scraped data has been saved to {filename}")

def get_timestamp():
    """
    Returns the current timestamp as a string.

    Returns:
        str: The current timestamp in YYYYMMDD_HHMMSS format.
    """
    from datetime import datetime
    return datetime.now().strftime('%Y%m%d_%H%M%S')

def is_persian_character(char):  
    """Check if the character is a Persian character."""  
    return '\u0600' <= char <= '\u06FF' 

def convert_persian_url(url):  
    """Convert a URL containing Persian characters to a valid URL."""  
    logging.info(f"Converting url containing Persian characters to a valid URL")
    # It replaces spaces with %20 and other non-ASCII characters with their corresponding percent-encoded values.
    encoded_url = quote(url, safe='/')  # Encode, keeping '/' unencoded  
    return encoded_url 

def print_crawled_urls(articles):
    # Print all visited URLs at the end
    print("\nCrawled URLs:")
    for idx, url in enumerate(articles):
        print(f"{idx + 1}: {url}")

def print_crawled_contents(articles):

    # Print or process the collected articles' content
    for idx, article in enumerate(articles):
        print(f"Article {idx + 1}: {article['url']}\n")
        print(article['content'])
        print("\n" + "="*80 + "\n")
