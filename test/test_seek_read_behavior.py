import idzip
import io


def test_seeking():
    f = idzip.open("test/data/large.txt.dz")
    f.seek(0, io.SEEK_END)
    initial = f.tell()
    f.read(0)
    final = f.tell()
    assert initial != final