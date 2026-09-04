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

from .ayar import get_env
from .instagram import gecici_gorsel_yukle

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


def threads_metin_paylas(metin: str) -> Dict[str, Any]:
    """Threads üzerinde sadece metin postu paylaşır."""
    user_id, token = get_threads_bilgileri()

    # 1. Container oluştur
    res = requests.post(
        f"{THREADS_API_URL}/{user_id}/threads",
        data={
            "media_type": "TEXT",
            "text": metin,
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
            "text": metin,
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
