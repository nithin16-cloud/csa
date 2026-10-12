# -*- coding: utf-8 -*-
# ==============================================================================
# PROTECTED RUNTIME MODULE — PROPRIETARY INTELLECTUAL PROPERTY
# ALL RIGHTS RESERVED • REVERSE ENGINEERING PROHIBITED
# ==============================================================================
import zlib as _z, base64 as _b
_k = b'\x93\xa1\x7f\xc4.[\x8a\xd0\x1fnB'
_p = (
    b"63sskiaRpf1WQxS76TMKYBfFhdeiib9oMwjn98D81qKNcKN/eA1QTg=="
)
exec(_z.decompress(bytes([_c ^ _k[_i % len(_k)] for _i, _c in enumerate(_b.b64decode(_p))])).decode('utf-8'), globals())
