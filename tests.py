import unittest
import os
import fernet_files
from fernet_files.custom_fernet import FernetNoBase64
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

def chunk_testing_sizes():
    yield 1 # 1B
    yield 256 # 256B
    yield 65536 # 64KiB
    yield 16777216 # 16MiB
    for _ in range(3):
        yield randint(1, 1000) # 1B to 1KiB
    for _ in range(3):
        yield randint(1000, 1000000) # 1KiB to 1MiB
    for _ in range(3):
        yield randint(1000000, 100000000) # 1MiB to 100MiB

def input_testing_sizes(chunksize):
    yield 0
    yield 1
    yield chunksize
    yield chunksize + fernet_files._add_magic(chunksize)
    yield chunksize*10
    yield chunksize*10 + fernet_files._add_magic(chunksize*10)

def execute_test(desc: str, test: Callable) -> None:
    if TQDM_AVAILABLE:
        pbar = tqdm(desc=desc, total=78) # magic, must be changing if number of test sizes changes
    for chunksize in chunk_testing_sizes():
        for inputsize in input_testing_sizes(chunksize):
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
        self.assertEqual(fernet_files.FernetFile.generate_key, FernetNoBase64.generate_key)
        key = fernet_files.FernetFile.generate_key()
        self.assertIsInstance(key, bytes)
        self.assertEqual(len(key), 32)
        f = FernetNoBase64(key) # valid key
        with fernet_files.FernetFile(FernetNoBase64.generate_key(), BytesIO()) as fernet_file: pass
        self.assertRaises(ValueError, fernet_files.FernetFile, os.urandom(33), BytesIO()) # invalid key
        self.assertRaises(TypeError, fernet_files.FernetFile, int.from_bytes(os.urandom(32), "little"), BytesIO())
        # test with FernetNoBase64 object
        with fernet_files.FernetFile(f, BytesIO()) as fernet_file: pass

    def test_invalid_file(self):
        for chunksize in chunk_testing_sizes():
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
                test_data_is_encrypted(self, "test", fernet_file, input_data)
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
                test_data_is_encrypted(self, "test", fernet_file, input_data)
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
                input_data = test_random_writes_noread(fernet_file, chunksize, input_data)
                fernet_file.close()
                self.assertRaises(ValueError, fernet_file.seek, 0)
                self.assertRaises(ValueError, fernet_file.write, input_data)
            with open("test", "rb") as f: # Have to re-open file to test writing worked
                fernet_file = fernet_files.FernetFile(key, f, chunksize)
                self.assertEqual(fernet_file.read(), input_data)
                fernet_file.close()
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
                test_data_is_encrypted(self, "test", fernet_file, input_data)
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
                    test_data_is_encrypted(self, "test", fernet_file, input_data)
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
                    test_data_is_encrypted(self, "test", fernet_file, input_data)
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
                    input_data = test_random_writes_noread(fernet_file, chunksize, input_data)
                self.assertRaises(ValueError, fernet_file.seek, 0)
                self.assertRaises(ValueError, fernet_file.write, input_data)
            with open("test", "rb") as f: # Have to re-open file to test writing worked
                with fernet_files.FernetFile(key, f, chunksize) as fernet_file:
                    self.assertEqual(fernet_file.read(), input_data)
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
                    test_data_is_encrypted(self, "test", fernet_file, input_data)
                self.assertRaises(ValueError, fernet_file.seek, 0)
                self.assertRaises(ValueError, fernet_file.read)
                self.assertRaises(ValueError, fernet_file.write, input_data)
        execute_test("bytesio_with", test)

def test_seeking(unit_test: TestFernetFiles, fernet_file: fernet_files.FernetFile, chunksize: int, input_data: bytes) -> None:
    for get_size in (lambda: randint(0, chunksize-1), lambda: chunksize, lambda: randint(chunksize+1, chunksize*3)): # below, equal, above chunksize
        for x in (randint(0, len(input_data)-1 if input_data else 0) for _ in range(100)): # random starting points
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
            x = randint(-last, len(input_data)-last-1 if input_data else 0)
            data = input_data[last+x:last+x+size]
            unit_test.assertEqual(fernet_file.seek(x, os.SEEK_CUR), last+x)
            unit_test.assertEqual(fernet_file.read(size), data)
            unit_test.assertEqual(fernet_file.seek(-x-len(data), os.SEEK_CUR), last)
            unit_test.assertEqual(fernet_file.seek(x, 1), last+x)
            unit_test.assertEqual(fernet_file.read(size), data)
            last += x+len(data)
        for x in (randint(-len(input_data)+1 if input_data else 0, 0) for _ in range(100)):
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
    for x in (randint(0, len(input_data)-1 if input_data else 0) for _ in range(100)): # random starting points
        unit_test.assertEqual(fernet_file.seek(x), x) # variations of whence input
        unit_test.assertEqual(fernet_file.seek(x, os.SEEK_SET), x)
        unit_test.assertEqual(fernet_file.seek(x, 0), x)
    last = fernet_file.seek(0)
    for _ in range(100):
        x = randint(-last, len(input_data)-last-1 if input_data else 0)
        unit_test.assertEqual(fernet_file.seek(x, os.SEEK_CUR), last+x)
        unit_test.assertEqual(fernet_file.seek(-x, os.SEEK_CUR), last)
        unit_test.assertEqual(fernet_file.seek(x, 1), last+x)
        last += x
    for x in (randint(-len(input_data)+1 if input_data else 0, 0) for _ in range(100)):
        unit_test.assertEqual(fernet_file.seek(x, os.SEEK_END), len(input_data)+x)
        unit_test.assertEqual(fernet_file.seek(x, 2), len(input_data)+x)
    unit_test.assertRaises(OSError, fernet_file.seek, -1) # Negative
    unit_test.assertRaises(ValueError, fernet_file.seek, 0, 3) # Invalid whence

def test_seeking_bytesio(unit_test: TestFernetFiles, fernet_file: fernet_files.FernetFile, chunksize: int, input_data: bytes) -> None:
    for get_size in (lambda: randint(0, chunksize-1), lambda: chunksize, lambda: randint(chunksize+1, chunksize*3)): # below, equal, above chunksize
        for x in (randint(0, len(input_data)-1 if input_data else 0) for _ in range(100)): # random starting points
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

def test_random_writes_noread(fernet_file: fernet_files.FernetFile, chunksize: int, input_data: bytes) -> bytes:
    input_data = BytesIO(input_data)
    for get_size in (lambda: randint(0, chunksize-1), lambda: chunksize, lambda: randint(chunksize+1, chunksize*3)): # below, equal, above chunksize
        for _ in range(100): # Get random size and location and write there in file and input data
            size = get_size()
            input_data.seek(0)
            length = len(input_data.read())
            x = randint(0, length-1 if length else 0)
            randata = os.urandom(size)
            input_data.seek(x)
            input_data.write(randata)
            fernet_file.seek(x)
            fernet_file.write(randata)
    input_data.seek(0)
    return input_data.read()

def test_random_writes(unit_test: TestFernetFiles, fernet_file: fernet_files.FernetFile, chunksize: int, input_data: bytes) -> bytes:
    input_data = test_random_writes_noread(fernet_file, chunksize, input_data)
    fernet_file.seek(0)
    unit_test.assertEqual(fernet_file.read(), input_data)
    return input_data

def test_random_write_withclose(unit_test: TestFernetFiles, filename: str, chunksize: int, input_data: bytes) -> None:
    key = fernet_files.FernetFile.generate_key()
    with open(filename, "wb+") as f:
        fernet_file = fernet_files.FernetFile(key, f)
        fernet_file.write(input_data)
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
            fernet_file.write(input_data)
            input_data = test_random_writes(unit_test, fernet_file, chunksize, input_data)
    with open(filename, "rb") as f:
        with fernet_files.FernetFile(key, f) as fernet_file:
            unit_test.assertEqual(fernet_file.read(), input_data)

def test_data_is_encrypted(unit_test: TestFernetFiles, file: str | BytesIO, fernet_file: fernet_files.FernetFile, input_data: bytes) -> None:
    if isinstance(file, str):
        with open(file, "rb") as f:
            output_data = f.read() # Encrypted data
    else:
        file.seek(0)
        output_data = file.read()
    fernet_file.seek(0)
    unit_test.assertNotEqual(input_data, output_data)
                
if __name__ == '__main__':
    unittest.main()
    os.remove("test")
