import idzip


if __name__ == "__main__":
    src = "test/data/bigrandom"
    dest = "test/data/big_out.txt"
    with open(src, 'rb') as infh, idzip.open(dest, 'wb') as outfh:
        #chunk_size = idzip.MAX_MEMBER_SIZE
        chunk_size = 2 ** 28
        chunk = infh.read(chunk_size)
        while chunk:
            outfh.write(chunk)
            chunk = infh.read(chunk_size)