from fernet_files.custom_fernet import FernetNoBase64
import os
from io import BytesIO, RawIOBase, BufferedIOBase, StringIO, TextIOBase, UnsupportedOperation

# DON'T TOUCH UNLESS ABSOLUTELY NECESSARY
META_SIZE = 8

DEFAULT_CHUNKSIZE = 4096

class FernetFile:
    def __init__(self, key: bytes | FernetNoBase64, file: str | RawIOBase | BufferedIOBase, chunksize: int = DEFAULT_CHUNKSIZE) -> None:
        self.closed = False

        self.__fernet = key if isinstance(key, FernetNoBase64) else FernetNoBase64(key) # key validation
        # file validation
        if isinstance(file, (StringIO, TextIOBase)):
            raise TypeError("File provided must be binary, not string")
        elif isinstance(file, (RawIOBase, BufferedIOBase, BytesIO)):
            self.__file = file
        elif isinstance(file, str):
            self.__file = open(file, "wb+")
        else:
            raise TypeError("File must be binary file or a filename")
        
        if not isinstance(chunksize, int):
            raise TypeError("Invalid chunksize, must be integer greater than 0")
        if chunksize <= 0:
            raise ValueError("Invalid chunksize, must be integer greater than 0")

        # get metadata
        self.__file.seek(0)
        if x := self.__file.read(META_SIZE): # If metadata exists, read it
            self.__last_chunk = int.from_bytes(x, "little")
            self.__last_chunk_padding = int.from_bytes(self.__file.read(META_SIZE), "little")
        else:
            self.__last_chunk, self.__last_chunk_padding = 0, 0
        # write metadata + check writeability
        self.__file.seek(0)
        try:
            self.__file.write(bytes(META_SIZE*2))
            self.writeable = True
        except UnsupportedOperation:
            self.writeable = False

        self.__data_chunksize = chunksize # the size of the data in chunks
        self.__chunksize = chunksize + 73 - (chunksize % 16) # the size of chunks when written to disk
        # Uses a magic formula for Fernet metadata size that I got by trial-and-error
        
        self.__chunk_modified = False
        self._pos_pointer = 0 # your position inside a chunk
        self._chunk_pointer = 0 # what chunk you're currently in

    def __goto_current_chunk(self) -> None:
        self.__file.seek(self._chunk_pointer*self.__chunksize+META_SIZE*2)

    def __get_file_size(self) -> int:
        return (self.__last_chunk+1)*self.__data_chunksize-self.__last_chunk_padding
    
    def __read_chunk(self) -> BytesIO:
        if self.__chunk_modified:
            return self.__chunk
            # "But what if the chunk isn't loaded!" well how did you modify it then
        self.__goto_current_chunk()
        try:
            data = self.__fernet.decrypt(self.__file.read(self.__chunksize))
            if self._chunk_pointer == self.__last_chunk and self.__last_chunk_padding:
                data = data[:-self.__last_chunk_padding]
            self.__chunk = BytesIO(data)
        except:
            self.__chunk = BytesIO()
        return self.__chunk
    
    def __write_chunk(self) -> None:
        if not self.writeable:
            return # Raising an exception is write's job
        self.__goto_current_chunk()
        data = self.__chunk.getvalue()
        padding = self.__data_chunksize - len(data)
        data += bytes(padding)
        self.__file.write(self.__fernet.encrypt(data))
        if self._chunk_pointer >= self.__last_chunk:
            self.__last_chunk = self._chunk_pointer
            self.__last_chunk_padding = padding
            self.__file.seek(0)
            self.__file.write(self.__last_chunk.to_bytes(META_SIZE, "little"))
            self.__file.write(self.__last_chunk_padding.to_bytes(META_SIZE, "little"))
        self.__chunk_modified = False

    def seek(self, *args, whence: int = os.SEEK_SET) -> int:
        if self.closed:
            raise ValueError("I/O operation on closed file")

        if len(args) >= 2:
            offset, whence = args[:2]
        else:
            offset = args[0]

        original = self._chunk_pointer, self._pos_pointer

        try:
            if whence == os.SEEK_SET or whence == 0:
                self._chunk_pointer = 0
                self._pos_pointer = offset
            elif whence == os.SEEK_CUR or whence == 1:
                self._pos_pointer += offset
            elif whence == os.SEEK_END or whence == 2:
                size = self.__get_file_size()
                self._chunk_pointer = 0
                self._pos_pointer = size + offset
            else:
                raise ValueError("Invalid whence")
        except OSError:
            self._chunk_pointer, self._pos_pointer = original
            raise OSError("Invalid seek value")

        return self._pos_pointer + self._chunk_pointer*self.__data_chunksize

    def read(self, size: int = -1) -> bytes:
        if self.closed:
            raise ValueError("I/O operation on closed file")
        # data validation
        if not isinstance(size, int):
            raise TypeError("Size must be an integer")
        if size < 0:
            self.__write_chunk() # refreshes values for last chunk
            size = self.__get_file_size() - self._pos_pointer - self._chunk_pointer*self.__data_chunksize

        self.__read_chunk()
        if size <= self.__data_chunksize-self._pos_pointer: # if all wanted data is in current chunk
            self.__chunk.seek(self._pos_pointer)
            data = self.__chunk.read(size)
            self._pos_pointer += size # we do this after reading otherwise it could mess up our chunk pointer
        else:
            # else: read until start of next chunk.
            # read the stuff in the current chunk
            data = bytearray()
            read_size = self.__data_chunksize-self._pos_pointer
            self.__chunk.seek(self._pos_pointer)
            data += self.__chunk.read(read_size)
            self._pos_pointer = 0
            self._chunk_pointer += 1
            size -= read_size
            # loop over the rest
            while size >= self.__data_chunksize:
                data += self.__read_chunk().getvalue()
                size -= self.__data_chunksize
                self._chunk_pointer += 1
            # mop up the last chunk
            if size:
                data += self.__read_chunk().read(size)
                self._pos_pointer = size

        # For some reason if you read to the end of a file in python, the pointer should be at the end of the file
        # Original implementation puts the pointer at the distance specified by the read argument, this fixes that
        filesize = self.__get_file_size()
        if self._pos_pointer + self._chunk_pointer*self.__data_chunksize >= filesize:
            self.__chunk_pointer = 0
            self._pos_pointer = self.__get_file_size()

        return bytes(data)

    def write(self, b: bytes) -> int:
        if not self.writeable:
            raise UnsupportedOperation("write")
        if self.closed:
            raise ValueError("I/O operation on closed file")
        # data validation
        if not isinstance(b, bytes):
            raise TypeError("Data must be bytes")
        size = len(b)
        return_value = size

        if size < self.__data_chunksize-self._pos_pointer: # if all data fits in current chunk
            if self.__chunk is not None:
                self.__chunk.seek(self._pos_pointer)
                self.__chunk.write(b)
            else:
                self.__chunk = BytesIO(b)
            self._pos_pointer += size
            self.__chunk_modified = True
            return size
        # else: write until start of next chunk. else omitted for indent readability
        # write the stuff in the current chunk
        b = BytesIO(b)
        write_size = self.__data_chunksize-self._pos_pointer
        if self.__chunk is not None:
            self.__chunk.seek(self._pos_pointer)
            self.__chunk.write(b.read(write_size))
        else:
            self.__chunk = BytesIO(b.read(write_size))
        self._pos_pointer = 0
        self.__chunk_modified = True
        size -= write_size
        # loop over the rest
        while size >= self.__data_chunksize:
            self._chunk_pointer += 1
            self.__chunk = BytesIO(b.read(self.__data_chunksize))
            self.__chunk_modified = True
            size -= self.__data_chunksize
        # mop up the last chunk
        if size:
            self._chunk_pointer += 1
            self.__chunk = self.__read_chunk()
            self.__chunk.seek(0)
            self.__chunk.write(b.read(size))
            self._pos_pointer = size
            self.__chunk_modified = True
        return return_value
    
    def close(self) -> BytesIO | None:
        try: self.__write_chunk()
        except: pass
        self.closed = True
        try: self.file.close()
        except: pass

    generate_key = FernetNoBase64.generate_key

    def __enter__(self) -> "FernetFile":
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()

    @property
    def _pos_pointer(self) -> int:
        return self.__pos_pointer
    
    @_pos_pointer.setter
    def _pos_pointer(self, value: int) -> None:
        self.__pos_pointer = value
        if self.__pos_pointer >= self.__data_chunksize:
            chunk_difference = self.__pos_pointer//self.__data_chunksize
            self.__pos_pointer -= chunk_difference*self.__data_chunksize
            self._chunk_pointer += chunk_difference
        elif self.__pos_pointer < 0:
            chunk_difference = -(self.__pos_pointer//self.__data_chunksize)
            self.__pos_pointer += chunk_difference*self.__data_chunksize
            self._chunk_pointer -= chunk_difference
            if self._chunk_pointer < 0:
                raise OSError("Seek before beginning of file")

    @property
    def _chunk_pointer(self) -> int:
        return self.__chunk_pointer
    
    @_chunk_pointer.setter
    def _chunk_pointer(self, value: int) -> None:
        if self.__chunk_modified: self.__write_chunk()
        self.__chunk_pointer = value
        self.__read_chunk()