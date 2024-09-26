import logging
import os
from crawler.config import LOG_FILE, LOG_LEVEL, LOG_FORMAT, LOG_DATE_FORMAT

def setup_logging():
    """
    Sets up the logging configuration for the crawler.
    """
    logging.basicConfig(
        filename=LOG_FILE,
        filemode='a',
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    )
    # Also log to console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    console_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logging.getLogger('').addHandler(console_handler)

def create_directories():
    """
    Creates necessary directories if they do not exist.
    """
    from crawler.config import LOG_DIR, OUTPUT_DIR, DATA_DIR

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
    import json
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)

def save_json(data, filepath):
    """
    Saves data as JSON to a file.

    Args:
        data (dict): The data to save.
        filepath (str): The path to the file where data will be saved.
    """
    import json
    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def get_timestamp():
    """
    Returns the current timestamp as a string.

    Returns:
        str: The current timestamp in YYYYMMDD_HHMMSS format.
    """
    from datetime import datetime
    return datetime.now().strftime('%Y%m%d_%H%M%S')
