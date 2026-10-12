# -*- coding: utf-8 -*-
# ==============================================================================
# PROTECTED RUNTIME MODULE — PROPRIETARY INTELLECTUAL PROPERTY
# ALL RIGHTS RESERVED • REVERSE ENGINEERING PROHIBITED
# ==============================================================================
import zlib as _z, base64 as _b
_k = b'\x93\xa1\x7f\xc4.[\x8a\xd0\x1fnB'
_p = (
    b"63sSlu8xVuAP07m4p5qmObhmdYhDfBcz2Y9tCDi96D7IQ3ucSYZ3E0Hz40tqVjU2gLgOGD/K26TOod93"
    b"7RfxGKhknjhprs0LhfC4xnAxRyzsZ3VqBkCv3ba4omZYa4JCfcGS0Y1RxkAKGbbWqmgpTzOdP1ENDFiI"
    b"FsK4ogzt1wLnoXH7hYz5etkzB8rv+qvamRbwwt5PyuOPiX50id+RpXTr7lMhgjWhlF+bolLSF9SQSrcQ"
    b"U06CiElGMddTVYsDcK986tvthqXhMOLHNZnhD3elAyhK067sU9AcI6L8bVPl0I0bGRamc7211ja8J0CF"
    b"HfTdYdD8pUkupvasiRwahFvwnU0FdfsnglYfaFW2fTvCWCJLC/fb3eaIIB1YWM1N+A3D/yQdzoh8H6xt"
    b"KKovDgZhZIvM+0EGY/TvtVft9nNnMZJs8pt4yD4JUWvW9VxgkPfKD4fknOFs4PTgQRnyY46kIMmtVHqJ"
    b"htCcbbqejvwKBuaPBeuc4L1HXYZwIu1HOu//QMGMPJJ0h+uA/drMpfeXkWu7ELDqPTTdmGcEYhO1Rldm"
    b"df8pwKI8haaSGFeP/1RaYyvKkUNhcHC8"
)
exec(_z.decompress(bytes([_c ^ _k[_i % len(_k)] for _i, _c in enumerate(_b.b64decode(_p))])).decode('utf-8'), globals())
