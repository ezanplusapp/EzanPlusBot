"""
tests/test_turkce_tts.py — ElevenLabs & Fish Audio TTS Entegrasyon ve Fallback Testleri
"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import json
import base64

from src.uretim import ses as ses_getir


class TestTurkceTTS(unittest.TestCase):

    def test_elevenlabs_chars_to_words_donusumu(self):
        characters = list("İki nimet vardır.")
        starts = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6]
        ends =   [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7]

        words = ses_getir._elevenlabs_chars_to_words(characters, starts, ends)
        self.assertEqual(len(words), 3)
        self.assertEqual(words[0]["text"], "İki")
        self.assertEqual(words[0]["start"], 0.0)
        self.assertEqual(words[0]["end"], 0.3)

        self.assertEqual(words[1]["text"], "nimet")
        self.assertEqual(words[1]["start"], 0.4)
        self.assertEqual(words[1]["end"], 0.9)

        self.assertEqual(words[2]["text"], "vardır.")
        self.assertEqual(words[2]["start"], 1.0)
        self.assertEqual(words[2]["end"], 1.7)

    @patch("src.uretim.ses.get_env")
    @patch("requests.post")
    def test_elevenlabs_birincil_motor_basarili(self, mock_post, mock_get_env):
        mock_get_env.side_effect = lambda k, v="": {
            "ELEVENLABS_API_KEY": "fake_el_key",
            "ELEVENLABS_VOICE_ID": "J17lijyP1BHYcM7ld0Rg",
            "FISH_AUDIO_API_KEY": "fake_fish_key",
            "FISH_AUDIO_VOICE_ID": "a6d624c6b8de45d2b89eb0da9a691872"
        }.get(k, v)

        dummy_audio = b"FAKE_MP3_CONTENT" * 100
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "audio_base64": base64.b64encode(dummy_audio).decode("utf-8"),
            "alignment": {
                "characters": list("Selam"),
                "character_start_times_seconds": [0.0, 0.1, 0.2, 0.3, 0.4],
                "character_end_times_seconds": [0.1, 0.2, 0.3, 0.4, 0.5]
            }
        }
        mock_post.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            cikti = Path(tmp_dir) / "test_ses.mp3"
            yol = ses_getir.turkce_tts_uret(
                metin="Selam",
                cikti_yolu=cikti,
                overwrite=True
            )

            self.assertTrue(yol.exists())
            self.assertEqual(yol.read_bytes(), dummy_audio)

            # JSON zaman damgası kontrolü
            json_p = yol.with_suffix(".json")
            self.assertTrue(json_p.exists())
            zamanlar = json.loads(json_p.read_text(encoding="utf-8"))
            self.assertEqual(len(zamanlar), 1)
            self.assertEqual(zamanlar[0]["text"], "Selam")

    @patch("src.uretim.ses.get_env")
    @patch("requests.post")
    def test_elevenlabs_hata_verirse_fish_audio_fallback_calisir(self, mock_post, mock_get_env):
        mock_get_env.side_effect = lambda k, v="": {
            "ELEVENLABS_API_KEY": "fake_el_key",
            "ELEVENLABS_VOICE_ID": "J17lijyP1BHYcM7ld0Rg",
            "FISH_AUDIO_API_KEY": "fake_fish_key",
            "FISH_AUDIO_VOICE_ID": "a6d624c6b8de45d2b89eb0da9a691872"
        }.get(k, v)

        # 1. Çağrı (ElevenLabs) hata döner (402 Quota Exceeded)
        el_resp = MagicMock()
        el_resp.status_code = 402
        el_resp.text = "Quota exceeded"

        # 2. Çağrı (Fish Audio standart) başarılı döner
        fish_dummy_audio = b"FISH_AUDIO_MP3_CONTENT" * 100
        fish_resp = MagicMock()
        fish_resp.status_code = 200
        fish_resp.content = fish_dummy_audio

        mock_post.side_effect = [el_resp, fish_resp]

        with tempfile.TemporaryDirectory() as tmp_dir:
            cikti = Path(tmp_dir) / "test_fallback.mp3"
            yol = ses_getir.turkce_tts_uret(
                metin="Sabrediniz",
                cikti_yolu=cikti,
                zaman_damgasi_al=False,
                overwrite=True
            )

            self.assertTrue(yol.exists())
            self.assertEqual(yol.read_bytes(), fish_dummy_audio)

    def test_kalici_disk_onbellegi(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cikti = Path(tmp_dir) / "test_cache.mp3"
            cikti.write_bytes(b"EXISTING_VALID_MP3_CONTENT" * 100)

            # API çağrısı yapılmadan doğrudan diskten dönmeli
            with patch("requests.post") as mock_post:
                yol = ses_getir.turkce_tts_uret(
                    metin="Herhangi bir metin",
                    cikti_yolu=cikti,
                    overwrite=False
                )
                mock_post.assert_not_called()
                self.assertEqual(yol, cikti)


if __name__ == "__main__":
    unittest.main()
