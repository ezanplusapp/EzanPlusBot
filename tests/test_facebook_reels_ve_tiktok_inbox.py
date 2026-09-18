import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import src.platformlar.meta as meta
import src.platformlar.tiktok as tiktok

class TestFacebookReelsAndTikTokInbox(unittest.TestCase):
    @patch("src.platformlar.meta.requests.post")
    @patch("src.platformlar.meta.get_meta_bilgileri")
    @patch("src.platformlar.meta.get_env")
    def test_facebook_reels_paylas(self, mock_env, mock_meta_info, mock_post):
        mock_meta_info.return_value = ("ig_id", "page_123", "token_123")
        mock_env.return_value = "token_page_123"

        # Mock start response
        res_start = MagicMock()
        res_start.status_code = 200
        res_start.json.return_value = {"video_id": "vid_999", "upload_url": "https://rupload.facebook.com/test"}

        # Mock binary upload response
        res_upload = MagicMock()
        res_upload.status_code = 200

        # Mock finish response
        res_finish = MagicMock()
        res_finish.status_code = 200
        res_finish.json.return_value = {"success": True}

        mock_post.side_effect = [res_start, res_upload, res_finish]

        test_file = Path("tests/test_gorsel.png") # existing file
        res = meta.facebook_reels_paylas(test_file, caption="Test Reels Açıklaması")

        self.assertEqual(res["video_id"], "vid_999")
        self.assertTrue(res["success"])
        self.assertEqual(mock_post.call_count, 3)

        # Check finish call description
        finish_call = mock_post.call_args_list[2]
        self.assertEqual(finish_call[1]["data"]["description"], "Test Reels Açıklaması")
        self.assertEqual(finish_call[1]["data"]["video_state"], "PUBLISHED")
        self.assertEqual(finish_call[1]["data"]["upload_phase"], "finish")

    @patch("src.platformlar.tiktok.requests.post")
    @patch("src.platformlar.tiktok.requests.put")
    @patch("src.platformlar.tiktok.yetki_al")
    def test_tiktok_inbox_mode(self, mock_auth, mock_put, mock_post):
        mock_auth.return_value = {"access_token": "tt_tok_123"}

        res_init = MagicMock()
        res_init.status_code = 200
        res_init.json.return_value = {
            "error": {"code": "ok"},
            "data": {"publish_id": "pub_777", "upload_url": "https://upload.tiktok.com/test"}
        }

        res_put = MagicMock()
        res_put.status_code = 200
        mock_put.return_value = res_put

        res_status = MagicMock()
        res_status.status_code = 200
        res_status.json.return_value = {
            "data": {"status": "PUBLISH_COMPLETE"}
        }

        mock_post.side_effect = [res_init, res_status]

        test_file = Path("tests/test_gorsel.png")
        res = tiktok.tiktok_video_yukle(test_file, baslik="Test Başlık", taslak_modu=True)

        self.assertEqual(res["publish_id"], "pub_777")
        self.assertEqual(res["mod"], "inbox")
        # Ensure INBOX_INIT_URL was used
        init_call = mock_post.call_args_list[0]
        self.assertEqual(init_call[0][0], tiktok.INBOX_INIT_URL)

    @patch("src.platformlar.r2.r2ye_yukle")
    @patch("src.platformlar.tiktok.requests.post")
    @patch("src.platformlar.tiktok.yetki_al")
    def test_tiktok_foto_yukle(self, mock_auth, mock_post, mock_r2):
        mock_auth.return_value = {"access_token": "tt_tok_photo"}
        mock_r2.return_value = {"url": "https://r2.ezanplus.com/test.jpg"}

        res_init = MagicMock()
        res_init.status_code = 200
        res_init.json.return_value = {
            "error": {"code": "ok"},
            "data": {"publish_id": "pub_photo_888"}
        }

        res_status = MagicMock()
        res_status.status_code = 200
        res_status.json.return_value = {
            "data": {"status": "SEND_TO_USER_INBOX"}
        }

        mock_post.side_effect = [res_init, res_status]

        test_file = Path("tests/test_gorsel.png")
        res = tiktok.tiktok_foto_yukle([test_file], baslik="Test Fotoğraf Başlığı", aciklama="Açıklama #test", taslak_modu=True)

        self.assertEqual(res["publish_id"], "pub_photo_888")
        self.assertEqual(res["status"], "SEND_TO_USER_INBOX")
        self.assertEqual(res["mod"], "inbox")

        # Verify endpoint and payload
        init_call = mock_post.call_args_list[0]
        self.assertEqual(init_call[0][0], tiktok.PHOTO_INIT_URL)
        payload = init_call[1]["json"]
        self.assertEqual(payload["media_type"], "PHOTO")
        self.assertEqual(payload["post_mode"], "MEDIA_UPLOAD")
        self.assertEqual(payload["source_info"]["photo_images"], ["https://r2.ezanplus.com/test.jpg"])

if __name__ == "__main__":
    unittest.main()
