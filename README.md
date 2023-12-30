# Fernet Files - encryption/decryption of files with cryptography.fernet, but with file-like methods

Fernet Files is a very simple module that I'm creating to support one of my own projects.

Fernet encryption is pretty cool, however, the entire file has to be loaded into memory in order to encrypt or decrypt it. This module solves that problem by breaking the file down into chunks. This module provides an object that's similar to a file - it allows you to `read`, `write` and `seek` throughout the file without having to worry about those chunks. It can also be context managed (you can use it with a `with` statement). It won't create a massive CPU overhead by re-encrypting every time you write a single byte either - encryption only happens when switching to a different chunk, or when closing the file.

At this time, Fernet Files only supports the `read`, `write`, `seek` and `close` methods (as well as being context managed so you can close them with a `with` statement), so it is not a true file-like object. Maybe at some point in future I'll come back and make a version of this that returns a true file-like object.

Additionally, Fernet Files does not use the version of Fernet that the cryptography module provides. This is because of base64 - `cryptography.fernet.Fernet` outputs encrypted data as base64 and takes base64 as input for data to be decrypted. Base64 uses 33% more space than storing data as its raw binary, so we obviously want to decode the base64 output in order to save space. However, decoding base64 that has just been encoded is a waste of processing power, and a quick look at Fernet's source code will show you that the data is present in binary form before being base64 encoded. For this reason, `custom_fernet.py` includes the class `FernetNoBase64`, which does exactly was it says on the tin: raw output and raw input, no base64 required or supported. The processing time this saves is significant: in my own rough testing I've found that this provides between a 50% and 150% speedup depending on the context.

## Example usage

```py
from fernet_files import FernetFile
key = FernetFile.generate_key() # Keep this
with FernetFile(key, "filename.bin") as f:
  # Use like a normal file
  f.write(b'123456789') # Returns 9
  f.seek(4) # Returns 4
  f.read(3) # Returns b'567'
  ...

# If you check the file after closing (leaving the with statement)
# the contents will be encrypted and unreadable without using the module

# If you use the same key, you can then read the data again
with FernetFile(key, "filename.bin") as f:
    f.read() # Returns b'123456789'
```

## Installation

I haven't put it on pip yet, but feel free to clone the repository. The module is contained within the fernet_files folder and you can copy that to the directory where your script is.

## Docs

### class `fernet_files.FernetFile(self, key, file, chunksize=4096)`

The only class you should be interacting with.

Parameters:

- **key** - The key for Fernet encryption/decrytion. Accepts either a key, or a `fernet_files.custom_fernet.FernetNoBase64` object.
- - A key must be 32 random bytes. Get using `fernet_files.FernetFile.generate_key()` or `fernet_files.custom_fernet.FernetNoBase64.generate_key()` and then store somewhere secure
- - Alternatively, pass in a `fernet_files.custom_fernet.FernetNoBase64` object if you don't trust the module with your key
- **file** - The file to read/write to. Accepts both filenames as strings and file-like objects. If you want to do something like making the file read-only, pass in a file object, because filenames are opened in read and write mode. Any files should be open in binary mode (for the second argument of `open` for example, do "rb" instead of "r").
- **chunksize** - The size of chunks in bytes. 
- - Bigger chunks use more memory and take longer to read or write, but smaller chunks can be very slow when you try and read/write lots of them.
- - Bigger chunks apply padding so a very large chunksize will create a large file. Every chunk has its own metadata so a very small chunk size will create a large file.
- - Defaults to 4KiB (4096 bytes).

#### method `fernet_files.FernetFile.read(self, size=-1)`

Read. Returns bytes. Works the same as a file.

Parameters:

- **size** - Positive integer. Read this number of bytes. If -1 or not specified then read to the end of the file.

#### method `fernet_files.FernetFile.write(self, b)`

Writes the given bytes. Returns the number of bytes written. Works the same as a file.

Parameters:

- **b** - Bytes. Writes the bytes.

#### method `fernet_files.FernetFile.seek(self, offset, whence=os.SEEK_SET)`

Can be called as:
- seek(self, offset, whence)
- seek(self, offset, whence=whence)

Move through the file. Move by the offset relative to whence. Defaults to the offset being your absolute position (i.e. offset relative to the start of the file). Returns your new absolute position.

Parameters:

- **offset** - Integer. Move this number of bytes relative to whence.
- **whence** - Ignored if using a BytesIO object. Can also be parsed in as an argument (i.e. seek(0, 1)). Accepted values are:
- - `os.SEEK_SET` or `0` - relative to the start of the stream
- - `os.SEEK_CUR` or `1` - relative to the current stream position
- - `os.SEEK_END` or `2` - relative to the end of the stream (use negative offset)

#### method `fernet_files.FernetFile.close(self)`

Writes anything that hasn't been encrypted yet and closes the file. Returns `None` unless the file is a `BytesIO` object, in which case it returns the object without closing it.

#### static method `fernet_files.FernetFile.generate_key()`

Static method. Acts as a pointer to `custom_fernet.FernetNoBase64.generate_key()`, which itself just calls `os.urandom(32)`.

#### bool `fernet_files.FernetFile.closed`

"Is the file closed or not". Please don't modify this, please use `close` instead, however you can check if it's True or False if you want. True means the file is closed, False means the file is open.

#### bool `fernet_files.FernetFile.writeable`

"Is the file writeable or not". True if you can write to the file, False if you can't. Will only be False if you passed in a read-only file. Please don't modify this. Technically you could pass in a read-write file and then set this to False manually to lock the file from being written to, but please only do that if you know what you're doing.

### Misc

#### int `fernet_files.META_SIZE`

DON'T TOUCH UNLESS ABSOLUTELY NECESSARY. Defaults to 8. META_SIZE represented as $M$ in formulae.

The size of a file's metadata in bytes is $2M$.

The first number is a little-endian unsigned $(8M)$-bit integer, representing how many chunks are in the file.

The second number is a little-endian unsigned $(8M)$-bit integer, representing the size of the last chunk's padding.

This simultaneously limits both chunksize and the number of chunks a file can have:
- A chunk can have a max size of $2^{8M}-1$ bytes (default 18,446,744,073,709,551,615)
- A file can have a max $2^{8M}-1$ chunks (default 18,446,744,073,709,551,615)

You have the power to change this value in order to bypass these limitations for future-proofing, HOWEVER, the value you use must be consistent across reading and writing the same file.
Therefore, I recommend you don't change it unless you absolutely have to, for compatibility reasons.

TL;DR if write file with one META_SIZE, must read file with same META_SIZE, and you must store it yourself.

#### int `fernet_files.DEFAULT_CHUNKSIZE`

The chunksize that is used by default.

#### class `fernet_files.custom_fernet.FernetNoBase64(self, key)`

`cryptography.fernet.Fernet` without the base64. See `custom_fernet.py` for more info. You can use it the same as Fernet, but the key and data will never be in base64

## Docs for stuff you shouldn't touch

### `fernet_files.FernetFile`

#### (RawIOBase or BufferedIOBase or BytesIO) `fernet_files.FernetFile.__file`

The file object used for reading and writing. If a filename is provided then this is opened in "wb+" mode.

#### int `fernet_files.FernetFile.__last_chunk`

The chunk number of the last chunk in the file. Chunks are numbered sequentially, starting from 0.

#### int `fernet_files.FernetFile.__last_chunk_padding`

The last chunk is padded with null bytes to make it fill the size of the chunk. This integer stores the size of the padding in bytes.

#### int `fernet_files.FernetFile.__data_chunksize`

Chunksize.

#### int `fernet_files.FernetFile.__chunksize`

The size that chunks take up once they're written to disk. This is calculated with this formula, where c is chunkside:

True chunksize = $c + 73 - (c \mod{16})$

I got this by trial and error. Could I probably find out the actual size of metadata by reading the Fernet spec? Yes, but this was more fun and it hasn't failed yet.

#### bool `fernet_files.FernetFile.__chunk_modified`

True if the chunk has been modified, False if it hasn't. In this context, modified means the data stored within the `self.__chunk` attribute is different to the data stored in that chunk in the file.

#### property int `fernet_files.FernetFile._pos_pointer`

Store our current position in the chunk in bytes. The getter returns `self.__pos_pointer`. The setter ensures that $0\leq$ _pos_pointer $<$ chunksize. If it isn't, then it wraps the value round by adding or subtracting the chunksize, modifying the chunk pointer to compensate.

#### int `fernet_files.FernetFile.__pos_pointer`

Stores the value for `self._pos_pointer`.

#### property int `fernet_files.FernetFile._chunk_pointer`

Stores which chunk we're currently working on. The getter returns `self.__chunk_pointer`. The setter modifies this value, but before it switching chunks it checks if the current chunk has been modified and writes it if it has. After switching chunks, we read the new chunk into memory.

#### int `fernet_files.FernetFile.__chunk_pointer`

Stores the value for `self._chunk_pointer`.

#### method `fernet_files.FernetFile.__goto_current_chunk(self)`

Moves our position in `self.__file` to the location represented by the chunk pointer, taking into account the metadata at the start of the file. Calculated as follows: take the number of the chunk you're currently on, multiply by the size of chunks when they're written to disk. Take the META_SIZE, multiply that by 2 and add it to the number you had before.

#### method `fernet_files.FernetFile.__get__file_size(self)`

Calculate the size of the data contained within file in bytes using the file's metadata. This is the size of the data, not what is written to disk. Calculated as follows: take the number of the last chunk and add 1 to get the total number of chunks there are (because counting starts at 0). Multiply this by the chunksize. Subtract the size of the padding used on the last chunk.

#### method `fernet_files.FernetFile.__read_chunk(self)`

Reads and decrypts the current chunk, turns it into a BytesIO object, stores that object in `self.__chunk` and return it. If the chunk has been modified, it is already loaded into memory so no file operations are done. Also responsible for removing padding if the chunk being read is the last chunk.

#### method `fernet_files.FernetFile.__write_chunk(self)`

Encrypts and writes the chunk, and sets `self.__chunk_modified` to False. Also responsible for applying padding and modifying the metadata at the start of the file if this is the last chunk.

#### method `fernet_files.FernetFile.__enter__(self)`

Returns self so that `with` statements work.

#### method `fernet_files.FernetFile.__exit__(self, exc_type, exc_value, exc_traceback)`

Calls `self.close`, returns `None`.

#### method `fernet_files.FernetFile.__del__(self)`

Calls `self.close`, returns `None`.

### Misc

#### custom_fernet.FernetNoBase64 `fernet_files.FernetFile.__fernet`

FernetNoBase64 object created from the key provided. Used for encryption and decryption.