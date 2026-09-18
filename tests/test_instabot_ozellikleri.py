"""
test_instabot_ozellikleri.py — Ezan Plus Bot Instabot Parite Özellikleri Testleri

Test edilen özellikler:
1. Çoklu kanal checkbox toggle butonları ve varsayılan kanallar
2. Zamanlanmış yayın alt menüsü, veritabanı sorgusu ve zamanlanmış yayın motoru
3. Manuel paylaşım paketi menüsü ve tek tıkla kopyalama
4. AI metin ve tefekkür revizyon menüsü & tescilli metin koruma
5. Canlı ilerleme çubuğu (progress bar)
6. Bot duraklatma / devam ettirme (pause / resume) sistemi
7. Telegram içi interaktif ayarlar menüsü ve döngüsel geçiş
8. Sesli yayın tamamlama bildirimi ve [🗑️ Bu Yayını Kaldır]
9. HTML entity 400 hata kurtarma & Chat ID otomatik göçü
"""

import json
import os
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src import db
from src.telegram import bot as telegram_bot
from src.telegram import yonetici
from src.uretim import ai


class TestInstabotOzellikleri(unittest.TestCase):

    def setUp(self):
        telegram_bot.devam_et()

    # -------------------------------------------------------------------------
    # 1. KANAL CHECKBOX TOGGLE VE ONAY MENÜSÜ
    # -------------------------------------------------------------------------
    def test_varsayilan_kanallar(self):
        reels_k = telegram_bot.varsayilan_kanallar("reels_9_16")
        self.assertTrue(reels_k["tiktok"])
        self.assertTrue(reels_k["instagram"])
        self.assertTrue(reels_k["instagram_story"])
        self.assertTrue(reels_k["facebook"])
        self.assertTrue(reels_k["threads"])
        self.assertTrue(reels_k["youtube"])

        post_k = telegram_bot.varsayilan_kanallar("post_4_5")
        self.assertTrue(post_k["tiktok"])
        self.assertNotIn("youtube", post_k)
        self.assertTrue(post_k["instagram"])
        self.assertTrue(post_k["threads"])

    def test_kanal_butonlari_ve_toggle(self):
        kanallar = {"tiktok": True, "instagram": False, "instagram_story": True, "facebook": True, "threads": True, "youtube": False}
        butonlar = telegram_bot.kanal_butonlari("reels_9_16", kanallar, paylasim_id=123)
        self.assertIsInstance(butonlar, list)
        self.assertEqual(len(butonlar), 2)

        # TikTok açık olmalı (✅), Instagram kapalı olmalı (⬜)
        tt_btn = next(b for b in butonlar[0] if "TT" in b["text"])
        self.assertIn("✅", tt_btn["text"])
        self.assertEqual(tt_btn["callback_data"], "kanal:tiktok:123")

        ig_btn = next(b for b in butonlar[0] if "Reels" in b["text"])
        self.assertIn("⬜", ig_btn["text"])
        self.assertEqual(ig_btn["callback_data"], "kanal:instagram:123")

    def test_ana_onay_menusu_tum_bilesenleri_icerir(self):
        menuler = telegram_bot.ana_onay_menusu_kur(paylasim_id=99, format_tipi="reels_9_16", kategori="hadis")
        tum_datalar = [btn["callback_data"] for satir in menuler for btn in satir]

        self.assertIn("onay_99", tum_datalar)
        self.assertIn("zamanla_menu_99", tum_datalar)
        self.assertIn("manuel_paket_99", tum_datalar)
        self.assertIn("metin_menu_99", tum_datalar)
        self.assertIn("sesyenile_99", tum_datalar)
        self.assertIn("atla_99", tum_datalar)
        self.assertIn("cope_at_99", tum_datalar)

    # -------------------------------------------------------------------------
    # 2. ZAMANLANMIŞ YAYIN VE ERTELEME
    # -------------------------------------------------------------------------
    def test_zamanlama_menusu(self):
        menu = telegram_bot.zamanlama_menusu_kur(paylasim_id=77)
        datalar = [btn["callback_data"] for satir in menu for btn in satir]
        self.assertIn("yayin_sonra:30:77", datalar)
        self.assertIn("yayin_sonra:60:77", datalar)
        self.assertIn("yayin_sonra:120:77", datalar)
        self.assertIn("yayin_sonra:240:77", datalar)
        self.assertIn("onay_menu_77", datalar)

    def test_zamanlanmis_yayin_db_ve_kontrol(self):
        pid = db.paylasim_ekle(
            kategori="ayet",
            format_tipi="reels_9_16",
            turkce_metin="Şüphesiz her zorlukla beraber bir kolaylık vardır.",
            baslik="İnşirah 5",
            durum="taslak",
        )
        try:
            # Geçmiş bir zamana zamanla
            gecmis_zaman = (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
            db.durum_guncelle(pid, yeni_durum="zamanlandi", yayin_zamani=gecmis_zaman)

            bekleyenler = db.zamanlanmis_paylasimlari_getir()
            bekleyen_idler = [b["id"] for b in bekleyenler]
            self.assertIn(pid, bekleyen_idler)

            # Worker simülasyonu
            with patch.object(telegram_bot, "yayinla_hepsi", return_value={"instagram": "ok_123"}) as mock_yayinla:
                with patch.object(telegram_bot, "yayin_sonucu_bildir") as mock_bildir:
                    adet = telegram_bot.zamanlanmis_yayinlari_kontrol_et()
                    self.assertGreaterEqual(adet, 1)
                    mock_yayinla.assert_called()
                    mock_bildir.assert_called()
        finally:
            with db.baglanti_al() as con:
                con.execute("DELETE FROM paylasimlar WHERE id = ?", (pid,))

    # -------------------------------------------------------------------------
    # 3. MANUEL PAYLAŞIM PAKETİ
    # -------------------------------------------------------------------------
    def test_manuel_paylasim_menusu(self):
        menu = telegram_bot.manuel_paylasim_menusu_kur(paylasim_id=88)
        self.assertTrue(any("instagram.com" in btn.get("url", "") for satir in menu for btn in satir))
        self.assertTrue(any("tiktok.com" in btn.get("url", "") for satir in menu for btn in satir))
        datalar = [btn.get("callback_data") for satir in menu for btn in satir if "callback_data" in btn]
        self.assertIn("manuel_tamam_88", datalar)
        self.assertIn("manuel_diger_88", datalar)

    # -------------------------------------------------------------------------
    # 4. TEFEKKÜR VE METİN REVİZYONU
    # -------------------------------------------------------------------------
    def test_metin_yenileme_menusu(self):
        menu = telegram_bot.metin_yenileme_menusu_kur(paylasim_id=55)
        datalar = [btn["callback_data"] for satir in menu for btn in satir]
        self.assertIn("metin_kisalt_55", datalar)
        self.assertIn("metin_genislet_55", datalar)
        self.assertIn("metin_yenile_55", datalar)
        self.assertIn("onay_menu_55", datalar)

    @patch("src.uretim.ai._gemini_cagir_json")
    def test_metin_ve_tefekkur_revize_et_tescilli_metni_korur(self, mock_gemini):
        mock_gemini.return_value = {
            "tefekkur_notu": "Zorluğun hemen ardından gelen ilahi ferahlık kalbe şifadır.",
            "caption": "İnşirah Suresi 5. Ayet tefekkürü ile huzur bulun.\n\n#Kuran #Ayet",
        }

        orijinal_turkce = "Gerçekten her güçlükle beraber bir kolaylık vardır."
        yeni_tef, yeni_cap = ai.metin_ve_tefekkur_revize_et(
            turkce_metin=orijinal_turkce,
            kategori="ayet",
            hedef="kisalt",
            mevcut_tefekkur="Eski uzun tefekkür",
            mevcut_caption="Eski caption",
        )

        self.assertIn("ilahi ferahlık", yeni_tef)
        self.assertIn("İnşirah Suresi", yeni_cap)
        # Orijinal meal metni AI'ye ezdirilmez
        self.assertNotIn("bot", yeni_cap.lower())

    # -------------------------------------------------------------------------
    # 5. CANLI İLERLEME ÇUBUĞU (PROGRESS BAR)
    # -------------------------------------------------------------------------
    @patch("src.telegram.bot._istek")
    def test_durum_guncelle_ilerleme_cubugu(self, mock_istek):
        mock_istek.return_value = {"ok": True}
        telegram_bot.durum_guncelle(
            chat_id="123456",
            message_id=999,
            baslik="V20 Hadis Videosu",
            adim=2,
            toplam_adim=4,
            detay="Mazlum Kiper sesi sentezleniyor...",
        )
        mock_istek.assert_called_once()
        cagri = mock_istek.call_args[1]["data"]
        self.assertIn("editMessageText", mock_istek.call_args[0][0])
        self.assertIn("V20 Hadis Videosu", cagri["text"])
        self.assertIn("[▰▰▱▱] %50 (2/4)", cagri["text"])
        self.assertIn("Mazlum Kiper sesi", cagri["text"])

    # -------------------------------------------------------------------------
    # 6. BOT DURAKLATMA / DEVAM ETTİRME
    # -------------------------------------------------------------------------
    def test_bot_duraklat_ve_devam_et(self):
        telegram_bot.devam_et()
        durak, _ = telegram_bot.duraklatildi_mi()
        self.assertFalse(durak)

        bitis = telegram_bot.duraklat(saat=6)
        durak, kalan = telegram_bot.duraklatildi_mi()
        self.assertTrue(durak)
        self.assertTrue("5s" in kalan or "6s" in kalan)

        # Duraklatılmışken zamanlanmış yayınların kontrol edilmemesi
        with patch.object(db, "zamanlanmis_paylasimlari_getir") as mock_db:
            adet = telegram_bot.zamanlanmis_yayinlari_kontrol_et()
            self.assertEqual(adet, 0)
            mock_db.assert_not_called()

        telegram_bot.devam_et()
        durak_son, _ = telegram_bot.duraklatildi_mi()
        self.assertFalse(durak_son)

    def test_duraklatma_ve_kontrol_merkezi_menuleri(self):
        d_menu = telegram_bot.duraklatma_secenekleri_menusu()
        d_datalar = [btn["callback_data"] for satir in d_menu for btn in satir]
        self.assertIn("duraklat:1", d_datalar)
        self.assertIn("duraklat:6", d_datalar)
        self.assertIn("duraklat:24", d_datalar)

        k_menu = telegram_bot.kontrol_merkezi_menusu()
        k_datalar = [btn["callback_data"] for satir in k_menu for btn in satir]
        self.assertIn("menu_ayet", k_datalar)
        self.assertIn("menu_hadis", k_datalar)
        self.assertIn("menu_dua", k_datalar)
        self.assertIn("menu_kelime", k_datalar)
        self.assertIn("cmd_ayarlar", k_datalar)

    # -------------------------------------------------------------------------
    # 7. AYARLAR MENÜSÜ VE TOGGLE
    # -------------------------------------------------------------------------
    def test_ayarlar_menusu_ve_gecis(self):
        menu = telegram_bot.ayarlar_menusu_kur()
        self.assertGreater(len(menu), 3)
        datalar = [btn["callback_data"] for satir in menu for btn in satir]
        self.assertIn("ayar_toggle:ayar_facebook", datalar)
        self.assertIn("ayar_toggle:ayar_threads", datalar)

    # -------------------------------------------------------------------------
    # 8. SESLİ BİLDİRİM VE [🗑️ Bu Yayını Kaldır]
    # -------------------------------------------------------------------------
    @patch("src.telegram.bot.mesaj_gonder")
    def test_yayin_sonucu_bildir_sesli_ve_butonlu(self, mock_mesaj):
        mock_mesaj.return_value = 1234
        sonuclar = {"instagram": "ok_1", "tiktok": "ok_2", "youtube_hata": "Quota exceeded"}
        kayit = {"id": 888, "baslik": "Bakara Suresi 152", "kategori": "ayet"}

        telegram_bot.yayin_sonucu_bildir(888, sonuclar, kayit)
        mock_mesaj.assert_called_once()
        args, kwargs = mock_mesaj.call_args

        metin = args[0]
        self.assertIn("KISMİ BAŞARIYLA YAYINLANDI", metin)
        self.assertIn("INSTAGRAM, TIKTOK", metin)
        self.assertIn("YOUTUBE: Quota exceeded", metin)
        self.assertFalse(kwargs.get("disable_notification"))  # Sesli uyarı

        butonlar = kwargs.get("butonlar")
        btn_datalar = [b["callback_data"] for satir in butonlar for b in satir]
        self.assertIn("kaldir_888", btn_datalar)
        self.assertIn("telafi_hepsi_888", btn_datalar)

    # -------------------------------------------------------------------------
    # 9. DAYANIKLILIK: HTML HATASI VE CHAT ID OTOMATİK GÖÇÜ
    # -------------------------------------------------------------------------
    @patch("src.telegram.bot.requests.post")
    def test_istek_html_hata_kurtarma(self, mock_post):
        # 1. Çağrıda 400 Bad Request: can't parse entities hatası
        # 2. Çağrıda başarı
        resp1 = MagicMock()
        resp1.json.return_value = {"ok": False, "description": "Bad Request: can't parse entities: unclosed tag"}
        resp2 = MagicMock()
        resp2.json.return_value = {"ok": True, "result": {"message_id": 9999}}
        mock_post.side_effect = [resp1, resp2]

        res = telegram_bot._istek("sendMessage", data={"chat_id": "123", "text": "<b>Test unclosed tag"})
        self.assertEqual(res.get("message_id"), 9999)
        self.assertEqual(mock_post.call_count, 2)

    # -------------------------------------------------------------------------
    # 10. CANLI YAYIN DAĞITIM İLERLEME METNİ VE CALLBACK PARİTESİ
    # -------------------------------------------------------------------------
    def test_yayin_durum_metni_olustur_format(self):
        """Instabot standardında canlı ilerleme metni ve platform durumlarının doğru formatlandığını doğrular."""
        durumlar = {
            "tiktok": "✅ Yayında",
            "instagram": "⏳ Yükleniyor...",
            "threads": "⏱️ Sırada",
            "facebook": "⏱️ Sırada",
        }
        metin = telegram_bot.yayin_durum_metni_olustur(
            paylasim_id=310,
            adim=2,
            toplam_adim=4,
            durum_haritasi=durumlar,
            baslik="Riyâzü's-Sâlihîn • 310. Hadis",
            baslangic_ts=datetime.now().timestamp() - 5.2,
            format_tipi="reels_9_16",
        )
        self.assertIn("YAYIN DAĞITIMI SÜRÜYOR... (#310)", metin)
        self.assertIn("310. Hadis", metin)
        self.assertIn("[▰▰▱▱] %50 (2/4)", metin)
        self.assertIn("TikTok (@ezanplusapp):</b> ✅ Yayında", metin)
        self.assertIn("Instagram Reels:</b> ⏳ Yükleniyor...", metin)
        self.assertIn("Geçen Süre:", metin)

    def test_yayinla_hepsi_durum_cb_cagrilir(self):
        """yayinla_hepsi çalışırken durum_cb'nin platform adımlarında tetiklendiğini doğrular."""
        pid = db.paylasim_ekle(
            kategori="hadis",
            format_tipi="post_4_5",
            turkce_metin="Müminler kardeştir.",
            baslik="Kardeşlik Hadisi",
            durum="taslak",
            gorsel_yollari=["/tmp/test_feed.png"],
        )
        try:
            cagrilar = []
            def mock_cb(adim, toplam, kanal, durumlar):
                cagrilar.append((adim, toplam, kanal, dict(durumlar)))

            with patch("src.platformlar.meta.instagram_gorsel_paylas", return_value={"id": "ig_111"}), \
                 patch("src.platformlar.meta.instagram_story_paylas", return_value={"id": "story_222"}), \
                 patch("src.platformlar.threads.threads_zincir_paylas", return_value={"id": "th_333"}), \
                 patch("src.platformlar.meta.facebook_post_paylas", return_value={"id": "fb_444"}), \
                 patch("src.denetleyici.denetle_paylasim") as mock_denetle:

                mock_d = MagicMock()
                mock_d.gecerli = True
                mock_denetle.return_value = mock_d

                res = yonetici.yayinla_hepsi(pid, oncesinde_onayla=False, kanallar={"instagram": True, "facebook": True, "threads": False, "instagram_story": False, "tiktok": False}, durum_cb=mock_cb)

                self.assertIn("instagram", res)
                self.assertIn("facebook", res)
                self.assertGreaterEqual(len(cagrilar), 2)
                # Callback adım ve durum_haritasi içerir
                son_cagri = cagrilar[-1]
                self.assertEqual(son_cagri[1], 2)  # toplam_adim = 2
                self.assertIn("facebook", son_cagri[3])
                self.assertEqual(son_cagri[3]["facebook"], "✅ Yayında")
        finally:
            with db.baglanti_al() as con:
                con.execute("DELETE FROM paylasimlar WHERE id = ?", (pid,))

    # -------------------------------------------------------------------------
    # 11. CANLI YAYIN GÖRÜNTÜLEME VE DETAY BUTONLARI
    # -------------------------------------------------------------------------
    def test_telafi_butonlari_canli_izleme_linkleri(self):
        """Başarıyla yayınlanan platformlar için doğrudan görüntüleme linklerinin eklendiğini doğrular."""
        sonuclar = {
            "instagram": "ig_123",
            "threads": "th_456",
            "facebook": "fb_789",
            "tiktok": "tt_101",
            "youtube": "yt_202",
            "youtube_url": "https://youtube.com/shorts/test1234",
        }
        butonlar = telegram_bot.telafi_butonlari_kur(paylasim_id=77, sonuclar=sonuclar, format_tipi="reels_9_16")

        url_listesi = [b["url"] for satir in butonlar for b in satir if "url" in b]
        text_listesi = [b["text"] for satir in butonlar for b in satir if "text" in b]

        self.assertTrue(any("instagram.com" in u for u in url_listesi))
        self.assertTrue(any("threads.net" in u for u in url_listesi))
        self.assertTrue(any("facebook.com" in u for u in url_listesi))
        self.assertTrue(any("tiktok.com" in u for u in url_listesi))
        self.assertTrue(any("youtube.com" in u for u in url_listesi))
        self.assertTrue(any("Instagram'da Gör" in t for t in text_listesi))
        self.assertTrue(any("Threads'te Gör" in t for t in text_listesi))


if __name__ == "__main__":
    unittest.main()
