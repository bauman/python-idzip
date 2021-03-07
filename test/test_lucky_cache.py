from idzip import decompressor, caching


decompressor.SELECTED_CACHE = caching.LuckyCache  # default is one item cache
caching.LUCKY_SIZE = 2  # default 32, force swapping for test



def test_thrashing(f="test/data/large.txt.dz"):


    dzfile = decompressor.IdzipFile(f)
    for i in range(3000):  # thrash about
        dzfile.seek(50)
        d = dzfile.read(4)

        dzfile.seek(100000)
        d = dzfile.read(4)

        dzfile.seek(510000)
        d = dzfile.read(4)

        dzfile.seek(7000000)
        d = dzfile.read(4)

if __name__ == "__main__":
    test_thrashing()
