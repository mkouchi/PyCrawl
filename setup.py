from setuptools import setup, find_packages
import nltk

nltk.download('punkt', quiet=True)

setup(
    name='PyCrawl',
    version='0.1.0',
    description='A python web crawler for scraping websites',
    author='M.Kouchi',
    author_email='kouchi.mohammad@gmail.com',
    url='https://github.com/mkouchi/PyCrawl',
    packages=find_packages(),
    install_requires=[
        'requests',
        'beautifulsoup4',
        'newspaper3k',
        'lxml',
        'nltk',
    ],
    entry_points={
        'console_scripts': [
            'PyCrawl=crawler.main:main',
        ],
    },
)
