# Fernet Files - encryption/decryption of files with cryptography.fernet, but with file-like methods

Fernet Files is a very simple module that I'm creating to support one of my own projects.

Fernet encryption is pretty cool, however, the entire file has to be loaded into memory in order to encrypt or decrypt it. This module solves that problem by breaking the file down into chunks. Additionally, this module provides an object that's sort of like a file - it allows you to `read`, `write` and `seek` throughout the file without having to worry about those chunks, and works as being context managed (you can use it with a `with` statement). It won't create a massive CPU overhead by re-encrypting every time you write a single byte either - encryption only happens when switching to a different chunk, or when closing the file.

At this time, Fernet Files only supports the `read`, `write`, `seek` and `close` methods (as well as being context managed so you can close them with a `with` statement), so it is not a true file-like object. Maybe at some point in future (once I've learnt C) I'll come back and make a version of this that returns a true file-like object.

## Installation

It doesn't exist yet.

## Docs

### class `fernet-files.FernetFile(self, key, file, mode, chunksize=65536)`

The only class you should be interacting with.

Parameters:
- **key** - The key for Fernet encryption/decrytion. "Fernet key must be 32 url-safe base64-encoded bytes." Get using `fernet-files.FernetFile.generate_key()` or `cryptography.fernet.Fernet.generate_key()` and then store somewhere secure
- **file** - The file to read/write to. Accepts both filenames as strings and file-like objects.
- **mode** - The mod in which the file is opened. Because I can only encrypt bytes, if "b" is not in the mode string and the string is not "+", then "b" will be appended.
- **chunksize** - The size of chunks in bytes. Bigger chunks use more memory and take longer to read or write, but smaller chunks can be very slow when you try and read lots of them consecutively. Defaults to 64KB.

#### `fernet-files.FernetFile.read(self, size=-1)`

Read. Returns bytes. Works the same as a file.

Parameters:
- **size** - Positive integer. Read this number of bytes. If -1 or not specified then read to the end of the file.

#### `fernet-files.FernetFile.write(self, b)`

Writes the given bytes. Returns the number of bytes written. Works the same as a file.

Parameters:
- **b** - Bytes. Writes the bytes.

#### `fernet-files.FernetFile.seek(self, offset, whence=os.SEEK_SET)`

Move through the file. Move by the offset relative to whence. Defaults to the offset being your absolute position (i.e. offset relative to the start of the file). Returns your new absolute position.

Parameters:
- **offset** - Integer. Move this number of bytes relative to whence.
- **whence** - Accepted values are:
- - `os.SEEK_SET` or `0` - start of the stream
- - `os.SEEK_CUR` or `1` - relative to the current stream position
- - `os.SEEK_END` or `2` - relative to the end of the stream (use negative offset)

#### `fernet-files.FernetFile.close(self)`

Writes anything that hasn't been encrypted yet and closes the file. Returns `None`. Works the same as a file.

#### `fernet-files.FernetFile.generate_key()`

Static method. Acts as a pointer to `cryptography.fernet.Fernet.generate_key()` so you can generate a key without importing `cryptography`.

#### `fernet-files.FernetFile.__enter__(self)`

Returns self so that with statements work.

#### `fernet-files.FernetFile.__exit__(self, exc_type, exc_value, exc_traceback)`

Calls `self.close`, returns `None`.

#### `fernet-files.FernetFile.__del__(self)`

Calls `self.close`, returns `super().__del__()`.

### dictionary `fernet-files._magic_numbers`

This might be incorrect because it comes from my own experimentation and observation but I believe that Fernet enrypted data is always between 58 and 73 bytes (inclusive) bigger than the original data after being decoded from base64. I have also observed that for any given number of bytes of input data (no matter the contents of those bytes), the number of bytes of additional data that Fernet adds is always the same. The keys in this dictionary represent the size of the data that's being encrypted in bytes, and the value is how much bigger the Fernet encrypted output is. You can then get the number of bytes to read by adding the key and the value together.

### function `fernet-files._add_magic(size)`

The function that should be used to get the number of bytes to read, dependent on the size of the input data (the chunk size, except for the last chunk, where the magic number is irrelevant). If the value is in the dictionary, this will return the size plus magic number, returning the number of bytes to read. If the value is not in the dictionary, the magic number will be calculated by completing an encryption operation on some empty data of the desired size.