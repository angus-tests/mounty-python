import unittest
from unittest.mock import MagicMock

from app.models.mount import Mount
from app.repositories.mount_config_repository import MountConfigRepository
from app.repositories.mount_repository import MountRepository
from app.util.config import ConfigManager


def setup_mount_config_repo(system_mounts: list[Mount] = None, remove_failures: list[Mount] = None):
    """
    Helper method to set up a mock repository
    :param system_mounts - Optionally specify fake system mount info this mock should return
    :param remove_failures - Optionally specify a list of mounts that the repo failed to remove from the system
    """
    mock_config_repository = MagicMock(spec=MountConfigRepository)
    mock_config_repository.get_all_system_mounts.return_value = system_mounts or []
    mock_config_repository.remove_mounts.return_value = remove_failures or []
    return mock_config_repository


class TestGetCurrentMounts(unittest.TestCase):

    def test_get_current_mounts_only(self):
        """
        This test simulates that the only mounts
        on the system are our mounts (no system mounts)
        """

        # Simulate only two system mounts
        mock_config_repository = setup_mount_config_repo(
            system_mounts=[
                Mount(mount_path="/shares/our/share/1", actual_path="//SomeServer/Somewhere"),
                Mount(mount_path="/shares/our/share2/2", actual_path="//SomeServer/Somewhere"),
            ]
        )

        # Create a mock config manager
        mock_config_manager = MagicMock(spec=ConfigManager)

        # Create the MountRepo
        mount_repo = MountRepository(
            mock_config_manager,
            mock_config_repository
        )

        # Run the get_current_mounts
        current_mounts = mount_repo.get_current_mounts()

        # Assert the list matches our shares
        self.assertListEqual(
            [
                Mount(mount_path="/shares/our/share/1", actual_path="//SomeServer/Somewhere"),
                Mount(mount_path="/shares/our/share2/2", actual_path="//SomeServer/Somewhere"),
            ],
            current_mounts
        )

    def test_get_current_mounts_with_some_system_mounts(self):
        """
        This test will simulate that the system has some of our
        mounts as well as some system mounts
        """

        # Simulate a mix of our mounts with some system mounts
        mock_config_repository = setup_mount_config_repo(
            system_mounts=[
                Mount(mount_path="/user/important/thing", actual_path="//Secret/share/elsewhere"),
                Mount(mount_path="/shares/our/share/1", actual_path="//SomeServer/Somewhere"),
                Mount(mount_path="/shares/our/share2/2", actual_path="//SomeServer/Somewhere"),
                Mount(mount_path="/root/system/thing", actual_path="//Secret/share"),
            ]
        )

        # Create a mock config manager
        mock_config_manager = MagicMock(spec=ConfigManager)

        # Create the MountRepo
        mount_repo = MountRepository(
            mock_config_manager,
            mock_config_repository
        )

        # Run the get_current_mounts
        current_mounts = mount_repo.get_current_mounts()

        # Assert the list matches our shares
        self.assertListEqual(
            [
                Mount(mount_path="/shares/our/share/1", actual_path="//SomeServer/Somewhere"),
                Mount(mount_path="/shares/our/share2/2", actual_path="//SomeServer/Somewhere"),
            ],
            current_mounts
        )


if __name__ == '__main__':
    unittest.main()
