from app.enums.enums import MountType
from app.models.mount import Mount


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

    @staticmethod
    def standard_mount(mount_path: str = None, actual_path: str = None) -> Mount:
        return Mount(
            mount_path=mount_path or "/shares/standard",
            actual_path=actual_path or "/mnt/standard",
            mount_type=MountType.NONE
        )
