#!/usr/bin/env python3
"""news-image-20261122 entrypoint.

Validates the front-page image (assets/entry.png: "The World in One Day
-- Sunday 22 November 2026, 36 stories, 7 regions") and writes it out
byte-for-byte. Standard library only: the grader runs this in a bare
Python 3.13 container with no network and no third-party packages.

Output: if MAKEFUN_OUTPUT_DIR is set, writes <dir>/entry.png; else if a
path is given as the first argument, writes there; otherwise writes the
PNG bytes to stdout. A short summary goes to stderr in every case.
"""
import hashlib
import os
import struct
import sys
import zlib
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024


def validate_png(data):
    """Check the PNG signature, the IHDR dimensions, and every chunk's
    CRC. Returns (width, height). Raises ValueError on any problem."""
    if data[:8] != PNG_SIGNATURE:
        raise ValueError("not a PNG file (bad signature)")
    offset = 8
    width = height = None
    seen_iend = False
    seen_idat = False
    while offset + 8 <= len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        ctype = data[offset + 4:offset + 8]
        end = offset + 8 + length + 4
        if end > len(data):
            raise ValueError("truncated chunk: %r" % ctype)
        stored_crc = struct.unpack(">I", data[offset + 8 + length:end])[0]
        actual_crc = zlib.crc32(ctype + data[offset + 8:offset + 8 + length])
        if actual_crc != stored_crc:
            raise ValueError("bad CRC in chunk: %r" % ctype)
        if ctype == b"IHDR":
            width, height, depth, colour = struct.unpack(
                ">IIBB", data[offset + 8:offset + 18])
            if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
                raise ValueError("unexpected size: %dx%d" % (width, height))
            if depth != 8 or colour != 2:
                raise ValueError("unexpected colour format")
        if ctype == b"IDAT":
            seen_idat = True
        if ctype == b"IEND":
            seen_iend = True
            if end != len(data):
                raise ValueError("trailing data after IEND")
            break
        offset = end
    if width is None:
        raise ValueError("missing IHDR chunk")
    if not seen_idat:
        raise ValueError("missing IDAT chunk")
    if not seen_iend:
        raise ValueError("missing IEND chunk")
    return width, height


def main(argv):
    here = Path(__file__).resolve().parent
    src = here / "assets" / "entry.png"
    data = src.read_bytes()
    width, height = validate_png(data)
    digest = hashlib.sha256(data).hexdigest()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if out_dir:
        out_path = Path(out_dir) / "entry.png"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(data)
    elif len(argv) > 1:
        Path(argv[1]).write_bytes(data)
    else:
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
    print("entry.png: %dx%d, %d bytes, sha256 %s"
          % (width, height, len(data), digest), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
