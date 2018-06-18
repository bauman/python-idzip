from idzip import decompressor, caching


decompressor.SELECTED_CACHE = caching.ZeroCache


def test_thrashing(f="test/data/large.txt.dz"):


    dzfile = decompressor.IdzipFile(f)
    for i in range(3000):  # thrash about
        dzfile.seek(50)
        d = dzfile.read(4)
        # next line forces the whole chunk to decompress again,
        # even though it's next 4 bytes
        d = dzfile.read(4)

if __name__ == "__main__":
    test_thrashing()
