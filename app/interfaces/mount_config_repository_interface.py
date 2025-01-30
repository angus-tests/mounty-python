from abc import ABC, abstractmethod

from app.models.mount import Mount


class MountConfigRepositoryInterface(ABC):
    """
    Interface for a mount config repository, which is responsible for
    storing persistent mount config / info e.g (FSTAB)
    """

    @abstractmethod
    def store_mount_information(self, mount: Mount):
        """Save this mount information to the the system"""
        pass

    @abstractmethod
    def remove_mount_information(self, mount_path: str):
        """Remove this mount information from the system"""
        pass

    @abstractmethod
    def get_all_system_mounts(self) -> list[Mount]:
        """Get all mount information from the system"""
        pass

    @abstractmethod
    def is_mounted(self, mount_path: str) -> bool:
        """Return True if the mount is currently mounted"""
        pass

    @abstractmethod
    def remove_mounts(self, mounts: list[Mount]):
        """
        Remove a list of mounts from the system
        """
        pass

    @abstractmethod
    def cleanup(self):
        """
        Cleanup the mount information from the system
        """
        pass
