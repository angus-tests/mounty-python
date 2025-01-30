from app.interfaces.mount_config_repository_interface import MountConfigRepositoryInterface
from app.models.mount import Mount


class AutoRepository(MountConfigRepositoryInterface):
    """
    Concrete implementation of a mounting config repository
    for use with the automount protocol
    """

    def remove_mount_information(self, mount_path: str):
        pass

    def get_all_system_mounts(self) -> list[Mount]:
        pass

    def is_mounted(self, mount_path: str) -> bool:
        pass

    def remove_mounts(self, mounts: list[Mount]):
        pass

    def cleanup(self):
        pass

    def store_mount_information(self, mount: Mount):
        pass
    