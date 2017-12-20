import io
import os
import errno

from idzip.compressor import IdzipWriter, MAX_MEMBER_SIZE
from idzip.decompressor import IdzipReader
from gzip import GzipFile


def open(filename, mode='rb', sync_size=MAX_MEMBER_SIZE):
    return IdZipFile(filename, mode, sync_size=MAX_MEMBER_SIZE)


def compress(data, sync_size=MAX_MEMBER_SIZE):
    out = io.BytesIO()
    writer = IdZipFile(mode='w', fileobj=out, sync_size=sync_size)
    writer.write(data)
    return out.getvalue()


def decompress(data):
    in_ = io.BytesIO(data)
    return IdZipFile(fileobj=in_).read()


class IdzipFile(object):
    def __init__(self, filename=None, mode="rb", fileobj=None, sync_size=MAX_MEMBER_SIZE):
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
                self._impl = self._make_writer(fileobj, sync_size=sync_size)
            else:
                self._impl = self._make_writer(filename, sync_size=sync_size)
        else:
            raise IOError("Unsupported mode %r" % mode)
        self.mode = mode

    def _make_reader(self, filename, mode, fileobj):
        return IdzipReader(filename, fileobj=fileobj)

    def _fallback_to_gzip(self, filename, mode, fileobj):
        return GzipFile(filename, mode=mode, fileobj=fileobj)

    def _make_writer(self, filespec, sync_size):
        return IdZipWriter(filespec, sync_size=sync_size)

    @property
    def name(self):
        return self._impl.name

    def close(self):
        return self._impl.close()

    def flush(self):
        return self._impl.flush()

    def write(self, b):
        if "r" in self.mode:
            raise OSError(errno.EBADF, "Cannot write to a read-only file")
        self._impl.write(b)

    def read(self, size=-1):
        if "r" not in self.mode:
            raise OSError(errno.EBADF, "Cannot read from a write-only file")
        return self._impl.read(size)

    def _check_can_read(self):
        if "r" not in self.mode:
            raise OSError(errno.EBADF, "Cannot read from a write-only file")
        if self.closed():
            raise OSError(errno.EBADF, "Cannot read from a closed file")

    def _check_can_write(self):
        if not (set("wax") & set(self.mode)):
            raise OSError(errno.EBADF, "Cannot write to a read-only file")
        if self.closed():
            raise OSError(errno.EBADF, "Cannot write to a closed file")

    def readable(self):
        return self._impl.stream.readable()

    def writable(self):
        return self._impl.stream.writable()

    def closed(self):
        return self._impl.stream.closed()

    def seekable(self):
        return self._impl.stream.seekable()

    def seek(self, offset, whence=io.SEEK_SET):
        return self._impl.seek(offset, whence)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def readline(self, size=-1):
        self._check_can_read()
        return self._impl.readline()

    def __iter__(self):
        line = self.readline()
        while line:
            yield line
            line = self.readline()
