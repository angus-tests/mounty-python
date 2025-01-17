from typing import Callable

from app.facades.log_facade import LogFacade
from app.repositories.file_sytem_repository import FileSystemRepository
from app.repositories.mount_config_repository import FstabRepository
from app.repositories.mount_repository import MountRepository
from app.services.mounting_service import MountingService
from app.services.validation_service import ValidationService
from app.util.config import ConfigManager
from app.util.message import MESSAGE, DRY_RUN, CLEANUP, UNMOUNT_ALL


def _setup_logger():
    """
    Set up the logger facade
    """
    LogFacade.configure_logger()


def _setup_config() -> ConfigManager:
    """
    Set up the logger and load the configuration.
    """

    # Initialize a config manager and load the configuration from the environment
    config_manager = ConfigManager()
    config_manager.load_from_env()
    LogFacade.info(config_manager)

    return config_manager


def _get_mounting_service(config_manager):
    """
    Create and return a MountingService instance.
    """

    # File system repository that interacts with the file system
    file_system_repository = FileSystemRepository()

    # Fstab repository that interacts with the fstab file
    fstab_repository = FstabRepository(config_manager, file_system_repository)

    # Mount repository that interacts with the mounts
    mount_repository = MountRepository(config_manager, fstab_repository, file_system_repository)

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


def _run(message: str, config_manager: ConfigManager, callback: Callable):

    _setup_logger()

    # Setup a validation service
    validation_service = ValidationService(config_manager, FileSystemRepository())

    # Print the welcome message
    LogFacade.info(message)

    # Run the validation service
    status = validation_service.validate()

    # Exit if the validation failed
    if not status:
        LogFacade.error("Validation failed. Exiting...")
        exit(1)

    # Run the callback
    status = callback()
    _handle_status(status, "Operation completed successfully", "Operation failed")


def main(dry_run=False):
    """
    Script entry point
    """
    message = "Starting Mounty Python [DRY RUN] " + MESSAGE + DRY_RUN if dry_run else "Starting Mounty Python " + MESSAGE

    config_manager = _setup_config()
    mounting_service = _get_mounting_service(config_manager)
    callback = mounting_service.dry_run if dry_run else mounting_service.run

    _run(message, config_manager, callback)


def unmount_all():
    """
    Unmount all mounts from the system (not system mounts).
    """

    message = "Starting Mounty Python (REMOVE ALL MOUNTS) " + MESSAGE + UNMOUNT_ALL

    config_manager = _setup_config()
    mounting_service = _get_mounting_service(config_manager)

    _run(message, config_manager, mounting_service.unmount_all)


def cleanup():
    """
    Cleanup the fstab file.
    """

    message = "Starting Mounty Python [CLEANUP] " + MESSAGE + CLEANUP

    config_manager = _setup_config()
    mounting_service = _get_mounting_service(config_manager)

    _run(message, config_manager, mounting_service.cleanup)


if __name__ == "__main__":
    main()
