import datetime
import unittest
from unittest.mock import MagicMock, patch

from src.hadis_db import _hadis_etkilesim_puani, _hadis_sosyal_medya_uygun_mu
from src.kuran_db import _ayet_etkilesim_puani, _ayet_sosyal_medya_uygun_mu
from src.platformlar import threads, youtube
from src.uretim import ai
from src.uretim.multipage import build_v20_base_layout
from src.uretim.ses import dua_fonetik_ve_es_hazirla, turkce_kisaltmalari_genislet


class TestBuyumeVeRenderIyilestirmeleri(unittest.TestCase):
    def test_dua_fonetik_rabbim_noktalama_ve_egik_cizgi(self):
        ham = "Rabbim! Şeytanların kışkırtmalarından/vesveselerinden sana sığınırım. Onların yanımda bulunmalarından da sana sığınırım Rabbim."
        sonuc = turkce_kisaltmalari_genislet(dua_fonetik_ve_es_hazirla(ham))
        self.assertNotIn("Rabbim, .", sonuc)
        self.assertTrue(sonuc.endswith("Rabbim."))
        self.assertIn("kışkırtmalarından ve vesveselerinden", sonuc)

        # Devamında kelime olan nida ise virgül almalı
        ham2 = "Ey Rabbim beni bağışla."
        sonuc2 = dua_fonetik_ve_es_hazirla(ham2)
        self.assertIn("Ey Rabbim, beni", sonuc2)

    def test_v20_uzun_kelime_ve_tefekkur_tasma_korumasi(self):
        # Eğik çizgili önbellekli ham token gelse dahi 1080px genişlik dışına taşmamalı
        layout = build_v20_base_layout(
            kategori="dua",
            format_tipi="9:16",
            custom_meal="Rabbim! Şeytanların kışkırtmalarından/vesveselerinden sana sığınırım.",
            custom_tef=(
                "Bu dua, hayatımızın her anında ve sevdiklerimizin ahiret yolculuğunda "
                "Allah'ın rahmetine sığınmanın en nebevi ifadesidir. Hem dirimiz hem ölüümüz için "
                "dilediğimiz bu istikamet, imanla yaşayıp imanla ölmenin en güzel temennisidir."
            ),
        )
        for w in layout["flattened_words"]:
            self.assertGreaterEqual(w["x"], 40)
            self.assertLessEqual(w["x"] + w["w"], 1040)

    def test_youtube_kanca_basligi_ve_ses_dili(self):
        ayet_kayit = {
            "kategori": "ayet",
            "baslik": "Rahmân Sûresi • 76. Âyet",
            "caption": "Dünyanın geçici yükleri altında ezildiğinde ruhun nereye sığınmak ister?\n\n📖 Rahmân 76",
            "turkce_metin": "Yeşil yastıklara yaslanırlar.",
        }
        yt_ayet = youtube.youtube_baslik_olustur(ayet_kayit)
        self.assertIn("Rahmân 76", yt_ayet)
        self.assertIn("Dünyanın geçici yükleri", yt_ayet)
        self.assertLessEqual(len(yt_ayet) + len(" #Shorts"), 100)

        hadis_kayit = {
            "kategori": "hadis",
            "baslik": "Müslim, Fiten 126. Ayrıca bk. Ahmed İbni Hanbel, Müsned, IV, 19-21",
            "caption": "Dünyanın gürültüsü içinde kalbini korumaya çalışanlara selam olsun.\n\nHadis...",
            "turkce_metin": "Fitne anında ibadet bana hicret gibidir.",
        }
        yt_hadis = youtube.youtube_baslik_olustur(hadis_kayit)
        self.assertNotIn("Ahmed İbni Hanbel", yt_hadis)
        self.assertIn("Hadis-i Şerif", yt_hadis)

    def test_icerik_kurasyon_suzgecleri(self):
        self.assertFalse(_hadis_sosyal_medya_uygun_mu({"hadis_metni": "Yahudi ve hıristiyanlara öncelikle siz selâm vermeyin."}))
        self.assertFalse(_hadis_sosyal_medya_uygun_mu({"hadis_metni": "Allâhumme innî eûzü bike mine’l-barasi ve’l-cüzâmi"}))
        iyi_hadis = {"hadis_metni": "İnsanlara merhamet etmeyene Allah da merhamet etmez.", "kelime_sayisi": 12}
        self.assertTrue(_hadis_sosyal_medya_uygun_mu(iyi_hadis))
        self.assertGreaterEqual(_hadis_etkilesim_puani(iyi_hadis), 50)

        self.assertFalse(_ayet_sosyal_medya_uygun_mu({"meal_elmalili": "Dediler ki: Ey Mûsâ!"}))
        iyi_ayet = {"meal_elmalili": "Kalpler ancak Allah'ı anmakla huzur bulur.", "kelime_sayisi": 8}
        self.assertTrue(_ayet_sosyal_medya_uygun_mu(iyi_ayet))
        self.assertGreaterEqual(_ayet_etkilesim_puani(iyi_ayet), 45)

    def test_cuma_ozel_modu(self):
        cuma_dt = datetime.datetime(2026, 11, 27, 10, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=3)))
        sonuc = ai.cuma_ozel_bilgisi(cuma_dt)
        self.assertIsNotNone(sonuc)
        self.assertEqual(sonuc[0], "Mübarek Cuma Günü")

        carsamba_dt = datetime.datetime(2026, 11, 25, 10, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=3)))
        self.assertIsNone(ai.cuma_ozel_bilgisi(carsamba_dt))

    def test_threads_auth_url(self):
        with patch("src.platformlar.threads.get_env", return_value="123456789"):
            url = threads.auth_url_uret()
            self.assertIn("threads.net/oauth/authorize", url)
            self.assertIn("client_id=123456789", url)


if __name__ == "__main__":
    unittest.main()
