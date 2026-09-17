"""
test_r2_entegrasyonu.py — Cloudflare R2 S3 SigV4 ve Fallback Entegrasyon Testleri
"""

import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.platformlar import r2, meta
from src import db


class TestR2Entegrasyonu(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("tests")
        self.test_file = self.test_dir / "test_gorsel.png"

    def test_r2_bilgileri_env(self):
        """R2 bilgilerinin env üzerinden eksiksiz okunduğunu doğrular."""
        bilgi = r2._r2_bilgileri()
        self.assertIsNotNone(bilgi)
        acc_id, key_id, sec_key, bucket, domain = bilgi
        self.assertTrue(len(acc_id) > 5)
        self.assertTrue(len(key_id) > 5)
        self.assertTrue(len(sec_key) > 5)
        self.assertEqual(bucket, "ezanplus-media")
        self.assertEqual(domain, "media.ezanplus.ozbornstudio.com")

    def test_r2_bilgileri_db_fallback(self):
        """Env değişkenleri boşsa veritabanındaki ayarlar tablosundan okuduğunu doğrular."""
        with patch("src.platformlar.r2.get_env", return_value=""):
            with patch("src.db.ayar_getir") as mock_ayar:
                mock_ayar.side_effect = lambda k, default="": {
                    "r2_account_id": "db_acc_123",
                    "r2_access_key_id": "db_key_123",
                    "r2_secret_access_key": "db_sec_123",
                    "r2_bucket_name": "db-bucket",
                    "r2_public_domain": "media.test.com",
                }.get(k, default)

                bilgi = r2._r2_bilgileri()
                self.assertIsNotNone(bilgi)
                acc, key, sec, bkt, dom = bilgi
                self.assertEqual(acc, "db_acc_123")
                self.assertEqual(key, "db_key_123")
                self.assertEqual(sec, "db_sec_123")
                self.assertEqual(bkt, "db-bucket")
                self.assertEqual(dom, "media.test.com")


    @patch("src.platformlar.r2.requests.put")
    def test_r2ye_yukle_sigv4_headers(self, mock_put):
        """R2 SigV4 PUT isteğinin doğru başlıklarla ve formatla gönderildiğini doğrular."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_put.return_value = mock_resp

        sonuc = r2.r2ye_yukle(self.test_file, alt_klasor="sosyal")
        self.assertIn("url", sonuc)
        self.assertIn("media.ezanplus.ozbornstudio.com/sosyal/", sonuc["url"])

        self.assertTrue(mock_put.called)

        args, kwargs = mock_put.call_args
        headers = kwargs.get("headers", {})
        self.assertIn("Authorization", headers)
        self.assertTrue(headers["Authorization"].startswith("AWS4-HMAC-SHA256 Credential="))
        self.assertIn("x-amz-content-sha256", headers)
        self.assertIn("x-amz-date", headers)
        self.assertEqual(headers["Content-Type"], "image/png")

    @patch("src.platformlar.r2.requests.delete")
    def test_r2den_sil(self, mock_delete):
        """R2 S3 SigV4 DELETE isteğini doğrular."""
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_delete.return_value = mock_resp

        res = r2.r2den_sil("sosyal/test.png")
        self.assertTrue(res)
        self.assertTrue(mock_delete.called)

        args, kwargs = mock_delete.call_args
        headers = kwargs.get("headers", {})
        self.assertIn("Authorization", headers)
        self.assertTrue(headers["Authorization"].startswith("AWS4-HMAC-SHA256 Credential="))

    def test_cdn_adlandir_r2(self):
        """_cdn_adlandir fonksiyonunun R2 URL'lerini doğru sınıflandırdığını doğrular."""
        self.assertEqual(
            meta._cdn_adlandir("https://media.dailybrief.ozbornstudio.com/sosyal/123_test.png"),
            "r2",
        )
        self.assertEqual(
            meta._cdn_adlandir("https://10fbe7ac.r2.cloudflarestorage.com/bucket/123.mp4"),
            "r2",
        )
        self.assertEqual(meta._cdn_adlandir("https://uguu.se/test.png"), "uguu")
        self.assertEqual(meta._cdn_adlandir("https://litterbox.catbox.moe/test.png"), "litterbox")

    @patch("src.platformlar.r2.r2ye_yukle")
    @patch("src.platformlar.meta.requests.post")
    def test_gecici_medya_yukle_fallback_on_r2_error(self, mock_post, mock_r2):
        """R2 geçici bir hata verdiğinde sistemin sessizce Uguu'ya düştüğünü doğrular."""
        mock_r2.side_effect = RuntimeError("R2 Bağlantı zaman aşımı")

        mock_uguu_resp = MagicMock()
        mock_uguu_resp.status_code = 200
        mock_uguu_resp.json.return_value = {
            "files": [{"url": "https://uguu.se/fallback_test.png"}]
        }
        mock_post.return_value = mock_uguu_resp

        url = meta.gecici_medya_yukle(self.test_file)
        self.assertEqual(url, "https://uguu.se/fallback_test.png")


if __name__ == "__main__":
    unittest.main()
