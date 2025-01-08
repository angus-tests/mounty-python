import unittest
from unittest.mock import MagicMock

from app.models.mount import Mount
from app.repositories.mount_repository import MountRepositoryInterface
from app.services.mounting_service import MountingService


class TestMountingServiceRun(unittest.TestCase):

    def test_add_new_mounts(self):

        # Mock the mount repository
        mock_mount_repository = MagicMock(spec=MountRepositoryInterface)

        # Mock the desired mounts for the repository
        mock_mount_repository.get_desired_mounts.return_value = [
            Mount(mount_path="/shares/test", actual_path="//SomeServer/Somewhere"),
            Mount(mount_path="/shares/test2", actual_path="//AnotherServer/Somewhere")
        ]

        # Mock the mount and unmount methods for the repository
        mock_mount_repository.mount.return_value = None
        mock_mount_repository.unmount.return_value = None

        # Mock the current mounts for the repository
        mock_mount_repository.get_current_mounts.return_value = []

        # Create the mounting service
        mounting_service = MountingService(mock_mount_repository)

        # Run the mounting service
        mounting_service.run()

        # Check that the mount repository's mount method was called twice
        self.assertEqual(mock_mount_repository.mount.call_count, 2)

        # Check that the mount repository's unmount method was not called
        self.assertEqual(mock_mount_repository.unmount.call_count, 0)


if __name__ == '__main__':
    unittest.main()
