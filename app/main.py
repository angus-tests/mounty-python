from app.facades.log_facade import LogFacade
from app.repositories.mount_config_repository import FstabRepository
from app.repositories.mount_repository import MountRepository
from app.services.mounting_service import MountingService
from app.util.config import ConfigManager
from app.util.message import MESSAGE, DRY_RUN, CLEANUP


def _setup_logger_and_config():
    """
    Set up the logger and load the configuration.
    """
    # Set up the logger facade
    LogFacade.configure_logger()

    # Initialize a config manager and load the configuration from the environment
    config_manager = ConfigManager()
    config_manager.load_from_env()
    LogFacade.info(config_manager)

    return config_manager


def _get_mounting_service(config_manager):
    """
    Create and return a MountingService instance.
    """
    mount_repository = MountRepository(config_manager, FstabRepository(config_manager))
    return MountingService(mount_repository)


def _handle_status(status, success_message, failure_message):
    """
    Handle the status of a service operation and exit with the appropriate code.
    """
    if status:
        LogFacade.info(success_message)
        exit(0)
    else:
        LogFacade.error(failure_message)
        exit(1)


def main(dry_run=False):
    """
    Script entry point
    """
    config_manager = _setup_logger_and_config()
    mounting_service = _get_mounting_service(config_manager)

    # Print the welcome message
    message = "Starting Mounty Python [DRY RUN] " + MESSAGE + DRY_RUN if dry_run else "Starting Mounty Python " + MESSAGE
    LogFacade.info(message)

    # Run the mounting service
    status = mounting_service.dry_run() if dry_run else mounting_service.run()
    _handle_status(status, "Mounting service completed successfully", "Mounting service failed")


def unmount_all():
    """
    Unmount all mounts from the system (not system mounts).
    """
    config_manager = _setup_logger_and_config()
    mounting_service = _get_mounting_service(config_manager)

    # Print the welcome message
    LogFacade.info("Starting Mounty Python (REMOVE ALL MOUNTS) " + MESSAGE)

    # Run the unmounting service
    status = mounting_service.unmount_all()
    _handle_status(status, "Unmounted all mounts successfully", "Failed to remove all mounts")


def cleanup():
    """
    Cleanup the fstab file.
    """
    config_manager = _setup_logger_and_config()
    mounting_service = _get_mounting_service(config_manager)

    # Print the welcome message
    LogFacade.info("Starting Mounty Python [CLEANUP] " + MESSAGE + CLEANUP)

    # Run the cleanup service
    status = mounting_service.cleanup()
    _handle_status(status, "Cleanup run successfully", "Failed running cleanup")


if __name__ == "__main__":
    main()
