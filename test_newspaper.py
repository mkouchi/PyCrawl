# test_newspaper.py

from newspaper import Article

def test_article(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        print(f"Article successfully parsed. text: {article.text}")
    except ImportError as ie:
        print(f"ImportError: {ie}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_article("https://www.hra-news.org/2024/hranews/a-50986/")
