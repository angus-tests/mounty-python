from abc import abstractmethod, ABC

from pyfstab import Fstab, Entry

from app.enums.enums import MountType
from app.exceptions.mount_exception import MountException
from app.factories.mount_factory import MountFactory
from app.models.mount import Mount


class MountConfigRepository(ABC):
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


class FstabRepository(MountConfigRepository):
    """
    Concrete implementation of a mounting config repository
    for use with the fstab file
    """

    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.fstab_location = self.config_manager.get_config("FSTAB_LOCATION")
        self.proc_mounts_location = self.config_manager.get_config("PROC_MOUNTS_LOCATION")

    def store_mount_information(self, mount: Mount):
        """
        Add the mount to the fstab file
        # In order for mounts to persist, we need to add the line to the /etc/fstab file
        # Windows: <file system>       <dir>      <type> <options>
        # Linux:   <Linux share>       <dir>      fuse.sshfs IdentityFile=/path/to/.ssh/id_rsa_linux,uid=1001,gid=5001
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

        local_dir = mount.mount_path
        actual_dir = mount.actual_path

        # TODO did someone says strategy pattern?
        if mount.mount_type == MountType.WINDOWS:
            # Get the location of the CIFS file
            cifs_file_location = self.config_manager.get_config("CIFS_FILE_LOCATION")
            options = f"credentials={cifs_file_location},domain=ONS,uid=1001,gid=5001,auto"
        elif mount.mount_type == MountType.LINUX:
            # We need to use SSHFS to mount linux shares
            linux_ssh_location = self.config_manager.get_config("LINUX_SSH_LOCATION")

            # We need to update the actual path to include the SSH user
            actual_dir = mount.actual_path
            options = f"IdentityFile={linux_ssh_location},uid=1001,gid=5001,auto"
        else:
            raise MountException(f"Mount type {mount.mount_type} not supported")

        # Strip all bad stuff from the paths
        replacements = {"\n": "", "\r": "", "\\": "/"}
        local_dir = replace_all(local_dir, replacements)
        actual_dir = replace_all(actual_dir, replacements)
        mount_type = str(mount.mount_type.value)

        # Have to do this one separately as the double back slash was being replaced by a forward slash above
        replacement_space = {" ": "\\040"}
        local_dir = replace_all(local_dir, replacement_space)
        actual_dir = replace_all(actual_dir, replacement_space)

        # Read the file

        # TODO abstract this out
        with open(self.fstab_location, "r") as f:
            fstab = Fstab().read_file(f)

        # Add our new mount point
        fstab.entries.append(Entry(actual_dir, local_dir, mount_type, options, 0, 0))

        # Write our new fstab file
        # TODO abstract this out
        formatted = str(fstab)
        with open(self.fstab_location, "w") as f:
            f.write(formatted)

    def remove_mount_information(self, mount_path: str):
        """
        Remove the mount from the fstab file
        """

        # Read the file
        with open(self.fstab_location, "r") as f:
            fstab = Fstab().read_file(f)

        # Keep every other entry except the one we want to remove
        fstab.entries = [entry for entry in fstab.entries if not entry.dir == mount_path]

        # Write our new fstab file
        formatted = str(fstab)
        with open(self.fstab_location, "w") as f:
            f.write(formatted)

    def get_all_system_mounts(self) -> list[Mount]:
        """
        Get all system mounts from the fstab file
        """
        # Read the file
        with open(self.fstab_location, "r") as f:
            fstab = Fstab().read_file(f)

        return [
            MountFactory.create_from_fstab_entry(entry)
            for entry in fstab.entries
        ]

    def is_mounted(self, mount_path: str) -> bool:
        """
        Use the proc mounts file to check if the mount is currently mounted
        """

        # Read the file
        with open(self.proc_mounts_location, "r") as f:
            fstab = Fstab().read_file(f)

        return any([entry.dir == mount_path for entry in fstab.entries])

    def remove_mounts(self, mounts: list[Mount]):
        """
        Clear all mount information from the fstab file
        :param mounts: A list of mounts to remove from the fstab
        """

        # Read the file
        with open(self.fstab_location, "r") as f:
            fstab = Fstab().read_file(f)

        # Make a list of the entries we want to keep
        fstab.entries = [entry for entry in fstab.entries if entry.dir not in [mount.mount_path for mount in mounts]]

        # Write our new fstab file
        formatted = str(fstab)

        with open(self.fstab_location, "w") as f:
            f.write(formatted)
