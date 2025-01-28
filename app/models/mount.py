import re
from dataclasses import dataclass

from app.enums.enums import MountType


@dataclass(order=True)
class Mount:
    """
    A mount is made up of...
    mount_path: The directory on the current machine
    actual_path: The directory the mount maps to
    mount_type: The type of mount
    """
    mount_path: str
    actual_path: str
    mount_type: MountType = MountType.NONE

    def __eq__(self, other) -> bool:
        """
        Compare two mounts
        :param other: Another mount
        """
        return ((self.mount_path == other.mount_path)
                and (self.actual_path == other.actual_path and self.mount_type == other.mount_type))
