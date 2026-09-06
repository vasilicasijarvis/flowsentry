"""Generate current TOTP code for PyPI 2FA setup (RFC 6238, HMAC-SHA1)."""
import hmac
import hashlib
import base64
import struct
import time
import sys

SECRET = "I3VX36VYRAOFJOXDGHMWBY37EB4QP4YE"


def totp(secret: str, offset_windows: int = 0) -> str:
    key = base64.b32decode(secret + "=" * ((8 - len(secret) % 8) % 8))
    counter = int(time.time()) // 30 + offset_windows
    msg = struct.pack(">Q", counter)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    o = h[19] & 15
    code = (struct.unpack(">I", h[o:o + 4])[0] & 0x7FFFFFFF) % 1000000
    return "%06d" % code


if __name__ == "__main__":
    offset = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    print(totp(SECRET, offset))
    print("window_seconds_remaining:", 30 - (int(time.time()) % 30))
