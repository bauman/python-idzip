import io
import errno
from typing import BinaryIO
from io import RawIOBase

from idzip.compressor import IdzipWriter, MAX_MEMBER_SIZE
from idzip.decompressor import IdzipReader
from gzip import GzipFile


def open(filename: str, mode: str='rb', sync_size: int=MAX_MEMBER_SIZE):
    return IdzipFile(filename, mode, sync_size=sync_size)


def compress(data: bytes, sync_size: int = MAX_MEMBER_SIZE):
    out = io.BytesIO()
    writer = IdzipFile(mode='w', fileobj=out, sync_size=sync_size)
    writer.write(data)
    writer.flush()
    return out.getvalue()


def decompress(data: bytes):
    in_ = io.BytesIO(data)
    return IdzipFile(fileobj=in_).read()


class IdzipFile(RawIOBase):
    def __init__(self, filename: str = None, mode: str = "rb",
                 fileobj: BinaryIO=None,
                 sync_size: int=MAX_MEMBER_SIZE, mtime: int=None):
        self._impl = None
        if 'b' not in mode:
            mode += 'b'
        if "r" in mode:
            try:
                self._impl = self._make_reader(filename, mode, fileobj)
            except IOError:
                self._impl = self._fallback_to_gzip(filename, mode, fileobj)
        elif 'w' in mode:
            if filename is None:
                if fileobj is None:
                    raise ValueError("Must provide a filename or a fileobj argument")
                self._impl = self._make_writer(fileobj, sync_size=sync_size, mtime=mtime)
            else:
                self._impl = self._make_writer(filename, sync_size=sync_size, mtime=mtime)
        else:
            raise IOError("Unsupported mode %r" % mode)
        self.mode = mode

    def _make_reader(self, filename: str, mode: str, fileobj: BinaryIO) -> IdzipReader:
        return IdzipReader(filename, fileobj=fileobj)

    def _fallback_to_gzip(self, filename: str, mode: str, fileobj: BinaryIO) -> GzipFile:
        return GzipFile(filename, mode=mode, fileobj=fileobj)

    def _make_writer(self, filespec, sync_size: int, mtime: int) -> IdzipWriter:
        return IdzipWriter(filespec, sync_size=sync_size, mtime=mtime)

    @property
    def name(self) -> str:
        return self._impl.name

    def close(self):
        return self._impl.close()

    def flush(self):
        return self._impl.flush()

    def write(self, b):
        self._check_can_write()
        value = self._impl.write(b)
        return value

    def read(self, size: int=-1) -> bytes:
        self._check_can_read()
        return self._impl.read(size)

    def tell(self) -> int:
        return self._impl.tell()

    def _check_can_read(self):
        if "r" not in self.mode:
            raise OSError(errno.EBADF, "Cannot read from a write-only file")
        if self.closed:
            raise OSError(errno.EBADF, "Cannot read from a closed file")

    def _check_can_write(self):
        if not (set("wax") & set(self.mode)):
            raise OSError(errno.EBADF, "Cannot write to a read-only file")
        if self.closed:
            raise OSError(errno.EBADF, "Cannot write to a closed file")

    def readable(self) -> bool:
        return self._impl.readable()

    def writable(self) -> bool:
        return self._impl.writable()

    @property
    def closed(self):
        return self._impl.closed

    def seekable(self) -> bool:
        return self._impl.seekable()

    def seek(self, offset: int, whence: int = io.SEEK_SET):
        return self._impl.seek(offset, whence)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def readline(self, size=-1) -> bytes:
        self._check_can_read()
        return self._impl.readline()

    def __iter__(self):
        line = self.readline()
        while line:
            yield line
            line = self.readline()

    def __repr__(self) -> str:
        return "<idzip %s file %r at %s>" % (
            "open" if not self.closed else "closed",
            self.name,
            hex(id(self)))
