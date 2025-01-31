import os
import shutil

from app.interfaces.file_sytem_repository_interface import FileSystemRepositoryInterface


class FileSystemRepository(FileSystemRepositoryInterface):

    def read_file(self, file_path: str) -> str:
        """
        Read the contents of a file
        """
        with open(file_path, "r") as f:
            return f.read()

    def write_file(self, file_path: str, content: str):
        """
        Write content to a file
        """
        with open(file_path, "w") as f:
            f.write(content)

    def remove_file(self, file_path: str):
        """
        Remove a file
        """
        os.remove(file_path)

    def file_exists(self, file_path: str) -> bool:
        """
        Return True if the file exists
        """
        return os.path.exists(file_path)

    def create_directory(self, directory_path: str):
        """
        Create a directory
        """
        os.makedirs(directory_path, exist_ok=True)

    def remove_directory(self, directory_path: str):
        """
        Remove a directory
        """
        shutil.rmtree(directory_path)

    def directory_exists(self, directory_path: str) -> bool:
        """
        Return True if the directory exists
        """
        return os.path.exists(directory_path)

    def directory_empty(self, directory_path: str) -> bool:
        """
        Return True if the directory is empty
        """
        if self.directory_exists(directory_path):
            return not os.listdir(directory_path)
        return True
