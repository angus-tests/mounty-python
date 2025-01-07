import logging

from tabulate import tabulate


class LogFacade:
    """
    A facade for logging operations, providing a consistent interface for logging messages
    Note: we use stacklevel=2 to ensure the correct file and line number are logged, otherwise the log will point to the
    LogFacade method that called the logger method.
    """
    _loggers = {
        "application": logging.getLogger(__name__),
    }

    @staticmethod
    def configure_logger(level=logging.INFO):
        """
        Set up a basic logging configuration with a consistent format and default level.
        """

        # Set up a formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%d-%m-%Y %H:%M:%S",
        )

        # Set up a handler for the application logger
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        # Set the level and add the handler to the application logger
        app_logger = LogFacade._loggers["application"]
        app_logger.setLevel(level)
        app_logger.addHandler(handler)

    @staticmethod
    def info(message: any, logger: str = "application"):
        """Log an INFO level message."""
        LogFacade._get_logger(logger).info(message, stacklevel=2)

    @staticmethod
    def log(level, message: any, logger: str = "application"):
        """Log an INFO level message."""
        LogFacade._get_logger(logger).log(level, message, stacklevel=2)

    @staticmethod
    def warning(message: any, logger: str = "application"):
        """Log a WARNING level message."""
        LogFacade._get_logger(logger).warning(message, stacklevel=2)

    @staticmethod
    def error(message: any, logger: str = "application"):
        """Log an ERROR level message."""
        LogFacade._get_logger(logger).error(message, stacklevel=2)

    @staticmethod
    def debug(message: any, logger: str = "application"):
        """Log a DEBUG level message."""
        LogFacade._get_logger(logger).debug(message, stacklevel=2)

    @staticmethod
    def critical(message: any, logger: str = "application"):
        """Log a CRITICAL level message."""
        LogFacade._get_logger(logger).critical(message, stacklevel=2)

    @staticmethod
    def _get_logger(logger_name: str) -> logging.Logger:
        """
        Retrieve a logger by name.

        Args:
            logger_name (str): The name of the logger (e.g., 'application', 'uvicorn').

        Returns:
            logging.Logger: The logger instance.

        Raises:
            KeyError: If the logger name is invalid.
        """
        if logger_name not in LogFacade._loggers:
            raise KeyError(
                f"Logger '{logger_name}' not found. Available loggers: {list(LogFacade._loggers.keys())}"
            )
        return LogFacade._loggers[logger_name]

    @staticmethod
    def log_mounts(level, title: str, message: str, items: list[str]):
        """
        Function to log messages with configurable level, title, message, and content.

        :param level: Logging level (e.g., logging.INFO, logging.DEBUG, etc.)
        :param title: The title of the log message.
        :param message: The message to display in the header.
        :param items: The list of items to display in the log content.
        """
        # Format the header
        header = f"\n\n================== {title} ==================\n"
        header += "+-------------------------------------------+\n"
        header += f"| {message:<40} |\n"
        header += "+-------------------------------------------+\n"

        # Check if the items list is empty and set content accordingly
        if not items:
            content = f"| {'EMPTY':<40} |"
        else:
            content = "\n".join(f"- {item:<25} " for item in items)

        footer = "\n+-------------------------------------------\n+"

        # Combine header, content, and footer
        full_message = header + content + footer

        # Log the message with the specified level
        if level == logging.INFO:
            LogFacade.info(full_message)
        elif level == logging.DEBUG:
            logging.debug(full_message)
        elif level == logging.WARNING:
            LogFacade.warning(full_message)
        elif level == logging.ERROR:
            LogFacade.error(full_message)
        elif level == logging.CRITICAL:
            LogFacade.critical(full_message)
        else:
            LogFacade.log(level, full_message)

    @staticmethod
    def log_table(level, title: str, headers: list[str], table: list[list[str]]):

        # Format the table
        table_with_title = LogFacade.format_table(title, headers, table)

        # Log the table with the specified level
        LogFacade.log(level, table_with_title)

    @staticmethod
    def format_table(title: str, headers: list[str], table: list[list[str]]) -> str:
        formatted_table = tabulate(table, headers=headers, tablefmt="grid")

        # Add a title to the table
        return f"\n\n{title}\n{'=' * len(title)}\n{formatted_table}\n"

