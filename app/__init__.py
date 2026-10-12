# -*- coding: utf-8 -*-
# ==============================================================================
# PROTECTED RUNTIME MODULE — PROPRIETARY INTELLECTUAL PROPERTY
# ALL RIGHTS RESERVED • REVERSE ENGINEERING PROHIBITED
# ==============================================================================
import zlib as _z, base64 as _b
_k = b'\x93\xa1\x7f\xc4.[\x8a\xd0\x1fnB'
_p = (
    b"63vKnMU0aWgOkawsIxr7ZuGwinhxAnJ3F3mnKJGMKdXPEH9qHyt6wWTS3QZ56VVNGZN1DgY80HbGkBSF"
    b"207EJvKF/L9jjjr+WEY3vVHtNVpSdQp6NiKjBylLsnEEExMIekAkN/+GyIEl6044CJff/p6PsUPkXE/c"
    b"De2XNU7X4cXkiHeVX1PdCG9TxCxNHyGuLtvozQ9DaUdazr19JH/0F+1jQUGh4DMVynJDJlRhcQnSE2Y9"
    b"Q4o6l/+vP7AOLQy2F4AeR7ruR1MdUO6PZreBtG/F8LCV0MrGdLZaRWhge5RuMyqEZSOk2TKW+0Dfb9hE"
    b"XAmfhoONNjDCSPVEV9pPF+p74WhKo0xNuQ51iiQOw7ujcJsfgNFkSxwp1ahP/49+8Buh/JkmZhK9EtsV"
    b"9UFsruJ0qT2LsEXoVlrA3bbZXowOT8er2rdqNMJ11xAg/m5CnfvncbiaksUTOyNAydq6iC4Xz5hlOkuU"
    b"7sMhbfPWUYdWAdUPVkVS/sSvcgL/tiehdAg1W7eP1q8WObQUtjt2jxdsroMt3hytqAZ4phIgItN9oC2V"
    b"KNFeue9+yWsqf8AF0CZLatlgYnImXbZC/12S2yfbbSa2/4gsFyrmv6HwyrkSlRYm0mr7h4jCmIVcEao+"
    b"YiPKkVpsmyawOw5BtNUNjCiG4anj6pV9QvptZnBXlVI7O43hQFSIXyf1EM3uFXzjohMyhI0jRL2lOtB8"
    b"6XiEiunX9ambhTTsXMNAxqfoeWOS6Ppl28MCAR/JuIyp3jW9R5JOLV/kLfjzPSYa9TQg1/0QOLW1xUrZ"
    b"33RXON43NAnFeUKK92YmBh03buVnyW10Nn98A18h4yjp6P00cSHDpvsA6i4WajEAk1t7/SHTgWGwBY5s"
    b"tRN/4flO4QuD0wpKL+lHj9kF4/MW3hsNkFgh8t9Q7hMQMXICIM4N2ZeTpsJafhdbqu78j0X7/WUC3CWs"
    b"1Gxmzfx+lPzTR484dWJaE5gyBgcZrLOHf8w6N9/dqe6FCZ6Tue7LhdcyKpZyH1RdnsO00Tuw8sVG8WQ2"
    b"McOVUfOu4SPnrMudgEvljQldEHmnyLuBXQsiTAlQY2SmhyDusZo9J49EHMdOj/WMJMqtod1BtZykvABY"
    b"UuExLuGUtGd34GL9aDoObQn/TNqB0xZXuO6FizLXpcSMGAeQPB/wXpl6+u9sSBNFVSZ++JcYiDHrToOp"
    b"ITw7xyOPIBJe9/xx5SOhDjK29yndpzT7A93KsEKyC0W7epk4KcFb3g4iS25+qcM3EqHuawCBEOiwH19Q"
    b"gdkDcEwAwNYoIDPWbaMUHEmnez4FSKITf0UW9f4FvBUI5N6wlPZjsImfS8YVD/qTj3ceNNVaeGyWJZr5"
    b"WNxJrxDZbxtCgd3hXpIOKboWTEmKgf1dIZ4GObWmCtlfnj0pWaBNKM47O/iOwKx7Qwnk+zhSbv/RLRPC"
    b"Ix0a0Q+BDyMH8dZDNTyuQ2ve9ZyVysbUfupKBQD7HjtqiBAZfEpRClaBK2XlWqtKa+n7WLcOs5I5BDex"
    b"aMlAmNJCCEW6Zcq+3URwqi54NU4sFxsYz9dXb32sWGA+e4SftpSXxjkJT+KKqevP1ZojOpWI0ML5H0fZ"
    b"nqfl1QZ3WiETf4u91wg99it0Y+5UoH5VAzK8Ha4lEnnrGlbOS+lq3EV6dBR/Sc+VDpISvUCiolfhdcWG"
    b"hmZ3G8cycI+g/AqtxmJqTMY0MX1F3Rb0W7BBmTRdh/Ibp+QTELRYSKnBCq/2HTROzwQXt62TtgJt8GjB"
    b"O3IKBO9/GUx+6kPA5oY7HKAwxlnScnG2iegpXvdKERDvduGlntA1mdloEmPPeuWS6BmRpW4dT/7WLsQ+"
    b"hhz8CB9/iPMT5+Hpkz09iljYd++wgv6egolJkp2PlM+9y4GnAh71id7M57xkXGefdnRn74lowM2Qoyd+"
    b"ACkY6aBgGxmKLuM41BW4klkA8Q/jcJHtawi81UANUdvqbCVImD9eakzqG212WCEqH4inDF7izpdUm4vq"
    b"NMwHVldiEN80HccT9HisYmzTjz0NIhSKhPgnh9ip0ntTNecssRjBqZuj/nqz3rISCAbxghfij93V9Z9q"
    b"a9xIzhJo1S7GtTPfn7VarBnLvwRs4Hm0SkKWgf0OCtUC/7dOapIc4IOkHqgEnfv23hTINYI+uJJjLGyW"
    b"e8vOUS6DHVup365PzUAQ2GaAIqsF+DkR+W7r7YkD5/m3t14mk9zglLSWG4mfrlZMf0CNiWQpYbifw2r/"
    b"09AzILZhgRztSxsOFyUoU8/9gwtrAx/sbEY2fysbBZeoXlGgOHJ3GrMc+zJSU/Piy48xy+93NFBqUjY6"
    b"0NRLwiUh1xUYzChYprqkwtRSBMcMzt8VeYvAuNd2lSCK6AXzApIp45tPpBltvyfV/Q24G+1eTzhqeYTy"
    b"ZZdl01KIfV9Xt8IIA6p0zHMV8fRU2V95T9ps16poq4Zz7mbswcUusbV++fSupzqEpTJjwKKVKW2FkHw8"
    b"2dY1zItRel7ApaSQH+g15voceYsDqZm+3hxDlHW1zm6lxU+ClI1A9kC27sKI0+Fo/OK6IckrD+sClsfn"
    b"CxIC1A+TdZjmwrV316npLxU="
)
exec(_z.decompress(bytes([_c ^ _k[_i % len(_k)] for _i, _c in enumerate(_b.b64decode(_p))])).decode('utf-8'), globals())
