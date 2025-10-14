#!/usr/bin/env python
"""Usage: %prog [OPTION]... FILE...
Compresses the given files.
"""

import os
import argparse
import logging

import idzip
from idzip import compressor

DEFAULT_SUFFIX = ".dz"

def _parse_args():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("-d", "--decompress", action="store_true",
            help="decompress the file")
    parser.add_argument("-S", "--suffix",
            help="change the default suffix (default=%s)" % DEFAULT_SUFFIX)
    parser.add_argument("-k", "--keep", action="store_true",
            help="don't unlink the processed files")
    parser.add_argument("-v", "--verbose", action="count",
            help="increase verbosity")
    parser.add_argument('files', nargs='+', help='the files to compress')
    parser.set_defaults(verbose=0, suffix=DEFAULT_SUFFIX, keep=False)

    args = parser.parse_args()
    if not args.suffix or "/" in args.suffix:
        parser.error("Incorrect suffix: %r" % args.suffix)

    if len(args.files) == 0:
        parser.error("An input file is required.")

    return args


def _compress(filename, options):
    input = open(filename, "rb")
    inputinfo = os.fstat(input.fileno())
    basename = os.path.basename(filename)

    target = filename + options.suffix
    logging.info("compressing %r to %r", filename, target)
    output = open(target, "wb")
    compressor.compress(input, inputinfo.st_size, output,
            basename, int(inputinfo.st_mtime))

    _finish_output(output, options)
    input.close()
    return True


def _decompress(filename, options):
    """Decompresses the whole file.
    It is useful mainly for testing. Normal gunzip is enough
    when uncompressing a file from the beginning.
    """
    suffix = options.suffix
    if not filename.endswith(suffix) or len(filename) == len(suffix):
        logging.warn("without %r suffix -- ignored: %r",
                suffix, filename)
        return False

    target = filename[:-len(suffix)]
    input = idzip.open(filename)
    logging.info("uncompressing %r to %r", filename, target)
    output = open(target, "wb")
    while True:
        data = input.read(1024)
        if not data:
            break

        output.write(data)

    _finish_output(output, options)
    input.close()
    return True


def _finish_output(output, options):
    if not options.keep:
        # We want to preserve at least one copy of the data.
        output.flush()
        os.fsync(output.fileno())
    output.close()


def main():
    args = _parse_args()
    logging.basicConfig(level=logging.WARNING - 10*args.verbose)

    action = _compress
    if args.decompress:
        action = _decompress

    for filename in args.files:
        ok = action(filename, args)
        if ok and not args.keep:
            os.unlink(filename)


if __name__ == "__main__":
    main()

