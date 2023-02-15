import idzip
import gzip
import io
from time import time


def test_seeking(report_time=False):
    # tests that SEEK_END behavior matches gzip
    # testing a few things
    # 1. Multi-member (>2GB) works the same as single member
    # 2. idzip should still be faster than gzip
    # 3. Seek to end behaves the same, but
    # 4. Seek to before the end behaves the same
    # 5. Seek to after the end behaves the same

    f = idzip.open("test/data/large.txt.dz")
    g = gzip.open("test/data/large.txt.dz")
    f_s_s = time()  # file_seek_start time
    f_pos = f.seek(0, io.SEEK_END)
    f_s_e = time() # file_seek_end time
    if report_time:
        print(f"idzip seek time: {f_s_e - f_s_s}")
    g_s_s = time()
    g_pos = g.seek(0, io.SEEK_END)
    g_s_e = time()
    if report_time:
        print(f"gzip seek time: {g_s_e - g_s_s}")
    # gzip will find the exact EOF position during the seek
    # idzip can find the exact EOF position during only if using SEEK_END
    assert g_pos == f_pos

    f_r_s = time()  # file_read_start
    f.read(0)
    f_r_e = time()  # file_read_end
    if report_time:
        print(f"idzip read time: {f_r_e - f_r_s}")
    g_r_s = time()
    g.read(0)
    g_r_e = time()
    if report_time:
        print(f"gzip read time: {g_r_e - g_r_s}")

    # the file position should now be synchronized
    f_pos = f.tell()
    g_pos = g.tell()
    if report_time:
        print(f"idzip END: {f_pos}")
        print(f"gzip END:  {g_pos}")
    assert f_pos == g_pos

    g_pos = g.seek(-50, io.SEEK_END)
    f_pos = f.seek(-50, io.SEEK_END)
    assert f_pos == g_pos

    # read past EOF, data should match and position should match
    g_data = g.read(200)
    f_data = f.read(200)
    assert g_data == f_data

    g_pos = g.tell()
    f_pos = f.tell()
    assert g_pos == f_pos

    g.seek(-50, io.SEEK_END)
    f.seek(-50, io.SEEK_END)
    assert f_pos == g_pos

    _ = g.read()
    _ = f.read()
    g_pos = g.tell()
    f_pos = f.tell()
    assert g_pos == f_pos

    g_pos = g.seek(50, io.SEEK_END)
    f_pos = f.seek(50, io.SEEK_END)
    assert f_pos == g_pos
    _ = g.read()
    _ = f.read()
    g_pos = g.tell()
    f_pos = f.tell()
    assert g_pos == f_pos


if __name__ == "__main__":
    test_seeking(report_time=True)
