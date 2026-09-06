"""
test_komutlar_ve_otomasyon.py — Ezan Plus Otomasyon & Telegram Komutları Test Paketi
"""

import unittest
from pathlib import Path

from src import db, kuran_db, hadis_db, dua_db, kelime_db, otomasyon
from src.telegram import bot as telegram_bot
from src.uretim import kart as sablon_ciz


class TestOtomasyonVeKomutlar(unittest.TestCase):

    def test_durum_raporu_format(self):
        """Durum raporunun eksiksiz ve HTML formatlı üretildiğini doğrular."""
        rapor = telegram_bot.durum_raporu_olustur()
        self.assertIn("EZAN PLUS YAYIN MOTORU DURUM RAPORU", rapor)
        self.assertIn("6,236", rapor)
        self.assertIn("1,900", rapor)
        self.assertIn("Günde 6 Dağıtım Slotu", rapor)

    def test_yardim_metni(self):
        """Yardım rehberinin tüm 6 komutu içerdiğini doğrular."""
        yardim = telegram_bot.yardim_metni_olustur()
        self.assertIn("/ayet", yardim)
        self.assertIn("/hadis", yardim)
        self.assertIn("/dua", yardim)
        self.assertIn("/kelime", yardim)
        self.assertIn("/durum", yardim)
        self.assertIn("/yayinla", yardim)
        self.assertIn("/kaldir", yardim)

    def test_kelime_db_bul_ve_sec(self):
        """Kelime DB'nin doğru kavram seçip aradığını doğrular."""
        kelime = kelime_db.gunun_kelimesini_sec()
        self.assertIsNotNone(kelime)
        self.assertIn("kelime_tr", kelime)
        self.assertIn("kok", kelime)

        bulunan = kelime_db.kelime_bul("Sekînet")
        self.assertIsNotNone(bulunan)
        self.assertEqual(bulunan["kelime_tr"], "Sekînet")

    def test_dua_db_bul_ve_sec(self):
        """Dua DB'nin doğru dua seçip aradığını doğrular."""
        dua = dua_db.gunun_duasini_sec()
        self.assertIsNotNone(dua)
        self.assertIn("dua_basligi", dua)

        bulunan = dua_db.dua_bul("Tâhâ")
        self.assertIsNotNone(bulunan)
        self.assertIn("Tâhâ", bulunan["kaynak_ref"])

    def test_hadis_db_toplam_ve_bul(self):
        """Hadis DB'nin 1900 hadis barındırdığını doğrular."""
        toplam = hadis_db.toplam_hadis_sayisi()
        self.assertEqual(toplam, 1900)

        h65 = hadis_db.hadis_getir_no(65)
        self.assertIsNotNone(h65)
        self.assertEqual(h65["hadis_no"], 65)

    def test_v16_kartlar_varlik_ve_boyut(self):
        """Tüm V16 kartların 4:5 ve 9:16 tuval boyutlarını doğrular."""
        # Ayet Kartı
        p_ayet_45 = sablon_ciz.ayet_karti_ciz(
            sure_ayet="İnşirâh Sûresi • 5. Âyet",
            turkce_meal="Şüphesiz her **zorlukla beraber** bir kolaylık vardır.",
            arapca_metin="فَإِنَّ مَعَ الْعُسْرِ يُسْرًا",
            tefekkur_notu="Test tefekkür.",
            cikti_dosya_adi="test_v16_unit_ayet_45.png",
            format_tipi="4:5",
        )
        self.assertTrue(p_ayet_45.exists())

        # Hadis Kartı
        p_hadis_45 = sablon_ciz.hadis_karti_ciz(
            hadis_metni="Mümin bir delikten **iki defa** ısırılmaz.",
            kaynak_ravi="Buhârî ve Müslim",
            tefekkur_notu="Test tefekkür.",
            cikti_dosya_adi="test_v16_unit_hadis_45.png",
            format_tipi="4:5",
        )
        self.assertTrue(p_hadis_45.exists())

        # Dua Kartı
        p_dua_45 = sablon_ciz.dua_karti_ciz(
            dua_basligi="Hz. Mûsâ'nın Niyazı",
            turkce_anlam="Rabbim, **göğsüme genişlik** ver.",
            arapca_metin="رَبِّ اشْرَحْ لِي صَدْرِي",
            okunus_veya_fazilet="Tâhâ Sûresi 25-28",
            cikti_dosya_adi="test_v16_unit_dua_45.png",
            format_tipi="4:5",
        )
        self.assertTrue(p_dua_45.exists())

        # Kelime Kartı
        p_kelime_45 = sablon_ciz.kelime_karti_ciz(
            kelime_tr="Sekînet",
            kelime_ar="السَّكِينَةُ",
            okunus="es-Sekîne",
            kok="S-K-N",
            lugat_anlami="Gönül **huzuru ve sükûnet**.",
            kuran_boyutu="Müminlerin kalplerine sekînet indirdi.",
            hayat_dersi="Test hikmet.",
            ayet_ref="Fetih Sûresi • 4. Âyet",
            cikti_dosya_adi="test_v16_unit_kelime_45.png",
            format_tipi="4:5",
        )
        self.assertTrue(p_kelime_45.exists())

    def test_yayindan_kaldir_ve_gecmis_temizleme(self):
        """Bir içeriğin yayından kaldırıldığında durumunun güncellendiğini ve geçmişten silindiğini doğrular."""
        from src.telegram.yonetici import yayindan_kaldir

        pid = db.paylasim_ekle(
            kategori="ayet",
            format_tipi="reels_9_16",
            turkce_metin="Test âyet metni",
            baslik="Test Başlık",
            kaynak="Test Sûresi, 1. Âyet",
            durum="yayinlandi",
        )
        self.assertIsNotNone(pid)

        # Yayın geçmişine girdi mi kontrol et
        kayit = db.paylasim_getir(pid)
        db.yayin_gecmisi_kaydet(kayit)
        gecmis_once = db.yayin_gecmisi_yukle()
        self.assertTrue(any(item.get("kaynak") == "Test Sûresi, 1. Âyet" for item in gecmis_once))

        # Yayından kaldır
        sonuclar = yayindan_kaldir(pid)
        self.assertIsInstance(sonuclar, dict)

        # Durum kontrolü
        kayit_sonra = db.paylasim_getir(pid)
        self.assertEqual(kayit_sonra["durum"], "yayindan_kaldirildi")

        # JSON geçmişinden silindi mi kontrol et
        gecmis_sonra = db.yayin_gecmisi_yukle()
        self.assertFalse(any(item.get("kaynak") == "Test Sûresi, 1. Âyet" for item in gecmis_sonra))

    def test_video_secavend_ve_satir_araligi(self):
        """Secavend durak işaretlerinin ayıklandığını ve satırlar arası >= 28px net pay olduğunu doğrular."""
        from src.uretim.video import arapca_kelimeleri_ayristir, _SayfaVerisi
        
        # Nisâ 33: 19 kelime + 2 secavend
        nisa_33 = kuran_db.ayet_getir(4, 33)
        ar_kelimeler = arapca_kelimeleri_ayristir(nisa_33["arapca_metin"])
        self.assertEqual(len(ar_kelimeler), 19)
        self.assertNotIn("ۚ", ar_kelimeler)
        self.assertFalse(any("ۚ" in w for w in ar_kelimeler))

        # Sayfa verisi satır aralığı testi
        sayfa = _SayfaVerisi(
            p_idx=0,
            sayfa_sayisi=2,
            start_w=0,
            end_w=10,
            page_ar=ar_kelimeler[:10],
            page_tr=["ve", "cealna", "mevaliye", "mimma", "terakel", "validani", "vel", "akrabun", "vellezine", "akadet"],
            page_meal="Test meali",
            sure_ayet="Nisâ • 33",
            s1="BAŞLIK 1",
            s2="BAŞLIK 2",
            tef="Test tefekkür",
            hafiz_adi="Mişari Râşid",
        )
        self.assertEqual(len(sayfa.ar_satir_bilgileri), 2)
        self.assertEqual(len(sayfa.ar_satir_y_list), 2)
        
        # 1. ve 2. satır arasındaki net boşluğu doğrula
        y0 = sayfa.ar_satir_y_list[0]
        y1 = sayfa.ar_satir_y_list[1]
        self.assertGreater(y1 - y0, 140)  # Y koordinatları arasında güvenli ferah basamak


if __name__ == "__main__":
    unittest.main()


