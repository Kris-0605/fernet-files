from cryptography.fernet import Fernet
from base64 import urlsafe_b64decode, urlsafe_b64encode
import os
from typing import Union, Optional, Type
from io import BytesIO, RawIOBase, BufferedIOBase, StringIO, TextIOBase
from types import TracebackType

_magic_dict = {}
_fernet_for_magic = Fernet(Fernet.generate_key())

def _add_magic(size: int) -> int:
    try:
        return _magic_dict[size]
    except:
        _magic_dict[size] = len(urlsafe_b64decode(_fernet_for_magic.encrypt(bytes(size))))-size
        return _magic_dict[size]
    
class FernetFile:
    def __init__(self, key: bytes, file: Union[str, RawIOBase, BufferedIOBase], chunksize: int = 65536) -> None:
        self.fernet = Fernet(key)
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

    generate_key = Fernet.generate_key

    def __enter__(self) -> "FernetFile":
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_value: Optional[BaseException], exc_traceback: Optional[TracebackType]) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()