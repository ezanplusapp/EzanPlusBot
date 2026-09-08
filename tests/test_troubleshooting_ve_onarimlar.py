"""
tests/test_troubleshooting_ve_onarimlar.py — Hata Senaryoları & Otomatik Onarım Test Paketi
"""

import json
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.uretim import ai as icerik_uret
from src.platformlar import threads
from src.telegram import bot as telegram_bot
from src import hata_bildir


class TestTroubleshootingVeOnarimlar(unittest.TestCase):

    # -------------------------------------------------------------
    # Senaryo 1: Gemini AI JSON Sözdizimi Bozuklukları ve Otomatik Onarım
    # -------------------------------------------------------------
    def test_json_onar_virguller_ve_bloklar(self):
        """Sondaki gereksiz virgüllerin ve markdown bloklarının temizlendiğini doğrular."""
        bozuk_json = """```json
        {
            "arapca_okunus": "ve huve ala kulli seyin kadir",
            "latin_kelimeler": ["ve", "huve", "ala", "kulli", "seyin", "kadir", ],
            "tefekkur_notu": "Her seye gucu yeten Allah'a guven.",
        }
        ```"""
        ayiklanmis = icerik_uret._json_ayikla(bozuk_json)
        self.assertIsInstance(ayiklanmis, dict)
        self.assertEqual(len(ayiklanmis["latin_kelimeler"]), 6)
        self.assertEqual(ayiklanmis["latin_kelimeler"][-1], "kadir")

    def test_json_ayikla_kontrol_karakterleri(self):
        """String içindeki kaçışsız satır başlarının strict=False ile okunduğunu doğrular."""
        metin = '{\n"tefekkur_notu": "Birinci satir\nIkinci satir"\n}'
        veri = icerik_uret._json_ayikla(metin)
        self.assertIn("Birinci satir", veri["tefekkur_notu"])

    @patch("src.uretim.ai._gemini_cagir")
    def test_gemini_cagir_json_retry_basarisi(self, mock_cagir):
        """İlk çağrıda geçersiz JSON dönüp 2. çağrıda düzelen senaryoyu doğrular."""
        # 1. Çağrı bozuk JSON (virgül eksik / tırnak hatası)
        # 2. Çağrı düzeltilmiş temiz JSON
        mock_cagir.side_effect = [
            '{"tefekkur_notu": "bozuk tırnak "hatası", "caption": "test"}',
            '{"tefekkur_notu": "temiz metin", "caption": "test"}'
        ]

        veri = icerik_uret._gemini_cagir_json("test prompt", "test sistem")
        self.assertEqual(veri["tefekkur_notu"], "temiz metin")
        self.assertEqual(mock_cagir.call_count, 2)
        # 2. çağrıda düzeltme talimatı içerdiğini doğrula
        ikinci_cagri_prompt = mock_cagir.call_args_list[1][0][0]
        self.assertIn("KRİTİK DÜZELTME TALİMATI", ikinci_cagri_prompt)

    def test_hata_bildir_gemini_json_syntax(self):
        """Gemini JSON sözdizimi hatalarının katalogda tanındığını doğrular."""
        hata_metni = "Expecting ',' delimiter: line 23 column 320 (char 1289)"
        tani = hata_bildir.tani(hata_metni)
        self.assertEqual(tani["kod"], "GEMINI_JSON_SYNTAX_ERROR")
        self.assertEqual(tani["eylem"], "yeniden_uret")

    # -------------------------------------------------------------
    # Senaryo 2: Meta Threads Container Replikasyon Gecikmesi & Media Not Found
    # -------------------------------------------------------------
    @patch("time.sleep", return_value=None)
    @patch("src.platformlar.threads.requests.get")
    @patch("src.platformlar.threads.requests.post")
    def test_threads_container_readiness_polling(self, mock_post, mock_get, mock_sleep):
        """Container ilk yoklamada IN_PROGRESS iken 2. yoklamada FINISHED olduğunda yayınlandığını doğrular."""
        # Mock GET /container_id
        res_pending = MagicMock()
        res_pending.json.return_value = {"status": "IN_PROGRESS"}
        res_ready = MagicMock()
        res_ready.json.return_value = {"status": "FINISHED"}
        mock_get.side_effect = [res_pending, res_ready]

        # Mock POST /threads_publish
        res_pub = MagicMock()
        res_pub.json.return_value = {"id": "th_published_123"}
        mock_post.return_value = res_pub

        sonuc = threads._threads_container_yayinla("user1", "token1", "cont_999", maks_yoklama=5)
        self.assertEqual(sonuc["id"], "th_published_123")
        self.assertEqual(mock_get.call_count, 2)
        mock_post.assert_called_once()

    @patch("time.sleep", return_value=None)
    @patch("src.platformlar.threads.requests.get")
    @patch("src.platformlar.threads.requests.post")
    def test_threads_media_not_found_retry_basarisi(self, mock_post, mock_get, mock_sleep):
        """threads_publish ilk çağrıda Code 24 (Media Not Found) dönüp 2. çağrıda başarılı olduğunu doğrular."""
        # Mock GET -> doğrudan FINISHED
        res_ready = MagicMock()
        res_ready.json.return_value = {"status": "FINISHED"}
        mock_get.return_value = res_ready

        # Mock POST -> 1. çağrıda Code 24 Media Not Found, 2. çağrıda ID döner
        res_err = MagicMock()
        res_err.json.return_value = {
            "error": {
                "message": "The requested resource does not exist",
                "code": 24,
                "error_subcode": 4279009,
                "error_user_title": "Media Not Found",
            }
        }
        res_ok = MagicMock()
        res_ok.json.return_value = {"id": "th_success_456"}
        mock_post.side_effect = [res_err, res_ok]

        sonuc = threads._threads_container_yayinla("user1", "token1", "cont_999", maks_yoklama=2)
        self.assertEqual(sonuc["id"], "th_success_456")
        self.assertEqual(mock_post.call_count, 2)

    def test_hata_bildir_threads_media_not_found(self):
        """Threads Media Not Found hatasının katalogda tanındığını doğrular."""
        hata_metni = "The media with id 18107449003936152 cannot be found."
        tani = hata_bildir.tani(hata_metni)
        self.assertEqual(tani["kod"], "THREADS_MEDIA_NOT_FOUND")
        self.assertEqual(tani["eylem"], "tekrar_yayinla")

    # -------------------------------------------------------------
    # Senaryo 3: Telegram Message Not Modified Sessiz Karşılama
    # -------------------------------------------------------------
    @patch("src.telegram.bot.requests.post")
    @patch("src.telegram.bot.get_token_ve_chat_id", return_value=("fake_token", "fake_chat"))
    def test_telegram_message_not_modified_hata_firlatmaz(self, mock_env, mock_post):
        """Telegram editMessageCaption 'message is not modified' yanıtı verdiğinde hata fırlatmadığını doğrular."""
        mock_res = MagicMock()
        mock_res.json.return_value = {
            "ok": False,
            "description": "Bad Request: message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message"
        }
        mock_post.return_value = mock_res

        sonuc = telegram_bot._istek("editMessageCaption", data={"chat_id": 123, "message_id": 456})
        self.assertEqual(sonuc, {})


if __name__ == "__main__":
    unittest.main()
