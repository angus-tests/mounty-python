from abc import ABC, abstractmethod

from pyfstab import Fstab

from app.enums.enums import MountType
from app.models.mount import Mount


class MountRepositoryInterface(ABC):
    """
    Interface for a mount repository, which is responsible for
    providing the application with mounts to work with
    """

    @abstractmethod
    def get_mounts(self) -> list[Mount]:
        """Fetch a list of mounts to work with"""
        pass

    @abstractmethod
    def mount(self, mount: Mount):
        """mount a mount to the system"""
        pass

    @abstractmethod
    def unmount(self, mount: Mount):
        """unmount a mount from the system"""
        pass


class MountRepository(MountRepositoryInterface):
    """
    Concrete implementation of a mount repository
    """

    def __init__(self, config_manager):
        self.config_manager = config_manager

    def get_mounts(self) -> list[Mount]:
        """
        Open the fstab file and read in all the mounts
        that match our regex.

        We currently juts look for mounts that start with /shares
        as we know these are the ones we control (not system or root mounts)
        """

        fstab_location = self.config_manager.get_config("FSTAB_LOCATION")

        # Read the file
        with open(fstab_location, "r") as f:
            fstab = Fstab().read_file(f)

        # Get the mounts that start with /shares
        return [
            Mount(entry.dir, entry.device, MountType.from_str(entry.type))  # TODO test this
            for entry in fstab.entries
            if entry.dir.startswith("/shares")
        ]

    def mount(self, mount: Mount):
        # TODO implement
        pass

    def unmount(self, mount: Mount):
        # TODO implement
        pass


