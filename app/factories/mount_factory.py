from pyfstab import Entry

from app.enums.enums import MountType
from app.models.mount import Mount


class MountFactory:

    @staticmethod
    def create_from_fstab_entry(entry: Entry) -> Mount:
        return Mount(entry.dir, entry.device, MountType.from_str(entry.type))

    @staticmethod
    def create_from_json(data: dict) -> Mount:
        return Mount(data["mount_path"], data["actual_path"], MountType.from_str(data["mount_type"]))


class FakeMountFactory:
    """
    Used for creating fake Mount objects for testing
    """

    @staticmethod
    def windows_mount(mount_path: str = None, actual_path: str = None) -> Mount:
        return Mount(
            mount_path=mount_path or "/shares/windows",
            actual_path=actual_path or "//windowsServer/share",
            mount_type=MountType.WINDOWS
        )

    @staticmethod
    def linux_mount(mount_path: str = None, actual_path: str = None) -> Mount:
        return Mount(
            mount_path=mount_path or "/shares/linux",
            actual_path=actual_path or "/mnt/linux",
            mount_type=MountType.LINUX
        )