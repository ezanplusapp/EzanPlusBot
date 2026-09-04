"""
instagram.py — Ezan Plus Instagram & Facebook Paylaşım Yöneticisi
Meta Graph API (v22.0) kullanarak tekil görsel, çoklu görsel (Carousel),
dikey Reels videosu ve Facebook Sayfası paylaşımlarını gerçekleştirir.
"""

from __future__ import annotations

import base64
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

from .ayar import get_env

log = logging.getLogger(__name__)

GRAPH_API_URL = "https://graph.facebook.com/v22.0"
RUPLOAD_URL = "https://rupload.facebook.com/ig-reels-upload/v22.0"


def get_meta_bilgileri() -> tuple[str, str, str]:
    """
    .env içerisinden Instagram Account ID, Page ID ve Access Token'ı çeker.
    """
    ig_id = get_env("INSTAGRAM_ACCOUNT_ID")
    page_id = get_env("FACEBOOK_PAGE_ID")
    token = get_env("INSTAGRAM_ACCESS_TOKEN")

    if not ig_id or not token:
        raise ValueError("INSTAGRAM_ACCOUNT_ID veya INSTAGRAM_ACCESS_TOKEN .env içinde tanımlı değil!")

    return ig_id, page_id, token


def gecici_gorsel_yukle(dosya_yolu: str | Path) -> str:
    """
    Yerel görsel dosyasını Meta'nın erişebileceği geçici/kalıcı bir genel URL'ye yükler.
    Önce .env'deki IMGBB_API_KEY kontrol edilir, yoksa tmpfiles.org kullanılır.
    """
    p = Path(dosya_yolu)
    if not p.exists():
        raise FileNotFoundError(f"Görsel bulunamadı: {dosya_yolu}")

    imgbb_key = get_env("IMGBB_API_KEY")
    if imgbb_key:
        try:
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            res = requests.post(
                "https://api.imgbb.com/1/upload",
                data={"key": imgbb_key, "image": b64},
                timeout=30
            )
            data = res.json()
            if data.get("success"):
                return data["data"]["url"]
        except Exception as e:
            log.warning(f"ImgBB yüklemesi başarısız oldu, tmpfiles deneniyor: {e}")

    # Alternatif: tmpfiles.org üzerinden direkt indirme URL'si
    with open(p, "rb") as f:
        res = requests.post(
            "https://tmpfiles.org/api/v1/upload",
            files={"file": f},
            timeout=30
        )
    data = res.json()
    if data.get("status") == "success":
        url = data["data"]["url"]
        # tmpfiles.org/123/resim.png -> tmpfiles.org/dl/123/resim.png
        direct_url = url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
        return direct_url

    raise RuntimeError(f"Görsel genel URL'ye yüklenemedi: {data}")


def instagram_gorsel_paylas(gorsel_url_veya_yolu: str | Path, aciklama: str) -> Dict[str, Any]:
    """
    Instagram'da tekil görsel paylaşır.
    Yerel dosya yolu verilirse önce genel URL'ye yükler, ardından Meta Container açıp yayınlar.
    """
    ig_id, _, token = get_meta_bilgileri()

    # Dosya yolu mu yoksa doğrudan URL mi?
    if str(gorsel_url_veya_yolu).startswith("http://") or str(gorsel_url_veya_yolu).startswith("https://"):
        image_url = str(gorsel_url_veya_yolu)
    else:
        log.info("Görsel genel URL'ye aktarılıyor...")
        image_url = gecici_gorsel_yukle(gorsel_url_veya_yolu)

    # 1. Adım: Media Container Oluştur
    log.info("Instagram Media Container oluşturuluyor...")
    container_res = requests.post(
        f"{GRAPH_API_URL}/{ig_id}/media",
        data={
            "image_url": image_url,
            "caption": aciklama,
            "access_token": token
        },
        timeout=30
    )
    c_data = container_res.json()
    if "id" not in c_data:
        raise RuntimeError(f"Instagram Container hatası: {c_data}")

    container_id = c_data["id"]

    # 2. Adım: Yayınla
    log.info(f"Container {container_id} yayınlanıyor...")
    publish_res = requests.post(
        f"{GRAPH_API_URL}/{ig_id}/media_publish",
        data={
            "creation_id": container_id,
            "access_token": token
        },
        timeout=30
    )
    p_data = publish_res.json()
    if "id" not in p_data:
        raise RuntimeError(f"Instagram Yayınlama hatası: {p_data}")

    log.info(f"Instagram gönderisi başarıyla yayınlandı! ID: {p_data['id']}")
    return p_data


def instagram_reels_paylas(video_dosya_yolu: str | Path, aciklama: str) -> Dict[str, Any]:
    """
    Instagram'da 9:16 dikey Reels videosu paylaşır.
    Meta Resumable Upload protokolü ile doğrudan Mac'ten Meta sunucularına yüklenir.
    """
    ig_id, _, token = get_meta_bilgileri()
    v_path = Path(video_dosya_yolu)
    if not v_path.exists():
        raise FileNotFoundError(f"Video dosyası bulunamadı: {video_dosya_yolu}")

    dosya_boyutu = v_path.stat().st_size

    # 1. Adım: Resumable Reels Container Başlat
    log.info("Instagram Reels Resumable Container başlatılıyor...")
    init_res = requests.post(
        f"{GRAPH_API_URL}/{ig_id}/media",
        data={
            "media_type": "REELS",
            "upload_type": "resumable",
            "caption": aciklama,
            "share_to_feed": "true",
            "access_token": token
        },
        timeout=30
    )
    init_data = init_res.json()
    if "id" not in init_data:
        raise RuntimeError(f"Reels başlatma hatası: {init_data}")

    container_id = init_data["id"]
    upload_url = init_data.get("uri", f"{RUPLOAD_URL}/{container_id}")

    # 2. Adım: Video Baytlarını Yükle
    log.info(f"Reels videosu yükleniyor ({dosya_boyutu / (1024*1024):.2f} MB)...")
    with open(v_path, "rb") as f:
        video_bytes = f.read()

    headers = {
        "Authorization": f"OAuth {token}",
        "offset": "0",
        "file_size": str(dosya_boyutu),
        "Content-Type": "application/octet-stream"
    }
    upload_res = requests.post(upload_url, headers=headers, data=video_bytes, timeout=120)
    log.info(f"Video yükleme yanıtı: {upload_res.status_code}")

    # 3. Adım: Video İşleme Durumunu Bekle (Polling)
    log.info("Videonun Meta tarafında işlenmesi bekleniyor...")
    for _ in range(30):  # Maksimum 2.5 dakika bekle
        time.sleep(5)
        status_res = requests.get(
            f"{GRAPH_API_URL}/{container_id}",
            params={"fields": "status_code,status", "access_token": token},
            timeout=15
        )
        s_data = status_res.json()
        status_code = s_data.get("status_code")
        log.info(f"İşlenme durumu: {status_code} ({s_data.get('status')})")

        if status_code == "FINISHED":
            break
        elif status_code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Video işleme hatası: {s_data}")
    else:
        raise TimeoutError("Reels videosu işleme zaman aşımına uğradı!")

    # 4. Adım: Reels Yayınla
    log.info(f"Reels {container_id} yayınlanıyor...")
    publish_res = requests.post(
        f"{GRAPH_API_URL}/{ig_id}/media_publish",
        data={
            "creation_id": container_id,
            "access_token": token
        },
        timeout=30
    )
    p_data = publish_res.json()
    if "id" not in p_data:
        raise RuntimeError(f"Reels Yayınlama hatası: {p_data}")

    log.info(f"Reels başarıyla yayınlandı! Medya ID: {p_data['id']}")
    return p_data


def facebook_post_paylas(metin: str, gorsel_yolu: Optional[str | Path] = None) -> Dict[str, Any]:
    """
    Facebook 'Ezan Plus App' Sayfasına metin veya görsel paylaşır.
    """
    _, page_id, token = get_meta_bilgileri()
    if not page_id:
        raise ValueError("FACEBOOK_PAGE_ID bulunamadı!")

    if gorsel_yolu and Path(gorsel_yolu).exists():
        log.info("Facebook sayfasına fotoğraflı post atılıyor...")
        with open(gorsel_yolu, "rb") as f:
            res = requests.post(
                f"{GRAPH_API_URL}/{page_id}/photos",
                data={"message": metin, "access_token": token},
                files={"source": f},
                timeout=45
            )
    else:
        log.info("Facebook sayfasına metin postu atılıyor...")
        res = requests.post(
            f"{GRAPH_API_URL}/{page_id}/feed",
            data={"message": metin, "access_token": token},
            timeout=30
        )

    data = res.json()
    if "id" not in data:
        raise RuntimeError(f"Facebook paylaşım hatası: {data}")

    log.info(f"Facebook gönderisi başarıyla yayınlandı! ID: {data['id']}")
    return data
