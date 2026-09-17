"""
r2.py — Ezan Plus Cloudflare R2 Medya Barındırma Motoru
AWS SigV4 protokolünü harici kütüphane (boto3) olmadan, saf Python standart modülleri
(hmac, hashlib, datetime, mimetypes) ve requests ile çalıştırır.

Görsel ve videoları Cloudflare R2 bucket'ına yükler ve özel alan adı üzerinden
doğrudan herkese açık HTTPS URL sağlar.
"""

from __future__ import annotations

import datetime
import hashlib
import hmac
import logging
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests

from ..ayar import get_env

log = logging.getLogger(__name__)


def _r2_bilgileri() -> Optional[Tuple[str, str, str, str, str]]:
    """
    R2 kimlik bilgilerini sırasıyla:
    1. .env / os.environ ortam değişkenlerinden
    2. SQLite veritabanındaki 'ayarlar' tablosundan okur.

    Döner: (account_id, access_key, secret_key, bucket, domain) veya eksikse None
    """
    acc_id = get_env("R2_ACCOUNT_ID", "").strip()
    key_id = get_env("R2_ACCESS_KEY_ID", "").strip()
    sec_key = get_env("R2_SECRET_ACCESS_KEY", "").strip()
    bucket = get_env("R2_BUCKET_NAME", "ezanplus-media").strip()
    domain = get_env("R2_PUBLIC_DOMAIN", "media.ezanplus.ozbornstudio.com").strip().rstrip("/")

    # Ortam değişkenlerinde eksik varsa SQLite ayarlar tablosuna bak
    if not (acc_id and key_id and sec_key):
        try:
            from ..db import ayar_getir
            acc_id = acc_id or ayar_getir("r2_account_id")
            key_id = key_id or ayar_getir("r2_access_key_id")
            sec_key = sec_key or ayar_getir("r2_secret_access_key")
            bucket = bucket or ayar_getir("r2_bucket_name", "ezanplus-media")
            domain = (domain or ayar_getir("r2_public_domain", "media.ezanplus.ozbornstudio.com")).rstrip("/")
        except Exception as e:
            log.debug(f"Veritabanından R2 ayarları okunamadı: {e}")


    if acc_id and key_id and sec_key and bucket:
        return acc_id, key_id, sec_key, bucket, domain
    return None


def r2_hazir_mi() -> bool:
    """R2 kimlik bilgilerinin eksiksiz tanımlı olup olmadığını döner."""
    return _r2_bilgileri() is not None


def _sigv4_imza_hesapla(
    sec_key: str,
    date_stamp: str,
    region: str,
    service: str,
    string_to_sign: str,
) -> str:
    """AWS SigV4 için türetilmiş anahtarla HMAC-SHA256 imzası hesaplar."""
    def sign(key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    k_date = sign(("AWS4" + sec_key).encode("utf-8"), date_stamp)
    k_region = sign(k_date, region)
    k_service = sign(k_region, service)
    k_signing = sign(k_service, "aws4_request")

    return hmac.new(k_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()


def r2ye_yukle(
    yol: Path | str,
    alt_klasor: str = "sosyal",
    zaman_asimi: int = 45,
) -> Dict[str, Any]:
    """
    Belirtilen görsel veya video dosyasını Cloudflare R2 bucket'ına yükler.

    Parametreler:
        yol: Yüklenecek yerel dosya yolu (Path veya str)
        alt_klasor: Bucket içerisindeki ön ek (örn: 'sosyal' veya 'video')
        zaman_asimi: İstek zaman aşımı süresi (saniye)

    Döner:
        dict: {"url": str, "object_key": str, "silme_url": None, "boyut_kb": float}
    """
    bilgi = _r2_bilgileri()
    if not bilgi:
        raise RuntimeError("R2 ortam değişkenleri tanımlı değil! (.env veya DB ayarlarını kontrol edin)")

    acc_id, key_id, sec_key, bucket, domain = bilgi
    p = Path(yol)
    if not p.exists():
        raise FileNotFoundError(f"Yüklenecek dosya bulunamadı: {p}")

    ham = p.read_bytes()

    # Prefix & çakışma önleyici isimlendirme (7 günlük lifecycle kuralına uygun)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    guvenli_ad = f"{ts}_{p.name}"
    object_key = f"{alt_klasor.strip('/')}/{guvenli_ad}" if alt_klasor else guvenli_ad

    content_type = mimetypes.guess_type(p.name)[0]
    if not content_type:
        if p.suffix.lower() == ".mp4":
            content_type = "video/mp4"
        elif p.suffix.lower() == ".png":
            content_type = "image/png"
        elif p.suffix.lower() in [".jpg", ".jpeg"]:
            content_type = "image/jpeg"
        else:
            content_type = "application/octet-stream"

    # AWS SigV4 Parametreleri
    now = datetime.datetime.now(datetime.timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    region = "auto"
    service = "s3"
    host = f"{acc_id}.r2.cloudflarestorage.com"
    endpoint = f"https://{host}"

    payload_hash = hashlib.sha256(ham).hexdigest()

    canonical_uri = f"/{bucket}/{object_key}"
    canonical_querystring = ""
    canonical_headers = f"host:{host}\nx-amz-content-sha256:{payload_hash}\nx-amz-date:{amz_date}\n"
    signed_headers = "host;x-amz-content-sha256;x-amz-date"

    canonical_request = f"PUT\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = f"{algorithm}\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"

    signature = _sigv4_imza_hesapla(sec_key, date_stamp, region, service, string_to_sign)
    auth_header = f"{algorithm} Credential={key_id}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"

    headers = {
        "host": host,
        "x-amz-date": amz_date,
        "x-amz-content-sha256": payload_hash,
        "Authorization": auth_header,
        "Content-Type": content_type,
    }

    url = f"{endpoint}/{bucket}/{object_key}"
    cevap = requests.put(url, data=ham, headers=headers, timeout=zaman_asimi)

    if cevap.status_code not in (200, 204):
        raise RuntimeError(f"R2 HTTP {cevap.status_code} hatası: {cevap.text[:150]}")

    public_url = f"https://{domain}/{object_key}"
    boyut_kb = round(len(ham) / 1024, 1)
    log.info(f"Medya Cloudflare R2'ye başarıyla yüklendi ({boyut_kb} KB): {public_url}")

    return {
        "url": public_url,
        "object_key": object_key,
        "silme_url": None,
        "boyut_kb": boyut_kb,
    }


def r2den_sil(object_key: str, zaman_asimi: int = 30) -> bool:
    """
    Belirtilen object_key'i Cloudflare R2 bucket'ından S3 SigV4 DELETE ile siler.
    """
    bilgi = _r2_bilgileri()
    if not bilgi:
        return False

    acc_id, key_id, sec_key, bucket, _ = bilgi

    now = datetime.datetime.now(datetime.timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    region = "auto"
    service = "s3"
    host = f"{acc_id}.r2.cloudflarestorage.com"
    endpoint = f"https://{host}"

    payload_hash = hashlib.sha256(b"").hexdigest()

    canonical_uri = f"/{bucket}/{object_key.lstrip('/')}"
    canonical_querystring = ""
    canonical_headers = f"host:{host}\nx-amz-content-sha256:{payload_hash}\nx-amz-date:{amz_date}\n"
    signed_headers = "host;x-amz-content-sha256;x-amz-date"

    canonical_request = f"DELETE\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = f"{algorithm}\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"

    signature = _sigv4_imza_hesapla(sec_key, date_stamp, region, service, string_to_sign)
    auth_header = f"{algorithm} Credential={key_id}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"

    headers = {
        "host": host,
        "x-amz-date": amz_date,
        "x-amz-content-sha256": payload_hash,
        "Authorization": auth_header,
    }

    url = f"{endpoint}/{bucket}/{object_key.lstrip('/')}"
    try:
        cevap = requests.delete(url, headers=headers, timeout=zaman_asimi)
        if cevap.status_code in (200, 204):
            log.info(f"R2 nesnesi başarıyla silindi: {object_key}")
            return True
        log.warning(f"R2 nesne silme HTTP {cevap.status_code}: {cevap.text[:100]}")
    except Exception as e:
        log.warning(f"R2 silme hatası ({object_key}): {e}")

    return False
