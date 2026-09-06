from tests.prototipler.test_hadis_v11_mukemmel import hadis_karti_ciz_v11
import re

with open("tests/prototipler/test_hadis_v11_mukemmel.py", "r") as f:
    kod = f.read()

# 9:16 için dikey flex dağıtımını güncelle
yeni_kod = re.sub(
    r'if format_tipi == "9:16":\s*pad_ust = min\(110, int\(kalan_bosluk \* 0\.22\)\)\s*gap_kutu_tr = min\(130, int\(kalan_bosluk \* 0\.45\)\)\s*gap_tr_kaynak = 26',
    '''if format_tipi == "9:16":
        pad_ust = int(kalan_bosluk * 0.26)
        gap_kutu_tr = int(kalan_bosluk * 0.36)
        gap_tr_kaynak = 30''',
    kod
)

with open("tests/prototipler/test_hadis_v11_mukemmel.py", "w") as f:
    f.write(yeni_kod)

print("Güncellendi")
