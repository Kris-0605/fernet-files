import tracemalloc
from os import urandom, remove
from os.path import getsize
from time import perf_counter
from cryptography.fernet import Fernet
from fernet_files import FernetFile
from fernet_files.custom_fernet import FernetNoBase64
from tqdm import tqdm

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

    size_difference_percentage = getsize("test")/datasize-1

    remove("test")
    return encryption_time, decryption_time, encryption_memory, decryption_memory, size_difference_percentage

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

    size_difference_percentage = getsize("test")/datasize-1

    remove("test")
    return encryption_time, decryption_time, encryption_memory, decryption_memory, size_difference_percentage

def get_average(func):
    al, bl, cl, dl, el = [], [], [], [], []
    for _ in range(5):
        a, b, c, d, e = func()
        al.append(a), bl.append(b), cl.append(c), dl.append(d), el.append(e)
    output.append((sum(al)/5, sum(bl)/5, sum(cl)/5, sum(dl)/5, sum(el)/5))

def size_3sf(size):
    sig_figs = str(float(f"{(size*100):.3g}"))
    if sig_figs.endswith(".0"): sig_figs = sig_figs[:-2]
    return sig_figs + "%"

def time_3sf(time):
    sig_figs = str(float(f"{(time*1000):.3g}"))
    if sig_figs.endswith(".0"): sig_figs = sig_figs[:-2]
    return sig_figs + "ms"

def bytes_3sf(bytes):
    units = ('B', 'KiB', 'MiB', 'GiB')
    unit_index = 0
    while bytes >= 1024 and unit_index < len(units) - 1:
        bytes /= 1024
        unit_index += 1
    sig_figs = str(float(f"{bytes:.3g}"))
    if sig_figs.endswith(".0"): sig_figs = sig_figs[:-2]
    return sig_figs + units[unit_index]

ff_key = FernetFile.generate_key()
output = []

for datasize in tqdm(iterable=[2**a for a in (0, 10, 20, 25, 28, 30, 31, 32)]):
    data = urandom(datasize)
    fernet = Fernet(Fernet.generate_key())
    get_average(test_fernet)
    fernet = FernetNoBase64(FernetNoBase64.generate_key())
    get_average(test_fernet)
    for chunksize in tqdm(iterable=[2**b for b in (12, 16, 20, 24)]):
        get_average(test_ff)

with open("benchmark_results.txt", "w") as f:
    f.write(f'''
| Raw data size      | 1B | 1KiB | 1MiB | 32MiB | 256MiB | 1GiB | 2GiB | 4GiB |
|---------------=----|----|------|------|-------|--------|------|------|------|
| Fernet             | {time_3sf(output[0][0])}  | {time_3sf(output[6][0])}  | {time_3sf(output[12][0])} | {time_3sf(output[18][0])}  | {time_3sf(output[24][0])}   | {time_3sf(output[30][0])} | {time_3sf(output[36][0])}  | {time_3sf(output[42][0])}  |
| FF 64KiB (default) | {time_3sf(output[3][0])}  | {time_3sf(output[9][0])}  | {time_3sf(output[15][0])} | {time_3sf(output[21][0])}  | {time_3sf(output[27][0])}   | {time_3sf(output[33][0])} | {time_3sf(output[39][0])}  | {time_3sf(output[45][0])}  |
| FernetNoBase64     | {time_3sf(output[1][0])}  | {time_3sf(output[7][0])}  | {time_3sf(output[13][0])} | {time_3sf(output[19][0])}  | {time_3sf(output[25][0])}   | {time_3sf(output[31][0])} | {time_3sf(output[37][0])}  | {time_3sf(output[43][0])}  |
| FF 4KiB            | {time_3sf(output[2][0])}  | {time_3sf(output[8][0])}  | {time_3sf(output[14][0])} | {time_3sf(output[20][0])}  | {time_3sf(output[26][0])}   | {time_3sf(output[32][0])} | {time_3sf(output[38][0])}  | {time_3sf(output[44][0])}  |
| FF 1MiB            | {time_3sf(output[4][0])}  | {time_3sf(output[10][0])} | {time_3sf(output[16][0])} | {time_3sf(output[22][0])}  | {time_3sf(output[28][0])}   | {time_3sf(output[34][0])} | {time_3sf(output[40][0])}  | {time_3sf(output[46][0])}  |
| FF 16MiB           | {time_3sf(output[5][0])}  | {time_3sf(output[11][0])} | {time_3sf(output[17][0])} | {time_3sf(output[23][0])}  | {time_3sf(output[29][0])}   | {time_3sf(output[35][0])} | {time_3sf(output[41][0])}  | {time_3sf(output[47][0])}  |

| Raw data size      | 1B | 1KiB | 1MiB | 32MiB | 256MiB | 1GiB | 2GiB | 4GiB |
|---------------=----|----|------|------|-------|--------|------|------|------|
| Fernet             | {time_3sf(output[0][1])}  | {time_3sf(output[6][1])}  | {time_3sf(output[12][1])} | {time_3sf(output[18][1])}  | {time_3sf(output[24][1])}   | {time_3sf(output[30][1])} | {time_3sf(output[36][1])}  | {time_3sf(output[42][1])}  |
| FF 64KiB (default) | {time_3sf(output[3][1])}  | {time_3sf(output[9][1])}  | {time_3sf(output[15][1])} | {time_3sf(output[21][1])}  | {time_3sf(output[27][1])}   | {time_3sf(output[33][1])} | {time_3sf(output[39][1])}  | {time_3sf(output[45][1])}  |
| FernetNoBase64     | {time_3sf(output[1][1])}  | {time_3sf(output[7][1])}  | {time_3sf(output[13][1])} | {time_3sf(output[19][1])}  | {time_3sf(output[25][1])}   | {time_3sf(output[31][1])} | {time_3sf(output[37][1])}  | {time_3sf(output[43][1])}  |
| FF 4KiB            | {time_3sf(output[2][1])}  | {time_3sf(output[8][1])}  | {time_3sf(output[14][1])} | {time_3sf(output[20][1])}  | {time_3sf(output[26][1])}   | {time_3sf(output[32][1])} | {time_3sf(output[38][1])}  | {time_3sf(output[44][1])}  |
| FF 1MiB            | {time_3sf(output[4][1])}  | {time_3sf(output[10][1])} | {time_3sf(output[16][1])} | {time_3sf(output[22][1])}  | {time_3sf(output[28][1])}   | {time_3sf(output[34][1])} | {time_3sf(output[40][1])}  | {time_3sf(output[46][1])}  |
| FF 16MiB           | {time_3sf(output[5][1])}  | {time_3sf(output[11][1])} | {time_3sf(output[17][1])} | {time_3sf(output[23][1])}  | {time_3sf(output[29][1])}   | {time_3sf(output[35][1])} | {time_3sf(output[41][1])}  | {time_3sf(output[47][1])}  |

| Raw data size      | 1B | 1KiB | 1MiB | 32MiB | 256MiB | 1GiB | 2GiB | 4GiB |
|---------------=----|----|------|------|-------|--------|------|------|------|
| Fernet             | {bytes_3sf(output[0][2])}  | {bytes_3sf(output[6][2])}  | {bytes_3sf(output[12][2])} | {bytes_3sf(output[18][2])}  | {bytes_3sf(output[24][2])}   | {bytes_3sf(output[30][2])} | {bytes_3sf(output[36][2])}  | {bytes_3sf(output[42][2])}  |
| FF 64KiB (default) | {bytes_3sf(output[3][2])}  | {bytes_3sf(output[9][2])}  | {bytes_3sf(output[15][2])} | {bytes_3sf(output[21][2])}  | {bytes_3sf(output[27][2])}   | {bytes_3sf(output[33][2])} | {bytes_3sf(output[39][2])}  | {bytes_3sf(output[45][2])}  |
| FernetNoBase64     | {bytes_3sf(output[1][2])}  | {bytes_3sf(output[7][2])}  | {bytes_3sf(output[13][2])} | {bytes_3sf(output[19][2])}  | {bytes_3sf(output[25][2])}   | {bytes_3sf(output[31][2])} | {bytes_3sf(output[37][2])}  | {bytes_3sf(output[43][2])}  |
| FF 4KiB            | {bytes_3sf(output[2][2])}  | {bytes_3sf(output[8][2])}  | {bytes_3sf(output[14][2])} | {bytes_3sf(output[20][2])}  | {bytes_3sf(output[26][2])}   | {bytes_3sf(output[32][2])} | {bytes_3sf(output[38][2])}  | {bytes_3sf(output[44][2])}  |
| FF 1MiB            | {bytes_3sf(output[4][2])}  | {bytes_3sf(output[10][2])} | {bytes_3sf(output[16][2])} | {bytes_3sf(output[22][2])}  | {bytes_3sf(output[28][2])}   | {bytes_3sf(output[34][2])} | {bytes_3sf(output[40][2])}  | {bytes_3sf(output[46][2])}  |
| FF 16MiB           | {bytes_3sf(output[5][2])}  | {bytes_3sf(output[11][2])} | {bytes_3sf(output[17][2])} | {bytes_3sf(output[23][2])}  | {bytes_3sf(output[29][2])}   | {bytes_3sf(output[35][2])} | {bytes_3sf(output[41][2])}  | {bytes_3sf(output[47][2])}  |

| Raw data size      | 1B | 1KiB | 1MiB | 32MiB | 256MiB | 1GiB | 2GiB | 4GiB |
|---------------=----|----|------|------|-------|--------|------|------|------|
| Fernet             | {bytes_3sf(output[0][3])}  | {bytes_3sf(output[6][3])}  | {bytes_3sf(output[12][3])} | {bytes_3sf(output[18][3])}  | {bytes_3sf(output[24][3])}   | {bytes_3sf(output[30][3])} | {bytes_3sf(output[36][3])}  | {bytes_3sf(output[42][3])}  |
| FF 64KiB (default) | {bytes_3sf(output[3][3])}  | {bytes_3sf(output[9][3])}  | {bytes_3sf(output[15][3])} | {bytes_3sf(output[21][3])}  | {bytes_3sf(output[27][3])}   | {bytes_3sf(output[33][3])} | {bytes_3sf(output[39][3])}  | {bytes_3sf(output[45][3])}  |
| FernetNoBase64     | {bytes_3sf(output[1][3])}  | {bytes_3sf(output[7][3])}  | {bytes_3sf(output[13][3])} | {bytes_3sf(output[19][3])}  | {bytes_3sf(output[25][3])}   | {bytes_3sf(output[31][3])} | {bytes_3sf(output[37][3])}  | {bytes_3sf(output[43][3])}  |
| FF 4KiB            | {bytes_3sf(output[2][3])}  | {bytes_3sf(output[8][3])}  | {bytes_3sf(output[14][3])} | {bytes_3sf(output[20][3])}  | {bytes_3sf(output[26][3])}   | {bytes_3sf(output[32][3])} | {bytes_3sf(output[38][3])}  | {bytes_3sf(output[44][3])}  |
| FF 1MiB            | {bytes_3sf(output[4][3])}  | {bytes_3sf(output[10][3])} | {bytes_3sf(output[16][3])} | {bytes_3sf(output[22][3])}  | {bytes_3sf(output[28][3])}   | {bytes_3sf(output[34][3])} | {bytes_3sf(output[40][3])}  | {bytes_3sf(output[46][3])}  |
| FF 16MiB           | {bytes_3sf(output[5][3])}  | {bytes_3sf(output[11][3])} | {bytes_3sf(output[17][3])} | {bytes_3sf(output[23][3])}  | {bytes_3sf(output[29][3])}   | {bytes_3sf(output[35][3])} | {bytes_3sf(output[41][3])}  | {bytes_3sf(output[47][3])}  |

| Raw data size      | 1B | 1KiB | 1MiB | 32MiB | 256MiB | 1GiB | 2GiB | 4GiB |
|---------------=----|----|------|------|-------|--------|------|------|------|
| Fernet             | {size_3sf(output[0][4])}  | {size_3sf(output[6][4])}  | {size_3sf(output[12][4])} | {size_3sf(output[18][4])}  | {size_3sf(output[24][4])}   | {size_3sf(output[30][4])} | {size_3sf(output[36][4])}  | {size_3sf(output[42][4])}  |
| FF 64KiB (default) | {size_3sf(output[3][4])}  | {size_3sf(output[9][4])}  | {size_3sf(output[15][4])} | {size_3sf(output[21][4])}  | {size_3sf(output[27][4])}   | {size_3sf(output[33][4])} | {size_3sf(output[39][4])}  | {size_3sf(output[45][4])}  |
| FernetNoBase64     | {size_3sf(output[1][4])}  | {size_3sf(output[7][4])}  | {size_3sf(output[13][4])} | {size_3sf(output[19][4])}  | {size_3sf(output[25][4])}   | {size_3sf(output[31][4])} | {size_3sf(output[37][4])}  | {size_3sf(output[43][4])}  |
| FF 4KiB            | {size_3sf(output[2][4])}  | {size_3sf(output[8][4])}  | {size_3sf(output[14][4])} | {size_3sf(output[20][4])}  | {size_3sf(output[26][4])}   | {size_3sf(output[32][4])} | {size_3sf(output[38][4])}  | {size_3sf(output[44][4])}  |
| FF 1MiB            | {size_3sf(output[4][4])}  | {size_3sf(output[10][4])} | {size_3sf(output[16][4])} | {size_3sf(output[22][4])}  | {size_3sf(output[28][4])}   | {size_3sf(output[34][4])} | {size_3sf(output[40][4])}  | {size_3sf(output[46][4])}  |
| FF 16MiB           | {size_3sf(output[5][4])}  | {size_3sf(output[11][4])} | {size_3sf(output[17][4])} | {size_3sf(output[23][4])}  | {size_3sf(output[29][4])}   | {size_3sf(output[35][4])} | {size_3sf(output[41][4])}  | {size_3sf(output[47][4])}  |''')