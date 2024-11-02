from crawler.utils import setup_logging, create_directories, get_timestamp, save_json
import logging
import signal

# Signal handler for graceful exit on Ctrl+C
def signal_handler(sig, frame):
    print("\n\nCtrl+C detected. Stopping the crawl process...")
    logging.info(f"Total documents scraped: {len(articles_content)}")
    save_json(articles_content, start_url=start_url)
    exit(0)

# Register the signal handler for Ctrl+C (SIGINT)
signal.signal(signal.SIGINT, signal_handler)

def main():
    # setup logging
    setup_logging()

    # Create necessary directories
    create_directories()

    # Get current timestamp
    timestamp = get_timestamp()



if __name__ == "__main__":
    main()