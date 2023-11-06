# Fernet Files - treat encryption and decryption of files with cryptography.fernet like a file-like object

Fernet Files is a very simple module that I'm creating to support one of my own projects.

Fernet encryption is pretty cool, however, the entire file has to be loaded into memory in order to encrypt or decrypt it. This module solves that problem by breaking the file down into chunks. Additionally, this module provides a file-like object that allows you to read, write, seek, whatever you want throughout the file without having to worry about those chunks. It won't create a massive CPU overhead by re-encrypting every time you write a single byte either - encryption only happens when switching to a different chunk, or when closing the file.

## Installation

It doesn't exist yet.

## Docs

I'll write this later.
