from app.facades.log_facade import LogFacade
from app.repositories.mount_repository import MountRepository
from app.services.mounting_service import MountingService
from app.util.config import ConfigManager
from app.util.message import MESSAGE


def main():
    """
    Script entry point
    """

    # Set up the logger facade
    LogFacade.configure_logger()

    # Print the welcome message
    LogFacade.info("Starting Mounty Python "+MESSAGE)

    # Initialize a config manager and load the configuration from the environment
    config_manager = ConfigManager()
    config_manager.load_from_env()
    LogFacade.info(config_manager)

    # Create a mount repository
    mount_repository = MountRepository(config_manager)

    # Pass the mount repository to the mounting service
    mounting_service = MountingService(mount_repository)

    # Run the mounting service
    mounting_service.run()


if __name__ == "__main__":
    main()
