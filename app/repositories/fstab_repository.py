from pyfstab import Fstab, Entry

from app.enums.enums import MountType
from app.exceptions.mount_exception import MountException
from app.factories.mount_factory import MountFactory
from app.interfaces.mount_config_repository_interface import MountConfigRepositoryInterface
from app.models.mount import Mount
from app.interfaces.file_sytem_repository_interface import FileSystemRepositoryInterface
from app.util.config import ConfigManager


class FstabRepository(MountConfigRepositoryInterface):
    """
    Concrete implementation of a mounting config repository
    for use with the fstab file
    """

    def __init__(self, config_manager: ConfigManager, fs_repository: FileSystemRepositoryInterface):
        """
        :param config_manager: ConfigManager - An instance of the config manager to fetch configuration variables
        :param fs_repository: FileSystemRepositoryInterface - An instance of the file system repository
        """
        self.config_manager = config_manager
        self.fs_repository = fs_repository
        self.fstab_location = self.config_manager.get_config("FSTAB_LOCATION")
        self.proc_mounts_location = self.config_manager.get_config("PROC_MOUNTS_LOCATION")

    def _read_fstab(self) -> Fstab:
        """
        Read the contents of the fstab file
        :return Fstab: The fstab file object
        """
        fstab = Fstab().read_string(
            self.fs_repository.read_file(self.fstab_location)
        )

        # Remove any duplicates
        fstab.entries = self._remove_duplicates(fstab.entries)

        return fstab

    def _write_fstab(self, fstab: Fstab):
        """
        Write the contents of the fstab file
        """

        # Remove any duplicates
        fstab.entries = self._remove_duplicates(fstab.entries)

        self.fs_repository.write_file(self.fstab_location, str(fstab))

    def _remove_duplicates(self, entries: list[Entry]):
        """
        Remove any duplicates from the fstab file
        :entries list[Entry]: The entries to remove duplicates from
        """
        keep = []

        # Store the device and dir of each entry
        seen: list[tuple] = []

        for entry in entries:
            if (entry.device, entry.dir) not in seen:
                seen.append((entry.device, entry.dir))
                keep.append(entry)
        return keep

    def _read_proc_mounts(self) -> Fstab:
        """
        Read the contents of the proc mounts file
        """

        return Fstab().read_string(
            self.fs_repository.read_file(self.proc_mounts_location)
        )

    def _sanitize_path(self, path: str) -> str:
        replacements = {"\n": "", "\r": "", "\\": "/", " ": "\\040"}
        for old, new in replacements.items():
            path = path.replace(old, new)
        return path

    def _generate_mount_options(self, mount: Mount) -> str:
        if mount.mount_type == MountType.WINDOWS:
            cifs_file_location = self.config_manager.get_config("CIFS_FILE_LOCATION")
            cifs_domain = self.config_manager.get_config("CIFS_DOMAIN")
            return f"credentials={cifs_file_location},domain={cifs_domain},uid=1001,gid=5001,auto"
        elif mount.mount_type == MountType.LINUX:
            linux_ssh_location = self.config_manager.get_config("LINUX_SSH_LOCATION")
            return f"IdentityFile={linux_ssh_location},uid=1001,gid=5001,auto"
        else:
            raise MountException(f"Mount type {mount.mount_type} not supported")

    def _filter_entries(self, entries: list[Entry], condition) -> list[Entry]:
        """
        Filter a list of entries based on a condition
        """
        return [entry for entry in entries if condition(entry)]

    def store_mount_information(self, mount: Mount):
        """
        Add a mount to the FSTAB
        """
        sanitized_local_dir = self._sanitize_path(mount.mount_path)
        sanitized_actual_dir = self._sanitize_path(mount.actual_path)
        options = self._generate_mount_options(mount)

        fstab = self._read_fstab()
        fstab.entries.append(
            Entry(sanitized_actual_dir, sanitized_local_dir, str(mount.mount_type.value), options, 0, 0)
        )
        self._write_fstab(fstab)

    def remove_mount_information(self, mount_path: str):
        """
        Remove a mount from the FSTAB
        """

        # Sanitize the path
        mount_path = self._sanitize_path(mount_path)

        # Read the fstab file
        fstab = self._read_fstab()

        # Remove the entry
        fstab.entries = self._filter_entries(fstab.entries, lambda entry: entry.dir != mount_path)

        self._write_fstab(fstab)

    def get_all_system_mounts(self) -> list[Mount]:
        """
        Get a list of the current mounts on the system from the FSTAB
        """
        fstab = self._read_fstab()
        return [MountFactory.create_from_fstab_entry(entry) for entry in fstab.entries]

    def is_mounted(self, mount_path: str) -> bool:
        """
        Return True if the mount is currently mounted
        """
        proc_mounts = self._read_proc_mounts()
        return any(entry.dir == mount_path for entry in proc_mounts.entries)

    def remove_mounts(self, mounts: list[Mount]):
        """
        Remove a list of mounts from the system
        """
        mount_paths = {self._sanitize_path(mount.mount_path) for mount in mounts}
        fstab = self._read_fstab()
        fstab.entries = self._filter_entries(fstab.entries, lambda entry: entry.dir not in mount_paths)
        self._write_fstab(fstab)

    def cleanup(self):
        """
        Remove duplicates and any mounts not present in the proc mounts file
        """
        fstab = self._read_fstab()
        proc_mounts = self._read_proc_mounts()

        fstab.entries = self._filter_entries(
            fstab.entries,
            lambda entry: any(
                proc_entry.dir == entry.dir and proc_entry.device == entry.device
                for proc_entry in proc_mounts.entries
            )
        )
        self._write_fstab(fstab)
