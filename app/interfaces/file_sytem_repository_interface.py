from abc import ABC, abstractmethod


class FileSystemRepositoryInterface(ABC):

    @abstractmethod
    def read_file(self, file_path: str) -> str:
        """Read the contents of a file"""
        pass

    @abstractmethod
    def write_file(self, file_path: str, content: str):
        """Write content to a file"""
        pass

    @abstractmethod
    def remove_file(self, file_path: str):
        """Remove a file"""
        pass

    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """Return True if the file exists"""
        pass

    @abstractmethod
    def create_directory(self, directory_path: str):
        """Create a directory"""
        pass

    @abstractmethod
    def remove_directory(self, directory_path: str):
        """Remove a directory"""
        pass

    @abstractmethod
    def directory_exists(self, directory_path: str) -> bool:
        """Return True if the directory exists"""
        pass

    @abstractmethod
    def directory_empty(self, directory_path: str) -> bool:
        """Return True if the directory is empty"""
        pass
