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


