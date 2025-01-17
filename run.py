import argparse
from app.main import main, unmount_all, cleanup

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the mount or unmount script.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Simulate the mount script execution without making changes."
    )
    parser.add_argument(
        "--unmount-all", action="store_true", help="Run the unmount_all function instead of the mount script."
    )
    parser.add_argument(
        "--cleanup", action="store_true", help="Cleanup the fstab file"
    )
    args = parser.parse_args()

    # Cleanup the fstab file
    if args.cleanup:
        cleanup()
    # Unmount all mounts
    elif args.unmount_all:
        unmount_all()
    else:
        main(args.dry_run)
