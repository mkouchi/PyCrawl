from crawler.utils import setup_logging, create_directories, get_timestamp

def main():
    # setup logging
    setup_logging()

    # Create necessary directories
    create_directories()

    # Get current timestamp
    timestamp = get_timestamp()



if __name__ == "__main__":
    main()