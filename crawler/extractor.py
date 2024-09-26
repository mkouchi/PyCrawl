import logging
from newspaper import Article
import nltk

# Ensure necessary NLTK data is downloaded (Natural Language Toolkit library in Python)
nltk.download('punkt', quiet=True)

def extract_main_content(url):
    """
    Extracts the main textual content from a webpage using newspaper3k.

    Args:
        url (str): The URL of the webpage to extract content from.

    Returns:
        str: The extracted text content of the page.
    """
    try:
        article = Article(url)
        article.download()
        article.parse()
        # Optional: Perform NLP tasks
        # article.nlp()
        return article.text
    except Exception as e:
        logging.error(f"Failed to extract content from {url}: {e}")
        return ""
