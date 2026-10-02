"""
test_araf_ve_hadis_duzeltmeleri.py — A'râf 126 Senkron & Tirmizî Birr 71 Hadis Düzeltme Testleri
"""

import unittest
import sqlite3
from src.uretim.ses import ayet_kelime_zamanlari_getir
from src.uretim.video import kelime_zamanlarini_hizala, arapca_kelimeleri_ayristir
from src.hadis_db import arapca_veciz_ayikla, DB_YOLU as HADIS_DB_YOLU
from src.kuran_db import DB_YOLU as KURAN_DB_YOLU


class TestArafVeHadisDuzeltmeleri(unittest.TestCase):
    def test_araf_126_kelime_zaman_senkronu(self):
        """A'râf 126 ayetinde 'minnâ' sonrası ileri-geri sıçrama hatasının çözüldüğünü doğrular."""
        with sqlite3.connect(str(KURAN_DB_YOLU)) as con:
            cur = con.execute("SELECT arapca_metin FROM ayetler WHERE sure_no = 7 AND ayet_no = 126")
            ar_text = cur.fetchone()[0]

        words = arapca_kelimeleri_ayristir(ar_text)
        self.assertEqual(len(words), 16, "A'râf 126 tam 16 kelimeden oluşmalıdır.")

        zamanlar = ayet_kelime_zamanlari_getir(7, 126)
        self.assertEqual(len(zamanlar), 16, "16 kelime için 16 segment zaman damgası dönmelidir.")

        # Zaman damgalarının kesinlikle sıralı (0, 1, 2, ..., 15) ve monoton artan olduğunu denetle
        hizali = kelime_zamanlarini_hizala(zamanlar, len(words), 30.0)
        word_indices = [item[0] for item in hizali]
        self.assertEqual(word_indices, list(range(16)), "Kelime indeksleri 0'dan 15'e kesintisiz ve sıçramasız gitmelidir.")

        # minnâ (indeks 2) sonrasındaki kelimenin indeks 3 olduğunu teyit et
        self.assertEqual(hizali[2][0], 2)
        self.assertEqual(hizali[3][0], 3)
        self.assertEqual(hizali[4][0], 4)

    def test_tirmizi_birr_71_veciz_ve_metin_butunlugu(self):
        """Tirmizî Birr 71 (ID 1741) hadisinde Arapça metnin kırpılmadığını ve takhric notunun veciz yerine geçmediğini doğrular."""
        with sqlite3.connect(str(HADIS_DB_YOLU)) as con:
            con.row_factory = sqlite3.Row
            cur = con.execute("SELECT * FROM hadisler WHERE id = 1741")
            row = cur.fetchone()

        self.assertIsNotNone(row)
        veciz = row["arapca_veciz"]

        # Veciz metin takhric notu ("حديث حسن" veya "باب حسن الخلق") İÇERMEMELİDİR
        self.assertNotIn("حديثٌ حسن", veciz)
        self.assertNotIn("باب حُسْنِ الخُلقِ", veciz)
        self.assertNotIn("رواه الترمذي", veciz)

        # Veciz metin Resûlullah'ın (s.a.v.) asıl Nebevî kelamını içermelidir
        self.assertTrue(veciz.startswith("إِنَّ مِنْ أَحَبِّكُمْ إِليَّ"))
        self.assertTrue("الثَّرْثَارُونَ" in veciz)
        self.assertTrue("المُتَفَيْهِقُونَ" in veciz)
        self.assertGreaterEqual(len(veciz.split()), 20, "Nebevî veciz metin tam uzunlukta olmalıdır.")

        # Parser'ın arapca_veciz_ayikla fonksiyonunun bu metni doğru ayıkladığını da test et
        extracted = arapca_veciz_ayikla(row["arapca_metin"])
        self.assertEqual(extracted, veciz)


if __name__ == "__main__":
    unittest.main()
