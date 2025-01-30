from pyfstab import Fstab

from app.enums.enums import MountType
from app.exceptions.mount_exception import MountException
from app.factories.mount_factory import MountFactory
from app.interfaces.mount_config_repository_interface import MountConfigRepositoryInterface
from app.models.mount import Mount
from app.interfaces.file_sytem_repository_interface import FileSystemRepositoryInterface
from app.util.config import ConfigManager


class AutoRepository(MountConfigRepositoryInterface):
    """
    Concrete implementation of a mounting config repository
    for use with the automount configuration
    """

    def __init__(self, config_manager: ConfigManager, fs_repository: FileSystemRepositoryInterface):
        """
        :param config_manager: ConfigManager - An instance of the config manager to fetch configuration variables
        :param fs_repository: FileSystemRepositoryInterface - An instance of the file system repository
        """
        self.config_manager = config_manager
        self.fs_repository = fs_repository

        # Fetch the locations of the auto.master and auto mounts files from the config
        self.auto_master_location = self.config_manager.get_config("AUTO_MASTER_LOCATION")
        self.auto_mounts_location = self.config_manager.get_config("AUTO_MOUNTS_LOCATION")
        self.proc_mounts_location = self.config_manager.get_config("PROC_MOUNTS_LOCATION")

    def _read_proc_mounts(self) -> Fstab:
        """
        Read the contents of the proc mounts file
        """
        # TODO this is repeated in FSTAB repo, parent class?
        return Fstab().read_string(
            self.fs_repository.read_file(self.proc_mounts_location)
        )

    def is_mounted(self, mount_path: str) -> bool:
        proc_mounts = self._read_proc_mounts()
        return any(entry.dir == mount_path for entry in proc_mounts.entries)

    def remove_mounts(self, mounts: list[Mount]):
        for mount in mounts:
            self.remove_mount_information(mount.mount_path)

    def _read_auto_master(self) -> list[str]:
        """
        Read the contents of the auto.master file
        """
        return self.fs_repository.read_file(self.auto_master_location).splitlines()

    def _write_auto_master(self, lines: list[str]):
        """
        Write the contents to the auto.master file
        :param lines: list[str] - The lines to write to the file
        """
        self.fs_repository.write_file(self.auto_master_location, "\n".join(lines) + "\n")

    def _read_auto_mounts(self) -> list[str]:
        """
        Read the contents of the auto mounts file
        """
        return self.fs_repository.read_file(self.auto_mounts_location).splitlines()

    def _write_auto_mounts(self, lines: list[str]):
        """
        Write the contents to the auto mounts file
        :param lines: list[str] - The lines to write to the file
        """
        self.fs_repository.write_file(self.auto_mounts_location, "\n".join(lines) + "\n")

    def _sanitize_path(self, path: str) -> str:
        """
        Sanitize a path for use in the auto mounts file
        :param path: str - The path to sanitize
        :return: str - The sanitized path
        """
        replacements = {"\n": "", "\r": "", " ": "\\040"}
        for old, new in replacements.items():
            path = path.replace(old, new)
        return path

    def _generate_mount_options(self, mount: Mount) -> str:
        if mount.mount_type == MountType.WINDOWS:
            cifs_file_location = self.config_manager.get_config("CIFS_FILE_LOCATION")
            cifs_domain = self.config_manager.get_config("CIFS_DOMAIN")
            return f"-fstype=cifs,credentials={cifs_file_location},domain={cifs_domain},uid=1001,gid=5001"
        elif mount.mount_type == MountType.LINUX:
            linux_ssh_location = self.config_manager.get_config("LINUX_SSH_LOCATION")
            return f"-fstype=nfs,IdentityFile={linux_ssh_location},uid=1001,gid=5001"
        else:
            raise MountException(f"Mount type {mount.mount_type} not supported")

    def store_mount_information(self, mount: Mount):
        """
        Add a mount to the auto mounts
        """
        sanitized_local_dir = self._sanitize_path(mount.mount_path)
        sanitized_actual_dir = self._sanitize_path(mount.actual_path)
        options = self._generate_mount_options(mount)

        mounts = self._read_auto_mounts()
        mounts.append(f"{sanitized_local_dir} {sanitized_actual_dir} {options}")
        self._write_auto_mounts(mounts)

    def remove_mount_information(self, mount_path: str):
        """
        Remove a mount from the auto mounts
        """
        mount_path = self._sanitize_path(mount_path)
        mounts = self._read_auto_mounts()
        mounts = [line for line in mounts if not line.startswith(mount_path)]
        self._write_auto_mounts(mounts)

    def get_all_system_mounts(self) -> list[Mount]:
        """
        Get a list of the current mounts on the system
        """
        mounts = self._read_auto_mounts()
        return [MountFactory.create_from_auto_mount_entry(line) for line in mounts]

    def cleanup(self):
        """
        Remove duplicate entries and ensure consistency
        """
        mounts = self._read_auto_mounts()
        seen = set()
        cleaned_mounts = []
        for line in mounts:
            if line not in seen:
                seen.add(line)
                cleaned_mounts.append(line)
        self._write_auto_mounts(cleaned_mounts)
