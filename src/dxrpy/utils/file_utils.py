from io import BytesIO
import mimetypes
from pathlib import Path
from typing import BinaryIO, List, Union

class File:
    def __init__(self, file: Union[str, Path, bytes, BinaryIO]):
        self.file = file

    def to_tuple(self) -> tuple:
        """
        Converts the File object into a tuple suitable for upload.

        Returns:
            tuple: A tuple representing the file for upload.
        """
        # print file instance type (str, Path, bytes, BinaryIO...)
        print(type(self.file))
        if isinstance(self.file, (str, Path)):
            path = Path(self.file)
            content_type = (
                mimetypes.guess_type(path)[0] or "application/octet-stream"
            )
            return ("files", (path.name, open(path, "rb"), content_type))
        elif isinstance(self.file, bytes):
            return ("files", ("file.bin", BytesIO(self.file), "application/octet-stream"))
        elif hasattr(self.file, "read"):  # file-like object
            name = getattr(self.file, "name", "file.bin")
            content_type = (
                mimetypes.guess_type(name)[0] or "application/octet-stream"
            )
            return ("files", (name, self.file, content_type))
        else:
            raise ValueError("Unsupported file type")
