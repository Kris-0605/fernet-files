# THIS CODE IS MOSTLY NOT MINE
# THIS CODE IS TAKEN FROM THE CRYPTOGRAPHY LIBRARY
#
# This file contains a modified version of cryptography.fernet.Fernet
# The purpose of this modification is to remove base64 encoding/decoding
# While base64 is required for the Fernet spec, it adds processing and storage overhead
# Since I will be storing the data as binary anyway, encoding and then decoding myself felt unnecessary
# I have found that removing base64 encoding and decoding can make encryption/decryption speed twice as fast in some cases
#
# This code is based on https://github.com/pyca/cryptography/blob/f558199dbf33ccbf6dce8150c2cd4658686d6018/src/cryptography/fernet.py
# Therefore, the original code is subject to the same licenses as the above link
# Please see the cryptography library's license at the time of the linked commit for more information
#
# Any code that I have modifed is labelled with a comment
# One change is that I have removed all comments which I didn't create

from cryptography.fernet import Fernet, InvalidToken
from cryptography import utils
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.hmac import HMAC
from os import urandom # Changes to imports
from time import time

class FernetNoBase64(Fernet):
    def __init__(
        self,
        key: bytes # Expects raw key, not base 64 encoded
    ) -> None: # Remove unused parameter backend
        # Modifies input validation to match new input
        if len(key) != 32:
            raise ValueError(
                # Modified error messages
                "Fernet key must be 32 bytes"
            )
        if not isinstance(key, bytes):
            raise TypeError(
                "Fernet key must be 32 bytes"
            )

        self._signing_key = key[:16]
        self._encryption_key = key[16:]

    @staticmethod # We don't need the class, why was this a class method?
    def generate_key() -> bytes:
        return urandom(32) # No encoding

    @staticmethod
    def _get_unverified_token_data(data: bytes) -> tuple[int, bytes]:
        # Modify type hinting so _get_unverified_token_data can't take str
        if not isinstance(data, bytes): # Modify input validation
            raise TypeError("data must be bytes")

        if not data or data[0] != 0x80:
            raise InvalidToken

        if len(data) < 9:
            raise InvalidToken

        timestamp = int.from_bytes(data[1:9], byteorder="big")
        return timestamp, data

    def _encrypt_from_parts(
        self, data: bytes, current_time: int, iv: bytes
    ) -> bytes:
        utils._check_bytes("data", data)

        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(data) + padder.finalize()
        encryptor = Cipher(
            algorithms.AES(self._encryption_key),
            modes.CBC(iv),
        ).encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        basic_parts = (
            b"\x80"
            + current_time.to_bytes(length=8, byteorder="big")
            + iv
            + ciphertext
        )

        h = HMAC(self._signing_key, hashes.SHA256())
        h.update(basic_parts)
        hmac = h.finalize()
        return basic_parts + hmac # Doesn't encode to base64, since we're decoding it anyway
    
    def decrypt(self, token: bytes, ttl: int | None = None) -> bytes: # Modify type hinting so decrypt can't take str
        timestamp, data = FernetNoBase64._get_unverified_token_data(token) # Modify which class is referenced
        if ttl is None:
            time_info = None
        else:
            time_info = (ttl, int(time.time()))
        return self._decrypt_data(data, timestamp, time_info)

    def decrypt_at_time(
        self, token: bytes, ttl: int, current_time: int
    ) -> bytes: # Modify type hinting so decrypt_at_time can't take str
        if ttl is None:
            raise ValueError(
                "decrypt_at_time() can only be used with a non-None ttl"
            )
        timestamp, data = FernetNoBase64._get_unverified_token_data(token) # Modify which class is referenced
        return self._decrypt_data(data, timestamp, (ttl, current_time))

    def extract_timestamp(self, token: bytes) -> int: # Modify type hinting so extract_timestamp can't take str
        timestamp, data = FernetNoBase64._get_unverified_token_data(token) # Modify which class is referenced
        self._verify_signature(data)
        return timestamp