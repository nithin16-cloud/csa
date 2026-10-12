# -*- coding: utf-8 -*-
# ==============================================================================
# PROTECTED RUNTIME MODULE — PROPRIETARY INTELLECTUAL PROPERTY
# ALL RIGHTS RESERVED • REVERSE ENGINEERING PROHIBITED
# ==============================================================================
import zlib as _z, base64 as _b
_k = b'\x93\xa1\x7f\xc4.[\x8a\xd0\x1fnB'
_p = (
    b"63syCBNRSeAT6KPOBm9dPHNPm4juLEL813VyV3vf3YC7+PJ1FdqqeHB/S+O87IzDTfFPyoErfmyzIzKU"
    b"Wg55urh9ru3a7aFZuuNCpLaigQxSipfCVBQd0As46Nleh9qn9Be3aUsQvnSMkR6gmjJdzI/B8OC+8Q=="
)
exec(_z.decompress(bytes([_c ^ _k[_i % len(_k)] for _i, _c in enumerate(_b.b64decode(_p))])).decode('utf-8'), globals())
