'''encryption/decryption of files with cryptography.fernet, but with file-like methods

Fernet encryption requires all data to be encrypted or decrypted at once.
This is memory intensive, and it is slow if you only want to read part of a file.
Fernet Files provides a simple interface that breaks data up into chunks when encrypting and decrypting them to lower memory usage.
Data is only encrypted when it's necessary to do so.
You may treat the class similar to a file: it has `read`, `write`, `seek` and `close` methods.
It can also be context managed, so you can close it using a `with` statement.'''

__version__ = "0.1.2"

from fernet_files.custom_fernet import FernetNoBase64
import os
import os.path
from io import BytesIO, RawIOBase, BufferedIOBase, StringIO, TextIOBase, UnsupportedOperation

# Don't modify without reading documentation
META_SIZE = 8
'''The size of a file's metadata is META_SIZE*2.
See documentation for more information.'''

DEFAULT_CHUNKSIZE = 65536
'''The default size of chunks in bytes.'''

class FernetFile:
    '''Parameters:

- key - A key (recommended) or a `fernet_files.custom_fernet.FernetNoBase64` object
- - A key must be 32 random bytes. Get using `fernet_files.FernetFile.generate_key()` and store somewhere secure
- - Alternatively, pass in a `fernet_files.custom_fernet.FernetNoBase64` object
- file - Accepts a filename as a string, or a file-like object. If passing in a file-like object, it would be opened in binary mode.
- chunksize - The size of chunks in bytes. 
- - Bigger chunks use more memory and take longer to read or write, but smaller chunks can be very slow when trying to read/write in large quantities.
- - Bigger chunks apply padding so a very large chunksize will create a large file. Every chunk has its own metadata so a very small chunk size will create a large file.
- - Defaults to 64KiB (65536 bytes).'''

    def __init__(self, key: bytes | FernetNoBase64, file: str | RawIOBase | BufferedIOBase, chunksize: int = DEFAULT_CHUNKSIZE) -> None:
        self.closed = False

        self.__fernet = key if isinstance(key, FernetNoBase64) else FernetNoBase64(key) # key validation
        # file validation
        if isinstance(file, (StringIO, TextIOBase)):
            raise TypeError("File provided must be binary, not string")
        elif isinstance(file, (RawIOBase, BufferedIOBase, BytesIO)):
            self.__file = file
        elif isinstance(file, str):
            if os.path.exists(file):
                self.__file = open(file, "rb+")
            else:
                self.__file = open(file, "wb+")
        else:
            raise TypeError("File must be binary file or a filename")
        
        if not self.__file.seekable():
            raise IOError("Fernet File only supports seekable files")

        # chunksize validation
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
        
        self.__chunk_modified = False
        self._pos_pointer = 0 # your position inside a chunk
        self._chunk_pointer = 0 # what chunk you're currently in

    def __goto_current_chunk(self) -> None:
        '''Moves our position in `self.__file` to the location represented by the chunk pointer, taking into account the metadata at the start of the file.\nCalculated as follows: take the number of the chunk you're currently on, multiply by the size of chunks when they're written to disk. Take the META_SIZE, multiply that by 2 and add it to the number you had before.'''
        self.__file.seek(self._chunk_pointer*self.__chunksize+META_SIZE*2)

    def __get_file_size(self) -> int:
        '''Calculate the size of the data contained within the file in bytes using the file's metadata. This is the size of the data, not the size of what is written to disk.\nCalculated as follows: take the number of the last chunk and add 1 to get the total number of chunks (because counting starts at 0). Multiply this by the chunksize. Finally, subtract the size of the padding used on the last chunk.'''
        return (self.__last_chunk+1)*self.__data_chunksize-self.__last_chunk_padding
    
    def __read_chunk(self) -> BytesIO:
        '''Reads and decrypts the current chunk, turns it into a BytesIO object, stores that object in `self.__chunk` and returns it.\nIf the chunk has been modified, it is already loaded into memory so no file operations are done. Also responsible for removing padding if the chunk being read is the last chunk.'''
        if self.__chunk_modified:
            return self.__chunk
            # you can't modify a chunk without it already being loaded
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
        '''Encrypts and writes the chunk, and sets `self.__chunk_modified` to False.\nAlso responsible for applying padding and modifying the metadata at the start of the file if this is the last chunk.'''
        if not self.writeable:
            return # Raising an exception is the write method's responsibility
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
        '''Can be called as:
- seek(self, offset, whence)
- seek(self, offset, whence=whence)

Moves through the file by the specified number of bytes. "whence" determines what this is relative to. Returns your new absolute position as an integer.

Parameters:

- offset - Integer. Move this number of bytes relative to whence.
- whence - Ignored if using a BytesIO object. Accepted values are:
- - `os.SEEK_SET` or `0` - relative to the start of the stream
- - `os.SEEK_CUR` or `1` - relative to the current stream position
- - `os.SEEK_END` or `2` - relative to the end of the stream (use negative offset)'''
        if self.closed:
            raise ValueError("I/O operation on closed file")

        # argument parsing
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
        '''Reads the number of bytes specified and returns them.

Parameters:

- size - Positive integer. If -1 or not specified then read to the end of the file.'''
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
            self._pos_pointer += size
        else: # else: read until start of next chunk
            # read in the current chunk
            data = bytearray()
            read_size = self.__data_chunksize-self._pos_pointer
            self.__chunk.seek(self._pos_pointer)
            data += self.__chunk.read(read_size)
            self._pos_pointer = 0
            self._chunk_pointer += 1
            size -= read_size
            # loop, reading all the data in each chunk
            while size >= self.__data_chunksize:
                data += self.__read_chunk().getvalue()
                size -= self.__data_chunksize
                self._chunk_pointer += 1
            # partially read the last chunk
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
        '''Writes the given bytes. Returns the number of bytes written.

Parameters:

- b - The bytes to be written.'''
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
        # write in the current chunk
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
        # loop, writing full chunks
        while size >= self.__data_chunksize:
            self._chunk_pointer += 1
            self.__chunk = BytesIO(b.read(self.__data_chunksize))
            self.__chunk_modified = True
            size -= self.__data_chunksize
        # partially write the last chunk
        if size:
            self._chunk_pointer += 1
            self.__chunk = self.__read_chunk()
            self.__chunk.seek(0)
            self.__chunk.write(b.read(size))
            self._pos_pointer = size
            self.__chunk_modified = True
        return return_value
    
    def close(self) -> BytesIO | None:
        '''Writes all outstanding data closes the file.\nReturns `None` unless the file is a `BytesIO` object, in which case it returns the object without closing it.'''
        # write data stored in memory
        try: self.__write_chunk()
        except: pass
        # mark as closed
        self.closed = True
        try:
            # if file is BytesIO, return it, otherwise close the file
            if isinstance(self.__file, BytesIO):
                return self.__file
            else:
                try: self.__file.close()
                except: pass
        except AttributeError:
            # fixes https://github.com/Kris-0605/fernet_files/issues/4
            pass

    def seekable(self) -> bool:
        '''Returns if the file is seekable or not. Will always return `True`.'''
        return True

    generate_key = FernetNoBase64.generate_key
    '''Static method used to generate a key. Acts as a pointer to `custom_fernet.FernetNoBase64.generate_key()`.'''

    def __enter__(self) -> "FernetFile":
        '''Returns self to allow context management.'''
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        '''Calls `self.close` and returns `None`.'''
        self.close()

    def __del__(self) -> None:
        '''Calls `self.close` and returns `None`.'''
        self.close()

    @property
    def _pos_pointer(self) -> int:
        '''Stores the Fernet file's current position in the chunk in bytes.\nThe getter returns `self.__pos_pointer`.\nThe setter ensures that 0 < _pos_pointer < chunksize. If it isn't, then it wraps the value round by adding or subtracting the chunksize, modifying the chunk pointer to compensate.'''
        return self.__pos_pointer
    
    @_pos_pointer.setter
    def _pos_pointer(self, value: int) -> None:
        self.__pos_pointer = value
        # wrapping value of pos pointer by changing chunk pointer
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
        '''Stores the Fernet file's current chunk number.\nThe getter returns `self.__chunk_pointer`.\nThe setter modifies this value. Before it switching chunks it checks if the current chunk has been modified and writes it if it has. After switching chunks, we read the new chunk into memory.'''
        return self.__chunk_pointer
    
    @_chunk_pointer.setter
    def _chunk_pointer(self, value: int) -> None:
        # write a chunk only if it's been modified
        if self.__chunk_modified: self.__write_chunk()
        self.__chunk_pointer = value
        self.__read_chunk()