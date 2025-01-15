import argparse
from app.main import main, unmount_all

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the mount or unmount script.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Simulate the mount script execution without making changes."
    )
    parser.add_argument(
        "--unmount-all", action="store_true", help="Run the unmount_all function instead of the mount script."
    )
    args = parser.parse_args()

    if args.unmount_all:
        unmount_all()
    else:
        main(args.dry_run)
