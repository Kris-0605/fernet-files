# Benchmarking

**Based on these benchmarks, the default chunk size is now 64KiB. It is recommended you change this to a smaller value (e.g. 4KiB) for smaller files.**

- Tests can be found in `benchmark.py` and raw results in `benchmark_results.py`
- All values are given to 3sf (significant figures).
- All times are given in milliseconds.
- All bytes are given with their units.

## Time to encrypt

### Data

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

### Observations

- Fernet encryption for 1 byte is an outliar, likely influenced by external factors
- FernetNoBase64 is slower than Fernet for data less than 4KiB, and faster for larger data.
- When using FernetFiles, encryption with low chunk sizes is slow.
- As chunk size increases, encryption speed increases, as chunk size approaches the size of the raw data.
- This gives diminishing returns, as can be seen in the 4GiB tests: 16MiB chunks are only marginally faster than 1MiB chunks.
- When chunk size is equal to raw data size, this is when encryption is fastest.
- As chunk size increases past the data size, encryption slows down again. For any given chunk size, the new encryption speed seems to be relatively constant (if data size is less than the chunk size).
- 64KiB appears to be the optimal default chunk size that covers the most reasonable file sizes. 4KiB may be more reasonable for smaller files.

## Time to read first byte (decryption)

### Data

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

### Observations

- FernetNoBase64 is much faster at Fernet at decryption. This is more noticeable the smaller the input data.
- Read times for FernetFiles are too inconsistent for small chunk sizes to draw conclusions. This is likely due to inconsistency in the time it takes to read a file. For this reason, some data has been omitted due to not providing useful insight. Perhaps in future, a random read test, or manipulating data in memory, would be more useful.
- Very large chunk sizes take longer to read, but this isn't noticeable for most typical chunk sizes (less than 1MiB).
- Regardless of the inconsistency, reading a byte of a FernetFile is almost always faster than with Fernet (Fernet requires you to decrypt the entire file).

## Peak memory usage

### Data

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

### Observations

- Fernet uses approximately 10KB $+$ datasize $\times$ 6.67
- FernetNoBase64 uses approximately 10KB $+$ datasize $\times$ 4
- As a result, FernetFiles uses approximately 10KB $+$ chunksize $\times$ 5, though this can vary slightly due to overhead from padding. (the additional x1 is the memory used to store the chunk)
- FernetFiles offers a trade off: much less memory usage, in exchange for increased processing time. If your objective is to encrypt an extremely large file as quickly as possible, then set the chunk size equal to your available memory divided by 6.
- Memory usage during decryption has not been included in a table because it is very similar to the table. Not this does not mean that the memory usage is similar, but that the trends seen in the data are similar.
