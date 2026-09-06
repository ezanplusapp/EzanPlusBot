import re
from pathlib import Path
from PIL import Image
import src.uretim.kart as kart

tonlar = [
    ("#C0392B", "koyu_c0392b.png", "C0392B (Canli Koyu Kirmizi)"),
    ("#A82227", "koyu_a82227.png", "A82227 (Zengin Asil Kirmizi)"),
    ("#9B1B1B", "koyu_9b1b1b.png", "9B1B1B (Kurumsal Ezan Plus Kirmizisi)"),
]

# Read kart.py original code
with open("src/uretim/kart.py", "r") as f:
    kod = f.read()

for ton, dosya, etiket in tonlar:
    yeni_kod = kod.replace('kirmizi_ton = "#E2585D"', f'kirmizi_ton = "{ton}"')
    with open("src/uretim/kart.py", "w") as f:
        f.write(yeni_kod)
    
    # Reload and draw
    import importlib
    importlib.reload(kart)
    p = kart.hadis_karti_ciz(
        hadis_metni="Selâm size, ey mü’minler diyârı! Başınıza geleceği söylenen şeylerle nihâyet karşılaştınız. Şimdilik ileri bir tarihe bırakıldınız. İnşallah yakında biz de aranıza katılacağız. Allahım! Bakîü’l-garkad mezarlığında yatanları bağışla!",
        kaynak_ravi="Müslim, Cenâiz 102. Ayrıca bk. Ebû Dâvûd, Cenâiz 79; Nesâî, Cenâiz 103",
        tefekkur_notu="Ölüm gerçeğiyle yüzleşmek, elimizdeki ömür ve sağlık nimetinin değerini idrak etmemiz için en büyük ikazdır. Geçmişlerimize dua gönderirken kendi ahiret yolculuğumuza hazırlanmak, hayatı daha şükür dolu ve anlamlı yaşamamızı sağlar.",
        arapca_metin="السَّلامُ عَلَيْكُمْ دَارَ قَوْمٍ مُؤْمِنينَ ، وأَتَاكُمْ ما تُوعَدُونَ ، غَداً مُؤَجَّلُونَ ، وإِنَّا إِنْ شَاءَ اللَّهُ بِكُمْ لاحِقُونَ ، اللَّهُمَّ اغْفِرْ لأَهْلِ بَقِيعِ الغَرْقَدِ",
        arapca_okunus="Es-selâmü aleyküm dâre kavmin mü'minîn, ve etâküm mâ tû'adûne ğadan müeccelûn, ve innâ in şâallâhu biküm lâhikûn. Allâhümma'ğfir li-ehli Bakî'i'l-Garkad.",
        format_tipi="4:5",
        cikti_dosya_adi=dosya
    )
    print(f"Uretildi: {dosya}")

# Restore original code
with open("src/uretim/kart.py", "w") as f:
    f.write(kod)
