import unittest
import os
import fernet_files
from cryptography.fernet import Fernet
from base64 import urlsafe_b64decode, urlsafe_b64encode
from io import BytesIO, UnsupportedOperation
from random import randint
from typing import Callable
try:
    from tqdm import tqdm # optional progress bar
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

# Variables:
# BytesIO or normal file
# with or nowith
# invalid, valid, valid from cryptography, incorrect key
# read-only, write-only, or both file
# chunksize: different, invalid
# reading different sizes
# input data: smaller than, equal to and larger than chunk size, empty
# input data: see if random or specific cases cause issues
# test different seeking offsets: random, invalid, smaller, equal and larger than chunk size
# test different whences

# must test EVERY combination of these variables to pass, don't miss anything!

def testing_sizes():
    yield 1 # 1B
    yield 256 # 256B
    yield 4096 # 4KiB
    yield 65536 # 64KiB
    yield 1048576 # 1MiB
    yield 16777216 # 16MiB
    for _ in range(5):
        yield randint(1, 1000) # 1B to 1KiB
    for _ in range(5):
        yield randint(1000, 1000000) # 1KiB to 1MiB
    for _ in range(5):
        yield randint(1000000, 100000000) # 1MiB to 100MiB

def testing_sizes():
    yield 256

def execute_test(desc: str, test: Callable) -> None:
    if TQDM_AVAILABLE:
        pbar = tqdm(desc=desc, total=441) # magic, must be changing if number of test sizes changes
    for chunksize in testing_sizes():
        for inputsize in testing_sizes():
            input_data = os.urandom(inputsize)
            test(chunksize, input_data)
            if TQDM_AVAILABLE: pbar.update(1)

class TestFernetFiles(unittest.TestCase):
    def test_invalid_chunksizes(self):
        for chunksize in (1.5, "1", b"1"):
            self.assertRaises(TypeError, fernet_files.FernetFile, fernet_files.FernetFile.generate_key(), BytesIO(), chunksize=chunksize)
        for chunksize in (0, -1, -2):
            self.assertRaises(ValueError, fernet_files.FernetFile, fernet_files.FernetFile.generate_key(), BytesIO(), chunksize=chunksize)

    def test_key(self):
        # test generate key
        self.assertEqual(fernet_files.FernetFile.generate_key, Fernet.generate_key)
        key = fernet_files.FernetFile.generate_key()
        self.assertIsInstance(key, bytes)
        self.assertEqual(len(urlsafe_b64decode(key)), 32)
        Fernet(key) # valid key
        with fernet_files.FernetFile(Fernet.generate_key(), BytesIO()) as fernet_file: pass # test key from cryptography
        self.assertRaises(ValueError, Fernet, urlsafe_b64encode(os.urandom(33))) # invalid key
        self.assertRaises(TypeError, Fernet, int.from_bytes(os.urandom(32), "little"))

    def test_invalid_file(self):
        for chunksize in testing_sizes():
            with open("test", "wt") as invalid_file:
                self.assertRaises(TypeError, fernet_files.FernetFile, fernet_files.FernetFile.generate_key(), invalid_file, chunksize=chunksize)

    def test_file_nowith_readwrite(self):
        def test(chunksize, input_data):
            key = fernet_files.FernetFile.generate_key()
            with open("test", "wb+") as f:
                fernet_file = fernet_files.FernetFile(key, f, chunksize)
                fernet_file.write(input_data)
                fernet_file.seek(0)
                test_seeking(self, fernet_file, chunksize, input_data)
                test_random_reads(self, fernet_file, chunksize, input_data)
                test_other_read(self, fernet_file, input_data)
                input_data = test_random_writes(self, fernet_file, chunksize, input_data)
                fernet_file.close()
                self.assertRaises(ValueError, fernet_file.seek, 0)
                self.assertRaises(ValueError, fernet_file.read)
                self.assertRaises(ValueError, fernet_file.write, input_data)
            test_random_write_withclose(self, "test", chunksize, input_data)
        execute_test("test_file_nowith_readwrite", test)

    def test_file_nowith_readonly(self):
        def test(chunksize, input_data):
            key = fernet_files.FernetFile.generate_key()
            with open("test", "wb") as f:
                fernet_file = fernet_files.FernetFile(key, f, chunksize)
                fernet_file.write(input_data)
                fernet_file.close()
            with open("test", "rb") as f:
                fernet_file = fernet_files.FernetFile(key, f, chunksize)
                self.assertRaises(UnsupportedOperation, fernet_file.write, input_data)
                fernet_file.seek(0)
                test_seeking(self, fernet_file, chunksize, input_data)
                test_random_reads(self, fernet_file, chunksize, input_data)
                test_other_read(self, fernet_file, input_data)
                fernet_file.close()
                self.assertRaises(ValueError, fernet_file.seek, 0)
                self.assertRaises(ValueError, fernet_file.read)
        execute_test("test_file_nowith_readonly", test)

    def test_file_nowith_writeonly(self):
        def test(chunksize, input_data):
            key = fernet_files.FernetFile.generate_key()
            with open("test", "wb") as f:
                fernet_file = fernet_files.FernetFile(key, f, chunksize)
                fernet_file.write(input_data)
                fernet_file.seek(0)
                test_seeking_noread(self, fernet_file, chunksize, input_data)
                self.assertRaises(UnsupportedOperation, fernet_file.read)
                input_data = test_random_writes(self, fernet_file, chunksize, input_data)
                fernet_file.close()
                self.assertRaises(ValueError, fernet_file.seek, 0)
                self.assertRaises(ValueError, fernet_file.write, input_data)
        execute_test("test_file_nowith_writeonly", test)

    def test_bytesio_nowith(self):
        def test(chunksize, input_data):
            key = fernet_files.FernetFile.generate_key()
            with BytesIO(input_data) as f:
                fernet_file = fernet_files.FernetFile(key, f, chunksize)
                fernet_file.seek(0)
                test_seeking_bytesio(self, fernet_file, chunksize, input_data)
                test_random_reads(self, fernet_file, chunksize, input_data)
                test_other_read(self, fernet_file, input_data)
                input_data = test_random_writes(self, fernet_file, chunksize, input_data)
                fernet_file.close()
                self.assertRaises(ValueError, fernet_file.seek, 0)
                self.assertRaises(ValueError, fernet_file.read)
                self.assertRaises(ValueError, fernet_file.write, input_data)
        execute_test("bytesio_nowith", test)

    def test_file_with_readwrite(self):
        def test(chunksize, input_data):
            key = fernet_files.FernetFile.generate_key()
            with open("test", "wb+") as f:
                with fernet_files.FernetFile(key, f, chunksize) as fernet_file:
                    fernet_file.write(input_data)
                    fernet_file.seek(0)
                    test_seeking(self, fernet_file, chunksize, input_data)
                    test_random_reads(self, fernet_file, chunksize, input_data)
                    test_other_read(self, fernet_file, input_data)
                    input_data = test_random_writes(self, fernet_file, chunksize, input_data)
                self.assertRaises(ValueError, fernet_file.seek, 0)
                self.assertRaises(ValueError, fernet_file.read)
                self.assertRaises(ValueError, fernet_file.write, input_data)
            test_random_write_withclose_withwith(self, "test", chunksize, input_data)
        execute_test("test_file_with_readwrite", test)

    def test_file_with_readonly(self):
        def test(chunksize, input_data):
            key = fernet_files.FernetFile.generate_key()
            with open("test", "wb") as f:
                with fernet_files.FernetFile(key, f, chunksize) as fernet_file:
                    fernet_file.write(input_data)
            with open("test", "rb") as f:
                with fernet_files.FernetFile(key, f, chunksize) as fernet_file:
                    self.assertRaises(UnsupportedOperation, fernet_file.write, input_data)
                    fernet_file.seek(0)
                    test_seeking(self, fernet_file, chunksize, input_data)
                    test_random_reads(self, fernet_file, chunksize, input_data)
                    test_other_read(self, fernet_file, input_data)
                self.assertRaises(ValueError, fernet_file.seek, 0)
                self.assertRaises(ValueError, fernet_file.read)
        execute_test("test_file_with_readonly", test)

    def test_file_with_writeonly(self):
        def test(chunksize, input_data):
            key = fernet_files.FernetFile.generate_key()
            with open("test", "wb") as f:
                with fernet_files.FernetFile(key, f, chunksize) as fernet_file:
                    fernet_file.write(input_data)
                    fernet_file.seek(0)
                    test_seeking_noread(self, fernet_file, chunksize, input_data)
                    self.assertRaises(UnsupportedOperation, fernet_file.read)
                    input_data = test_random_writes(self, fernet_file, chunksize, input_data)
                self.assertRaises(ValueError, fernet_file.seek, 0)
                self.assertRaises(ValueError, fernet_file.write, input_data)
        execute_test("test_file_with_writeonly", test)

    def test_bytesio_with(self):
        def test(chunksize, input_data):
            key = fernet_files.FernetFile.generate_key()
            with BytesIO(input_data) as f:
                with fernet_files.FernetFile(key, f, chunksize) as fernet_file:
                    fernet_file.seek(0)
                    test_seeking_bytesio(self, fernet_file, chunksize, input_data)
                    test_random_reads(self, fernet_file, chunksize, input_data)
                    test_other_read(self, fernet_file, input_data)
                    input_data = test_random_writes(self, fernet_file, chunksize, input_data)
                self.assertRaises(ValueError, fernet_file.seek, 0)
                self.assertRaises(ValueError, fernet_file.read)
                self.assertRaises(ValueError, fernet_file.write, input_data)
        execute_test("bytesio_with", test)

def test_seeking(unit_test: TestFernetFiles, fernet_file: fernet_files.FernetFile, chunksize: int, input_data: bytes) -> None:
    for get_size in (lambda: randint(0, chunksize-1), lambda: chunksize, lambda: randint(chunksize+1, chunksize*3)): # below, equal, above chunksize
        for x in (randint(0, len(input_data)-1) for _ in range(100)): # random starting points
            size = get_size()
            data = input_data[x:x+size]
            unit_test.assertEqual(fernet_file.seek(x), x) # variations of whence input
            unit_test.assertEqual(fernet_file.read(size), data)
            unit_test.assertEqual(fernet_file.seek(x, os.SEEK_SET), x)
            unit_test.assertEqual(fernet_file.read(size), data)
            unit_test.assertEqual(fernet_file.seek(x, 0), x)
            unit_test.assertEqual(fernet_file.read(size), data)
        last = fernet_file.seek(0)
        for _ in range(100):
            size = get_size()
            x = randint(-last, len(input_data)-last-1)
            data = input_data[last+x:last+x+size]
            unit_test.assertEqual(fernet_file.seek(x, os.SEEK_CUR), last+x)
            unit_test.assertEqual(fernet_file.read(size), data)
            unit_test.assertEqual(fernet_file.seek(-x-len(data), os.SEEK_CUR), last)
            unit_test.assertEqual(fernet_file.seek(x, 1), last+x)
            unit_test.assertEqual(fernet_file.read(size), data)
            last += x+len(data)
        for x in (randint(-len(input_data)+1, 0) for _ in range(100)):
            size = get_size()
            if x+size < 0:
                data = input_data[x:x+size]
            elif x == 0:
                data = b''
            else:
                data = input_data[x:]
            unit_test.assertEqual(fernet_file.seek(x, os.SEEK_END), len(input_data)+x)
            unit_test.assertEqual(fernet_file.read(size), data)
            unit_test.assertEqual(fernet_file.seek(x, 2), len(input_data)+x)
            unit_test.assertEqual(fernet_file.read(size), data)
    unit_test.assertRaises(OSError, fernet_file.seek, -1) # Negative
    unit_test.assertRaises(ValueError, fernet_file.seek, 0, 3) # Invalid whence

def test_seeking_noread(unit_test: TestFernetFiles, fernet_file: fernet_files.FernetFile, chunksize: int, input_data: bytes) -> None:
    for x in (randint(0, len(input_data)-1) for _ in range(100)): # random starting points
        unit_test.assertEqual(fernet_file.seek(x), x) # variations of whence input
        unit_test.assertEqual(fernet_file.seek(x, os.SEEK_SET), x)
        unit_test.assertEqual(fernet_file.seek(x, 0), x)
    last = fernet_file.seek(0)
    for _ in range(100):
        x = randint(-last, len(input_data)-last-1)
        unit_test.assertEqual(fernet_file.seek(x, os.SEEK_CUR), last+x)
        unit_test.assertEqual(fernet_file.seek(-x, os.SEEK_CUR), last)
        unit_test.assertEqual(fernet_file.seek(x, 1), last+x)
    for x in (randint(-len(input_data), 0) for _ in range(100)):
        unit_test.assertEqual(fernet_file.seek(x, os.SEEK_END), len(input_data)+x-1)
        unit_test.assertEqual(fernet_file.seek(x, 2), len(input_data)+x-1)
    unit_test.assertRaises(OSError, fernet_file.seek, -1) # Negative
    unit_test.assertRaises(ValueError, fernet_file.seek, 0, 3) # Invalid whence

def test_seeking_bytesio(unit_test: TestFernetFiles, fernet_file: fernet_files.FernetFile, chunksize: int, input_data: bytes) -> None:
    for get_size in (lambda: randint(0, chunksize-1), lambda: chunksize, lambda: randint(chunksize+1, chunksize*3)): # below, equal, above chunksize
        for x in (randint(0, len(input_data)-1) for _ in range(100)): # random starting points
            size = get_size()
            data = input_data[x:x+size]
            unit_test.assertEqual(fernet_file.seek(x), x)
            unit_test.assertEqual(fernet_file.read(size), data)
            unit_test.assertEqual(fernet_file.seek(x, -1), x) # ignored whence
            unit_test.assertEqual(fernet_file.read(size), data)
    unit_test.assertRaises(ValueError, fernet_file.seek, -1) # Negative

def test_random_reads(unit_test: TestFernetFiles, fernet_file: fernet_files.FernetFile, chunksize: int, input_data: bytes) -> None:
    for _ in range(100): # Read data below chunksize
        x = randint(0, readrange) if (readrange := len(input_data)-chunksize-1) >= 0 else 0
        y = randint(x, x+chunksize)
        fernet_file.seek(x)
        unit_test.assertEqual(fernet_file.read(y-x), input_data[x:y])
    for _ in range(100): # Read data equal to chunksize
        x = randint(0, readrange) if (readrange := len(input_data)-chunksize-1) >= 0 else 0
        fernet_file.seek(x)
        unit_test.assertEqual(fernet_file.read(chunksize), input_data[x:x+chunksize])
    for _ in range(100): # Read data above chunksize
        x = randint(0, readrange) if (readrange := len(input_data)-chunksize-1) >= 0 else 0
        y = randint(x+chunksize+1, x+chunksize*3)
        fernet_file.seek(x)
        unit_test.assertEqual(fernet_file.read(y-x), input_data[x:y])

def test_other_read(unit_test: TestFernetFiles, fernet_file: fernet_files.FernetFile, input_data: bytes) -> None:
    fernet_file.seek(0)
    unit_test.assertEqual(fernet_file.read(), input_data) # Full
    fernet_file.seek(0)
    unit_test.assertEqual(fernet_file.read(-1), input_data) # Negative
    fernet_file.seek(0)
    unit_test.assertEqual(fernet_file.read(0), b"") # Empty
    unit_test.assertRaises(TypeError, fernet_file.read, 1.5) # Float
    unit_test.assertRaises(TypeError, fernet_file.read, "1") # String

def test_random_writes(unit_test: TestFernetFiles, fernet_file: fernet_files.FernetFile, chunksize: int, input_data: bytes) -> bytes:
    input_data = bytearray(input_data)
    for get_size in (lambda: randint(0, chunksize-1), lambda: chunksize, lambda: randint(chunksize+1, chunksize*3)): # below, equal, above chunksize
        for _ in range(100): # Get random size and location and write there in file and input data
            size = get_size()
            x = randint(0, writerange) if (writerange := len(input_data)-size-1) >= 0 else 0
            randata = os.urandom(size)
            input_data[x:x+size] = randata
            fernet_file.seek(x)
            fernet_file.write(randata)
    fernet_file.seek(0)
    unit_test.assertEqual(fernet_file.read(), input_data) # if whole file good then all our writes worked
    return input_data

def test_random_write_withclose(unit_test: TestFernetFiles, filename: str, chunksize: int, input_data: bytes) -> None:
    key = fernet_files.FernetFile.generate_key()
    with open(filename, "wb+") as f:
        fernet_file = fernet_files.FernetFile(key, f)
        input_data = test_random_writes(unit_test, fernet_file, chunksize, input_data)
        fernet_file.close()
    with open(filename, "rb") as f:
        fernet_file = fernet_files.FernetFile(key, f)
        unit_test.assertEqual(fernet_file.read(), input_data)
        fernet_file.close()

def test_random_write_withclose_withwith(unit_test: TestFernetFiles, filename: str, chunksize: int, input_data: bytes) -> None:
    key = fernet_files.FernetFile.generate_key()
    with open(filename, "wb+") as f:
        with fernet_files.FernetFile(key, f) as fernet_file:
            input_data = test_random_writes(unit_test, fernet_file, chunksize, input_data)
    with open(filename, "rb") as f:
        with fernet_files.FernetFile(key, f) as fernet_file:
            unit_test.assertEqual(fernet_file.read(), input_data)
                
if __name__ == '__main__':
    unittest.main()
    os.remove("test")