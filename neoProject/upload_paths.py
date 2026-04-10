import os
from pathlib import Path
from django.utils.deconstruct import deconstructible


def _is_dev_environment() -> bool:
    return os.environ.get("ENV", "DEV").upper() == "DEV"


@deconstructible
class CloudinaryFolderPath:
    """
    Migration-safe upload_to callable:
    - DEV -> dev/<filename>
    - non-DEV -> <folder_name>/<filename>
    """

    def __init__(self, folder_name: str):
        self.folder_name = folder_name

    def __call__(self, instance, filename):
        target_root = "dev" if _is_dev_environment() else self.folder_name
        safe_name = Path(filename).name
        return f"{target_root}/{safe_name}"
