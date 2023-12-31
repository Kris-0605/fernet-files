import tracemalloc
from os import urandom, remove
from os.path import getsize
from time import perf_counter
from cryptography.fernet import Fernet
from fernet_files import FernetFile
from fernet_files.custom_fernet import FernetNoBase64

def fernet_encrypt():
    with open("test", "wb") as f:
        f.write(fernet.encrypt(data))

def fernet_decrypt():
    with open("test", "rb") as f:
        fernet.decrypt(f.read())[0]

def test_fernet():
    timer = perf_counter()
    fernet_encrypt()
    encryption_time = perf_counter() - timer

    timer = perf_counter()
    fernet_decrypt()
    decryption_time = perf_counter() - timer

    remove("test")

    tracemalloc.start()
    fernet_encrypt()
    _, encryption_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    tracemalloc.start()
    fernet_decrypt()
    _, decryption_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"{'FernetNoBase64' if isinstance(fernet, FernetNoBase64) else 'Fernet'} {datasize} bytes:\n{encryption_time} seconds to encrypt\n{decryption_time} seconds to read first byte\n{encryption_memory} bytes peak memory to encrypt\n{decryption_memory} bytes peak memory to decrypt\nOutput filesize {getsize('test')} bytes")
    remove("test")

def ff_encrypt():
    with FernetFile(ff_key, "test", chunksize=chunksize) as f:
        f.write(data)

def ff_decrypt():
    with FernetFile(ff_key, "test", chunksize=chunksize) as f:
        f.read(1)

def test_ff():
    timer = perf_counter()
    ff_encrypt()
    encryption_time = perf_counter() - timer

    timer = perf_counter()
    ff_decrypt()
    decryption_time = perf_counter() - timer

    remove("test")

    tracemalloc.start()
    ff_encrypt()
    _, encryption_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    tracemalloc.start()
    ff_decrypt()
    _, decryption_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"FernetFile chunksize {chunksize} bytes, datasize {datasize} bytes:\n{encryption_time} seconds to encrypt\n{decryption_time} seconds to read first byte\n{encryption_memory} bytes peak memory to encrypt\n{decryption_memory} bytes peak memory to decrypt\nOutput filesize {getsize('test')} bytes")
    remove("test")

ff_key = FernetFile.generate_key()

for datasize in (2**a for a in range(0, 36, 4)):
    data = urandom(datasize)
    fernet = Fernet(Fernet.generate_key())
    test_fernet()
    for chunksize in (2**b for b in range(0, 36, 4)):
        test_ff()