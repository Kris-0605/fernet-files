# Fernet Files - encryption/decryption of files with cryptography.fernet, but with file-like methods

Fernet encryption requires all data to be encrypted or decrypted at once. This is memory intensive, and it is slow if you only want to read part of a file. Fernet Files provides a simple interface that breaks data up into chunks when encrypting and decrypting them to lower memory usage. Data is only encrypted when it's necessary to do so.

You may treat the class similar to a file: it has `read`, `write`, `seek`, `tell` and `close` methods. It can also be context managed, so you can close it using a `with` statement.

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

Note: The default chunksize is 64KiB. This means the minimum output file size is 64KiB. If you are encrypting a small amount of data, I recommend you lower the chunksize. However, only do this if necessary as this will damage performance.

## Requirements

- cryptography <= 42.0.5, >= 36.0.2
- Python 3.10 or greater (3.10, 3.11 and 3.12 tested)

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

## Repository and documentation

The repository for this project, which contains more detailed documentation, can be found [here](https://github.com/Kris-0605/fernet_files).