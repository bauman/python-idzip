"""
This compressor produces a seekable compression format.
It is possible to decompress any part of the output.
The decompression does not need to start from the file beginning.

The format is gzip compatible. Gunzip can uncompress it.
Extra info is stored in the gzip header.

Project description:
http://code.google.com/p/idzip/
"""

import zlib
import struct

from io import BytesIO, UnsupportedOperation
from os import path, SEEK_END, SEEK_SET

from ._stream import _CompressedStreamWrapperMixin

# The chunk length used by dictzip.
CHUNK_LENGTH = 58315

# The max number of chunks is given by the max length of the gzip extra field.
# A new gzip member with a new header is started if hitting that limit.
MAX_NUM_CHUNKS = (0xffff - 10) // 2
MAX_MEMBER_SIZE = MAX_NUM_CHUNKS * CHUNK_LENGTH

# Slow compression is OK.
COMPRESSION_LEVEL = zlib.Z_BEST_COMPRESSION

# Gzip header flags from RFC 1952.
GZIP_DEFLATE_ID = b"\x1f\x8b\x08"
FTEXT, FHCRC, FEXTRA, FNAME, FCOMMENT = 1, 2, 4, 8, 16
FRESERVED = 0xff - (FTEXT | FHCRC | FEXTRA | FNAME | FCOMMENT)
OS_CODE_UNIX = 3


def compress(input, in_size, output, basename=None, mtime=0):
    """Produces a valid gzip output for the given input.
    A gzip file consists of one or many members.
    Each member would be a valid gzip file.
    """
    while True:
        member_size = min(in_size, MAX_MEMBER_SIZE)
        if basename is not None:
            basename = basename.encode("UTF-8")
        _compress_member(input, member_size, output, basename, mtime)
        # Only the first member will carry the basename and mtime.
        basename = None
        mtime = 0

        in_size -= member_size
        if in_size == 0:
            return


def compress_member(input, in_size, output, basename, mtime):
    """ Make the 'private' function public for the writer class
    """
    return _compress_member(input, in_size, output, basename, mtime)


def _compress_member(input, in_size, output, basename, mtime):
    """A gzip member contains:
    1) The header.
    2) The compressed data.
    """
    zlengths_pos = _prepare_header(output, in_size, basename, mtime)
    zlengths = _compress_data(input, in_size, output)

    # Writes the lengths of compressed chunks to the header.
    end_pos = output.tell()
    output.seek(zlengths_pos)
    for zlen in zlengths:
        _write16(output, zlen)

    output.seek(end_pos)


def _compress_data(input, in_size, output):
    """Compresses the given number of input bytes to the output.
    The output consists of:
    1) The compressed data.
    2) 4 bytes of CRC.
    3) 4 bytes of file size.
    """
    assert in_size <= 0xffffffff
    zlengths = []
    crcval = zlib.crc32(b"")
    compobj = zlib.compressobj(COMPRESSION_LEVEL, zlib.DEFLATED,
                               -zlib.MAX_WBITS)

    need = in_size
    while need > 0:
        read_size = min(need, CHUNK_LENGTH)
        chunk = input.read(read_size)
        if len(chunk) != read_size:
            raise IOError("Need %s bytes, got %s" % (read_size, len(chunk)))

        need -= len(chunk)
        crcval = zlib.crc32(chunk, crcval)
        zlen = _compress_chunk(compobj, chunk, output)
        zlengths.append(zlen)

    # An empty block with BFINAL=1 flag ends the zlib data stream.
    output.write(compobj.flush(zlib.Z_FINISH))
    _write32(output, crcval)
    _write32(output, in_size)
    return zlengths


def _compress_chunk(compobj, chunk, output):
    data = compobj.compress(chunk)
    zlen = len(data)
    output.write(data)

    data = compobj.flush(zlib.Z_FULL_FLUSH)
    zlen += len(data)
    output.write(data)
    return zlen


def _prepare_header(output, in_size, basename, mtime):
    """Writes a prepared gzip header to the output.
    The gzip header is defined in RFC 1952.

    The gzip header starts with:
    +---+---+---+---+---+---+---+---+---+---+
    |x1f|x8b|x08|FLG|     MTIME     |XFL|OS |
    +---+---+---+---+---+---+---+---+---+---+
    where:
    FLG ... flags. FEXTRA|FNAME is used by idzip.
    MTIME ... the modification time of the original file or 0.
    XFL ... extra flags about the compression.
    OS ... operating system used for the compression.

    The next header sections are:
    1) Extra field, if the FEXTRA flag is set.
       Its format is described in _write_extra_field().
    2) The original file name, if the FNAME flag is set.
       The file name string is zero-terminated.
    """
    output.write(GZIP_DEFLATE_ID)
    flags = FEXTRA
    if basename:
        flags |= FNAME
    output.write(bytearray([flags]))

    # The mtime will be undefined if it does not fit.
    if mtime > 0xffffffff:
        mtime = 0
    _write32(output, mtime)

    deflate_flags = b"\0"
    if COMPRESSION_LEVEL == zlib.Z_BEST_COMPRESSION:
        deflate_flags = b"\x02"  # slowest compression algorithm
    output.write(deflate_flags)
    output.write(bytearray([OS_CODE_UNIX]))

    zlengths_pos = _write_extra_field(output, in_size)
    if basename:
        output.write(basename + b'\0')  # original basename

    return zlengths_pos


def _write_extra_field(output, in_size):
    """Writes the dictzip extra field.
    It will be initiated with zeros on the place of
    the lengths of compressed chunks.

    The gzip extra field is present when the FEXTRA flag is set.
    RFC 1952 defines the used bytes:
    +---+---+================================+
    | XLEN  | XLEN bytes of "extra field" ...|
    +---+---+================================+

    Idzip adds only one subfield:
    +---+---+---+---+===============================+
    |'R'|'A'|  LEN  | LEN bytes of subfield data ...|
    +---+---+---+---+===============================+

    The subfield ID "RA" stands for Random Access.
    That subfield ID signalizes the dictzip gzip extension.
    The dictzip stores the length of uncompressed chunks
    and the lengths of compressed chunks to the gzip header:
    +---+---+---+---+---+---+==============================================+
    | VER=1 | CHLEN | CHCNT | CHCNT 2-byte lengths of compressed chunks ...|
    +---+---+---+---+---+---+==============================================+

    Two bytes are used to store a length of a compressed chunk.
    So the length of a compressed chunk has to be max 0xfffff.
    That puts a restriction on the CHLEN -- the length of
    uncompressed chunks. Dictzip uses CHLEN=58315.

    Only a fixed number of chunk lengths will fit to the gzip header.
    That limits the max file size of a dictzip file.
    Idzip does not have that limitation. It starts a new gzip member if needed.
    The new member would be also a valid dictzip file.
    """
    num_chunks = in_size // CHUNK_LENGTH
    if in_size % CHUNK_LENGTH != 0:
        num_chunks += 1

    field_length = 3 * 2 + 2 * num_chunks
    extra_length = 2 * 2 + field_length
    assert extra_length <= 0xffff
    _write16(output, extra_length)  # XLEN

    # Dictzip extra field (Random Access)
    output.write(b"RA")
    _write16(output, field_length)
    _write16(output, 1)  # version
    _write16(output, CHUNK_LENGTH)
    _write16(output, num_chunks)
    zlengths_pos = output.tell()
    output.write(b"\0\0" * num_chunks)
    return zlengths_pos


def _write16(output, value):
    """Writes only the lowest 2 bytes from the given number.
    """
    output.write(struct.pack("<H", value & 0xffff))


def _write32(output, value):
    """Writes only the lowest 4 bytes from the given number.
    """
    output.write(struct.pack("<I", value & 0xffffffff))


class IdzipWriter(_CompressedStreamWrapperMixin):
    FILE_EXTENSION = 'dz'
    enforce_extension = True

    def __init__(self, output, sync_size=MAX_MEMBER_SIZE, mtime=0):

        if isinstance(output, basestring):
            self.output = self._prepare_file_stream(output)
            self._should_close = True
        else:
            self.output = output  # hopefully a file like object
            self.output.seek(0)  # throw exception now if this isnt a file like obj
            self._should_close = False
        self.input_buffer = BytesIO()
        try:
            name = path.abspath(self.output.name)
            basename = path.basename(name)
            self.name = name
            self.basename = basename
        except AttributeError:
            self.name = self.basename = ""
        self.pos = 0
        self.sync_size = sync_size
        self.mtime = mtime
        self.compressobj = None
        self._reset_compressor()
        self.version = 1

    def _prepare_file_stream(self, path):
        if self.enforce_extension and not path.endswith(self.FILE_EXTENSION):
            path = "%s.%s" % (path, self.FILE_EXTENSION)
        return open(path, 'wb')

    @property
    def stream(self):
        return self.output

    def _make_compressor(self):
        return zlib.compressobj(
            COMPRESSION_LEVEL, zlib.DEFLATED,
            -zlib.MAX_WBITS)

    def _reset_compressor(self):
        self.compressobj = self._make_compressor()

    def seek(self, offset, whence=SEEK_SET):
        raise UnsupportedOperation("Cannot seek on a write-only stream")

    def write(self, b):
        start_pos = self.pos
        self.input_buffer.write(b)
        self.pos += len(b)
        curpos = self.input_buffer.tell()
        self.input_buffer.seek(0, SEEK_END)
        buffer_len = self.input_buffer.tell()
        self.input_buffer.seek(curpos)
        if buffer_len > self.sync_size:
            self.sync()
            self.input_buffer = BytesIO()
        return start_pos, len(b)

    def sync(self):
        self.compress_member()
        self.input_buffer.truncate(0)
        return self.output.tell()

    def tell(self):
        return self.pos

    def flush(self):
        self.sync()
        return self.output.flush()

    def close(self):
        self.sync()
        if self._should_close:
            return self.output.close()
        return None

    def fileno(self):
        return self.stream.fileno()

    def compress_member(self):
        """A gzip member contains:
        1) The header.
        2) The compressed data.
        """
        self.input_buffer.seek(0, SEEK_END)
        member_size = self.input_buffer.tell()
        self.input_buffer.seek(0)
        zlengths_pos = self._prepare_header(member_size)
        zlengths = self._compress_data(member_size)

        # Writes the lengths of compressed chunks to the header.
        end_pos = self.output.tell()
        self.output.seek(zlengths_pos)
        for zlen in zlengths:
            _write16(self.output, zlen)

        self.output.seek(end_pos)

    def _prepare_header(self, in_size):
        """Writes a prepared gzip header to the output.
        The gzip header is defined in RFC 1952.

        The gzip header starts with:
        +---+---+---+---+---+---+---+---+---+---+
        |x1f|x8b|x08|FLG|     MTIME     |XFL|OS |
        +---+---+---+---+---+---+---+---+---+---+
        where:
        FLG ... flags. FEXTRA|FNAME is used by idzip.
        MTIME ... the modification time of the original file or 0.
        XFL ... extra flags about the compression.
        OS ... operating system used for the compression.

        The next header sections are:
        1) Extra field, if the FEXTRA flag is set.
           Its format is described in _write_extra_field().
        2) The original file name, if the FNAME flag is set.
           The file name string is zero-terminated.
        """
        self.output.write(GZIP_DEFLATE_ID)
        flags = FEXTRA
        if self.basename:
            flags |= FNAME
        self.output.write(bytearray([flags]))

        # The mtime will be undefined if it does not fit.
        if self.mtime > 0xffffffff:
            mtime = 0
        else:
            mtime = self.mtime
        _write32(self.output, mtime)

        deflate_flags = b"\0"
        if COMPRESSION_LEVEL == zlib.Z_BEST_COMPRESSION:
            deflate_flags = b"\x02"  # slowest compression algorithm
        self.output.write(deflate_flags)
        self.output.write(bytearray([OS_CODE_UNIX]))

        zlengths_pos = self._write_extra_field(in_size)
        if self.basename:
            self.output.write(self.basename + b'\0')  # original basename

        return zlengths_pos

    def _write_extra_field(self, in_size):
        """Writes the dictzip extra field.
        It will be initiated with zeros on the place of
        the lengths of compressed chunks.

        The gzip extra field is present when the FEXTRA flag is set.
        RFC 1952 defines the used bytes:
        +---+---+================================+
        | XLEN  | XLEN bytes of "extra field" ...|
        +---+---+================================+

        Idzip adds only one subfield:
        +---+---+---+---+===============================+
        |'R'|'A'|  LEN  | LEN bytes of subfield data ...|
        +---+---+---+---+===============================+

        The subfield ID "RA" stands for Random Access.
        That subfield ID signalizes the dictzip gzip extension.
        The dictzip stores the length of uncompressed chunks
        and the lengths of compressed chunks to the gzip header:
        +---+---+---+---+---+---+==============================================+
        | VER=1 | CHLEN | CHCNT | CHCNT 2-byte lengths of compressed chunks ...|
        +---+---+---+---+---+---+==============================================+

        Two bytes are used to store a length of a compressed chunk.
        So the length of a compressed chunk has to be max 0xfffff.
        That puts a restriction on the CHLEN -- the length of
        uncompressed chunks. Dictzip uses CHLEN=58315.

        Only a fixed number of chunk lengths will fit to the gzip header.
        That limits the max file size of a dictzip file.
        Idzip does not have that limitation. It starts a new gzip member if needed.
        The new member would be also a valid dictzip file.
        """
        num_chunks = in_size // CHUNK_LENGTH
        if in_size % CHUNK_LENGTH != 0:
            num_chunks += 1

        field_length = 3 * 2 + 2 * num_chunks
        extra_length = 2 * 2 + field_length
        assert extra_length <= 0xffff
        _write16(self.output, extra_length)  # XLEN

        # Dictzip extra field (Random Access)
        self.output.write(b"RA")
        _write16(self.output, field_length)
        _write16(self.output, self.version)  # version
        _write16(self.output, CHUNK_LENGTH)
        _write16(self.output, num_chunks)
        zlengths_pos = self.output.tell()
        self.output.write(b"\0\0" * num_chunks)
        return zlengths_pos

    def _compress_data(self, in_size):
        """Compresses the given number of input bytes to the output.
        The output consists of:
        1) The compressed data.
        2) 4 bytes of CRC.
        3) 4 bytes of file size.
        """
        assert in_size <= 0xffffffff
        zlengths = []
        crcval = zlib.crc32(b"")

        need = in_size
        while need > 0:
            read_size = min(need, CHUNK_LENGTH)
            chunk = self.input_buffer.read(read_size)
            if len(chunk) != read_size:
                raise IOError("Need %s bytes, got %s" % (read_size, len(chunk)))

            need -= len(chunk)
            crcval = zlib.crc32(chunk, crcval)
            zlen = self._compress_chunk(chunk)
            zlengths.append(zlen)

        # An empty block with BFINAL=1 flag ends the zlib data stream.
        self.output.write(self.compressobj.flush(zlib.Z_FINISH))
        self._reset_compressor()
        _write32(self.output, crcval)
        _write32(self.output, in_size)
        return zlengths

    def _compress_chunk(self, chunk):
        data = self.compressobj.compress(chunk)
        zlen = len(data)
        self.output.write(data)

        data = self.compressobj.flush(zlib.Z_FULL_FLUSH)
        zlen += len(data)
        self.output.write(data)
        return zlen
