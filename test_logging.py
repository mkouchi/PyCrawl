# crawler/test_logging.py

from crawler_utils import setup_logging
import logging

def main():
    setup_logging()
    logging.debug("This is a DEBUG message.")
    logging.info("This is an INFO message.")
    logging.warning("This is a WARNING message.")
    logging.error("This is an ERROR message.")
    logging.critical("This is a CRITICAL message.")

if __name__ == "__main__":
    main()
