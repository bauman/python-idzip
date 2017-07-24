from idzip.compressor import MAX_MEMBER_SIZE, compress_member
from io import BytesIO
from os import path, SEEK_END

#get a copy of the open standard file open before overwriting
fopen = open

def open(filename):
    from idzip.decompressor import IdzipFile
    try:
        return IdzipFile(filename)
    except IOError as e:
        import logging
        import gzip
        logging.info("Using gzip fallback: %r", e)
        return gzip.open(filename, "rb")

class Writer(object):
    def __init__(self, output, sync_size=MAX_MEMBER_SIZE):
        if isinstance(output, basestring):
            self.output = fopen(output, "wb")
        else:
            self.output = output #hopefully a file like object
            self.output.seek(0) #throw exception now if this isnt a file like obj
        self.input_buffer = BytesIO()
        self.basename = path.basename(path.abspath(self.output.name))
        self.pos = 0
        self.sync_size = sync_size

    def write(self, str_buffer):
        start_pos = self.pos
        self.input_buffer.write(str_buffer)
        self.pos += len(str_buffer)
        curpos = self.input_buffer.tell()
        self.input_buffer.seek(0, SEEK_END)
        buffer_len = self.input_buffer.tell()
        self.input_buffer.seek(curpos)
        if buffer_len > self.sync_size:
            self.sync()
            self.input_buffer = BytesIO()
        return start_pos, len(str_buffer)

    def sync(self):
        self.input_buffer.seek(0, SEEK_END)
        member_size = self.input_buffer.tell()
        self.input_buffer.seek(0)
        compress_member(self.input_buffer, member_size, self.output, self.basename, 0)
        self.input_buffer.truncate(0)
        return self.output.tell()

    def tell(self):
        return self.pos

    def close(self):
        self.sync()
        return self.output.close()

