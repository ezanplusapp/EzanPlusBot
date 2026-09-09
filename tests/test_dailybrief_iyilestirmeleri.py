"""
test_dailybrief_iyilestirmeleri.py — Daily Brief mimarisinden Ezan Plus'a aktarılan
güvenilirlik, dayanıklılık ve otomasyon iyileştirmelerinin birim testleri.
"""

import os
import re
import sys
import unittest
from unittest.mock import patch, MagicMock

from src import db
from src.telegram import bot as telegram_bot
from src.telegram import yonetici
from src.platformlar import meta, threads, youtube, tiktok
from src.uretim import ai
from src import denetleyici


class TestDailyBriefIyilestirmeleri(unittest.TestCase):

    def test_yayinla_hepsi_mukerrer_kilidi(self):
        """
        Daha önce yayınlanmış bir paylaşıma tekrar yayinla_hepsi çağrıldığında
        mükerrer yayın kilidinin devreye girip yayinla_telafi'ye yönlendirdiğini doğrular.
        """
        kayit_id = 8888
        sahte_kayit = {
            "id": kayit_id,
            "durum": "yayinlandi",
            "kategori": "hadis",
            "format": "post_4_5",
            "caption": "Hadis-i Şerif metni #ezanplus",
            "gorsel_yollari": ["g1.png", "g2.png"],
            "instagram_post_id": "ig_12345",
            "threads_post_id": "th_67890",
            "facebook_post_id": "fb_11111",
        }

        with patch.object(db, "paylasim_getir", return_value=sahte_kayit), \
             patch.object(yonetici, "yayinla_telafi", return_value={"hepsi": True}) as mock_telafi:
            
            sonuclar = yonetici.yayinla_hepsi(kayit_id)
            mock_telafi.assert_called_once_with(kayit_id, hedef_kanal="hepsi")
            self.assertEqual(sonuclar, {"hepsi": True})

    def test_cevapsiz_telegram_callback_korumasi(self):
        """
        Bilinmeyen, geçersiz veya süresi dolmuş Telegram butonlarına basıldığında
        sonsuz spinner kalmaması için callback_cevapla çağrıldığını doğrular.
        """
        sahte_updates = [
            {
                "update_id": 99999,
                "callback_query": {
                    "id": "cq_stale_123",
                    "data": "bilinmeyen_veya_gecersiz_aksiyon:123",
                    "from": {"id": 12345},
                }
            }
        ]

        sahte_yanit = MagicMock()
        sahte_yanit.json.return_value = {"ok": True, "result": sahte_updates}

        with patch("requests.get", return_value=sahte_yanit), \
             patch.object(telegram_bot, "get_token_ve_chat_id", return_value=("fake_token", "12345")), \
             patch.object(telegram_bot, "callback_cevapla") as mock_cevap:
            
            telegram_bot.tek_sefer_dinle(offset=0)

            mock_cevap.assert_called_with(
                "cq_stale_123",
                "⚠️ Bu buton artık geçerli değil veya süresi doldu.",
                alert=False
            )

    def test_threads_jetonu_yenile(self):
        """Threads uzun ömürlü token yenileme fonksiyonunu doğrular."""
        sahte_yanit = MagicMock()
        sahte_yanit.status_code = 200
        sahte_yanit.json.return_value = {
            "access_token": "TH_NEW_LONG_LIVED_TOKEN_123",
            "token_type": "bearer",
            "expires_in": 5184000  # 60 gün (5184000 saniye)
        }

        with patch("requests.get", return_value=sahte_yanit) as mock_get, \
             patch("pathlib.Path.exists", return_value=False), \
             patch.dict(os.environ, {"THREADS_ACCESS_TOKEN": "TH_OLD_TOKEN"}):
            
            token, gun = threads.jetonu_yenile()
            self.assertEqual(token, "TH_NEW_LONG_LIVED_TOKEN_123")
            self.assertEqual(gun, 60)
            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            self.assertIn("graph.threads.net/refresh_access_token", args[0])

    def test_meta_multi_cdn_fallback_ve_hata_kodlari(self):
        """
        Meta Graph API geçici indirme / işleme hatalarında subcode 2207003 / 2207052
        ve CDN fallback isimlerini doğrular.
        """
        self.assertIn(2207003, meta.GECICI_MEDYA_HATA_KODLARI)
        self.assertIn(2207052, meta.GECICI_MEDYA_HATA_KODLARI)

        self.assertEqual(meta._cdn_adlandir("https://files.catbox.moe/abc.png"), "catbox")
        self.assertEqual(meta._cdn_adlandir("https://litterbox.catbox.moe/abc.png"), "litterbox")
        self.assertEqual(meta._cdn_adlandir("https://uguu.se/abc.png"), "uguu")

    def test_youtube_headless_ci_korumasi(self):
        """
        CI / Headless ortamda YouTube token eksik veya geçersizse
        run_local_server ile kilitlenmek yerine açık hata fırlatıldığını doğrular.
        """
        with patch.object(sys.stdin, "isatty", return_value=False), \
             patch("pathlib.Path.exists", return_value=False):
            
            with self.assertRaises(RuntimeError) as ctx:
                youtube.yetki_al()
            self.assertIn("Headless CI", str(ctx.exception))

    def test_tiktok_headless_ci_korumasi(self):
        """
        CI / Headless ortamda TikTok refresh token yoksa
        input() ile kilitlenmek yerine RuntimeError fırlatıldığını doğrular.
        """
        with patch.object(tiktok, "get_tiktok_api_anahtarlari", return_value=("key123", "sec123")), \
             patch.object(sys.stdin, "isatty", return_value=False), \
             patch("pathlib.Path.exists", return_value=False), \
             patch.object(tiktok, "get_env", return_value=""):
            
            with self.assertRaises(RuntimeError) as ctx:
                tiktok.yetki_al()
            self.assertIn("Headless CI", str(ctx.exception))

    def test_tiktok_baslik_ve_etiketleri_birlestir(self):
        """
        TikTok için başlık ve etiket birleştirici:
        Manşet metnini korur, azami sınırı aşarsa etiketleri sondan kırpar.
        """
        baslik = "İhlas Sûresi Tilaveti - Kalpleri Aydınlatan İlahi Mesaj"
        aciklama = "Ezan Plus ile Kur'an tilaveti dinleyin.\n\n#ezanplus #kuran #ayet #tilavet #tefekkur #dua"

        metin = tiktok.baslik_ve_etiketleri_birlestir(baslik, aciklama, maks_karakter=150)
        self.assertTrue(metin.startswith(baslik))
        self.assertLessEqual(len(metin), 150)
        self.assertIn("#ezanplus", metin)

    def test_hashtag_turkce_karakter_tekillestirme_ve_ezanplus(self):
        """
        Hashtaglerde Türkçe karakter tekilleştirmesi (ş/s, ı/i, ö/o, ü/u, ç/c, ğ/g, â/a)
        ve ilk etiket olarak #ezanplus garantisi ile azami 5 sınırını doğrular.
        """
        # 1. Anahtar fonksiyonu
        self.assertEqual(ai._etiket_anahtari("#şükür"), ai._etiket_anahtari("#sukur"))
        self.assertEqual(ai._etiket_anahtari("#duâ"), ai._etiket_anahtari("#dua"))
        self.assertEqual(ai._etiket_anahtari("#İslam"), ai._etiket_anahtari("#islam"))

        # 2. Normalleştirme
        ham_tags = ["#şükür", "#sukur", "#dua", "#duâ", "#kuran", "#namaz", "#huzur"]
        norm = ai.hashtaglari_normallestir(ham_tags, maks=5, zorunlu_ilk="ezanplus")
        
        # İlk etiket #ezanplus olmalı
        self.assertEqual(norm[0], "#ezanplus")
        # Tam 5 adet olmalı
        self.assertEqual(len(norm), 5)
        # #sukur tekrarlanmamalı çünkü #şükür zaten var
        self.assertIn("#şükür", norm)
        self.assertNotIn("#sukur", norm)
        # #duâ tekrarlanmamalı çünkü #dua var
        self.assertIn("#dua", norm)
        self.assertNotIn("#duâ", norm)

        # 3. Caption güncelleme
        ham_caption = (
            "Günün duasıdır. Kalbinize ferahlık versin.\n\n"
            "#şükür #sukur #dua #huzur #tefekkur #ekstra1 #ekstra2"
        )
        guncel_caption = ai.caption_hashtaglari_guncelle(ham_caption, maks=5)
        self.assertIn("#ezanplus", guncel_caption)
        self.assertIn("Günün duasıdır. Kalbinize ferahlık versin.", guncel_caption)
        
        cikarilan_etiketler = re.findall(r'#\w+', guncel_caption)
        self.assertEqual(len(cikarilan_etiketler), 5)
        self.assertEqual(cikarilan_etiketler[0], "#ezanplus")

    def test_denetleyici_otomatik_onar_hashtag_normalizasyonu(self):
        """
        denetleyici.otomatik_onar fonksiyonunun bozuk veya eksik hashtag setini
        tam 5 tekil hashtag ve #ezanplus ile onardığını doğrular.
        """
        sahte_kayit = {
            "id": 7777,
            "durum": "onay_bekliyor",
            "kategori": "ayet",
            "format": "reels",
            "baslik": "Bakara Sûresi, 152. Âyet",
            "turkce_metin": "Öyleyse yalnız beni anın ki ben de sizi anayım. Bana şükredin, sakın nankörlük etmeyin.",
            "arapca_metin": "فَاذْكُرُونِي أَذْكُرْكُمْ وَاشْكُرُوا لِي وَلَا تَكْفُرُونِ",
            "tefekkur": "Allah'ı anmak kalbin yegâne huzur kaynağıdır.",
            "caption": "Bakara 152 meali.\n\n#şükür #sukur #kuran",
            "gorsel_yollari": ["reels.mp4"],
        }

        with patch.object(db, "paylasim_getir", return_value=sahte_kayit), \
             patch.object(db, "paylasim_guncelle") as mock_guncelle, \
             patch.object(denetleyici, "denetle_paylasim") as mock_denetle:
            
            d_gecersiz = MagicMock()
            d_gecersiz.gecerli = False
            d_gecerli = MagicMock()
            d_gecerli.gecerli = True
            mock_denetle.side_effect = [d_gecersiz, d_gecerli]

            with patch.object(denetleyici, "denetle_video_dosyasi", return_value=([], [], {})):
                onardi_mi, duzeltmeler = denetleyici.otomatik_onar(7777)
                
                self.assertTrue(onardi_mi)
                self.assertTrue(mock_guncelle.called)
                yeni_caption = mock_guncelle.call_args.kwargs.get("caption", "")
                
                self.assertIn("#ezanplus", yeni_caption)
                tags = re.findall(r'#\w+', yeni_caption)
                self.assertEqual(len(tags), 5)

    def test_kelime_otomatik_yayinlanma_akisi(self):
        """
        kelime_postu_olustur_ve_gonder çağrıldığında auto_publish=True varsayılanıyla
        onay_istegi_gonder yerine yayinla_hepsi ve yayin_detay_karti_gonder çağrıldığını doğrular.
        """
        from src import otomasyon
        from src.uretim import ai as icerik_uret

        sahte_icerik = {
            "kelime_id": 14,
            "kelime_tr": "Vakar",
            "kelime_ar": "الْوَقَارُ",
            "turkce_okunus": "el-Vakâr",
            "koken": "Arapça",
            "kisa_anlam": "Ağırbaşlılık",
            "lugat_anlami": "Ağırbaşlılık, heybet ve vakar.",
            "kuran_boyutu": "Furkân 63",
            "hayat_dersi": "Vakar kibir değil; asil özgüvendir.",
            "ayet_ref": "Furkân Sûresi, 63. Âyet",
            "ayet_arapca": "وَعِبَادُ ٱلرَّحْمَـٰنِ",
            "tefekkur_notu": "Vakar müminin süsüdür.",
            "caption": "Kur'an Sözlüğü: Vakar #ezanplus",
            "hashtagler": ["#ezanplus", "#kuran", "#vakar", "#islam", "#ayet"]
        }

        with patch.object(icerik_uret, "kelime_icerigi_uret", return_value=sahte_icerik), \
             patch("src.uretim.kart.kelime_karti_ciz"), \
             patch.object(denetleyici, "denetle_paylasim") as mock_denetle, \
             patch.object(db, "paylasim_ekle", return_value=112), \
             patch.object(telegram_bot, "yayinla_hepsi", return_value={"instagram": True}) as mock_yayinla, \
             patch.object(telegram_bot, "yayin_detay_karti_gonder") as mock_detay, \
             patch.object(telegram_bot, "onay_istegi_gonder") as mock_onay:

            d_sonuc = MagicMock()
            d_sonuc.gecerli = True
            d_sonuc.metrikler = {}
            mock_denetle.return_value = d_sonuc

            pid = otomasyon.kelime_postu_olustur_ve_gonder(kavram="Vakar")

            self.assertEqual(pid, 112)
            mock_yayinla.assert_called_once_with(112)
            mock_detay.assert_called_once_with(112, {"instagram": True})
            mock_onay.assert_not_called()

    def test_kelimeyi_paylasildi_isaretle_kavram(self):
        """kelime_db.kelimeyi_paylasildi_isaretle_kavram fonksiyonunun doğruluğunu test eder."""
        from src import kelime_db

        sahte_kelimeler = [
            {"id": 1, "kelime_tr": "İhsan", "paylasildi_mi": False},
            {"id": 14, "kelime_tr": "Vakar", "paylasildi_mi": False},
        ]

        with patch.object(kelime_db, "kelimeleri_yukle", return_value=sahte_kelimeler), \
             patch("builtins.open", unittest.mock.mock_open()) as mock_file, \
             patch("json.dump") as mock_dump:

            kelime_db.kelimeyi_paylasildi_isaretle_kavram("Vakar")
            self.assertTrue(sahte_kelimeler[1]["paylasildi_mi"])
            self.assertFalse(sahte_kelimeler[0]["paylasildi_mi"])
            mock_dump.assert_called_once()

    def test_dinle_ve_bekle_zaman_asimi_mesaj_guncelleme(self):
        """
        dinle_ve_bekle zaman aşımına uğradığında Telegram mesajını güncelleyip
        butonları geçersiz kıldığını doğrular.
        """
        from src import otomasyon

        with patch("time.time", side_effect=[100.0, 100.0, 105.0]), \
             patch("time.sleep", return_value=None), \
             patch.object(telegram_bot, "tek_sefer_dinle", return_value=[]), \
             patch.object(db, "paylasim_getir", return_value={"telegram_mesaj_id": 5555}), \
             patch.object(telegram_bot, "get_token_ve_chat_id", return_value=("fake_tok", "fake_chat")), \
             patch.object(telegram_bot, "caption_ve_buton_guncelle") as mock_guncelle:

            sonuc = otomasyon.dinle_ve_bekle(sure_saniye=2, paylasim_id=110, yayin_sonrasi=False)
            self.assertFalse(sonuc)
            mock_guncelle.assert_called_once()
            kwargs = mock_guncelle.call_args.kwargs
            self.assertEqual(kwargs["chat_id"], "fake_chat")
            self.assertEqual(kwargs["mesaj_id"], 5555)
            self.assertIn("ONAY SÜRESİ DOLDU", kwargs["yeni_caption"])


if __name__ == "__main__":
    unittest.main()

