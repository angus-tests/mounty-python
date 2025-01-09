import json
import unittest
from unittest.mock import MagicMock, patch, mock_open

from app.enums.enums import MountType
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


class TestGetDesiredMounts(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open, read_data='[]')
    def test_get_desired_mounts_empty(self, mock_json_open):
        """
        Simulate an empty desired mounts file
        """

        # We don't need a mock config repository for this test
        mock_config_repository = setup_mount_config_repo()

        # Create a mock config manager
        mock_config_manager = MagicMock(spec=ConfigManager)
        mock_config_manager.get_config.return_value = "fake/path/to/desired/mounts.json"

        # Create the MountRepo
        mount_repo = MountRepository(
            mock_config_manager,
            mock_config_repository
        )

        # Run the get_current_mounts
        current_mounts = mount_repo.get_desired_mounts()

        # Assert the list is empty
        self.assertListEqual([], current_mounts)

    @patch("builtins.open", new_callable=mock_open)
    def test_get_desired_mounts_with_content(self, mock_json_open):
        """
        Simulate a desired mounts file with a few mounts
        """

        # Mock the json file
        mock_json_open.return_value.read.return_value = json.dumps(
            [
                {
                    "mount_path": "/shares/outputs/example_data",
                    "actual_path": "//ny334xx/EXAMPLE_LOCATION/PROD/ETC",
                    "mount_type": "cifs"
                },

                {
                    "mount_path": "/shares/inputs/another_example",
                    "actual_path": "example:/abc/live/location/example",
                    "mount_type": "fuse.sshfs"
                }

            ]
        )

        # We don't need a mock config repository for this test
        mock_config_repository = setup_mount_config_repo()

        # Create a mock config manager
        mock_config_manager = MagicMock(spec=ConfigManager)
        mock_config_manager.get_config.return_value = "fake/path/to/desired/mounts.json"

        # Create the MountRepo
        mount_repo = MountRepository(
            mock_config_manager,
            mock_config_repository
        )

        # Run the get_current_mounts
        current_mounts = mount_repo.get_desired_mounts()

        expected = [
            Mount(mount_path="/shares/outputs/example_data",
                  actual_path="//ny334xx/EXAMPLE_LOCATION/PROD/ETC",
                  mount_type=MountType.WINDOWS),
            Mount(mount_path="/shares/inputs/another_example",
                  actual_path="example:/abc/live/location/example",
                  mount_type=MountType.LINUX)
        ]
        # Assert the list is empty
        self.assertListEqual(expected, current_mounts)


if __name__ == '__main__':
    unittest.main()
