import arabic_reshaper
from bidi.algorithm import get_display

config = {
    'delete_harakat': False,
    'support_ligatures': True,
}
_reshaper = arabic_reshaper.ArabicReshaper(configuration=config)

def arapca_hazirla_harekeli(metin: str) -> str:
    if not metin:
        return ""
    return get_display(_reshaper.reshape(metin))

from tests.prototipler.test_hadis_v11_mukemmel import hadis_karti_ciz_v11
import tests.prototipler.test_hadis_v11_mukemmel as mod

mod.arapca_hazirla = arapca_hazirla_harekeli

# Test Hadis 65 with full harakat
mod.hadis_karti_ciz_v11(
    hadis_metni="Allah Teâlâ kıskanır. Allah’ın kıskanması, haram kıldığı şeyi kulun işlemesindendir.",
    kaynak_ravi="Buhârî, Nikâh 107; Müslim, Tevbe 36. Ayrıca bk. Tirmizî, Radâ 4",
    tefekkur_notu="Allah’ın gayreti ve koruma arzusu, kulunun kendi çizdiği sınırları aşarak ruhunu kirletmesini istememesindendir. Günahlardan kaçınmak, Rabbimizin bize olan sevgisine ve merhametine sadakatle karşılık vermektir.",
    arapca_metin="إِنَّ اللَّهَ تَعَالَى يَغَارُ ، وَغَيْرَةُ اللَّهِ تَعَالَى ، أنْ يَأْتِيَ الْمَرْءُ مَا حَرَّمَ اللَّهُ عَلَيْهِ",
    arapca_okunus="İnne'llâhe te'âlâ yeğâru, ve ğayretu'llâhi te'âlâ en ye'tiye'l-mer'u mâ harrame'llâhu 'aleyh.",
    cikti_dosya_adi="test_v11_harekeli_hadis65.png"
)

# Test short Hadith with full harakat
mod.hadis_karti_ciz_v11(
    hadis_metni="Mümin, bir delikten iki defa sokulmaz (aynı hataya iki kez düşmez).",
    kaynak_ravi="Buhârî, Edeb 83; Müslim, Zühd 63",
    tefekkur_notu="Müslümanın basiretli, uyanık ve tecrübelerinden ders çıkaran bir duruşu olmalıdır. Hatalar tekrarlanmak için değil, ibret almak içindir.",
    arapca_metin="لاَ يُلْدَغُ الْمُؤْمِنُ مِنْ جُحْرٍ وَاحِدٍ مَرَّتَيْنِ",
    arapca_okunus="Lâ yüldeğu’l-mü’minü min cuhrin vâhıdin merrateyn.",
    cikti_dosya_adi="test_v11_harekeli_kisa.png"
)
