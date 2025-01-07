from app.facades.log_facade import LogFacade
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

    #


if __name__ == "__main__":
    main()
