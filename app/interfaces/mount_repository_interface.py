from abc import ABC, abstractmethod

from app.models.mount import Mount


class MountRepositoryInterface(ABC):
    """
    Interface for a mount repository, which is responsible for
    providing the application with mounts to work with
    """

    @abstractmethod
    def get_desired_mounts(self) -> list[Mount]:
        """Fetch a list of mounts we want on the system"""
        pass

    @abstractmethod
    def get_current_mounts(self) -> list[Mount]:
        """Fetch a list of mounts currently on the system"""
        pass

    @abstractmethod
    def get_orphan_mounts(self) -> list[Mount]:
        """Fetch a list of mounts that are not present in config but are mounted on the system"""
        pass

    @abstractmethod
    def mount(self, mount: Mount):
        """
        mount a mount to the system
        :param mount: the mount to mount on the system
        """
        pass

    @abstractmethod
    def unmount(self, mount_path: str):
        """
        unmount a mount from the system
        :param mount_path: the path of the mount to unmount on the system
        """
        pass

    @abstractmethod
    def unmount_all(self) -> list[Mount]:
        """
        unmount all mounts from the system
        :return A list of mounts that failed to unmount
        """
        pass

    def cleanup(self):
        """
        Cleanup the system
        """
