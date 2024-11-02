import os

DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
# Custom headers including a User-Agent
headers = {
    'User-Agent': DEFAULT_USER_AGENT
}

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOG_DIR = os.path.join(DATA_DIR, 'logs')
OUTPUT_DIR = os.path.join(DATA_DIR, 'output')

# Log file settings
LOG_FILE = os.path.join(LOG_DIR, 'scraper.log')
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

MAX_RETRIES = 5
TIMEOUT = 15
MIN_DELAY = 2 
MAX_DELAY = 30

MAX_CRAWL_COUNT=30
