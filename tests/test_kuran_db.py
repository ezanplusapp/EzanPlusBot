"""
test_kuran_db.py — Tescilli Kur'an Veritabanı ve Arama Testleri
"""

import unittest
from src import kuran_db


class TestKuranDB(unittest.TestCase):
    def test_veritabani_mevcut_ve_tam(self):
        self.assertTrue(kuran_db.veritabani_mevcut_mu())

    def test_sureler_sayisi_ve_icerigi(self):
        sureler = kuran_db.sure_listesi_getir()
        self.assertEqual(len(sureler), 114)

        # Fâtiha
        fatiha = kuran_db.sure_bilgisi_getir(1)
        self.assertIsNotNone(fatiha)
        self.assertEqual(fatiha["sure_adi_tr"], "Fâtiha")
        self.assertEqual(fatiha["ayet_sayisi"], 7)
        self.assertEqual(fatiha["inis_yeri"], "Mekke")

        # İhlâs
        ihlas = kuran_db.sure_bilgisi_getir(112)
        self.assertIsNotNone(ihlas)
        self.assertEqual(ihlas["sure_adi_tr"], "İhlâs")
        self.assertEqual(ihlas["ayet_sayisi"], 4)

    def test_ayet_getir_ve_mealler(self):
        # Fâtiha 1
        f1 = kuran_db.ayet_getir(1, 1)
        self.assertIsNotNone(f1)
        self.assertEqual(f1["sure_ayet_key"], "1:1")
        self.assertIn("بِسْمِ ٱللَّهِ", f1["arapca_metin"])
        self.assertIn("Rahmân", f1["meal_elmalili"])
        self.assertIn("Rahman", f1["meal_diyanet"])
        self.assertEqual(f1["cuz_no"], 1)

        # Âyetü'l-Kürsî (Bakara 255)
        kursi = kuran_db.ayet_getir(2, 255)
        self.assertIsNotNone(kursi)
        self.assertEqual(kursi["sure_ayet_etiket"], "Bakara Sûresi • 255. Âyet")
        self.assertIn("ٱللَّهُ لَآ إِلَـٰهَ إِلَّا هُوَ ٱلْحَىُّ ٱلْقَيُّومُ", kursi["arapca_metin"])
        self.assertTrue("kayyum" in kursi["meal_elmalili"].lower() or "hayy" in kursi["meal_elmalili"].lower())
        self.assertEqual(kursi["cuz_no"], 3)

    def test_ayet_getir_key(self):
        a = kuran_db.ayet_getir_key("94:5")
        self.assertIsNotNone(a)
        self.assertEqual(a["sure_no"], 94)
        self.assertEqual(a["ayet_no"], 5)
        self.assertEqual(a["sure_adi_tr"], "İnşirâh")
        self.assertIn("kolaylık", a["meal_elmalili"].lower())

    def test_sure_ayetleri_aralik(self):
        ayetler = kuran_db.sure_ayetleri_getir(1, baslangic_ayet=1, bitis_ayet=7)
        self.assertEqual(len(ayetler), 7)
        self.assertEqual([a["ayet_no"] for a in ayetler], [1, 2, 3, 4, 5, 6, 7])

    def test_fts_tam_metin_arama(self):
        sonuclar = kuran_db.ayet_ara("sabır", limit=10)
        self.assertTrue(len(sonuclar) > 0)
        self.assertTrue(any("sabır" in s["meal_elmalili"].lower() or "sabır" in s["meal_diyanet"].lower() for s in sonuclar))

    def test_gunun_ayetini_sec(self):
        ayet = kuran_db.gunun_ayetini_sec(tema="Huzur ve Tevekkül")
        self.assertIsNotNone(ayet)
        self.assertGreater(ayet["sure_no"], 0)
        self.assertGreater(ayet["ayet_no"], 0)
        self.assertTrue(len(ayet["arapca_metin"]) > 0)
        self.assertTrue(len(ayet["meal_elmalili"]) > 0)
        self.assertTrue(len(ayet["sure_ayet_etiket"]) > 0)


if __name__ == "__main__":
    unittest.main()
