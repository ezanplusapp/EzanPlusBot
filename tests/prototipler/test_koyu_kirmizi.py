from PIL import Image, ImageDraw
from tests.prototipler.test_hadis_v11_mukemmel import hadis_karti_ciz_v11
import tests.prototipler.test_hadis_v11_mukemmel as mod
from src.uretim.kart import hadis_karti_ciz

# Test different shades of darker red:
tonlar = [
    ("#B83238", "koyu_v1_b83238.png", "Ton 1: #B83238 (Doygun Asil Kırmızı)"),
    ("#A82227", "koyu_v2_a82227.png", "Ton 2: #A82227 (Derin Zengin Kırmızı)"),
    ("#9B1B1B", "koyu_v3_9b1b1b.png", "Ton 3: #9B1B1B (Ezan Plus Marka Kırmızısı)"),
]

for ton, dosya, etiket in tonlar:
    # update kirmizi_ton in kart.py dynamically for test
    p = hadis_karti_ciz(
        hadis_metni="Selâm size, ey mü’minler diyârı! Başınıza geleceği söylenen şeylerle nihâyet karşılaştınız. Şimdilik ileri bir tarihe bırakıldınız. İnşallah yakında biz de aranıza katılacağız. Allahım! Bakîü’l-garkad mezarlığında yatanları bağışla!",
        kaynak_ravi="Müslim, Cenâiz 102. Ayrıca bk. Ebû Dâvûd, Cenâiz 79; Nesâî, Cenâiz 103",
        tefekkur_notu="Ölüm gerçeğiyle yüzleşmek, elimizdeki ömür ve sağlık nimetinin değerini idrak etmemiz için en büyük ikazdır. Geçmişlerimize dua gönderirken kendi ahiret yolculuğumuza hazırlanmak, hayatı daha şükür dolu ve anlamlı yaşamamızı sağlar.",
        arapca_metin="السَّلامُ عَلَيْكُمْ دَارَ قَوْمٍ مُؤْمِنينَ ، وأَتَاكُمْ ما تُوعَدُونَ ، غَداً مُؤَجَّلُونَ ، وإِنَّا إِنْ شَاءَ اللَّهُ بِكُمْ لاحِقُونَ ، اللَّهُمَّ اغْفِرْ لأَهْلِ بَقِيعِ الغَرْقَدِ",
        arapca_okunus="Es-selâmü aleyküm dâre kavmin mü'minîn, ve etâküm mâ tû'adûne ğadan müeccelûn, ve innâ in şâallâhu biküm lâhikûn. Allâhümma'ğfir li-ehli Bakî'i'l-Garkad.",
        format_tipi="4:5",
        cikti_dosya_adi=dosya
    )
    # recolor test by modifying the output with specific color replacement
    im = Image.open(p).convert("RGB")
    # Actually let's do it cleanly by updating kart.py kirmizi_ton
