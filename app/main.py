from app.facades.log_facade import LogFacade
from app.repositories.mount_config_repository import FstabRepository
from app.repositories.mount_repository import MountRepository
from app.services.mounting_service import MountingService
from app.util.config import ConfigManager
from app.util.message import MESSAGE, DRY_RUN, CLEANUP


def main(dry_run=False):
    """
    Script entry point
    """

    # Set up the logger facade
    LogFacade.configure_logger()

    # Print the welcome message
    if dry_run:
        LogFacade.info("Starting Mounty Python [DRY RUN] " + MESSAGE + DRY_RUN)
    else:
        LogFacade.info("Starting Mounty Python " + MESSAGE)

    # Initialize a config manager and load the configuration from the environment
    config_manager = ConfigManager()
    config_manager.load_from_env()
    LogFacade.info(config_manager)

    # Create a mount repository and use an Fstab repo for mounting config
    mount_repository = MountRepository(config_manager, FstabRepository(config_manager))

    # Pass the mount repository to the mounting service
    mounting_service = MountingService(mount_repository)

    # Run the mounting service
    if dry_run:
        status = mounting_service.dry_run()
    else:
        status = mounting_service.run()

    # Return an exit code
    if status:
        LogFacade.info("Mounting service completed successfully")
        exit(0)
    else:
        LogFacade.error("Mounting service failed")
        exit(1)


def unmount_all():
    """
    Another entry point to unmount
    all mounts from the system (not system mounts)
    """

    # Set up the logger facade
    LogFacade.configure_logger()

    # Print the welcome message
    LogFacade.info("Starting Mounty Python (REMOVE ALL MOUNTS) "+MESSAGE)

    # Initialize a config manager and load the configuration from the environment
    config_manager = ConfigManager()
    config_manager.load_from_env()
    LogFacade.info(config_manager)

    # Create a mount repository and use an Fstab repo for mounting config
    mount_repository = MountRepository(config_manager, FstabRepository(config_manager))

    # Pass the mount repository to the mounting service
    mounting_service = MountingService(mount_repository)

    # Run the mounting service
    status = mounting_service.unmount_all()

    # Return an exit code
    if status:
        LogFacade.info("Unmounted all mounts successfully")
        exit(0)
    else:
        LogFacade.error("Failed to remove all mounts")
        exit(1)


def cleanup():
    """
    Cleanup the fstab file
    """

    # Set up the logger facade
    LogFacade.configure_logger()

    # Print the welcome message
    LogFacade.info("Starting Mounty Python [CLEANUP] " + MESSAGE + CLEANUP)

    # Initialize a config manager and load the configuration from the environment
    config_manager = ConfigManager()
    config_manager.load_from_env()
    LogFacade.info(config_manager)

    # Create a mount repository and use an Fstab repo for mounting config
    mount_repository = MountRepository(config_manager, FstabRepository(config_manager))

    # Pass the mount repository to the mounting service
    mounting_service = MountingService(mount_repository)

    # Run the mounting service
    status = mounting_service.cleanup()

    # Return an exit code
    if status:
        LogFacade.info("Cleanup run successfully")
        exit(0)
    else:
        LogFacade.error("Failed running cleanup")
        exit(1)


if __name__ == "__main__":
    main()
