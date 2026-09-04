"""
tiktok.py — Ezan Plus TikTok Direct Post Motoru
TikTok Content Posting API (v2) kullanarak 9:16 dikey Reels videolarını
doğrudan @ezanplusapp TikTok hesabına otomatik olarak yayınlar.
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

from ..ayar import KOK_DIZIN, get_env

log = logging.getLogger(__name__)

AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
INIT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"

SCOPES = "user.info.basic,video.upload,video.publish"
REDIRECT_URI = "https://ezanplus.ozbornstudio.com/callback"

TOKEN_DOSYASI = KOK_DIZIN / "data" / "tiktok_token.json"


def get_tiktok_api_anahtarlari() -> tuple[str, str]:
    """Client key ve secret'ı .env dosyasından alır."""
    key = get_env("TIKTOK_CLIENT_KEY")
    secret = get_env("TIKTOK_CLIENT_SECRET")
    if not key or not secret:
        raise ValueError(
            "TIKTOK_CLIENT_KEY veya TIKTOK_CLIENT_SECRET .env içinde tanımlı değil!"
        )
    return key, secret


def yetki_al(manuel_kod: Optional[str] = None) -> Dict[str, Any]:
    """
    TikTok OAuth 2.0 erişim belirtecini yönetir.
    Token dosyası varsa okur, gerekirse yeniler.
    Yoksa kullanıcıdan yetkilendirme alır.
    """
    key, secret = get_tiktok_api_anahtarlari()

    # 1. Kayıtlı token kontrolü
    if TOKEN_DOSYASI.exists():
        try:
            with open(TOKEN_DOSYASI, "r", encoding="utf-8") as f:
                token_data = json.load(f)
            
            # Token süresi dolmuşsa yenile
            if time.time() > token_data.get("expires_at", 0) - 300:
                log.info("TikTok token süresi dolmak üzere, yenileniyor...")
                ref_res = requests.post(
                    TOKEN_URL,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={
                        "client_key": key,
                        "client_secret": secret,
                        "grant_type": "refresh_token",
                        "refresh_token": token_data["refresh_token"],
                    },
                    timeout=30,
                )
                ref_json = ref_res.json()
                if "access_token" in ref_json:
                    token_data["access_token"] = ref_json["access_token"]
                    token_data["refresh_token"] = ref_json.get("refresh_token", token_data["refresh_token"])
                    token_data["expires_at"] = time.time() + ref_json.get("expires_in", 86400)
                    with open(TOKEN_DOSYASI, "w", encoding="utf-8") as f:
                        json.dump(token_data, f, indent=2)
                    return token_data
            else:
                return token_data
        except Exception as e:
            log.warning(f"TikTok token yenileme hatası: {e}, yeniden giriş yapılıyor...")

    # 2. Yeni giriş akışı
    params = {
        "client_key": key,
        "scope": SCOPES,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "state": "ezanplus_tiktok_auth",
    }
    giris_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    code = manuel_kod
    if not code:
        log.info(f"TikTok Giriş Bağlantısı:\n{giris_url}\n")
        import webbrowser
        webbrowser.open(giris_url)
        print("\n" + "=" * 60)
        print("🔗 TIKTOK YETKİLENDİRME ADIMI:")
        print(f"Tarayıcınız açılmadıysa şu adrese gidin:\n{giris_url}\n")
        print("Giriş yapıp izin verdikten sonra yönlendirildiğiniz sayfanın adres çubuğundaki")
        print("tüm URL'yi (veya 'code=' sonrasındaki metni) kopyalayıp buraya yapıştırın:")
        print("=" * 60)
        raw_input = input("Yönlendirme URL'si veya Kod: ").strip()
        if "code=" in raw_input:
            parsed = urllib.parse.urlparse(raw_input)
            qs = urllib.parse.parse_qs(parsed.query)
            code = qs.get("code", [raw_input])[0]
        else:
            code = raw_input

    # Kodu Access Token ile takas et
    token_res = requests.post(
        TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key": key,
            "client_secret": secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        },
        timeout=30,
    )
    res_data = token_res.json()
    if "access_token" not in res_data:
        raise RuntimeError(f"TikTok token alma hatası: {res_data}")

    res_data["expires_at"] = time.time() + res_data.get("expires_in", 86400)
    TOKEN_DOSYASI.parent.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(res_data, f, indent=2)

    log.info("✅ TikTok erişim belirteci başarıyla alındı ve kaydedildi!")
    return res_data


def tiktok_video_yukle(
    video_yolu: str | Path,
    baslik: str,
    aciklama: Optional[str] = None,
) -> Dict[str, Any]:
    """
    9:16 dikey videoyu TikTok'a doğrudan yükler ve yayınlar.
    """
    v_path = Path(video_yolu)
    if not v_path.exists():
        raise FileNotFoundError(f"Video bulunamadı: {video_yolu}")

    token_data = yetki_al()
    access_token = token_data["access_token"]
    dosya_boyutu = v_path.stat().st_size

    tam_metin = f"{baslik}\n\n{aciklama}" if aciklama else baslik
    # TikTok başlık limiti ~2200 karakterdir
    caption_fmt = tam_metin[:2000]

    # 1. Adım: Video Yükleme Başlat
    log.info(f"TikTok video yükleme başlatılıyor ({dosya_boyutu / (1024*1024):.2f} MB)...")
    init_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    init_body = {
        "post_info": {
            "title": caption_fmt,
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "disable_duet": False,
            "disable_stitch": False,
            "disable_comment": False,
            "video_cover_timestamp_ms": 1000,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": dosya_boyutu,
            "chunk_size": dosya_boyutu,
            "total_chunk_count": 1,
        },
    }

    init_res = requests.post(INIT_URL, headers=init_headers, json=init_body, timeout=30)
    init_data = init_res.json()
    if init_data.get("error", {}).get("code") != "ok":
        raise RuntimeError(f"TikTok init hatası: {init_data}")

    publish_id = init_data["data"]["publish_id"]
    upload_url = init_data["data"]["upload_url"]

    # 2. Adım: Video Baytlarını Yükle
    log.info("Video baytları TikTok sunucularına aktarılıyor...")
    with open(v_path, "rb") as f:
        video_bytes = f.read()

    put_headers = {
        "Content-Type": "video/mp4",
        "Content-Range": f"bytes 0-{dosya_boyutu - 1}/{dosya_boyutu}",
    }
    put_res = requests.put(upload_url, headers=put_headers, data=video_bytes, timeout=120)
    if put_res.status_code not in (200, 201):
        raise RuntimeError(f"TikTok binary yükleme hatası ({put_res.status_code}): {put_res.text}")

    # 3. Adım: Yayın Durumunu Takip Et
    log.info(f"TikTok video işleniyor (Publish ID: {publish_id})...")
    for _ in range(30):
        time.sleep(5)
        st_res = requests.post(
            STATUS_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            json={"publish_id": publish_id},
            timeout=15,
        )
        st_data = st_res.json()
        status = st_data.get("data", {}).get("status")
        log.info(f"TikTok işlenme durumu: {status}")

        if status == "PUBLISH_COMPLETE":
            log.info(f"🎉 TikTok videosu başarıyla yayınlandı! Publish ID: {publish_id}")
            return {"publish_id": publish_id, "status": status}
        elif status == "FAILED":
            raise RuntimeError(f"TikTok yayınlama başarısız oldu: {st_data}")

    return {"publish_id": publish_id, "status": "PROCESSING"}
