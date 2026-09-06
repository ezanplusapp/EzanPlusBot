"""
threads.py — Ezan Plus Meta Threads Paylaşım Yöneticisi
Threads API (graph.threads.net) kullanarak metin, görsel ve video
paylaşımlarını gerçekleştirir.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional
import requests

from ..ayar import get_env
from .meta import gecici_gorsel_yukle

log = logging.getLogger(__name__)

THREADS_API_URL = "https://graph.threads.net/v1.0"


def get_threads_bilgileri() -> tuple[str, str]:
    """Threads User ID ve Access Token'ı .env'den alır."""
    user_id = get_env("THREADS_USER_ID")
    token = get_env("THREADS_ACCESS_TOKEN")
    if not user_id or not token:
        raise ValueError("THREADS_USER_ID veya THREADS_ACCESS_TOKEN .env içinde tanımlı değil!")
    return user_id, token


def code_ile_token_al(auth_code: str, redirect_uri: str = "https://ozbornstudio.com/") -> tuple[str, str]:
    """
    Kullanıcının tarayıcıdan aldığı OAuth auth_code'u 60 günlük kalıcı token'a çevirir
    ve Threads User ID ile birlikte döner.
    """
    app_id = get_env("THREADS_APP_ID")
    app_secret = get_env("THREADS_APP_SECRET")

    # 1. Adım: Kısa ömürlü token al
    res = requests.post(
        "https://graph.threads.net/oauth/access_token",
        data={
            "client_id": app_id,
            "client_secret": app_secret,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code": auth_code.split("#_")[0].strip(),
        },
        timeout=30
    )
    data = res.json()
    if "access_token" not in data:
        raise RuntimeError(f"Kısa ömürlü Threads token hatası: {data}")

    short_token = data["access_token"]
    user_id = str(data.get("user_id", ""))

    # 2. Adım: 60 Günlük Long-Lived Token'a çevir
    res_long = requests.get(
        "https://graph.threads.net/access_token",
        params={
            "grant_type": "th_exchange_token",
            "client_secret": app_secret,
            "access_token": short_token,
        },
        timeout=30
    )
    long_data = res_long.json()
    if "access_token" not in long_data:
        raise RuntimeError(f"Uzun ömürlü Threads token hatası: {long_data}")

    long_token = long_data["access_token"]
    return user_id, long_token


def _threads_metin_kirp(metin: str, limit: int = 500) -> str:
    """Threads 500 karakter sınırına göre metni güvenle kırpar."""
    if not metin or len(metin) <= limit:
        return metin
    return metin[:limit - 3].rstrip() + "..."


def metni_parcala(metin: str, max_karakter: int = 460) -> list[str]:
    """
    Uzun metinleri Threads'in 500 karakter sınırına uygun şekilde
    paragraf ve cümle bütünlüğünü bozmadan mantıklı parçalara böler.
    """
    import re
    paragraflar = [p.strip() for p in metin.split("\n\n") if p.strip()]
    parcalar = []
    mevcut_parca = ""

    for p in paragraflar:
        if len(p) > max_karakter:
            cumleler = re.split(r"(?<=[.!?])\s+", p)
            for c in cumleler:
                c = c.strip()
                if not c:
                    continue
                if len(mevcut_parca) + len(c) + 2 <= max_karakter:
                    mevcut_parca = f"{mevcut_parca}\n\n{c}" if mevcut_parca else c
                else:
                    if mevcut_parca:
                        parcalar.append(mevcut_parca)
                    mevcut_parca = c
        else:
            if len(mevcut_parca) + len(p) + 2 <= max_karakter:
                mevcut_parca = f"{mevcut_parca}\n\n{p}" if mevcut_parca else p
            else:
                if mevcut_parca:
                    parcalar.append(mevcut_parca)
                mevcut_parca = p

    if mevcut_parca:
        parcalar.append(mevcut_parca)

    return parcalar


def threads_zincir_paylas(
    metin: str,
    gorsel_url_veya_yolu: Optional[str | Path] = None,
    video_url_veya_yolu: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """
    Uzun metinleri parçalayarak Threads üzerinde zincir (thread) olarak paylaşır.
    İlk gönderiyi (video veya görsel ile) oluşturur, devamını sırayla bir önceki mesaja yanıt olarak ekler.
    """
    user_id, token = get_threads_bilgileri()
    parcalar = metni_parcala(metin)
    if not parcalar:
        raise ValueError("Paylaşılacak metin boş!")

    log.info(f"Threads zincir paylaşımı başlatılıyor ({len(parcalar)} parça)...")

    # 1. İlk gönderi (Root Post: Video veya Görsel + Metin)
    ilk_metin = parcalar[0]
    if len(parcalar) > 1:
        ilk_metin = f"{ilk_metin}\n\n🧵 (1/{len(parcalar)})"

    if video_url_veya_yolu:
        ilk_res = threads_video_paylas(video_url_veya_yolu, ilk_metin)
    elif gorsel_url_veya_yolu:
        ilk_res = threads_gorsel_paylas(gorsel_url_veya_yolu, ilk_metin)
    else:
        ilk_res = threads_metin_paylas(ilk_metin)

    root_id = ilk_res["id"]
    onceki_id = root_id
    reply_ids = []

    # 2. Takip eden yanıtlar (Zincir)
    for index, parca in enumerate(parcalar[1:], start=2):
        time.sleep(2)  # Rate limit koruması
        parca_metni = f"{parca}\n\n({index}/{len(parcalar)})"
        log.info(f"Threads zincir {index}/{len(parcalar)} yanıtı gönderiliyor...")

        # Yanıt container oluştur
        c_res = requests.post(
            f"{THREADS_API_URL}/{user_id}/threads",
            data={
                "media_type": "TEXT",
                "text": parca_metni,
                "reply_to_id": onceki_id,
                "access_token": token,
            },
            timeout=30,
        )
        c_data = c_res.json()
        if "id" not in c_data:
            log.error(f"Threads zincir yanıt container hatası ({index}): {c_data}")
            break

        # Yanıt yayınla
        p_res = requests.post(
            f"{THREADS_API_URL}/{user_id}/threads_publish",
            data={
                "creation_id": c_data["id"],
                "access_token": token,
            },
            timeout=30,
        )
        p_data = p_res.json()
        if "id" not in p_data:
            log.error(f"Threads zincir yanıt yayınlama hatası ({index}): {p_data}")
            break

        yeni_id = p_data["id"]
        reply_ids.append(yeni_id)
        onceki_id = yeni_id

    log.info(f"Threads zincir paylaşımı tamamlandı! Root: {root_id}, Yanıtlar: {len(reply_ids)}")
    return {"id": root_id, "reply_ids": reply_ids, "toplam_parca": len(parcalar)}


def threads_metin_paylas(metin: str) -> Dict[str, Any]:
    """Threads üzerinde sadece metin postu paylaşır."""
    user_id, token = get_threads_bilgileri()
    kirpilmis_metin = _threads_metin_kirp(metin)

    # 1. Container oluştur
    res = requests.post(
        f"{THREADS_API_URL}/{user_id}/threads",
        data={
            "media_type": "TEXT",
            "text": kirpilmis_metin,
            "access_token": token
        },
        timeout=30
    )
    c_data = res.json()
    if "id" not in c_data:
        raise RuntimeError(f"Threads Text Container hatası: {c_data}")

    container_id = c_data["id"]

    # 2. Yayınla
    pub_res = requests.post(
        f"{THREADS_API_URL}/{user_id}/threads_publish",
        data={
            "creation_id": container_id,
            "access_token": token
        },
        timeout=30
    )
    p_data = pub_res.json()
    if "id" not in p_data:
        raise RuntimeError(f"Threads Yayınlama hatası: {p_data}")

    log.info(f"Threads metin postu yayınlandı! ID: {p_data['id']}")
    return p_data


def threads_gorsel_paylas(gorsel_url_veya_yolu: str | Path, metin: str) -> Dict[str, Any]:
    """Threads üzerinde görselli gönderi paylaşır."""
    user_id, token = get_threads_bilgileri()

    if str(gorsel_url_veya_yolu).startswith("http://") or str(gorsel_url_veya_yolu).startswith("https://"):
        image_url = str(gorsel_url_veya_yolu)
    else:
        image_url = gecici_gorsel_yukle(gorsel_url_veya_yolu)

    # 1. Container oluştur
    res = requests.post(
        f"{THREADS_API_URL}/{user_id}/threads",
        data={
            "media_type": "IMAGE",
            "image_url": image_url,
            "text": _threads_metin_kirp(metin),
            "access_token": token
        },
        timeout=30
    )
    c_data = res.json()
    if "id" not in c_data:
        raise RuntimeError(f"Threads Image Container hatası: {c_data}")

    container_id = c_data["id"]

    # Durum kontrolü (Görsel işlenene kadar bekle)
    for _ in range(10):
        time.sleep(2)
        s_res = requests.get(
            f"{THREADS_API_URL}/{container_id}",
            params={"fields": "status,error_message", "access_token": token},
            timeout=15
        )
        s_data = s_res.json()
        if s_data.get("status") == "FINISHED":
            break
        elif s_data.get("status") == "ERROR":
            raise RuntimeError(f"Threads görsel işleme hatası: {s_data}")

    # 2. Yayınla
    pub_res = requests.post(
        f"{THREADS_API_URL}/{user_id}/threads_publish",
        data={
            "creation_id": container_id,
            "access_token": token
        },
        timeout=30
    )
    p_data = pub_res.json()
    if "id" not in p_data:
        raise RuntimeError(f"Threads Yayınlama hatası: {p_data}")

    log.info(f"Threads görselli gönderi yayınlandı! ID: {p_data['id']}")
    return p_data


def threads_video_paylas(video_url_veya_yolu: str | Path, metin: str) -> Dict[str, Any]:
    """Threads üzerinde video gönderisi paylaşır."""
    user_id, token = get_threads_bilgileri()

    if str(video_url_veya_yolu).startswith("http://") or str(video_url_veya_yolu).startswith("https://"):
        video_url = str(video_url_veya_yolu)
    else:
        video_url = gecici_gorsel_yukle(video_url_veya_yolu)

    # 1. Container oluştur
    res = requests.post(
        f"{THREADS_API_URL}/{user_id}/threads",
        data={
            "media_type": "VIDEO",
            "video_url": video_url,
            "text": _threads_metin_kirp(metin),
            "access_token": token,
        },
        timeout=30,
    )
    c_data = res.json()
    if "id" not in c_data:
        raise RuntimeError(f"Threads Video Container hatası: {c_data}")

    container_id = c_data["id"]

    # Durum kontrolü (Video işlenene kadar bekle)
    for _ in range(25):
        time.sleep(3)
        s_res = requests.get(
            f"{THREADS_API_URL}/{container_id}",
            params={"fields": "status,error_message", "access_token": token},
            timeout=15,
        )
        s_data = s_res.json()
        if s_data.get("status") == "FINISHED":
            break
        elif s_data.get("status") == "ERROR":
            raise RuntimeError(f"Threads video işleme hatası: {s_data}")

    # 2. Yayınla
    pub_res = requests.post(
        f"{THREADS_API_URL}/{user_id}/threads_publish",
        data={
            "creation_id": container_id,
            "access_token": token,
        },
        timeout=30,
    )
    p_data = pub_res.json()
    if "id" not in p_data:
        raise RuntimeError(f"Threads Video Yayınlama hatası: {p_data}")

    log.info(f"Threads video gönderisi yayınlandı! ID: {p_data['id']}")
    return p_data


def gonderiyi_sil(media_id: str) -> bool:
    """
    Threads üzerinden yayınlanmış bir gönderiyi siler.
    Threads API: DELETE /{threads_media_id}
    """
    if not media_id:
        return False
    try:
        _, token = get_threads_bilgileri()
        res = requests.delete(
            f"{THREADS_API_URL}/{media_id}",
            params={"access_token": token},
            timeout=30,
        )
        data = res.json()
        if data.get("success") is True or res.status_code == 200:
            log.info(f"Threads gönderisi başarıyla silindi: {media_id}")
            return True
    except Exception as e:
        log.warning(f"Threads silme hatası ({media_id}): {e}")
    return False

