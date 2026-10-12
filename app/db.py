# -*- coding: utf-8 -*-
# ==============================================================================
# PROTECTED RUNTIME MODULE — PROPRIETARY INTELLECTUAL PROPERTY
# ALL RIGHTS RESERVED • REVERSE ENGINEERING PROHIBITED
# ==============================================================================
import zlib as _z, base64 as _b
_k = b'\x93\xa1\x7f\xc4.[\x8a\xd0\x1fnB'
_p = (
    b"63uqnUc0URYJk6zM0ODGen8q+Kn9dhaqAmQLgZx62rsQtOl8RgwcWOxMctfYzcKb0ZWGpzIwECjh+sBP"
    b"Y7kngdWdKkXUcSZ5gC/tFoZNvrLHn/kzt5jZhgA0OkeyY4JIADe06dwLIJxiJyg93mH1GEwJs7Ltl5sx"
    b"78WSgvQgA8LxrE3wxG2YFagNpmJCVfBasCF43BjoJyOq8HwzYvR00P88nviZl6A67CRtg5XmbanDpavm"
    b"WY3GTirTGof/92GB2jIrZZzPdXn3g8wl8HzWgNuA5jNvc9QGG6Ev065S5wHT4lr02T7temxGT7L+Z6mF"
    b"kG+0bZggpRNb/7+mHVMDRzSnhVqUjSQ0lu2dYyPQeG3mrQgr3bF19PmBCxQ329bsHXT4R3a7lfxGLWIN"
    b"nzr4veFYWnNd2tmWWhPMd1yDI/x7YJRvynTgWYNp8AXi2MWPu/+TBy3RVIjjUY1g5aKs4pfQbQB738Hr"
    b"q7igHaRQwR58wg3eqv5XZ760bNjjf4jtfuqHQbIxXjw1ritiV0tatXhTlRZkkk4voAz4wHj6CP3L0gXp"
    b"QWT91EXQJmlJimZQQR74zcPsneZjZLg4nteji7TMOtBGybcVvBSXCFICwchctatUiJ1sIrukHJHcvVd8"
    b"HvW23gcC1YHbFDUE9ePQsBaXYJ+c1QT03DNjQ+gn6FWJKdRbRmGcsRoMWs2k0bJEzqaD/5xQB7O7iUQm"
    b"Nrd6M7X5z3aXttAsQThohoFD2SYAX86vEMmE08DFcFv+W/a60CPJA+6XmeXc+CnjzrPi1t8lTxZjbRiS"
    b"0bmu1FWJcnDt02eE8QPgvLDbgLTUmPAv52r/zNoOfIpFVPxeEtaDyZ+o3byQnVuCblD1tlMMVdoF92ST"
    b"Qsa3LhUh3eq4BUtgKOULeqL+NYSZfjEwx79D7jUv780orNz9EmMSjopIKtYoKj+yIwkw1kKfh2FMBwm+"
    b"TyqCN1qCWBcnaRPVZPKt7U+flHhti6dlw0oDeFG21Imz18v3jluYP/h94n+yuVyPvuCIT8Q7rnLETnfk"
    b"oU6pBxg6OI3dhP3I0d4Psvl7uYhXb7NpK6bqGLW9GsC4PlGVJhRcC1ehTavEMKuvftA3ccgjmposekPZ"
    b"oGjb8hZ3zBDFrmS/5mz+6qs1taKfsUL4sm6BB7hP1F4VFUHNaAy2w2hOSZc/aucEDEDQwdzyJg4nHlcO"
    b"rEr8CXiHk8c3rtdABRbwhS4QXDq3i7Kj+4e76V7d6jskorFHy4rOucQViWCJYAXQBSQAzbp46RDwwowc"
    b"d8jXb9300EEcFNJ96v5EpYRvz98CqzwZ7NEvu6vdVB8UHQVKcQGUTejD3nVYel8M484Fq9Sw2I2ZNAT3"
    b"WZF41IVCNR7/znsxqEFPqiATWnIZ7Qj+EIMVQqLVw8G8d2et1bqd5HAIWIaNMwYj/6X6rA4HmW2HMZPm"
    b"+BRYlxRZAxtziVfIjAiaF21cXK2d6WSnVSDIKECXBiXYEqtK7T0SF2/sURri5YewBdVpFHrf409Nypgy"
    b"Z80DWZ2mTtaDLKUEIr2+T7wwAisG5xdrJOp3wwX5xK0HAQiUj2/jubAct4SQrQFMtRr2cYzJYGVpGXGB"
    b"FmAeoGm83nvdzRw5AogphlV3+W0loNTdYXHRaDxk8n/vCWNEqSyvUywJEZNzCCvIrmSwS7F/CPtI/1ch"
    b"Nj/3VhQe4YJ0elzWrxC4Jh8UQFb1iFvYSdywBnyM0+3KU20DRpH5JI6wxrOIjiQG2XBj7vGXa5aABXkv"
    b"8H1J/kje7EEoRB9XF/hiAIKXpNOhGb1oor8FKMH7ekPb9U617HHbyaTwOerE3M0Ib5W4FXWr4ec3tioz"
    b"7QSg+P+9W8FC7oLT8WUF17BD+3a7D3dsG98b9/FN9WWuKJECwvzrOMogqsXHadT12310qvv5SPYCKDpN"
    b"y3SaXP2+xlPx/bEdMx62o4G1prvkJHFMxz1ilzub4sbXd2rTEhI0Q9V6hl+IJYaEbHrNjrQDHpJDr24t"
    b"IVwdk3RUqEXVm5Dm+70TN46pB+dFoeOaPni5pvggO6Pqw73j6TwzjwESsjtHTkrC0u/hj/VoPjT1k6oH"
    b"9T7l9lfG3icsXFo05NJRZTvwWKONqloQ7Ag7wKdnnlirRbCwVfF9PAppOvHC3MYVup2XzLO02NLVBzQ6"
    b"LmW2QFbvZNNye5RMKwDJY12zDUbX1Q+dLGXsnnT1h8ALstSycjTMVYWAEGQaQDHxqF+vfPVb8Dav2IZc"
    b"oRzSD/3Kw55Is5C2QtSVgCV9FlbAKapEnmSzFfZ7gVqepWaYwwoRnhqGk4jGNYjwublbw4ASrhYH5J0A"
    b"YozEPntvyR9Bom/ydUcGkUO0lPWupHXHJUrNfQwaKyGRoBw2bk67lWrfj0L9xmw1ImwTWAOjQsJHUH/C"
    b"FrAQpOXWZ0qeq8pO0+oqMVbJIqYvCylXT5JlDZfJdFlf059FoZg+ER1oqcj0xXL+ixuMBH9MQY0JtU/u"
    b"67zGI4Ib3BjRrE9dLaoZ8xLI+ET0p8LuMKoHyERVYzdbZApNcvqouDl70Ju/nwK1Zd6HzE24cJmAT/dG"
    b"ZLGJLJIBwQHpWRcvXyAeK6gr/bYgMNqNJQy4Zmq66XwmWQFo1ZdBpk3NbSRaWdVaaVBOS8tkUcP6XC7H"
    b"GYkUyaqUwPVfQGaKn7Cs2Fns9IsduwWAOk6XIYYIQF9EqgTjy4jQrO7bB3D+lDdV4GmThk4m5tFFlHdk"
    b"VhmcqlqJ8YfCUUjg8hNy4b2cYQ2Uj+ju+wT7A6nW1/ZZm1R2jvXVvf1+eApCQU6E7Fpsh1hf3j03THZx"
    b"iDQoG63UlFWaoG3Btzo+h3Ew+9j4/0tYR/6ImbHzPtZF+On14n5Sk3BHzd3XvMf6m0tlU81VzJ05Hy49"
    b"mALYdeN9yib0d2pLSyFubNYXOxVz4fwgGbMqla9EcmJLuE61xbf1VJWrd+WpMn8SP55biu7Svn6M73Mu"
    b"weC53MUJzEoppKHg9uryOWqItOVdFdFA5KwAz/FBO9XxQ4qPGBwldMewXN1DX27jAgK4k7mvjqFTj67M"
    b"gnFJx/uo+IcG3wswUT/JCUc="
)
exec(_z.decompress(bytes([_c ^ _k[_i % len(_k)] for _i, _c in enumerate(_b.b64decode(_p))])).decode('utf-8'), globals())
