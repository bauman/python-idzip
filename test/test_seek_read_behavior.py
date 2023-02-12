import idzip
import gzip
import io
from time import time

def test_seeking(report_time=False):
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
    # idzip can find the exact EOF position during a read call
    assert g_pos != f_pos

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
        print(f"seek+read END time comparison: {((f_r_e - f_r_s) / (g_s_e - g_s_s)) * 100}%")

    # the file position should now be synchronized
    f_pos = f.tell()
    g_pos = g.tell()
    if report_time:
        print(f"idzip END: {f_pos}")
        print(f"idzip END: {g_pos}")
    assert f_pos == g_pos


if __name__ == "__main__":
    test_seeking(report_time=True)
