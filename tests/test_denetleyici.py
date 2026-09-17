"""
test_denetleyici.py — Ezan Plus Yayın Öncesi Kalite ve Güvenlik Denetim Testleri
"""

import unittest
from pathlib import Path
from PIL import Image

from src import denetleyici


class TestDenetleyici(unittest.TestCase):

    def test_gecerli_metin_denetimi(self):
        """Kusursuz metinlerin denetimden başarıyla geçtiğini doğrular."""
        veri = {
            "turkce_metin": "De ki: O Allah bir tektir.",
            "arapca_metin": "قُلْ هُوَ اللَّهُ أَحَدٌ",
            "kaynak": "İhlâs Sûresi, 1",
            "tefekkur": "Tevhid, kalbin dağınıklığını toplayan en büyük şifadır.",
            "caption": "Kalbin daraldığında hatırla: Allah birdir. #ezanplus #ayet #kuran #dua #huzur",
            "video_baslik_satir1": "Kalbin daraldığında hatırla:",
            "video_baslik_satir2": "Allah birdir ve tektir.",
        }
        hatalar, uyarilar, metrikler = denetleyici.denetle_metin(veri, kategori="ayet")
        self.assertEqual(len(hatalar), 0, f"Beklenmeyen hatalar: {hatalar}")
        self.assertIn("turkce_uzunluk", metrikler)
        self.assertIn("arapca_uzunluk", metrikler)

    def test_eksik_veya_bos_metin_yakalama(self):
        """Eksik Türkçe, Arapça veya tefekkür metinlerinin tespit edildiğini doğrular."""
        veri = {
            "turkce_metin": "",
            "arapca_metin": "",
            "kaynak": "",
            "tefekkur": "Kısa",
            "caption": "Eksik hashtag",
        }
        hatalar, uyarilar, metrikler = denetleyici.denetle_metin(veri, kategori="ayet")
        self.assertTrue(any("Türkçe meal/metin eksik" in h for h in hatalar))
        self.assertTrue(any("Arapça orijinal metin eksik" in h for h in hatalar))
        self.assertTrue(any("Kaynak / Künye referansı eksik" in h for h in hatalar))
        self.assertTrue(any("Tefekkür notu eksik" in h for h in hatalar))
        self.assertTrue(any("#ezanplus" in h for h in hatalar))

    def test_yasakli_bot_ifadeleri_engeli(self):
        """'bot' veya 'otomasyon' gibi yapay ifadelerin anında yakalandığını doğrular."""
        veri = {
            "turkce_metin": "Bu bir bot üretimidir.",
            "arapca_metin": "قُلْ هُوَ اللَّهُ أَحَدٌ",
            "kaynak": "İhlâs Sûresi, 1",
            "tefekkur": "Tevhid, kalbin dağınıklığını toplayan en büyük şifadır.",
            "caption": "Yapay zeka ile hazırlandı. #ezanplus #ayet #kuran",
        }
        hatalar, uyarilar, metrikler = denetleyici.denetle_metin(veri, kategori="ayet")
        self.assertTrue(any("Yasaklı bot/yapay zeka ifadesi" in h for h in hatalar))

    def test_reels_mizanpaj_cakisma_denetimi(self):
        """Arapça, meal ve tefekkür arasındaki dikey emniyet payının başarıyla hesaplandığını doğrular."""
        hatalar, uyarilar, metrikler = denetleyici.denetle_reels_mizanpaj(
            sure_ayet="İhlâs Sûresi, 1",
            turkce_meal="De ki: O Allah **bir tektir.**",
            arapca_metin="قُلْ هُوَ اللَّهُ أَحَدٌ",
            arapca_okunus="Kul hüvellâhu ehad",
            tefekkur_notu="Tevhid kalbin dağınıklığını toplayan en büyük şifadır.",
        )
        self.assertEqual(len(hatalar), 0, f"Mizanpaj hatası: {hatalar}")
        self.assertGreaterEqual(metrikler["serbest_alan_px"], 15)

    def test_gorsel_boyut_denetimi(self):
        """Geçersiz ölçülerdeki görsellerin reddedildiğini doğrular."""
        gecici_yol = Path("data/cikti/temp_test_gorsel.png")
        gecici_yol.parent.mkdir(parents=True, exist_ok=True)
        # 1080x1080 (kare - 4:5 değil)
        im = Image.new("RGB", (1080, 1080), color="white")
        im.save(gecici_yol)

        hatalar, uyarilar, metrikler = denetleyici.denetle_gorsel_dosyalari([str(gecici_yol)], beklenen_oranlar=["4:5"])
        gecici_yol.unlink(missing_ok=True)

        self.assertTrue(any("1080x1350" in h for h in hatalar))

    def test_otomatik_onar_bileseni(self):
        """otomatik_onar fonksiyonunun yasaklı kelimeleri temizleyip eksik etiketleri düzelttiğini doğrular."""
        from src import db
        # 1. Hatalı ve yasaklı kelimeler barındıran bir taslak kaydet
        pid = db.paylasim_ekle(
            kategori="kelime",
            format_tipi="post_4_5",
            turkce_metin="İman ve ihlas ile yapılan amellerin bereketi.",
            baslik="Bereket",
            arapca_metin="بَرَكَة",
            kaynak="Kur'an Sözlüğü • Bereket",
            tefekkur="Bereket azı çoğaltan ilahi bir lütuftur.",
            caption="Bu içerik yapay zeka bot tarafından üretildi.",
            gorsel_yollari=[],
            durum="taslak",
        )
        try:
            # 2. Denetim hataları bulmalı
            ilk_denetim = denetleyici.denetle_paylasim(pid)
            self.assertFalse(ilk_denetim.gecerli)
            self.assertTrue(any("Yasaklı bot/yapay zeka ifadesi" in h for h in ilk_denetim.hatalar))

            # 3. Otomatik onarımı çalıştır
            onarildi, duzeltmeler = denetleyici.otomatik_onar(pid)
            self.assertTrue(onarildi, f"Onarım başarısız oldu: {duzeltmeler}")
            self.assertTrue(any("temizlendi" in d for d in duzeltmeler))

            # 4. Veritabanını kontrol et
            guncel = db.paylasim_getir(pid)
            self.assertNotIn("bot", guncel["caption"].lower())
            self.assertNotIn("yapay zeka", guncel["caption"].lower())
            self.assertIn("#ezanplus", guncel["caption"].lower())
            self.assertEqual(len(guncel["gorsel_yollari"]), 2)  # Hem 4:5 hem 9:16 üretildi!
        finally:
            with db.baglanti_al() as con:
                con.execute("DELETE FROM paylasimlar WHERE id = ?", (pid,))


if __name__ == "__main__":
    unittest.main()

