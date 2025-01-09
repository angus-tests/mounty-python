import unittest

from app.enums.enums import MountType
from app.models.mount import Mount


class TestEquals(unittest.TestCase):
    def test_equals(self):
        m1 = Mount(
            mount_path="/mnt",
            actual_path="/mnt",
            mount_type=MountType.NONE
        )

        m2 = Mount(
            mount_path="/mnt",
            actual_path="/mnt",
            mount_type=MountType.NONE
        )

        self.assertEqual(m1, m2)

    def test_equals_with_user(self):
        """
        These mounts should be equal because the user is removed from the actual path
        """

        m1 = Mount(
            mount_path="/mnt",
            actual_path="user@/mnt",
            mount_type=MountType.NONE
        )

        m2 = Mount(
            mount_path="/mnt",
            actual_path="/mnt",
            mount_type=MountType.NONE
        )

        self.assertEqual(m1, m2)


if __name__ == '__main__':
    unittest.main()
