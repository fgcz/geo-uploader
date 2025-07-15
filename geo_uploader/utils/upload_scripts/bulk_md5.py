import argparse
import sys

# Import our utility functions
from .utils import (
    ConfigParser,
    initialize_tsv,
    notify_server,
    setup_logger,
    write_to_tsv,
)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Calculate MD5 checksums for files listed in an INI file"
    )
    parser.add_argument(
        "-c", "--config", required=True, help="Path to the INI configuration file"
    )
    parser.add_argument(
        "-o", "--output", required=True, help="Path to the output TSV file"
    )
    parser.add_argument("-l", "--log", help="Path to the log file")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--raw-only", action="store_true", help="Process only raw files"
    )
    parser.add_argument(
        "--processed-only", action="store_true", help="Process only processed files"
    )
    parser.add_argument(
        "-s", "--sample", help="Process only files for the specified sample ID"
    )
    parser.add_argument(
        "--notify", action="store_true", help="Notify the server when done"
    )
    return parser.parse_args()


def process_samples(
    config_parser,
    tsv_file_path,
    logger,
    raw_only=False,
    processed_only=False,
    sample_filter=None,
):
    """Process all samples and calculate MD5 checksums."""
    # Get all sample sections
    sample_sections = config_parser.get_sample_sections(sample_filter)

    if not sample_sections:
        logger.warning(
            f"No sample sections found{' for sample ' + sample_filter if sample_filter else ''}"
        )
        return False

    total_files = 0
    successful_files = 0

    # Process each sample
    for sample_section in sample_sections:
        sample_id = sample_section.split(".")[1]
        logger.info(f"Processing sample {sample_id}")

        # Get all files for this sample
        files = config_parser.get_sample_files(
            sample_section, raw_only=raw_only, processed_only=processed_only
        )

        total_files += len(files)

        # Process each file
        for file_info in files:
            if write_to_tsv(tsv_file_path, file_info, logger):
                successful_files += 1

    # Log summary
    logger.info(f"Processed {total_files} files, {successful_files} successful")
    return successful_files > 0


def main():
    """Main entry point for the script."""
    # Parse command line arguments
    args = parse_args()

    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger("bulk_md5", args.log, log_level)

    logger.info("=== Starting calculation of MD5 checksums ===")
    logger.info(f"Using configuration file: {args.config}")

    # Parse the INI file
    config_parser = ConfigParser(args.config, logger)
    if not config_parser.config:
        logger.error("Failed to parse configuration file. Exiting.")
        sys.exit(1)

    # Initialize the output TSV file
    tsv_file_path = args.output.strip()
    if not initialize_tsv(tsv_file_path, logger):
        logger.error("Failed to initialize output file. Exiting.")
        sys.exit(1)

    # Process the samples
    success = process_samples(
        config_parser,
        tsv_file_path,
        logger,
        raw_only=args.raw_only,
        processed_only=args.processed_only,
        sample_filter=args.sample,
    )

    # Notify the server if requested
    if args.notify and success:
        logger.info("Notifying server of completion")
        notify_config = config_parser.get_server_notification_config()
        if notify_config:
            if notify_server(notify_config, "md5", logger):
                logger.info("Server notification successful")
            else:
                logger.error("Server notification failed")
                sys.exit(1)
        else:
            logger.error("Missing server notification configuration")
            sys.exit(1)

    if not success:
        logger.error("No files were processed successfully")
        sys.exit(1)

    logger.info("=== MD5 calculation completed successfully ===")
    sys.exit(0)


if __name__ == "__main__":
    import logging

    main()
