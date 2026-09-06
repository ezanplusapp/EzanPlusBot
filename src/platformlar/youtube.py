"""
youtube.py — Ezan Plus YouTube Shorts Yükleme Modülü
Google YouTube Data API v3 kullanarak onaylanan dikey Reels videolarını
otomatik olarak YouTube Shorts formatında kanala yükler.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from ..ayar import KOK_DIZIN

log = logging.getLogger(__name__)

# YouTube Video Yükleme İzni
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

CLIENT_SECRET_DOSYASI = KOK_DIZIN / "client_secret.json"
TOKEN_DOSYASI = KOK_DIZIN / "data" / "youtube_token.json"


def yetki_al() -> Optional[Credentials]:
    """
    Kullanıcının YouTube hesabına erişim için OAuth 2.0 kimlik doğrulamasını sağlar.
    token.json varsa oradan okur, süresi bittiyse yeniler.
    İlk kurulumda tarayıcı açarak kullanıcıdan izin ister.
    """
    creds = None

    # 1. Mevcut kayıtlı token kontrolü
    if TOKEN_DOSYASI.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_DOSYASI), SCOPES)
        except Exception as e:
            log.warning(f"Kayıtlı YouTube token dosyası okunamadı: {e}")
            creds = None

    # 2. Token geçersizse veya yoksa
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            log.info("YouTube erişim belirteci yenileniyor...")
            creds.refresh(Request())
        else:
            if not CLIENT_SECRET_DOSYASI.exists():
                log.error(
                    f"'{CLIENT_SECRET_DOSYASI}' bulunamadı! "
                    "Lütfen Google Cloud Console'dan indirdiğiniz OAuth JSON dosyasını "
                    "proje kök dizinine 'client_secret.json' adıyla koyun."
                )
                return None

            log.info("YouTube yetkilendirmesi için tarayıcı açılıyor...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRET_DOSYASI), SCOPES
            )
            # Yerel sunucu başlatıp tarayıcıda izin ekranını aç
            creds = flow.run_local_server(port=0, prompt="consent")

        # Yeni token'ı kaydet
        TOKEN_DOSYASI.parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_DOSYASI, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())
        log.info(f"YouTube yetki belirteci başarıyla kaydedildi: {TOKEN_DOSYASI}")

    return creds


def youtube_shorts_yukle(
    video_yolu: str | Path,
    baslik: str,
    aciklama: str,
    etiketler: Optional[List[str]] = None,
    gizlilik: str = "public",
) -> Dict[str, Any]:
    """
    Verilen dikey 9:16 videoyu YouTube Shorts olarak yükler.
    
    Parametreler:
        video_yolu: Yüklenecek .mp4 dosyasının yolu.
        baslik: Video başlığı (Shorts için başlığa veya açıklamaya #Shorts eklenir).
        aciklama: Video açıklaması (Caption + hashtagler).
        etiketler: Video etiketleri listesi.
        gizlilik: 'public', 'unlisted' veya 'private' (Varsayılan: 'public').
    """
    video_path = Path(video_yolu)
    if not video_path.exists():
        raise FileNotFoundError(f"Yüklenecek video bulunamadı: {video_path}")

    creds = yetki_al()
    if not creds:
        raise RuntimeError("YouTube kimlik doğrulaması yapılamadı. client_secret.json dosyasını kontrol edin.")

    youtube = build("youtube", "v3", credentials=creds)

    # Shorts algoritması kuralı: Başlık veya açıklamada #Shorts yer almalıdır
    if "#Shorts" not in baslik and "#shorts" not in baslik:
        # YouTube başlık sınırı 100 karakterdir
        if len(baslik) > 90:
            baslik = baslik[:89] + "…"
        baslik_fmt = f"{baslik} #Shorts"
    else:
        baslik_fmt = baslik[:100]

    varsayilan_etiketler = ["ezanplus", "kuran", "ayet", "tefekkur", "Shorts", "islam"]
    if etiketler:
        for tag in etiketler:
            t = tag.replace("#", "").strip()
            if t and t not in varsayilan_etiketler:
                varsayilan_etiketler.append(t)

    govde = {
        "snippet": {
            "title": baslik_fmt,
            "description": aciklama,
            "tags": varsayilan_etiketler[:15],
            "categoryId": "22",  # People & Blogs / İnsanlar ve Bloglar
            "defaultLanguage": "tr",
            "defaultAudioLanguage": "ar",
        },
        "status": {
            "privacyStatus": gizlilik,
            "selfDeclaredMadeForKids": False,
        },
    }

    log.info(f"YouTube Shorts yüklemesi başlatılıyor: '{baslik_fmt}'...")
    media = MediaFileUpload(
        str(video_path),
        chunksize=-1,
        resumable=True,
        mimetype="video/mp4",
    )

    istek = youtube.videos().insert(
        part="snippet,status",
        body=govde,
        media_body=media,
    )

    cevap = istek.execute()
    video_id = cevap.get("id")
    shorts_url = f"https://youtube.com/shorts/{video_id}"

    log.info(f"✅ YouTube Shorts başarıyla yüklendi! ID: {video_id} -> {shorts_url}")
    return {
        "video_id": video_id,
        "url": shorts_url,
        "raw": cevap,
    }


def videoyu_sil(video_id: str) -> bool:
    """
    YouTube Data API v3 üzerinden yüklenmiş bir videoyu / Shorts'u siler.
    """
    if not video_id:
        return False
    try:
        servis = yetkilendir()
        servis.videos().delete(id=video_id).execute()
        log.info(f"✅ YouTube videosu başarıyla silindi: {video_id}")
        return True
    except Exception as e:
        log.error(f"YouTube video silme hatası ({video_id}): {e}")
        return False

