import json
from abc import ABC, abstractmethod

from pyfstab import Fstab, Entry

from app.enums.enums import MountType
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
    def unmount_all(self):
        """
        unmount all mounts from the system
        """
        pass


class MountRepository(MountRepositoryInterface):
    """
    Concrete implementation of a mount repository
    """

    def __init__(self, config_manager, mount_prefix="/shares"):
        self.config_manager = config_manager
        self.mount_prefix = mount_prefix

    def get_current_mounts(self) -> list[Mount]:
        """
        Open the fstab file and read in all the mounts
        that match our regex.

        We currently juts look for mounts that start with our mount prefix
        as we know these are the ones we control (not system or root mounts)
        """

        fstab_location = self.config_manager.get_config("FSTAB_LOCATION")

        # Read the file
        with open(fstab_location, "r") as f:
            fstab = Fstab().read_file(f)

        # Get the mounts that start with the mount prefix
        return [
            Mount(entry.dir, entry.device, MountType.from_str(entry.type))
            for entry in fstab.entries
            if entry.dir.startswith(self.mount_prefix)
        ]

    def get_desired_mounts(self) -> list[Mount]:
        """
        Read in the mounts from the specified json file
        """
        with open(self.config_manager.get_config("DESIRED_MOUNTS_FILE"), "r") as f:
            mounts_data = json.load(f)

        mounts = [
            Mount(
                mount["mount_path"],
                mount["actual_path"],
                MountType.from_str(mount["mount_type"]),
            )
            for mount in mounts_data
        ]

        return mounts

    def mount(self, mount: Mount):
        # TODO implement
        pass

    def unmount(self, mount_path: str):
        # TODO implement
        pass

    def unmount_all(self):
        """
        Unmount all mounts from the system
        that start with our mount prefix and keep the rest
        """

        fstab_location = self.config_manager.get_config("FSTAB_LOCATION")

        # Read the file
        with open(fstab_location, "r") as f:
            fstab = Fstab().read_file(f)

        # Unmount all mounts that start with the mount prefix and keep the rest
        fstab_entries = []
        for entry in fstab.entries:
            if entry.dir.startswith(self.mount_prefix):
                self.unmount(entry.dir)
            else:
                fstab_entries.append(entry)

        # Write our new fstab file
        formatted = str(fstab)
        with open(fstab_location, "w") as f:
            f.write(formatted)

    def _make_mount_permanent(
        self, local_dir, actual_dir, mount_type, options="auto", dump=0, fsck=0
    ):
        """
         This function will add a new line to the fstab file to ensure
         the mount will persist on the VM
        :param local_dir: Mount point on local machine. eg. /shares/mymount
        :param actual_dir: The Mount point on another machine. eg. //servername/folder
        :param mount_type: Type of mount this is, cifs, sshfs etc
        :param options: String of options
        :param dump: Something that needs to go in a fstab file apparently
        :param fsck: Something else that needs to go in a fstab file apparently
        :return:
        """

        def replace_all(text: str, dic: dict):
            """
            Execute multiple replaces on a string
            in one go
            :param text: string to execute replace on
            :param dic: dictionary of replacements (key = target, value = replace with)
            :return: str
            """
            for i, j in dic.items():
                text = text.replace(i, j)
            return text

        fstab_location = self.config_manager.get_config("FSTAB_LOCATION")

        # Strip all bad stuff from the paths
        replacements = {"\n": "", "\r": "", "\\": "/"}
        local_dir = replace_all(local_dir, replacements)
        actual_dir = replace_all(actual_dir, replacements)

        # Have to do this one separately as the double back slash was being replaced by a forward slash above
        replacement_space = {" ": "\\040"}
        local_dir = replace_all(local_dir, replacement_space)
        actual_dir = replace_all(actual_dir, replacement_space)

        # Read the file
        with open(fstab_location, "r") as f:
            fstab = Fstab().read_file(f)

        # Add our new mount point
        fstab.entries.append(Entry(actual_dir, local_dir, mount_type, options, dump, fsck))

        # Write our new fstab file
        formatted = str(fstab)
        with open(fstab_location, "w") as f:
            f.write(formatted)

    def _remove_permanent_mount(self, local_dir: str):
        """
        This function will remove a single
        directory from the fstab file
        :param local_dir: The local mount path
        """

        fstab_location = self.config_manager.get_config("FSTAB_LOCATION")

        # Read the file
        with open(fstab_location, "r") as f:
            fstab = Fstab().read_file(f)

        # Keep every other entry except the one we want to remove
        fstab.entries = [entry for entry in fstab.entries if not entry.dir == local_dir]

        # Write our new fstab file
        formatted = str(fstab)
        with open(fstab_location, "w") as f:
            f.write(formatted)
