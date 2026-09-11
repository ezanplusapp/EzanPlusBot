"""
youtube.py — Ezan Plus YouTube Shorts Yükleme Modülü
Google YouTube Data API v3 kullanarak onaylanan dikey Reels videolarını
otomatik olarak YouTube Shorts formatında kanala yükler.
"""

from __future__ import annotations

import logging
import os
import sys
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
    
    Daily Brief Ders 108: Google Cloud Console 'Testing' modunda iken refresh token 7 günde
    bir iptal edilir. Kalıcı çözüm konsolda 'In production / Publish App' yapmaktır.
    Headless CI ortamlarında (GitHub Actions) tarayıcı açılamayacağı için güvenle hata fırlatılır.
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
        yenilendi = False
        if creds and creds.expired and creds.refresh_token:
            log.info("YouTube erişim belirteci yenileniyor...")
            try:
                creds.refresh(Request())
                yenilendi = True
            except Exception as e:
                log.critical(
                    f"⚠️ YouTube erişim belirteci yenilenemedi ({e})! "
                    "Kök Sebep (Daily Brief #108): Google Cloud Console OAuth consent screen "
                    "'Testing' modunda ise Google refresh token'ı 7 günde bir iptal eder. "
                    "Kalıcı çözüm için OAuth ekranını 'In production' (Publish App) yapın."
                )
                creds = None

        if not yenilendi:
            # Headless CI ortamında (GitHub Actions, cron vb.) tarayıcı açılamaz
            if not sys.stdin.isatty():
                raise RuntimeError(
                    "YouTube kimlik doğrulaması süresi dolmuş ve terminal etkileşimli değil (Headless CI)! "
                    "Lütfen yerel ortamda 'python -m src.platformlar.youtube' çalıştırarak yetkiyi yenileyin "
                    "ve oluşan data/youtube_token.json içeriğini GitHub Secrets (YOUTUBE_TOKEN_JSON) içine aktarın."
                )

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
            creds = flow.run_local_server(port=0, prompt="consent")

        # Yeni token'ı kaydet
        if creds:
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
        from googleapiclient.discovery import build
        creds = yetki_al()
        if not creds:
            log.error("YouTube yetkilendirmesi başarısız, video silinemedi.")
            return False
        servis = build("youtube", "v3", credentials=creds)
        servis.videos().delete(id=video_id).execute()
        log.info(f"✅ YouTube videosu başarıyla silindi: {video_id}")
        return True
    except Exception as e:
        log.error(f"YouTube video silme hatası ({video_id}): {e}")
        return False


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    print("\n" + "="*60)
    print("🎥 EZAN PLUS - YOUTUBE KALICI OAUTH YETKİLENDİRMESİ")
    print("="*60)

    # Eski süresi dolmuş token varsa kaldıralım ki temiz consent açılsın
    if TOKEN_DOSYASI.exists():
        try:
            c = Credentials.from_authorized_user_file(str(TOKEN_DOSYASI), SCOPES)
            c.refresh(Request())
            print("✅ Mevcut token yenilendi ve geçerli!")
            creds = c
        except Exception as e:
            print(f"⚠️ Eski token geçersiz ({e}), tarayıcı açılarak sıfırdan yetki alınacak...")
            TOKEN_DOSYASI.unlink(missing_ok=True)
            creds = None
    else:
        creds = None

    if not creds:
        if not CLIENT_SECRET_DOSYASI.exists():
            print(f"❌ '{CLIENT_SECRET_DOSYASI}' dosyası bulunamadı!")
            sys.exit(1)

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CLIENT_SECRET_DOSYASI), SCOPES
        )
        print("🌐 Varsayılan tarayıcınızda Google oturum açma sayfası açılıyor...")
        creds = flow.run_local_server(port=0, prompt="consent")
        TOKEN_DOSYASI.parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_DOSYASI, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
        print(f"🎉 Yetki başarıyla alındı ve kaydedildi: {TOKEN_DOSYASI}")

    if creds and creds.valid:
        print("\n✅ YouTube bağlantısı %100 BAŞARILI ve KALICI olarak hazır!")
        print("="*60 + "\n")

