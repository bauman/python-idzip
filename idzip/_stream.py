

class _CompressedStreamWrapperMixin(object):

    @property
    def closed(self):
        return self.stream.closed

    def seekable(self):
        return self.stream.seekable()

    def readable(self):
        return self.stream.readable()

    def writable(self):
        return self.stream.writable()
