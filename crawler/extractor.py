import logging
from newspaper import Article
import nltk

# Ensure necessary NLTK data is downloaded (Natural Language Toolkit library in Python)
nltk.download('punkt_tab', quiet=True)

def extract_main_content(html_content, url):
    """
    Extracts the main textual content from a webpage using newspaper3k.

    Args:
        url (str): The URL of the webpage to extract content from.

    Returns:
        str: The extracted text content of the page.
    """
    try:
        article = Article(url)
        article.set_html(html_content)
        article.parse()
        """ For better performance, these fields should be extracted in a background job(service) for processing scraped data 
        article.title
        article.publish_date
        article.authors
        article.top_image
        article.movies
        # Optional: Perform NLP tasks
        article.nlp()
        article.keywords
        article.summary """
        return article.text
    except ImportError as ie:
        logging.error(f"extract_main_content, ImportError: {ie}: {ie}")
    except Exception as e:
        logging.error(f"Failed to extract content from {url}: {e}")
        return ""
    
def download_and_extract_main_content(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        logging.error(f"Failed to extract content from {url}: {e}")
        return ""
