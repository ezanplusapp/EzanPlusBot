import unittest
from src.uretim.ses import turkce_metin_harf_duzelt


class TestTurkceHarfDuzelt(unittest.TestCase):
    def test_dua_cumle_ici_zamirler_kuculur(self):
        metin = "Rabbim! Şeytanların kışkırtmalarından Sana sığınırım. Onların yanımda bulunmalarından da Sana sığınırım."
        beklenen = "Rabbim! Şeytanların kışkırtmalarından sana sığınırım. Onların yanımda bulunmalarından da sana sığınırım."
        self.assertEqual(turkce_metin_harf_duzelt(metin), beklenen)

    def test_seyyidul_istigfar_zamirleri(self):
        metin = "Allah'ım! Sen benim Rabbimsin. Senden başka ilâh yoktur. Beni Sen yarattın; ben Senin kulunum ve gücüm yettiğince Sana verdiğim sözdeyim."
        beklenen = "Allah'ım! Sen benim Rabbimsin. Senden başka ilâh yoktur. Beni sen yarattın; ben senin kulunum ve gücüm yettiğince sana verdiğim sözdeyim."
        self.assertEqual(turkce_metin_harf_duzelt(metin), beklenen)

    def test_cumle_basi_korunur(self):
        metin = "Şifayı veren ancak Sensin. Senin şifandan başka şifa yoktur."
        beklenen = "Şifayı veren ancak sensin. Senin şifandan başka şifa yoktur."
        self.assertEqual(turkce_metin_harf_duzelt(metin), beklenen)

    def test_kutsal_isimler_asla_kuculmez(self):
        metin = "Kim bir kötülük yapmak ister de vazgeçerse, Cenâb-ı Hak bunu mükemmel bir iyilik olarak kaydeder."
        beklenen = "Kim bir kötülük yapmak ister de vazgeçerse, Cenâb-ı Hak bunu mükemmel bir iyilik olarak kaydeder."
        self.assertEqual(turkce_metin_harf_duzelt(metin), beklenen)

    def test_resulullah_ve_sahabi_korunur(self):
        metin = "Resûlullah sallallahu aleyhi vesellem bey'at sırasında, **ölüye yüksek sesle ağlamayacağımıza** dair biz kadınlardan söz aldı."
        beklenen = "Resûlullah sallallahu aleyhi vesellem bey'at sırasında, **ölüye yüksek sesle ağlamayacağımıza** dair biz kadınlardan söz aldı."
        self.assertEqual(turkce_metin_harf_duzelt(metin), beklenen)

    def test_konusma_ekleri_ve_alinti_baslangici(self):
        metin = "Malımın üçte ikisini sadaka olarak dağıtayım mı? Diye sordum. Hz. Peygamber: - “Hayır”, dedi."
        beklenen = "Malımın üçte ikisini sadaka olarak dağıtayım mı? diye sordum. Hz. Peygamber: - “Hayır”, dedi."
        self.assertEqual(turkce_metin_harf_duzelt(metin), beklenen)

    def test_hadis_kaynak_kalintilari_temizlenir(self):
        metin = "İnsanlara merhamet etmeyene Allah da merhamet etmez. (Müslim, İmâre 159)"
        beklenen = "İnsanlara merhamet etmeyene Allah da merhamet etmez."
        self.assertEqual(turkce_metin_harf_duzelt(metin), beklenen)


if __name__ == "__main__":
    unittest.main()
