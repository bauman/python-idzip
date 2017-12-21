import random
import string
import gzip
import os
import tempfile

from idzip import api

try:
    range = xrange
except NameError:
    pass


def random_string(size):
    size = int(size)
    letters = [random.choice(string.ascii_letters) for i in range(size)]
    return ''.join(letters).encode("utf8")


IdzipFile = api.IdzipFile


def test_idzip_file_api():
    data = random_string(5e6)

    dfd, dzfile = tempfile.mkstemp(suffix='.dz')
    with IdzipFile(dzfile, 'wb') as writer:
        writer.write(data)

    assert writer.closed

    with IdzipFile(dzfile, 'rb') as reader:
        decoded = reader.read()

    assert reader.closed
    assert data == decoded

    gfd, gzfile = tempfile.mkstemp(suffix='.gz')

    with gzip.open(gzfile, 'wb') as writer:
        writer.write(data)

    with IdzipFile(gzfile, 'rb') as reader:
        decoded = reader.read()

    assert reader.closed
    assert data == decoded

    os.close(gfd)
    os.close(dfd)
    os.remove(dzfile)
    os.remove(gzfile)


if __name__ == '__main__':
    test_idzip_file_api()
