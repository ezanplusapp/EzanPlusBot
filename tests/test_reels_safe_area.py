"""
test_reels_safe_area.py — Kur'an Tilaveti Reels mizanpajında metin kutularının
bağımsız güvenli alanlarını (safe area) koruma garantisi ve Latin okunuş glif
normalizasyon testleri.
"""

import unittest
from pathlib import Path
from PIL import Image

from src.uretim.video import (
    latin_okunus_temizle,
    sayfa_sayisi_belirle,
    _SayfaVerisi,
    parse_markdown_bold,
)


class TestLatinOkunusTemizle(unittest.TestCase):
    """
    Manrope fontunda tofu/kutu (■) hatası veren akademik transliterasyon işaretlerinin
    temizlenmesini ve şapkalı ünlülerin (â, î, û) korunmasını test eder.
    """

    def test_kehf_vedrib_tofu_fix(self):
        ham = "Veḍrib lehum meselen raculeyni"
        temiz = latin_okunus_temizle(ham)
        self.assertEqual(temiz, "Vedrib lehum meselen raculeyni")
        self.assertNotIn("ḍ", temiz)

    def test_academic_diacritics_mapping(self):
        testler = [
            ("ṣalât", "salât"),
            ("ṭayyib", "tayyib"),
            ("ẓâlim", "zâlim"),
            ("ḥamd", "hamd"),
            ("ġafûr", "gafûr"),
            ("‘alîm", "'alîm"),
            ("d\u0323", "d"),  # combining dot below
        ]
        for ham, beklenen in testler:
            self.assertEqual(latin_okunus_temizle(ham), beklenen)

    def test_preserves_circumflex_vowels(self):
        ham = "er-rahmânir-rahîm yâ eyyuhel-lezîne âmenû"
        temiz = latin_okunus_temizle(ham)
        self.assertIn("â", temiz)
        self.assertIn("î", temiz)
        self.assertIn("û", temiz)


class TestSayfaSayisiBelirle(unittest.TestCase):
    """
    Dikey yük denetimi: 11-14 kelimelik fakat meali 3+ satır tutan âyetlerin
    sıkışmayı önlemek için otomatik 2 sayfaya bölünmesini test eder.
    """

    def test_ultra_kisa_ayet(self):
        kelimeler = ["Kul", "huvallâhu", "ehad"]
        meal = "De ki: O Allah birdir."
        self.assertEqual(sayfa_sayisi_belirle(kelimeler, meal), 1)

    def test_kehf_32_yuksek_dikey_yuk(self):
        kelimeler = [
            "Veḍrib", "lehum", "meselen", "raculeyni", "ce'alnâ", "li-ehadihimâ",
            "cenneteyni", "min", "a'nâbin", "ve", "hafefnâhumâ", "bi-nahlin",
            "ve", "ce'alnâ"
        ]
        meal = (
            "Onlara **iki adamın durumunu** misal olarak anlat: "
            "Biz bunlardan birine **iki üzüm bağı** vermiş, "
            "her ikisinin etrafını **hurmalarla donatmış** ve "
            "aralarında da **ekinler bitirmiştik**."
        )
        # 14 kelime, meal >= 110 karakter -> 2 sayfa olmalı
        self.assertEqual(len(kelimeler), 14)
        self.assertEqual(sayfa_sayisi_belirle(kelimeler, meal), 2)

    def test_uzun_ayet_uc_sayfa(self):
        kelimeler = [f"kelime_{i}" for i in range(30)]
        meal = "Uzun bir meal metni..."
        self.assertEqual(sayfa_sayisi_belirle(kelimeler, meal), 3)


class TestReelsSafeAreaGuarantees(unittest.TestCase):
    """
    _SayfaVerisi hesaplamasında Kırmızı Keten Meal Bandının Latin okunuşun
    tabanını (tr_bottom) asla ihlal etmediğini (hard floor) ve tefekkür alanına
    taşmadığını matematiksel olarak doğrular.
    """

    def test_kehf_32_sayfa1_safe_area(self):
        page_ar = ["وَاضْرِبْ", "لَهُمْ", "مَثَلًا", "رَجُلَيْنِ", "جَعَلْنَا", "لِأَحَدِهِمَا", "جَنَّتَيْنِ"]
        page_tr = ["Vedrib", "lehum", "meselen", "raculeyni", "ce'alnâ", "li-ehadihimâ", "cenneteyni"]
        meal = "Onlara iki adamın durumunu misal olarak anlat: Biz bunlardan birine iki üzüm bağı vermiş..."

        sv = _SayfaVerisi(
            p_idx=0,
            sayfa_sayisi=2,
            start_w=0,
            end_w=7,
            page_ar=page_ar,
            page_tr=page_tr,
            page_meal=meal,
            sure_ayet="Kehf Sûresi, 32. Âyet",
            s1="İLAHÎ İMTİHAN VE",
            s2="NİMET ŞÜKRÜ",
            tef="Rabbimizin lütfettiği zenginlik ve imkanlar ebedi değil, birer emanet ve sınav vesilesidir.",
            hafiz_adi="Mişari Râşid el-Afâsî",
        )

        # 1. Okunuş çakışması kesinlikle False olmalı
        self.assertFalse(sv.okunus_cakismasi)

        # 2. fade_1_start (kırmızı bandın en üst noktası) >= tr_bottom + 24 olmalı
        self.assertGreaterEqual(sv.fade_1_start, sv.tr_bottom + 24)

        # 3. fade_2_end (kırmızı bandın en alt noktası) <= ay_y - 20 olmalı
        self.assertLessEqual(sv.fade_2_end, sv.ay_y - 20)

    def test_kehf_32_sayfa2_safe_area(self):
        page_ar = ["مِنْ", "أَعْنَابٍ", "وَحَفَفْنَاهُمَا", "بِنَخْلٍ", "وَجَعَلْنَا", "بَيْنَهُمَا", "زَرْعًا"]
        page_tr = ["min", "a'nâbin", "ve", "hafefnâhumâ", "bi-nahlin", "ve", "ce'alnâ"]
        meal = "Her ikisinin etrafını hurmalarla donatmış ve aralarında da ekinler bitirmiştik."

        sv = _SayfaVerisi(
            p_idx=1,
            sayfa_sayisi=2,
            start_w=7,
            end_w=14,
            page_ar=page_ar,
            page_tr=page_tr,
            page_meal=meal,
            sure_ayet="Kehf Sûresi, 32. Âyet",
            s1="İLAHÎ İMTİHAN VE",
            s2="NİMET ŞÜKRÜ",
            tef="Rabbimizin lütfettiği zenginlik ve imkanlar ebedi değil, birer emanet ve sınav vesilesidir.",
            hafiz_adi="Mişari Râşid el-Afâsî",
        )

        self.assertFalse(sv.okunus_cakismasi)
        self.assertGreaterEqual(sv.fade_1_start, sv.tr_bottom + 24)
        self.assertLessEqual(sv.fade_2_end, sv.ay_y - 20)

    def test_parse_markdown_bold_guarantee(self):
        """
        parse_markdown_bold fonksiyonunun yetim veya bozuk markdown işaretlerini
        temizleyip ekrana çıplak yıldız düşürmediğini test eder.
        """
        metin = "**Ey Rabbimiz**, bizden kabul buyur! **"
        tokens = parse_markdown_bold(metin)
        for tok, is_bold in tokens:
            self.assertNotIn("**", tok)


if __name__ == "__main__":
    unittest.main()
