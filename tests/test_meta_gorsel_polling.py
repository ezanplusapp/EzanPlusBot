import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.platformlar import meta


class TestMetaGorselPolling(unittest.TestCase):
    """
    Meta Graph API'de statik görsel (Feed 4:5 ve Story 9:16) container'larının
    hazır olma (polling) mekanizmasını ve CDN fallback senaryolarını test eder.
    """

    def setUp(self):
        self.test_img = Path("tests/test_gorsel.png")
        if not self.test_img.exists():
            self.test_img.write_bytes(b"dummy image data")

    @patch("src.platformlar.meta.get_meta_bilgileri", return_value=("17841400", "page_123", "token_abc"))
    @patch("src.platformlar.meta.gecici_gorsel_yukle", return_value="https://d.uguu.se/test.png")
    @patch("requests.post")
    @patch("requests.get")
    def test_gorsel_paylas_status_code_none_hemen_yayinlar(self, mock_get, mock_post, mock_cdn, mock_meta_info):
        """
        Meta statik resimlerde status_code döndürmediğinde (None)
        container'ın hazır kabul edilip ilk denemede başarıyla yayınlandığını doğrular.
        """
        # Container oluşturma (POST /media) -> id: cont_123
        # Yayınlama (POST /media_publish) -> id: pub_456
        res_container = MagicMock(status_code=200)
        res_container.json.return_value = {"id": "cont_123"}

        res_publish = MagicMock(status_code=200)
        res_publish.json.return_value = {"id": "pub_456"}

        mock_post.side_effect = [res_container, res_publish]

        # Polling (GET /cont_123) -> Meta resimlerde status_code alanı döndürmez: {"id": "cont_123"}
        res_poll = MagicMock(status_code=200)
        res_poll.json.return_value = {"id": "cont_123"}
        mock_get.return_value = res_poll

        sonuc = meta.instagram_gorsel_paylas(self.test_img, "Test Açıklama #ezanplus")

        self.assertEqual(sonuc.get("id"), "pub_456")
        # İlk poll'da hemen hazır kabul edilmeli (mock_get sadece 1 kez çağrılmalı, 15 kez beklenmemeli)
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(mock_post.call_count, 2)

    @patch("src.platformlar.meta.get_meta_bilgileri", return_value=("17841400", "page_123", "token_abc"))
    @patch("src.platformlar.meta.gecici_gorsel_yukle", return_value="https://d.uguu.se/test.png")
    @patch("requests.post")
    @patch("requests.get")
    def test_gorsel_paylas_status_code_finished_yayinlar(self, mock_get, mock_post, mock_cdn, mock_meta_info):
        """
        Meta status_code: FINISHED döndürdüğünde container'ın hazır kabul edilip yayınlandığını doğrular.
        """
        res_container = MagicMock(status_code=200)
        res_container.json.return_value = {"id": "cont_123"}

        res_publish = MagicMock(status_code=200)
        res_publish.json.return_value = {"id": "pub_456"}

        mock_post.side_effect = [res_container, res_publish]

        res_poll = MagicMock(status_code=200)
        res_poll.json.return_value = {"id": "cont_123", "status_code": "FINISHED"}
        mock_get.return_value = res_poll

        sonuc = meta.instagram_gorsel_paylas(self.test_img, "Test Açıklama #ezanplus")

        self.assertEqual(sonuc.get("id"), "pub_456")
        self.assertEqual(mock_get.call_count, 1)

    @patch("src.platformlar.meta.get_meta_bilgileri", return_value=("17841400", "page_123", "token_abc"))
    @patch("src.platformlar.meta.gecici_gorsel_yukle", return_value="https://d.uguu.se/test.png")
    @patch("requests.post")
    @patch("requests.get")
    def test_story_gorsel_paylas_status_code_none_yayinlar(self, mock_get, mock_post, mock_cdn, mock_meta_info):
        """
        Story görseli için status_code: None döndüğünde başarıyla yayınlandığını doğrular.
        """
        res_container = MagicMock(status_code=200)
        res_container.json.return_value = {"id": "story_cont_789"}

        res_publish = MagicMock(status_code=200)
        res_publish.json.return_value = {"id": "story_pub_999"}

        mock_post.side_effect = [res_container, res_publish]

        res_poll = MagicMock(status_code=200)
        res_poll.json.return_value = {"id": "story_cont_789"}
        mock_get.return_value = res_poll

        sonuc = meta.instagram_story_paylas(self.test_img, is_video=False)

        self.assertEqual(sonuc.get("id"), "story_pub_999")
        self.assertEqual(mock_get.call_count, 1)


if __name__ == "__main__":
    unittest.main()
