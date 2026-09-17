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

from ..ayar import get_env

log = logging.getLogger(__name__)

GRAPH_API_URL = "https://graph.facebook.com/v22.0"
RUPLOAD_URL = "https://rupload.facebook.com/ig-reels-upload/v22.0"

# Daily Brief Ders 171 & 540: Meta'nın geçici CDN indirme zaman aşımı kodları
GECICI_MEDYA_HATA_KODLARI = {2207003, 2207052}


def _cdn_adlandir(url: str) -> str:
    """Verilen URL'den barındırıcı CDN servisini belirler."""
    u = str(url).lower()
    if "r2" in u or "cloudflarestorage" in u or "media.dailybrief" in u or "media.ezanplus" in u:
        return "r2"
    if "uguu" in u:
        return "uguu"
    if "litterbox" in u:
        return "litterbox"
    if "catbox" in u:
        return "catbox"
    if "ibb" in u or "imgbb" in u:
        return "imgbb"
    return "diger"



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


def gecici_medya_yukle(dosya_yolu: str | Path, haric_cdnler: Optional[set[str]] = None) -> str:
    """
    Yerel görsel veya video dosyasını Meta'nın doğrudan erişebileceği genel bir CDN URL'sine yükler.
    haric_cdnler listesindeki servisler atlanır; Uguu ➔ Catbox ➔ Litterbox ➔ ImgBB sırasıyla denenir.
    """
    p = Path(dosya_yolu)
    if not p.exists():
        raise FileNotFoundError(f"Medya bulunamadı: {dosya_yolu}")

    haric = haric_cdnler or set()

    import mimetypes
    mime = mimetypes.guess_type(str(p))[0] or ("video/mp4" if p.suffix.lower() == ".mp4" else "image/png")

    ua_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    cdn_hatalari: List[str] = []

    # 1. Öncelik: Cloudflare R2 (Özel Domain, S3 SigV4, Meta & Threads doğrudan erişim)
    if "r2" not in haric:
        try:
            from .r2 import r2_hazir_mi, r2ye_yukle
            if r2_hazir_mi():
                alt = "video" if p.suffix.lower() == ".mp4" else "sosyal"
                r2_res = r2ye_yukle(p, alt_klasor=alt, zaman_asimi=40)
                url = r2_res.get("url")
                if url and url.startswith("http"):
                    log.info(f"Medya Cloudflare R2 CDN'e başarıyla yüklendi: {url}")
                    return url
                cdn_hatalari.append(f"R2 boş link döndü: {r2_res}")
        except Exception as e:
            cdn_hatalari.append(f"R2: {e}")
            log.warning(f"Cloudflare R2 CDN yükleme hatası: {e}, sonraki yedek CDN deneniyor...")

    # 2. Öncelik: Uguu.se (Yedek CDN #1 - Yüksek hızlı, doğrudan dosya linki, Meta & Threads tam uyumlu)
    if "uguu" not in haric:
        try:
            with open(p, "rb") as f:
                res = requests.post(
                    "https://uguu.se/upload",
                    files={"files[]": (p.name, f, mime)},
                    headers=ua_headers,
                    timeout=30,
                )
            if res.status_code == 200:
                veri = res.json()
                url = (veri.get("files") or [{}])[0].get("url")
                if url and url.startswith("http"):
                    log.info(f"Medya Uguu CDN'e başarıyla yüklendi: {url}")
                    return url
                cdn_hatalari.append(f"Uguu boş link döndü: {res.text[:100]}")
            else:
                cdn_hatalari.append(f"Uguu HTTP {res.status_code}")
        except Exception as e:
            cdn_hatalari.append(f"Uguu: {e}")
            log.warning(f"Uguu CDN yükleme hatası: {e}, sonraki CDN deneniyor...")

    # 2. Öncelik: Catbox.moe (Doğrudan dosya CDN linki)
    if "catbox" not in haric:
        try:
            with open(p, "rb") as f:
                res = requests.post(
                    "https://catbox.moe/user/api.php",
                    data={"reqtype": "fileupload"},
                    files={"fileToUpload": (p.name, f, mime)},
                    headers=ua_headers,
                    timeout=45,
                )
            if res.status_code == 200 and res.text.strip().startswith("http"):
                url = res.text.strip()
                log.info(f"Medya Catbox'a başarıyla yüklendi: {url}")
                return url
            cdn_hatalari.append(f"Catbox HTTP {res.status_code}: {res.text[:80]}")
        except Exception as e:
            cdn_hatalari.append(f"Catbox: {e}")
            log.warning(f"Catbox yükleme hatası: {e}, sonraki CDN deneniyor...")

    # 3. Öncelik: Litterbox (Catbox 72 saatlik doğrudan CDN servisi)
    if "litterbox" not in haric:
        try:
            with open(p, "rb") as f:
                res = requests.post(
                    "https://litterbox.catbox.moe/resources/internals/api.php",
                    data={"reqtype": "fileupload", "time": "72h"},
                    files={"fileToUpload": (p.name, f, mime)},
                    headers=ua_headers,
                    timeout=45,
                )
            if res.status_code == 200 and res.text.strip().startswith("http"):
                url = res.text.strip()
                log.info(f"Medya Litterbox'a başarıyla yüklendi: {url}")
                return url
            cdn_hatalari.append(f"Litterbox HTTP {res.status_code}: {res.text[:80]}")
        except Exception as e:
            cdn_hatalari.append(f"Litterbox: {e}")
            log.warning(f"Litterbox yükleme hatası: {e}, sonraki CDN deneniyor...")

    # 4. Öncelik: ImgBB (Tanımlı ise görsel dosyaları için)
    if "imgbb" not in haric:
        imgbb_key = get_env("IMGBB_API_KEY")
        if imgbb_key and p.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
            for anahtar in [k.strip() for k in imgbb_key.split(",") if k.strip()]:
                try:
                    with open(p, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode("utf-8")
                    res = requests.post(
                        "https://api.imgbb.com/1/upload",
                        data={"key": anahtar, "image": b64},
                        headers=ua_headers,
                        timeout=30,
                    )
                    data = res.json()
                    if data.get("success"):
                        url = data["data"]["url"]
                        log.info(f"Medya ImgBB'ye yüklendi: {url}")
                        return url
                    cdn_hatalari.append(f"ImgBB hata: {data.get('error', {}).get('message', 'Bilinmiyor')}")
                except Exception as e:
                    cdn_hatalari.append(f"ImgBB: {e}")

    hata_ozeti = "; ".join(cdn_hatalari)
    raise RuntimeError(f"Medya hiçbir CDN servisine yüklenemedi! Ayrıntılar: {hata_ozeti}")


def gecici_gorsel_yukle(dosya_yolu: str | Path, haric_cdnler: Optional[set[str]] = None) -> str:
    """Geriye dönük uyumluluk için takma ad."""
    return gecici_medya_yukle(dosya_yolu, haric_cdnler=haric_cdnler)


def instagram_gorsel_paylas(gorsel_url_veya_yolu: str | Path, aciklama: str) -> Dict[str, Any]:
    """
    Instagram'da tekil görsel paylaşır.
    Yerel dosya yolu verilirse önce genel URL'ye yükler, ardından Meta Container açıp yayınlar.
    Daily Brief Ders 171 & 1aa: Meta CDN indirme hatası (2207003/2207052) durumunda alternatif CDN ile otomatik tekrar dener.
    """
    ig_id, _, token = get_meta_bilgileri()
    is_yerel_dosya = not (str(gorsel_url_veya_yolu).startswith("http://") or str(gorsel_url_veya_yolu).startswith("https://"))

    denenen_cdnler: set[str] = set()
    son_hata: Optional[Exception] = None

    maks_deneme = 3 if is_yerel_dosya else 1
    for deneme_no in range(1, maks_deneme + 1):
        if is_yerel_dosya:
            image_url = gecici_gorsel_yukle(gorsel_url_veya_yolu, haric_cdnler=denenen_cdnler)
            denenen_cdnler.add(_cdn_adlandir(image_url))
        else:
            image_url = str(gorsel_url_veya_yolu)

        try:
            # 1. Adım: Media Container Oluştur
            log.info(f"Instagram Media Container oluşturuluyor (Deneme {deneme_no}/{maks_deneme}, CDN: {_cdn_adlandir(image_url)})...")
            container_res = requests.post(
                f"{GRAPH_API_URL}/{ig_id}/media",
                data={
                    "image_url": image_url,
                    "caption": aciklama,
                    "access_token": token
                },
                timeout=60
            )
            c_data = container_res.json()
            if "id" not in c_data:
                err_dict = c_data.get("error", {})
                subcode = err_dict.get("error_subcode")
                code = err_dict.get("code")
                if (subcode in GECICI_MEDYA_HATA_KODLARI or code in GECICI_MEDYA_HATA_KODLARI) and is_yerel_dosya and deneme_no < maks_deneme:
                    log.warning(f"Meta geçici indirme hatası aldı ({err_dict}). Alternatif CDN ile tekrar deneniyor...")
                    time.sleep(3)
                    continue
                raise RuntimeError(f"Instagram Container hatası: {c_data}")

            container_id = c_data["id"]

            # Container hazır olana kadar bekle (azami 30 saniye)
            gecerli = False
            for poll_no in range(1, 16):
                time.sleep(2)
                try:
                    status_res = requests.get(
                        f"{GRAPH_API_URL}/{container_id}",
                        params={"fields": "status_code,status", "access_token": token},
                        timeout=15,
                    )
                    s_data = status_res.json()
                    status_code = s_data.get("status_code")
                    log.info(f"Container durum kontrolü ({poll_no}/15): status_code={status_code}, status={s_data.get('status')}")

                    if status_code == "FINISHED" or (status_code is None and status_res.status_code == 200 and "error" not in s_data):
                        gecerli = True
                        break
                    elif status_code in ("ERROR", "EXPIRED"):
                        s_sub = s_data.get("error_subcode") or s_data.get("error", {}).get("error_subcode")
                        if (s_sub in GECICI_MEDYA_HATA_KODLARI or "media" in str(s_data).lower()) and is_yerel_dosya and deneme_no < maks_deneme:
                            log.warning(f"Container işleme hatası ({s_data}). Alternatif CDN ile tekrar deneniyor...")
                            break
                        raise RuntimeError(f"Instagram görsel işleme hatası: {s_data}")
                except Exception as e_poll:
                    if "işleme hatası" in str(e_poll):
                        raise e_poll
                    break

            if not gecerli and is_yerel_dosya and deneme_no < maks_deneme:
                time.sleep(3)
                continue

            # 2. Adım: Yayınla
            log.info(f"Container {container_id} yayınlanıyor...")
            publish_res = requests.post(
                f"{GRAPH_API_URL}/{ig_id}/media_publish",
                data={
                    "creation_id": container_id,
                    "access_token": token
                },
                timeout=60
            )
            p_data = publish_res.json()
            if "id" not in p_data:
                raise RuntimeError(f"Instagram Yayınlama hatası: {p_data}")

            log.info(f"Instagram gönderisi başarıyla yayınlandı! ID: {p_data['id']}")
            return p_data

        except Exception as e:
            son_hata = e
            if is_yerel_dosya and deneme_no < maks_deneme:
                log.warning(f"Instagram paylaşım denemesi ({deneme_no}/{maks_deneme}) başarısız oldu ({e}). Alternatif CDN deneniyor...")
                time.sleep(3)
                continue
            raise son_hata


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
    page_token = get_env("FACEBOOK_PAGE_ACCESS_TOKEN") or token
    if not page_id:
        raise ValueError("FACEBOOK_PAGE_ID bulunamadı!")

    if gorsel_yolu and Path(gorsel_yolu).exists():
        log.info("Facebook sayfasına fotoğraflı post atılıyor...")
        with open(gorsel_yolu, "rb") as f:
            res = requests.post(
                f"{GRAPH_API_URL}/{page_id}/photos",
                data={"message": metin, "access_token": page_token},
                files={"source": f},
                timeout=45
            )
    else:
        log.info("Facebook sayfasına metin postu atılıyor...")
        res = requests.post(
            f"{GRAPH_API_URL}/{page_id}/feed",
            data={"message": metin, "access_token": page_token},
            timeout=30
        )

    data = res.json()
    if "id" not in data:
        raise RuntimeError(f"Facebook paylaşım hatası: {data}")

    log.info(f"Facebook gönderisi başarıyla yayınlandı! ID: {data['id']}")
    return data


def facebook_reels_paylas(
    video_yolu: str | Path,
    caption: str = "",
) -> Dict[str, Any]:
    """
    Facebook 'Ezan Plus App' Sayfasına 9:16 dikey videoyu Facebook Reels olarak yükler ve yayınlar.
    Açıklama metni (caption) doğrudan 'description' alanına aktarılır.
    """
    _, page_id, token = get_meta_bilgileri()
    page_token = get_env("FACEBOOK_PAGE_ACCESS_TOKEN") or token
    if not page_id:
        raise ValueError("FACEBOOK_PAGE_ID bulunamadı!")

    v_path = Path(video_yolu)
    if not v_path.exists():
        raise FileNotFoundError(f"Facebook Reels videosu bulunamadı: {video_yolu}")

    dosya_boyutu = v_path.stat().st_size
    log.info(f"Facebook Reels yükleme başlatılıyor ({dosya_boyutu / (1024*1024):.2f} MB)...")

    # 1. Adım: Reels Yükleme Başlat
    init_res = requests.post(
        f"{GRAPH_API_URL}/{page_id}/video_reels",
        data={
            "upload_phase": "start",
            "access_token": page_token,
        },
        timeout=30
    )
    init_data = init_res.json()
    if "video_id" not in init_data:
        raise RuntimeError(f"Facebook Reels başlatma hatası: {init_data}")

    video_id = init_data["video_id"]
    upload_url = init_data.get("upload_url")
    if not upload_url:
        raise RuntimeError(f"Facebook Reels upload_url alınamadı: {init_data}")

    # 2. Adım: Video Baytlarını Yükle
    log.info(f"Facebook Reels video baytları aktarılıyor (Video ID: {video_id})...")
    with open(v_path, "rb") as f:
        video_bytes = f.read()

    headers = {
        "Authorization": f"OAuth {page_token}",
        "offset": "0",
        "file_size": str(dosya_boyutu),
        "Content-Type": "application/octet-stream",
    }
    upload_res = requests.post(upload_url, headers=headers, data=video_bytes, timeout=120)
    log.info(f"Facebook video upload yanıtı: {upload_res.status_code}")
    if upload_res.status_code not in (200, 201):
        raise RuntimeError(f"Facebook Reels video yükleme başarısız ({upload_res.status_code}): {upload_res.text}")

    # 3. Adım: Reels Yayınla (Finish Phase)
    log.info(f"Facebook Reels yayınlanıyor (Video ID: {video_id})...")
    finish_res = requests.post(
        f"{GRAPH_API_URL}/{page_id}/video_reels",
        data={
            "upload_phase": "finish",
            "access_token": page_token,
            "video_id": video_id,
            "video_state": "PUBLISHED",
            "description": caption,
        },
        timeout=30
    )
    finish_data = finish_res.json()
    if not finish_data.get("success") and "id" not in finish_data and "video_id" not in finish_data:
        raise RuntimeError(f"Facebook Reels finish hatası: {finish_data}")

    log.info(f"Facebook Reels başarıyla yayınlandı! Video ID: {video_id}")
    return {"id": video_id, "video_id": video_id, "success": True, "raw": finish_data}


def instagram_story_paylas(
    medya_yolu_veya_url: str | Path,
    is_video: bool = False,
) -> Dict[str, Any]:
    """
    Instagram'da Story (Hikaye) paylaşır.
    is_video=True: 9:16 dikey video story olarak yayınlanır (Resumable upload).
    is_video=False: Görsel story olarak yayınlanır.
    """
    ig_id, _, token = get_meta_bilgileri()
    medya_p = Path(medya_yolu_veya_url)

    if is_video:
        if not medya_p.exists():
            raise FileNotFoundError(f"Story video dosyası bulunamadı: {medya_yolu_veya_url}")

        dosya_boyutu = medya_p.stat().st_size

        # 1. Adım: Resumable Story Container Başlat
        log.info("Instagram Story Video Container başlatılıyor...")
        init_res = requests.post(
            f"{GRAPH_API_URL}/{ig_id}/media",
            data={
                "media_type": "STORIES",
                "upload_type": "resumable",
                "access_token": token,
            },
            timeout=30,
        )
        init_data = init_res.json()
        if "id" not in init_data:
            raise RuntimeError(f"Story başlatma hatası: {init_data}")

        container_id = init_data["id"]
        upload_url = init_data.get("uri", f"{RUPLOAD_URL}/{container_id}")

        # 2. Adım: Video Baytlarını Yükle
        log.info(f"Story videosu yükleniyor ({dosya_boyutu / (1024*1024):.2f} MB)...")
        with open(medya_p, "rb") as f:
            video_bytes = f.read()

        headers = {
            "Authorization": f"OAuth {token}",
            "offset": "0",
            "file_size": str(dosya_boyutu),
            "Content-Type": "application/octet-stream",
        }
        upload_res = requests.post(upload_url, headers=headers, data=video_bytes, timeout=120)
        log.info(f"Story video yükleme HTTP yanıtı: {upload_res.status_code}")

        # 3. Adım: İşlenme Durumunu Bekle
        log.info("Story videosunun Meta tarafında işlenmesi bekleniyor...")
        for _ in range(30):
            time.sleep(5)
            status_res = requests.get(
                f"{GRAPH_API_URL}/{container_id}",
                params={"fields": "status_code,status", "access_token": token},
                timeout=15,
            )
            s_data = status_res.json()
            status_code = s_data.get("status_code")
            log.info(f"Story video işlenme durumu: {status_code}")
            if status_code == "FINISHED":
                break
            elif status_code in ("ERROR", "EXPIRED"):
                raise RuntimeError(f"Story video işleme hatası: {s_data}")
        else:
            raise TimeoutError("Story videosu işleme zaman aşımına uğradı!")

    else:
        # Görsel Story (Daily Brief Ders 171: CDN indirme hatasında alternatif CDN ile tekrar deneme)
        is_yerel = not (str(medya_yolu_veya_url).startswith("http://") or str(medya_yolu_veya_url).startswith("https://"))
        denenen_cdnler: set[str] = set()
        maks_deneme = 3 if is_yerel else 1
        container_id = None

        for deneme_no in range(1, maks_deneme + 1):
            if is_yerel:
                image_url = gecici_gorsel_yukle(medya_yolu_veya_url, haric_cdnler=denenen_cdnler)
                denenen_cdnler.add(_cdn_adlandir(image_url))
            else:
                image_url = str(medya_yolu_veya_url)

            try:
                log.info(f"Instagram Story Image Container oluşturuluyor (Deneme {deneme_no}/{maks_deneme}, CDN: {_cdn_adlandir(image_url)})...")
                c_res = requests.post(
                    f"{GRAPH_API_URL}/{ig_id}/media",
                    data={
                        "media_type": "STORIES",
                        "image_url": image_url,
                        "access_token": token,
                    },
                    timeout=60,
                )
                c_data = c_res.json()
                if "id" not in c_data:
                    err_dict = c_data.get("error", {})
                    subcode = err_dict.get("error_subcode")
                    code = err_dict.get("code")
                    if (subcode in GECICI_MEDYA_HATA_KODLARI or code in GECICI_MEDYA_HATA_KODLARI) and is_yerel and deneme_no < maks_deneme:
                        log.warning(f"Meta geçici Story görsel indirme hatası ({err_dict}). Alternatif CDN deneniyor...")
                        time.sleep(3)
                        continue
                    raise RuntimeError(f"Story Image Container hatası: {c_data}")

                container_id = c_data["id"]

                # Container hazır olana kadar bekle (azami 30 saniye)
                gecerli = False
                for poll_no in range(1, 16):
                    time.sleep(2)
                    try:
                        status_res = requests.get(
                            f"{GRAPH_API_URL}/{container_id}",
                            params={"fields": "status_code,status", "access_token": token},
                            timeout=15,
                        )
                        s_data = status_res.json()
                        status_code = s_data.get("status_code")
                        log.info(f"Story container durum kontrolü ({poll_no}/15): status_code={status_code}, status={s_data.get('status')}")

                        if status_code == "FINISHED" or (status_code is None and status_res.status_code == 200 and "error" not in s_data):
                            gecerli = True
                            break
                        elif status_code in ("ERROR", "EXPIRED"):
                            s_sub = s_data.get("error_subcode") or s_data.get("error", {}).get("error_subcode")
                            if (s_sub in GECICI_MEDYA_HATA_KODLARI or "media" in str(s_data).lower()) and is_yerel and deneme_no < maks_deneme:
                                log.warning(f"Story container işleme hatası ({s_data}). Alternatif CDN deneniyor...")
                                break
                            raise RuntimeError(f"Story görsel işleme hatası: {s_data}")
                    except Exception as e_poll:
                        if "işleme hatası" in str(e_poll):
                            raise e_poll
                        break

                if gecerli:
                    break
                elif is_yerel and deneme_no < maks_deneme:
                    time.sleep(3)
                    continue

            except Exception as e_story:
                if is_yerel and deneme_no < maks_deneme:
                    log.warning(f"Story görsel denemesi ({deneme_no}/{maks_deneme}) başarısız ({e_story}). Alternatif CDN deneniyor...")
                    time.sleep(3)
                    continue
                raise e_story

        if not container_id:
            raise RuntimeError("Story container oluşturulamadı!")

    # Son Adım: Story Yayınla
    log.info(f"Instagram Story {container_id} yayınlanıyor...")
    publish_res = requests.post(
        f"{GRAPH_API_URL}/{ig_id}/media_publish",
        data={
            "creation_id": container_id,
            "access_token": token,
        },
        timeout=60,
    )
    p_data = publish_res.json()
    if "id" not in p_data:
        raise RuntimeError(f"Instagram Story Yayınlama hatası: {p_data}")

    log.info(f"Instagram Story başarıyla yayınlandı! Medya ID: {p_data['id']}")
    return p_data


def medyayi_sil(media_id: str) -> bool:
    """
    Instagram veya Facebook üzerinden yayınlanmış bir gönderiyi / videoyu siler.
    Meta Graph API: DELETE /{media_id}
    """
    if not media_id:
        return False

    _, _, token = get_meta_bilgileri()
    page_token = get_env("FACEBOOK_PAGE_ACCESS_TOKEN") or token

    # Önce sayfa tokeni / genel token ile silmeyi dene
    for t in [token, page_token]:
        if not t:
            continue
        try:
            url = f"{GRAPH_API_URL}/{media_id}"
            res = requests.delete(url, params={"access_token": t}, timeout=30)
            data = res.json()
            if data.get("success") is True or res.status_code == 200:
                log.info(f"Meta medyası başarıyla silindi: ID {media_id}")
                return True
        except Exception as e:
            log.warning(f"Meta medya silme denemesi başarısız ({media_id}): {e}")

    log.error(f"Meta medyası silinemedi: ID {media_id}")
    return False

