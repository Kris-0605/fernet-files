# Fernet Files - encryption/decryption of files with cryptography.fernet, but with file-like methods

Fernet encryption requires all data to be encrypted or decrypted at once. This is memory intensive, and it is slow if you only want to read part of a file. Fernet Files provides a simple interface that breaks data up into chunks when encrypting and decrypting them to lower memory usage. Data is only encrypted when it's necessary to do so.

You may treat the class similar to a file: it has `read`, `write`, `seek` and `close` methods. It can also be context managed, so you can close it using a `with` statement.

## Contents

- [Example usage](#example-usage)
- [Requirements](#requirements)
- [Installation](#installation)
- [Benchmarks](#benchmarks)
- [Documentation for module users](#documentation-for-module-usage)
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
  ...

# If you check the file after closing (leaving the with statement)
# the contents will be encrypted and unreadable without using the module

# If you use the same key, you can then read the data again
with FernetFile(key, "filename.bin") as f:
    f.read() # Returns b'123456789'
```

## Requirements

- cryptography >= 41.0.4 (might break in the future, I'll try and keep an eye on it)
- Python 3.10 or greater (3.10, 3.11 and 3.12 tested)

custom_fernet.py is based on cryptography 41.0.4. If the file it's based on is updated, it might break this module. If this has happened, created an issue in this repository.

## Installation

Pending upload to pip

## Benchmarks
### Info

**Based on these benchmarks, the default chunk size is now 64KiB. It is recommended you change this to a smaller value (e.g. 4KiB) for smaller files.**

- Tests can be found in `benchmark.py` and raw results in `benchmark_results.py`
- All values are given to 3sf (significant figures).
- All times are given in milliseconds.
- All bytes are given with their units.

### Time to encrypt

#### Data

| Raw data size  | 1B     | 16B     | 256B    | 4KiB   | 64KiB  | 1MiB   | 16MiB    | 256MiB  | 4GiB     |
|----------------|--------|---------|---------|--------|--------|--------|----------|---------|----------|
| Fernet         | 127ms  | 0.703ms | 0.802ms | 2.16ms | 2.79ms | 15.8ms | 240ms    | 5790ms  | 106000ms |
| FernetNoBase64 | 1.77ms | 2.00ms  | 1.76ms  | 1.89ms | 2.59ms | 8.01ms | 127ms    | 3560ms  | 73500ms  |
| FF 16B         | 1.72ms | 2.17ms  | 8.66ms  | 46.1ms | 368ms  | 5530ms | 260000ms | NT      | NT       |
| FF 256B        | 2.31ms | 2.19ms  | 2.17ms  | 7.97ms | 32.2ms | 338ms  | 21200ms  | NT      | NT       |
| FF 4KiB        | 3.20ms | 2.82ms  | 2.79ms  | 2.92ms | 9.23ms | 34.2ms | 1670ms   | 26600ms | 400000ms |
| FF 64KiB       | 3.85ms | 4.14ms  | 4.12ms  | 4.32ms | 4.42ms | 17.2ms | 214ms    | 3020ms  | 49400ms  |
| FF 1MiB        | 16.0ms | 22.1ms  | 14.8ms  | 15.2ms | 17.5ms | 13.5ms | 174ms    | 2590ms  | 39600ms  |
| FF 16MiB       | 161ms  | 157ms   | 158ms   | 157ms  | 165ms  | 182ms  | 159ms    | 2400ms  | 37300ms  |

#### Observations

- Fernet encryption for 1 byte is an outliar, likely influenced by external factors
- FernetNoBase64 is slower than Fernet for data less than 4KiB, and faster for larger data.
- When using FernetFiles, encryption with low chunk sizes is slow.
- As chunk size increases, encryption speed increases, as chunk size approaches the size of the raw data.
- This gives diminishing returns, as can be seen in the 4GiB tests: 16MiB chunks are only marginally faster than 1MiB chunks.
- When chunk size is equal to raw data size, this is when encryption is fastest.
- As chunk size increases past the data size, encryption slows down again. For any given chunk size, the new encryption speed seems to be relatively constant (if data size is less than the chunk size).
- 64KiB appears to be the optimal default chunk size that covers the most reasonable file sizes. 4KiB may be more reasonable for smaller files.

### Time to read first byte (decryption)

#### Data

| Raw data size  | 1B     | 16B    | 256B | 256MiB | 4GiB    |
|----------------|--------|--------|------|--------|---------|
| Fernet         | 202ms  | 161ms  | ...  | 3570ms | 54100ms |
| FernetNoBase64 | 16.0ms | 27.6ms | ...  | 2010ms | 30700ms |
| FF 16B         | 18.1ms | 33.0ms | ...  | NT     | NT      |
| FF 256B        | 35.0ms | 251ms  | ...  | NT     | NT      |
| FF 4KiB        | 309ms  | 22.4ms | ...  | 54.4ms | 84.6ms  |
| FF 64KiB       | 36.0ms | 38.1ms | ...  | 287ms  | 43.5ms  |
| FF 1MiB        | 94.7ms | 255ms  | ...  | 90.7ms | 58.1ms  |
| FF 16MiB       | 548ms  | 608ms  | ...  | 411ms  | 377ms   |

#### Observations

- FernetNoBase64 is much faster at Fernet at decryption. This is more noticeable the smaller the input data.
- Read times for FernetFiles are too inconsistent for small chunk sizes to draw conclusions. This is likely due to inconsistency in the time it takes to read a file. For this reason, some data has been omitted due to not providing useful insight. Perhaps in future, a random read test, or manipulating data in memory, would be more useful.
- Very large chunk sizes take longer to read, but this isn't noticeable for most typical chunk sizes (less than 1MiB).
- Regardless of the inconsistency, reading a byte of a FernetFile is almost always faster than with Fernet (Fernet requires you to decrypt the entire file).

### Peak memory usage

#### Data

| Raw data size  | 1B      | 16B     | 256B    | 4KiB    | 64KiB   | 1MiB    | 16MiB   | 256MiB  | 4GiB     |
|----------------|---------|---------|---------|---------|---------|---------|---------|---------|----------|
| Fernet         | 10.7KiB | 9.69KiB | 11.1KiB | 36.1KiB | 436KiB  | 6.68MiB | 107MiB  | 1.67GiB | 26.67GiB |
| FernetNoBase64 | 10.6KiB | 9.69KiB | 10.3KiB | 25.4KiB | 265KiB  | 4.01MiB | 64.0MiB | 1.00GiB | 16.0GiB  |
| FF 16B         | 11.2KiB | 10.1KiB | 11.8KiB | 10.9KiB | 11.2KiB | 11.3KiB | 11.0KiB | NT      | NT       |
| FF 256B        | 11.7KiB | 11.2KiB | 11.1KiB | 12.7KiB | 11.8KiB | 12.0KiB | 12.0KiB | NT      | NT       |
| FF 4KiB        | 30.2KiB | 29.9KiB | 30.1KiB | 29.9KiB | 30.5KiB | 30.7KiB | 30.8KiB | 30.9KiB | 30.4KiB  |
| FF 64KiB       | 330KiB  | 330KiB  | 330KiB  | 334KiB  | 330KiB  | 331KiB  | 331KiB  | 331KiB  | 331KiB   |
| FF 1MiB        | 5.01MiB | 5.01MiB | 5.01MiB | 5.01MiB | 5.07MiB | 5.01MiB | 5.01MiB | 5.01MiB | 5.01MiB  |
| FF 16MiB       | 80.0MiB | 80.0MiB | 80.0MiB | 80.0MiB | 80.1MiB | 81.0MiB | 80.0MiB | 80.0MiB | 80.0MiB  |

#### Observations

- Fernet uses approximately 10KB $+$ datasize $\times$ 6.67
- FernetNoBase64 uses approximately 10KB $+$ datasize $\times$ 4
- As a result, FernetFiles uses approximately 10KB $+$ chunksize $\times$ 5, though this can vary slightly due to overhead from padding. (the additional x1 is the memory used to store the chunk)
- FernetFiles offers a trade off: much less memory usage, in exchange for increased processing time. If your objective is to encrypt an extremely large file as quickly as possible, then set the chunk size equal to your available memory divided by 6.
- Memory usage during decryption has not been included in a table because it is very similar to the table. Not this does not mean that the memory usage is similar, but that the trends seen in the data are similar.

## Documentation for module users

### class `fernet_files.FernetFile(self, key, file, chunksize=65536)`

Parameters:

- **key** - A key (recommended) or a `fernet_files.custom_fernet.FernetNoBase64` object
- - A key must be 32 random bytes. Get using `fernet_files.FernetFile.generate_key()` and store somewhere secure
- - Alternatively, pass in a `fernet_files.custom_fernet.FernetNoBase64` object
- **file** - Accepts a filename as a string, or a file-like object. If passing in a file-like object, it would be opened in binary mode.
- **chunksize** - The size of chunks in bytes. 
- - Bigger chunks use more memory and take longer to read or write, but smaller chunks can be very slow when trying to read/write in large quantities.
- - Bigger chunks apply padding so a very large chunksize will create a large file. Every chunk has its own metadata so a very small chunk size will create a large file.
- - Defaults to 64KiB (65536 bytes).

#### method `fernet_files.FernetFile.read(self, size=-1)`

Reads the number of bytes specified and returns them.

Parameters:

- **size** - Positive integer. If -1 or not specified then read to the end of the file.

#### method `fernet_files.FernetFile.write(self, b)`

Writes the given bytes. Returns the number of bytes written.

Parameters:

- **b** - The bytes to be written.

#### method `fernet_files.FernetFile.seek(self, offset, whence=os.SEEK_SET)`

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

#### method `fernet_files.FernetFile.close(self)`

Writes all outstanding data closes the file. Returns `None` unless the file is a `BytesIO` object, in which case it returns the object without closing it.

#### static method `fernet_files.FernetFile.generate_key()`

Static method used to generate a key. Acts as a pointer to `custom_fernet.FernetNoBase64.generate_key()`.

#### bool `fernet_files.FernetFile.closed`

Boolean attribute representing whether the file is closed or not. True means the file is closed, False means the file is open. It is highly recommended that you do not modify this, and use the `close` method instead.

#### bool `fernet_files.FernetFile.writeable`

Boolean attribute representing whether the file can be written to or not. True if you can write to the file, False if you can't. Will only be False if you passed in a read-only file. It is highly recommended that you do not modify this.

### Misc

#### int `fernet_files.META_SIZE`

It is highly recommended you don't modify this. Defaults to 8. META_SIZE represented as $M$ in formulae.

The size of a file's metadata in bytes is $2M$. The first number is a little-endian unsigned $(8M)$-bit integer, representing how many chunks are in the file. The second number is a little-endian unsigned $(8M)$-bit integer, representing the size of the last chunk's padding.

This simultaneously limits both chunksize and the number of chunks a file can have:
- A chunk can have a max size of $2^{8M}-1$ bytes (default 18,446,744,073,709,551,615)
- A file can have a max $2^{8M}-1$ chunks (default 18,446,744,073,709,551,615)

You can change this value in order to bypass these limitations for future-proofing, however, the value you use must be consistent when reading and writing to the same file. Therefore, I recommend you don't change it unless you absolutely have to, for compatibility reasons.

#### int `fernet_files.DEFAULT_CHUNKSIZE`

The chunksize that is used by default, currently 4096 bytes.

#### class `fernet_files.custom_fernet.FernetNoBase64(self, key)`

`cryptography.fernet.Fernet` without any base64 encoding or decoding. See `custom_fernet.py` for more info.

## Documentation for module developers

### class `fernet_files.FernetFile`

#### (RawIOBase or BufferedIOBase or BytesIO) `fernet_files.FernetFile.__file`

The file object used for reading and writing. If a filename is provided then this is opened in "wb+" mode.

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

Boolean attribute representing whether the data stored in `self.__chunk` has been modified relative to the data stored within the `self.__file`. True if the chunk has been modified, False if it hasn't.

#### property int `fernet_files.FernetFile._pos_pointer`

Stores the Fernet file's current position in the chunk in bytes. The getter returns `self.__pos_pointer`. The setter ensures that $0\leq$ _pos_pointer $<$ chunksize. If it isn't, then it wraps the value round by adding or subtracting the chunksize, modifying the chunk pointer to compensate.

#### int `fernet_files.FernetFile.__pos_pointer`

Stores the value for `self._pos_pointer`.

#### property int `fernet_files.FernetFile._chunk_pointer`

Stores the Fernet file's current chunk number. The getter returns `self.__chunk_pointer`. The setter modifies this value. Before it switching chunks it checks if the current chunk has been modified and writes it if it has. After switching chunks, we read the new chunk into memory.

#### int `fernet_files.FernetFile.__chunk_pointer`

Stores the value for `self._chunk_pointer`.

#### method `fernet_files.FernetFile.__goto_current_chunk(self)`

Moves our position in `self.__file` to the location represented by the chunk pointer, taking into account the metadata at the start of the file. Calculated as follows: take the number of the chunk you're currently on, multiply by the size of chunks when they're written to disk. Take the META_SIZE, multiply that by 2 and add it to the number you had before.

#### method `fernet_files.FernetFile.__get__file_size(self)`

Calculate the size of the data contained within the file in bytes using the file's metadata. This is the size of the data, not the size of what is written to disk. Calculated as follows: take the number of the last chunk and add 1 to get the total number of chunks (because counting starts at 0). Multiply this by the chunksize. Finally, subtract the size of the padding used on the last chunk.

#### method `fernet_files.FernetFile.__read_chunk(self)`

Reads and decrypts the current chunk, turns it into a BytesIO object, stores that object in `self.__chunk` and returns it. If the chunk has been modified, it is already loaded into memory so no file operations are done. Also responsible for removing padding if the chunk being read is the last chunk.

#### method `fernet_files.FernetFile.__write_chunk(self)`

Encrypts and writes the chunk, and sets `self.__chunk_modified` to False. Also responsible for applying padding and modifying the metadata at the start of the file if this is the last chunk.

#### method `fernet_files.FernetFile.__enter__(self)`

Returns self to allow context management.

#### method `fernet_files.FernetFile.__exit__(self, exc_type, exc_value, exc_traceback)`

Calls `self.close` and returns `None`.

#### method `fernet_files.FernetFile.__del__(self)`

Calls `self.close` and returns `None`.

#### custom_fernet.FernetNoBase64 `fernet_files.FernetFile.__fernet`

FernetNoBase64 object created from the key provided. Used for encryption and decryption.