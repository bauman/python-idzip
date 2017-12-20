from idzip.compressor import MAX_MEMBER_SIZE, compress_member
from idzip.api import (
    IdZipFile, compress, decompress, open as dzopen,
    IdZipWriter as Writer)

# get a copy of the open standard file open before overwriting
fopen = open
open = dzopen


__all__ = [
    "MAX_MEMBER_SIZE", "compress_member",
    "IdZipFile", "compress", "decompress",
    "Writer", "open"
]
