"""
test_hatim_16_9.py — YouTube 16:9 Hatim Video Motoru Testleri
"""

import unittest
from pathlib import Path

from src.kuran_db import cuz_ayetleri_getir, ayet_getir
from src.uretim.hatim import (
    Hatim16x9Sayfa,
    hatim_ayet_klibi_uret,
    cuz_hatim_videosu_uret,
    W_16_9,
    H_16_9,
)
from src.uretim.ses import ses_sure_hesapla


class TestHatim16x9(unittest.TestCase):

    def test_cuz_ayetleri_getir(self):
        """1. Cüzün 148 âyet içerdiğini ve sıralı geldiğini doğrular."""
        ayetler = cuz_ayetleri_getir(1)
        self.assertEqual(len(ayetler), 148)
        self.assertEqual(ayetler[0]["sure_no"], 1)
        self.assertEqual(ayetler[0]["ayet_no"], 1)
        self.assertEqual(ayetler[-1]["sure_no"], 2)
        self.assertEqual(ayetler[-1]["ayet_no"], 141)

    def test_hatim_sayfa_kare_cizim(self):
        """Hatim 16:9 sayfasının 1920x1080 çözünürlükte RGB kare ürettiğini doğrular."""
        ayet = ayet_getir(1, 1)
        sayfa = Hatim16x9Sayfa(
            sure_no=1,
            ayet_no=1,
            cuz_no=1,
            sayfa_no=1,
            sure_adi_tr="Fâtiha",
            toplam_sure_ayet=7,
            ar_kelimeler=["بِسْمِ", "ٱللَّهِ", "ٱلرَّحْمَـٰنِ", "ٱلرَّحِيمِ"],
            tr_kelimeler=["Bismillâhir", "rahmânir", "rahîm"],
            kelime_offset=0,
            meal_metni=ayet["meal_elmalili"],
            tefekkur_notu="Fâtiha Sûresi, Kur'an'ın kalbidir.",
            cuz_ilerleme_yuzdesi=0.1,
        )
        kare = sayfa.kare_ciz(aktif_idx=1)
        self.assertEqual(kare.size, (W_16_9, H_16_9))
        self.assertEqual(kare.mode, "RGB")

    def test_hatim_pilot_ayet_render(self):
        """Fâtiha 1. Âyet için 16:9 MP4 klibi üretir ve dosya bütünlüğünü test eder."""
        hedef = Path("/tmp/test_hatim_fatiha_1.mp4")
        if hedef.exists():
            hedef.unlink()

        cikti = hatim_ayet_klibi_uret(sure_no=1, ayet_no=1, cikti_mp4=hedef)
        self.assertTrue(cikti.exists())
        self.assertGreater(cikti.stat().st_size, 50000)

        sure = ses_sure_hesapla(cikti)
        self.assertGreater(sure, 4.0)

    def test_hatim_pilot_cuz_birlestirme(self):
        """1. Cüzün ilk 2 âyetini üretip birleştirir ve YouTube chapters dosyasını doğrular."""
        cikti_mp4 = Path("/tmp/test_hatim_cuz1_pilot.mp4")
        if cikti_mp4.exists():
            cikti_mp4.unlink()

        video_p, ch_p = cuz_hatim_videosu_uret(cuz_no=1, cikti_mp4=cikti_mp4, ayet_limiti=2)
        self.assertTrue(video_p.exists())
        self.assertTrue(ch_p.exists())

        ch_content = ch_p.read_text(encoding="utf-8")
        self.assertIn("Fâtiha Sûresi, 1. Âyet", ch_content)
        self.assertIn("Fâtiha Sûresi, 2. Âyet", ch_content)
        self.assertIn("00:00 - Fâtiha Sûresi, 1. Âyet", ch_content)


if __name__ == "__main__":
    unittest.main()
