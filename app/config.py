# -*- coding: utf-8 -*-
# ==============================================================================
# PROTECTED RUNTIME MODULE — PROPRIETARY INTELLECTUAL PROPERTY
# ALL RIGHTS RESERVED • REVERSE ENGINEERING PROHIBITED
# ==============================================================================
import zlib as _z, base64 as _b
_k = b'\x93\xa1\x7f\xc4.[\x8a\xd0\x1fnB'
_p = (
    b"63vakPM1UOAH043A+eHwrw+4OKUHAEnk32KjEYnyeTztvzZn3k857OtzBpgobvFXPlHeRdkjimKYoBvX"
    b"uf5jCjxBMh3a0DXrLyqayY2z1I8QkuEJlHf4r7k9dF4+XPMOP+ZTKqwYJFWa5cGtInuwBZKPiF9VYUm1"
    b"ncFoTZkQ5wxsSsV9kklkxJhm5RG2PCK7Exp+xCBKLD/qQTn59iG8sd60oS/JQLlyoybIjSR7BFJZ/s7m"
    b"GmdqIBWuR4TY3RLVFUimAqtUAUixXsNgNzvQWR3f+2QtGJvLgc5agmRmvkqgF7Z1+j+zxtlAvai2uAqf"
    b"juW622oDr+2oJYzJ2FIXsAEBfdGe61bLfYcb+iXU7+Vz6/LalH5nzkoXc4gpj33qlqwyn4XUWlHM9pQT"
    b"4XVyGKx+SR/epnIiWbyOFZ77Npxs//AtdiK10YIDPK3+laKYQtYGP+wL9v/bbpecaVObXO+VAFEccgcF"
    b"ffNw4+4aBpxv0UVRqTOrKLe0HCKCwaapOqkouRJYN5hNvKrkbJm7shIrxq/c3V6nPbAUxYazk2Y5ycCV"
    b"BMgMT+uC2nbFsCW8Bow01b+lM5liVHK8P+LeBamx8I5CHX8fhA2L7fg5J0pwpAJNHudmefwVa9q+DBYl"
    b"sW2+/a4qrdt5hj6OmmWHjqkfrBmWXmn6DL0dkyJavWGRG+ix1GZ/zWjCS7l10vgf+87hYTSLptF+yJtZ"
    b"1C2NAK/9COu0yoDGIZsZ6zWxBE+1bpKI3vp91zPB7ORhg0698MgGvoePvuJUSfnAxOQGig13tX1A9Za/"
    b"4ge9T15eRtUOnf+zZyZyrm5UgcUEM1Vn"
)
exec(_z.decompress(bytes([_c ^ _k[_i % len(_k)] for _i, _c in enumerate(_b.b64decode(_p))])).decode('utf-8'), globals())
