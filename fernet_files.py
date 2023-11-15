from custom_fernet import FernetNoBase64
import os
from typing import Type
from io import BytesIO, RawIOBase, BufferedIOBase, StringIO, TextIOBase
from types import TracebackType

_magic_dict = {}
_fernet_for_magic = FernetNoBase64(FernetNoBase64.generate_key())

def _add_magic(size: int) -> int:
    try:
        return _magic_dict[size]
    except:
        _magic_dict[size] = len(_fernet_for_magic.encrypt(bytes(size)))-size
        return _magic_dict[size]
    
class FernetFile:
    def __init__(self, key: bytes, file: str | RawIOBase | BufferedIOBase, chunksize: int = 65536) -> None:
        self.fernet = FernetNoBase64(key)
        self.file = file
        if isinstance(file, StringIO) or isinstance(file, TextIOBase):
            raise TypeError("File must be a binary file")
        if not isinstance(chunksize, int):
            raise TypeError("Chunksize must be a positive integer")
        if chunksize <= 0:
            raise ValueError("Chunksize must be a positive integer")

    def seek(self, *args, whence=os.SEEK_SET):
        if type(self.file) == BytesIO:
            return self.file.seek(args[0])
        if len(args) == 2:
            whence = args[1]
        return self.file.seek(args[0], whence)

    def read(self, *args, **kwargs):
        return self.file.read(*args, **kwargs)
    
    def write(self, *args, **kwargs):
        return self.file.write(*args, **kwargs)
    
    def close(self) -> None:
        try: self.file.close()
        except: pass

    generate_key = FernetNoBase64.generate_key

    def __enter__(self) -> "FernetFile":
        return self

    def __exit__(self, exc_type: Type[BaseException] | None, exc_value: BaseException | None, exc_traceback: TracebackType | None) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()