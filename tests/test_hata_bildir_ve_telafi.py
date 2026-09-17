"""
test_hata_bildir_ve_telafi.py — Hata Bildirim, Teşhis ve Telafi Mekanizması Testleri
"""

import os
import json
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from src import db, hata_bildir
from src.telegram import bot as telegram_bot
from src.telegram import yonetici
from src.platformlar import meta, threads


class TestHataBildirVeTelafi(unittest.TestCase):

    def test_hata_bildir_tani(self):
        """Hata mesajlarından doğru tanı kodunu ve açıklamasını çıkardığını doğrular."""
        # 1. CDN Hatası
        tani_cdn = hata_bildir.tani("Meta Graph API: Görsel CDN yüklemesi başarısız oldu (Catbox 500)")
        self.assertEqual(tani_cdn["kod"], "CDN_UPLOAD_FAIL")
        self.assertIn("CDN", tani_cdn["ne_oldu"])

        # 2. Token Hatası
        tani_token = hata_bildir.tani("OAuthException: Error validating access token: Session has expired")
        self.assertEqual(tani_token["kod"], "META_TOKEN_EXPIRED")
        self.assertIn("API jetonunun", tani_token["ne_oldu"])

        # 3. Rate Limit
        tani_rate = hata_bildir.tani("GraphMethodException: (#17) User request limit reached")
        self.assertEqual(tani_rate["kod"], "META_RATE_LIMIT")

        # 4. Gemini Kota
        tani_gemini = hata_bildir.tani("ResourceExhausted: 429 Resource has been exhausted (quota)")
        self.assertEqual(tani_gemini["kod"], "GEMINI_QUOTA_EXCEEDED")

        # 5. FFmpeg / Video Render
        tani_ffmpeg = hata_bildir.tani("ffmpeg returned non-zero exit status 1")
        self.assertEqual(tani_ffmpeg["kod"], "RENDER_FFMPEG_FAIL")

        # 6. SQLite Kilit
        tani_sqlite = hata_bildir.tani("sqlite3.OperationalError: database is locked")
        self.assertEqual(tani_sqlite["kod"], "SQLITE_LOCKED")

        # 7. Bilinmeyen Hata (Fallback)
        tani_genel = hata_bildir.tani("Bir şeyler ters gitti beklenmedik durum")
        self.assertEqual(tani_genel["kod"], "GENERIC_ERROR")

    def test_hata_bildir_mesaji_kur_ve_kaydet(self):
        """Teşhis mesajının eksiksiz formatlandığını ve dosyalara kaydedildiğini doğrular."""
        ham_hata = "Test CDN Timeout error: uguu.se timed out"
        
        with patch.object(telegram_bot, "mesaj_gonder", return_value=123):
            kayit_id = hata_bildir.bildir(
                baslik="CDN Test Başlığı",
                hata=ham_hata,
                nerede="test_fonksiyonu",
                paylasim_id=999,
            )
            self.assertTrue(kayit_id)

        # Mesaj içeriği
        tani = hata_bildir.tani(ham_hata)
        mesaj = hata_bildir.mesaji_kur("CDN Test Başlığı", tani, nerede="test_fonksiyonu", paylasim_id=999)
        self.assertIn("NE OLDU?", mesaj)
        self.assertIn("NEDEN?", mesaj)
        self.assertIn("ÇÖZÜM / NE YAPILMALI?", mesaj)
        self.assertIn("HAM HATA İZİ", mesaj)

        # Son hata dosyası kontrolü
        son_hata_yolu = Path(__file__).resolve().parent.parent / "data" / "son_hata.txt"
        self.assertTrue(son_hata_yolu.exists())
        with open(son_hata_yolu, "r", encoding="utf-8") as f:
            icerik = f.read()
            self.assertIn("test_fonksiyonu", icerik)

    def test_telafi_butonlari_kur(self):
        """Kısmi hata durumlarında ilgili telafi butonlarının dinamik oluşturulduğunu doğrular."""
        # Senaryo: Instagram ve Threads başarısız oldu, Facebook başarılı oldu
        sonuclar = {
            "instagram": None,
            "instagram_hata": "CDN yüklenemedi",
            "instagram_story": None,
            "instagram_story_hata": "CDN yüklenemedi",
            "threads": None,
            "threads_hata": "Metin hatası",
            "facebook": "fb_123456",
        }

        butonlar = telegram_bot.telafi_butonlari_kur(
            paylasim_id=42,
            sonuclar=sonuclar,
            format_tipi="gorsel_4_5",
        )

        # Buton yapısı: inline keyboard matrix (list of lists)
        tum_callbackler = [b["callback_data"] for row in butonlar for b in row if "callback_data" in b]

        # Başarısızları toplu tekrar dene butonu
        self.assertIn("telafi_hepsi_42", tum_callbackler)
        # Tekil kanal butonları (sadece başarısız olanlar için)
        self.assertIn("telafi_ig_42", tum_callbackler)
        self.assertIn("telafi_story_42", tum_callbackler)
        self.assertIn("telafi_threads_42", tum_callbackler)
        # Başarılı olan Facebook için tekrar dene butonu OLMAMALI
        self.assertNotIn("telafi_facebook_42", tum_callbackler)
        # Teşhis ve Yayından kaldır butonları
        self.assertIn("teshis_42", tum_callbackler)
        self.assertIn("kaldir_42", tum_callbackler)

    def test_yayin_raporu_metni_kur(self):
        """Yayın raporu metninin başarılı ve başarısız kanalları net gösterdiğini doğrular."""
        kayit = {
            "id": 55,
            "kategori": "kelime",
            "baslik": "Bereket",
            "kaynak": "A'râf Sûresi • 96. Âyet",
        }
        sonuclar = {
            "facebook": "122106109269462192",
            "instagram_hata": "CDN yüklenemedi",
            "threads_hata": "Görsel indirilemedi",
        }
        rapor = telegram_bot.yayin_raporu_metni_kur(kayit, sonuclar)
        self.assertIn("KISMİ BAŞARI / DİKKAT", rapor)
        self.assertIn("Facebook Sayfası:", rapor)
        self.assertIn("Instagram Reels/Feed:", rapor)
        self.assertIn("Threads (@ezanplusapp):", rapor)
        self.assertIn("Bereket", rapor)

    def test_yayinla_telafi_zaten_basarili_kanali_atlar(self):
        """Daha önce başarıyla yayınlanan platformun atlandığını (mükerrer paylaşım engeli) doğrular."""
        # Sahte bir görsel dosyası yolu belirle
        gorsel_yolu = str(Path(__file__).resolve().parent / "test_gorsel.png")

        # DB'ye sahte bir paylaşım ekleyelim
        pid = db.paylasim_ekle(
            kategori="kelime",
            format_tipi="gorsel_4_5",
            turkce_metin="Bereket kavramı",
            baslik="Bereket",
            kaynak="A'râf Sûresi • 96. Âyet",
            durum="onaylandi",
            gorsel_yollari=[gorsel_yolu, gorsel_yolu],
        )
        try:
            # Facebook önceden başarılı olmuş gibi işaretle
            db.paylasim_guncelle(pid, facebook_post_id="fb_already_exists_123")

            # mock yayinla alt fonksiyonları
            with patch.object(meta, "instagram_gorsel_paylas", return_value={"id": "ig_new_999"}) as mock_ig, \
                 patch.object(meta, "instagram_story_paylas", return_value={"id": "story_new_999"}) as mock_story, \
                 patch.object(meta, "facebook_post_paylas") as mock_fb, \
                 patch.object(threads, "threads_zincir_paylas", return_value={"id": "th_new_999"}) as mock_th:

                sonuclar = yonetici.yayinla_telafi(pid, hedef_kanal="hepsi")

                # Facebook zaten var olduğu için çağrılmamalı
                mock_fb.assert_not_called()
                # Instagram eksik olduğu için çağrılmış olmalı
                self.assertIn("instagram", sonuclar)
                self.assertEqual(sonuclar["instagram"], "ig_new_999")

                # DB'de facebook id'si korunmuş olmalı
                guncel_kayit = db.paylasim_getir(pid)
                self.assertEqual(guncel_kayit["facebook_post_id"], "fb_already_exists_123")
                self.assertEqual(guncel_kayit["instagram_post_id"], "ig_new_999")
        finally:
            with db.baglanti_al() as con:
                con.execute("DELETE FROM paylasimlar WHERE id = ?", (pid,))

    @patch("src.platformlar.meta.requests.post")
    def test_gecici_medya_yukle_uguu_onceligi(self, mock_post):
        """gecici_medya_yukle fonksiyonunun R2 harici veya fallback durumunda uguu.se'yi denediğini doğrular."""
        # Sahte bir PNG oluştur
        test_file = Path(__file__).resolve().parent / "test_gorsel_temp.png"
        test_file.write_bytes(b"\x89PNG\r\n\x1a\nfakecontent")

        try:
            # Uguu.se yanıtını simüle et
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "files": [{"url": "https://h.uguu.se/testfile.png"}]
            }
            mock_post.return_value = mock_response

            # r2 hariç tutulduğunda doğrudan Uguu'ya düşmeli
            url = meta.gecici_medya_yukle(test_file, haric_cdnler={"r2"})
            self.assertEqual(url, "https://h.uguu.se/testfile.png")
            # requests.post ilk çağrıda uguu.se adresine istek göndermeli
            ilk_istek_url = mock_post.call_args[0][0]
            self.assertIn("uguu.se", ilk_istek_url)
        finally:
            if test_file.exists():
                test_file.unlink()

    @patch("src.platformlar.r2.requests.put")
    def test_gecici_medya_yukle_r2_onceligi(self, mock_put):
        """gecici_medya_yukle fonksiyonunun 1. öncelik olarak Cloudflare R2'yi denediğini doğrular."""
        test_file = Path(__file__).resolve().parent / "test_gorsel_temp_r2.png"
        test_file.write_bytes(b"\x89PNG\r\n\x1a\nfakecontent")

        try:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_put.return_value = mock_resp

            url = meta.gecici_medya_yukle(test_file)
            self.assertIn("media.ezanplus.ozbornstudio.com/sosyal/", url)
            self.assertTrue(mock_put.called)

        finally:
            if test_file.exists():
                test_file.unlink()



if __name__ == "__main__":
    unittest.main()
