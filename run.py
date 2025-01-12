import argparse

from app.main import main

# Run the main script

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the mount script.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate script execution without making changes.")
    args = parser.parse_args()
    main(args.dry_run)
