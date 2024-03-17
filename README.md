# Fernet Files - encryption/decryption of files with cryptography.fernet, but with file-like methods

Fernet encryption requires all data to be encrypted or decrypted at once. This is memory intensive, and it is slow if you only want to read part of a file. Fernet Files provides a simple interface that breaks data up into chunks when encrypting and decrypting them to lower memory usage. Data is only encrypted when it's necessary to do so.

You may treat the class similar to (but not the same as) a file: it has [`read`](#method-fernet_filesfernetfilereadself-size-1---bytes), [`write`](#method-fernet_filesfernetfilewriteself-b---int), [`seek`](#method-fernet_filesfernetfileseekself-offset-whenceosseek_set---int), [`tell`](#method-fernet_filesfernetfiletell---int) and [`close`](#method-fernet_filesfernetfilecloseself---bytesio--none) methods. It can also be context managed, so you can close it using a `with` statement.

## Contents

- [Example usage](#example-usage)
- [Requirements](#requirements)
- [Installation](#installation)
- [Benchmarking](#benchmarking)
- [Documentation for module users](#documentation-for-module-users)
- [Documentation for module developers](#documentation-for-module-developers)

## Example usage

```py
from fernet_files import FernetFile
key = FernetFile.generate_key() # Keep this
with FernetFile(key, "filename.bin") as f:
  # Use like a normal file
  f.write(b'123456789') # Returns 9
  f.seek(4) # Returns 4
  f.read(3) # Returns b'567'
  f.tell() # Returns 7
  ...

# If you check the file after closing (leaving the with statement)
# the contents will be encrypted and unreadable without using the module

# If you use the same key, you can then read the data again
with FernetFile(key, "filename.bin") as f:
    f.read() # Returns b'123456789'
```

You can also supply the chunksize of a file, which affects memory usage, disk usage and performance. Supply this using `FernetFile(key, file, chunksize=123456)`, or omit it to use the default. You can only specify chunksize when first creating a file, after which the chunksize will be read from the file metadata.

Note: The default chunksize is 64KiB. This means the minimum output file size is 64KiB. If you are encrypting a small amount of data, I recommend you lower the chunksize. However, only do this if necessary as this will damage performance.

## Requirements

- cryptography <= 42.0.5, >= 36.0.2
- Python 3.10 or greater (3.10, 3.11 and 3.12 tested)

custom_fernet.py is based on [cryptography 41.0.4](https://github.com/pyca/cryptography/blob/f558199dbf33ccbf6dce8150c2cd4658686d6018/src/cryptography/fernet.py) and is tested up to 42.0.5. Future versions might break this module. If this has happens, create an issue in this repository.

## Installation

```
pip install fernet_files
```

## Benchmarking

Significant results:
When encrypting a 4GiB file, vanilla Fernet:
- Took 106 seconds to encrypt
- Used 28.6GiB of memory to encrypt
- Took 54 seconds to decrypt the data enough that the first byte of unencrypted data could be read

When encrypting the same 4GiB file, Fernet Files with the default chunksize:
- Took 50 seconds to encrypt
- Used 331KiB of memory to encrypt
- Took less than 100ms to decrypt the data enough that the first byte of unencrypted data could be read

For more information, see [BENCHMARKING.md](/benchmarking/v0.1.0/BENCHMARKING.md).

## Documentation for module users

### Contents

- [`fernet_files.FernetFile`](#class-fernet_filesfernetfileself-key-file-chunksize65536)
- - [`fernet_files.FernetFile.read`](#method-fernet_filesfernetfilereadself-size-1---bytes)
- - [`fernet_files.FernetFile.write`](#method-fernet_filesfernetfilewriteself-b---int)
- - [`fernet_files.FernetFile.seek`](#method-fernet_filesfernetfileseekself-offset-whenceosseek_set---int)
- - [`fernet_files.FernetFile.tell`](#method-fernet_filesfernetfiletell---int)
- - [`fernet_files.FernetFile.close`](#method-fernet_filesfernetfilecloseself---bytesio--none)
- - [`fernet_files.FernetFile.generate_key`](#static-method-fernet_filesfernetfilegenerate_key---bytes)
- - [`fernet_files.FernetFile.closed`](#bool-fernet_filesfernetfileclosed)
- - [`fernet_files.FernetFile.writeable`](#method-fernet_filesfernetfilewriteableself---bool)
- - [`fernet_files.FernetFile.seekable`](#method-fernet_filesfernetfileseekableself---bool)
- - [`fernet_files.FernetFile.chunksize`](#property-int-fernet_filesfernetfilechunksize)
- [`fernet_files.META_SIZE`](#int-fernet_filesmeta_size)
- [`fernet_files.DEFAULT_CHUNKSIZE`](#int-fernet_filesdefault_chunksize)
- [`fernet_files.custom_fernet.FernetNoBase64`](#class-fernet_filescustom_fernetfernetnobase64self-key)

### class `fernet_files.FernetFile(self, key, file, chunksize=65536)`

Parameters:

- **key** - A key (recommended) or a [`fernet_files.custom_fernet.FernetNoBase64`](#class-fernet_filescustom_fernetfernetnobase64self-key) object
- - A key must be 32 random bytes. Get using [`fernet_files.FernetFile.generate_key()`](#static-method-fernet_filesfernetfilegenerate_key---bytes) and store somewhere secure
- - Alternatively, pass in a [`fernet_files.custom_fernet.FernetNoBase64`](#class-fernet_filescustom_fernetfernetnobase64self-key) object
- **file** - Accepts a filename as a string, or a file-like object. If passing in a file-like object, it must be open in binary mode and must be seekable.
- **chunksize** - The size of chunks in bytes.
- - Chunksize is stored after the file is created and cannot be altered without creating a new file. When reading an existing file, chunksize is ignored.
- - Bigger chunks use more memory and take longer to read or write, but smaller chunks can be very slow when trying to read/write in large quantities.
- - Bigger chunks apply padding so a very large chunksize will create a large file. Every chunk has its own metadata so a very small chunk size will create a large file.
- - Defaults to 64KiB (65536 bytes).

#### method `fernet_files.FernetFile.read(self, size=-1) -> bytes`

Reads the number of bytes specified and returns them.

Parameters:

- **size** - Positive integer. If -1 or not specified then read to the end of the file.

#### method `fernet_files.FernetFile.write(self, b) -> int`

Writes the given bytes. Returns the number of bytes written.

Parameters:

- **b** - The bytes to be written.

#### method `fernet_files.FernetFile.seek(self, offset, whence=os.SEEK_SET) -> int`

Can be called as:
- seek(self, offset, whence)
- seek(self, offset, whence=whence)

Moves through the file by the specified number of bytes. "whence" determines what this is relative to. Returns your new absolute position as an integer.

Parameters:

- **offset** - Integer. Move this number of bytes relative to whence.
- **whence** - Ignored if using a BytesIO object. Accepted values are:
- - `os.SEEK_SET` or `0` - relative to the start of the stream
- - `os.SEEK_CUR` or `1` - relative to the current stream position
- - `os.SEEK_END` or `2` - relative to the end of the stream (use negative offset)

#### method `fernet_files.FernetFile.tell(self) -> int`

Returns current stream position (position in the file) as an integer.

#### method `fernet_files.FernetFile.close(self) -> BytesIO | None`

Writes all outstanding data closes the file. Returns `None` unless the file is a `BytesIO` object, in which case it returns the object without closing it.

#### static method `fernet_files.FernetFile.generate_key() -> bytes`

Static method used to generate a key. Acts as a pointer to `custom_fernet.FernetNoBase64.generate_key()`.

#### bool `fernet_files.FernetFile.closed`

Boolean attribute representing whether the file is closed or not. True means the file is closed, False means the file is open. It is highly recommended that you do not modify this, and use the [`close`](#method-fernet_filesfernetfilecloseself---bytesio--none) method instead.

#### method `fernet_files.FernetFile.writeable(self) -> bool`

Returns a boolean representing whether the file can be written to or not. `True` if you can write to the file, `False` if you can't. Will only be `False` if you passed in a read-only file, or if the file is closed.

#### method `fernet_files.FernetFile.seekable(self) -> bool`

Returns if the file is seekable or not. Will return `True` unless the file is closed. FernetFile only supports seekable files.

#### property int `fernet_files.FernetFile.chunksize`

Returns the chunksize of the file. Read-only. When opening a file, will attempt to get the value in the following order:
- Try and read the value from the metadata if it exists, or
- Use the value that the user has supplied, or
- Use the default value

### Misc

#### int `fernet_files.META_SIZE`

The size of a file's metadata in bytes. As of v0.2.0, this size is 24 bytes, structured as 3 64-bit unsigned little-endian integers:
- The number of the last chunk in the file (see [`fernet_files.FernetFile.__last_chunk`](#int-fernet_filesfernetfile__last_chunk))
- The amount of padding applied to the last chunk in bytes (see [`fernet_files.FernetFile.__last_chunk_padding`](#int-fernet_filesfernetfile__last_chunk_padding))
- The chunksize of the file

#### int `fernet_files.DEFAULT_CHUNKSIZE`

The chunksize that is used by default, currently 65536 bytes.

#### class `fernet_files.custom_fernet.FernetNoBase64(self, key)`

`cryptography.fernet.Fernet` without any base64 encoding or decoding. See [`custom_fernet.py`](/src/fernet_files/custom_fernet.py) for more info.

## Documentation for module developers

### Contents

- [`fernet_files.FernetFile`](#class-fernet_filesfernetfile)
- - [`fernet_files.FernetFile.__chunk`](#bytesio-fernet_filesfernetfile__chunk)
- - [`fernet_files.FernetFile.__file`](#rawiobase-or-bufferediobase-or-bytesio-fernet_filesfernetfile__file)
- - [`fernet_files.FernetFile.__writeable`](#bool-fernet_filesfernetfile__writeable)
- - [`fernet_files.FernetFile.__last_chunk`](#int-fernet_filesfernetfile__last_chunk)
- - [`fernet_files.FernetFile.__last_chunk_padding`](#int-fernet_filesfernetfile__last_chunk_padding)
- - [`fernet_files.FernetFile.__data_chunksize`](#int-fernet_filesfernetfile__data_chunksize)
- - [`fernet_files.FernetFile.__chunksize`](#int-fernet_filesfernetfile__chunksize)
- - [`fernet_files.FernetFile.__chunk_modified`](#bool-fernet_filesfernetfile__chunk_modified)
- - [`fernet_files.FernetFile._pos_pointer`](#property-int-fernet_filesfernetfile_pos_pointer)
- - [`fernet_files.FernetFile.__pos_pointer`](#int-fernet_filesfernetfile__pos_pointer)
- - [`fernet_files.FernetFile._chunk_pointer`](#property-int-fernet_filesfernetfile_chunk_pointer)
- - [`fernet_files.FernetFile.__chunk_pointer`](#int-fernet_filesfernetfile__chunk_pointer)
- - [`fernet_files.FernetFile.__goto_current_chunk`](#method-fernet_filesfernetfile__goto_current_chunkself---none)
- - [`fernet_files.FernetFile.__get_file_size`](#method-fernet_filesfernetfile__get__file_sizeself---int)
- - [`fernet_files.FernetFile.__read_chunk`](#method-fernet_filesfernetfile__read_chunkself---bytesio)
- - [`fernet_files.FernetFile.__write_chunk`](#method-fernet_filesfernetfile__write_chunkself---none)
- - [`fernet_files.FernetFile.__enter__`](#method-fernet_filesfernetfile__enter__self---fernetfile)
- - [`fernet_files.FernetFile.__exit__`](#method-fernet_filesfernetfile__exit__self-exc_type-exc_value-exc_traceback---none)
- - [`fernet_files.FernetFile.__del__`](#method-fernet_filesfernetfile__del__self---none)
- - [`fernet_files.FernetFile.__fernet`](#custom_fernetfernetnobase64-fernet_filesfernetfile__fernet)

### class `fernet_files.FernetFile`

#### BytesIO `fernet_files.FernetFile.__chunk`

A BytesIO object that stores the contents of the current chunk in memory. When data is written to a chunk, it is this data in memory that is manipulated. The data is then only written to a file when [`__write_chunk`](#method-fernet_filesfernetfile__write_chunkself---none) is called.

#### (RawIOBase or BufferedIOBase or BytesIO) `fernet_files.FernetFile.__file`

The file object used for reading and writing. If a filename is provided then this is opened in "wb+" mode.

#### bool `fernet_files.FernetFile.__writeable`

Used to store if the file is writeable or not, for [`fernet_files.FernetFile.writeable`](#method-fernet_filesfernetfilewriteableself---bool).

#### int `fernet_files.FernetFile.__last_chunk`

The chunk number of the last chunk in the file. Chunks are numbered sequentially, starting from 0.

#### int `fernet_files.FernetFile.__last_chunk_padding`

The last chunk is padded with null bytes to fill the size of the chunk. This integer stores the size of the padding in bytes.

#### int `fernet_files.FernetFile.__data_chunksize`

The amount of data in a chunk in bytes.

#### int `fernet_files.FernetFile.__chunksize`

The size in bytes that chunks take up once they're written to disk. This is calculated with the following formula, where c is chunksize:

True chunksize = $c + 73 - (c \mod{16})$

This formula calculates the size of a Fernet token, based on the [Fernet specification](https://github.com/fernet/spec/blob/master/Spec.md#token-format).

#### bool `fernet_files.FernetFile.__chunk_modified`

Boolean attribute representing whether the data stored in [`self.__chunk`](#bytesio-fernet_filesfernetfile__chunk) has been modified relative to the data stored within the [`self.__file`](#rawiobase-or-bufferediobase-or-bytesio-fernet_filesfernetfile__file). True if the chunk has been modified, False if it hasn't.

#### property int `fernet_files.FernetFile._pos_pointer`

Stores the Fernet file's current position in the chunk in bytes. The getter returns [`self.__pos_pointer`](#int-fernet_filesfernetfile__pos_pointer). The setter ensures that $0\leq$ _pos_pointer $<$ chunksize. If it isn't, then it wraps the value round by adding or subtracting the chunksize, modifying the chunk pointer to compensate.

#### int `fernet_files.FernetFile.__pos_pointer`

Stores the value for [`self._pos_pointer`](#property-int-fernet_filesfernetfile_pos_pointer).

#### property int `fernet_files.FernetFile._chunk_pointer`

Stores the Fernet file's current chunk number. The getter returns [`self.__chunk_pointer`](#int-fernet_filesfernetfile__chunk_pointer). The setter modifies this value. Before it switching chunks it checks if the current chunk has been modified and writes it if it has. After switching chunks, we read the new chunk into memory.

#### int `fernet_files.FernetFile.__chunk_pointer`

Stores the value for [`self._chunk_pointer`](#property-int-fernet_filesfernetfile_chunk_pointer).

#### method `fernet_files.FernetFile.__goto_current_chunk(self) -> None`

Moves our position in [`self.__file`](#rawiobase-or-bufferediobase-or-bytesio-fernet_filesfernetfile__file) to the location represented by the chunk pointer, taking into account the metadata at the start of the file. Calculated as follows: take the number of the chunk you're currently on, multiply by the size of chunks when they're written to disk. Take the META_SIZE, multiply that by 2 and add it to the number you had before.

#### method `fernet_files.FernetFile.__get__file_size(self) -> int`

Calculate the size of the data contained within the file in bytes using the file's metadata. This is the size of the data, not the size of what is written to disk. Calculated as follows: take the number of the last chunk and add 1 to get the total number of chunks (because counting starts at 0). Multiply this by the chunksize. Finally, subtract the size of the padding used on the last chunk.

#### method `fernet_files.FernetFile.__read_chunk(self) -> BytesIO`

Reads and decrypts the current chunk, turns it into a BytesIO object, stores that object in [`self.__chunk`](#bytesio-fernet_filesfernetfile__chunk) and returns it. If the chunk has been modified, it is already loaded into memory so no file operations are done. Also responsible for removing padding if the chunk being read is the last chunk.

#### method `fernet_files.FernetFile.__write_chunk(self) -> None`

Encrypts and writes the chunk, and sets [`self.__chunk_modified`](#bool-fernet_filesfernetfile__chunk_modified) to False. Also responsible for applying padding and modifying the metadata at the start of the file if this is the last chunk.

#### method `fernet_files.FernetFile.__enter__(self) -> FernetFile`

Returns self to allow context management.

#### method `fernet_files.FernetFile.__exit__(self, exc_type, exc_value, exc_traceback) -> None`

Calls [`self.close`](#method-fernet_filesfernetfilecloseself---bytesio--none) and returns `None`.

#### method `fernet_files.FernetFile.__del__(self) -> None`

Calls [`self.close`](#method-fernet_filesfernetfilecloseself---bytesio--none) and returns `None`.

#### custom_fernet.FernetNoBase64 `fernet_files.FernetFile.__fernet`

FernetNoBase64 object created from the key provided. Used for encryption and decryption.