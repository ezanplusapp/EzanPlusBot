"""
telegram_bot.py — Ezan Plus Telegram Onay ve Önizleme Yöneticisi
Üretilen görsel postları ve dikey Reels videolarını 'Ezan Plus Onay' grubuna gönderir,
inline onay butonları ile kullanıcının tek tıkla onaylamasını veya reddetmesini sağlar.
Onaylandığında Instagram, Threads ve Facebook'ta otomatik yayınlar.
"""

from __future__ import annotations

import html
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import requests

from .ayar import AYARLAR, get_env
from . import db
from . import instagram
from . import threads

log = logging.getLogger(__name__)

TABAN_URL = "https://api.telegram.org/bot{token}/{metot}"


def get_token_ve_chat_id() -> tuple[str, str]:
    """Güncel Telegram Bot Token ve Chat ID'yi döner."""
    token = get_env("TELEGRAM_BOT_TOKEN")
    chat_id = get_env("TELEGRAM_CHAT_ID")
    return token, chat_id


def _istek(metot: str, data: Optional[Dict[str, Any]] = None, files: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Telegram Bot API'ye HTTP isteği atar."""
    token, _ = get_token_ve_chat_id()
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN tanımlı değil! .env dosyasını kontrol edin.")

    url = TABAN_URL.format(token=token, metot=metot)
    res = requests.post(url, data=data, files=files, timeout=60)
    res_json = res.json()

    if not res_json.get("ok"):
        hata = res_json.get("description", "Bilinmeyen hata")
        log.error(f"Telegram API Hatası ({metot}): {hata}")
        raise RuntimeError(f"Telegram Hatası: {hata}")

    return res_json.get("result", {})


def mesaj_gonder(metin: str, chat_id: Optional[str] = None, butonlar: Optional[List[List[Dict[str, str]]]] = None) -> int:
    """Telegram grubuna metin mesajı gönderir ve mesaj ID'sini döner."""
    _, varsayilan_chat_id = get_token_ve_chat_id()
    hedef_chat = chat_id or varsayilan_chat_id
    if not hedef_chat:
        raise ValueError("TELEGRAM_CHAT_ID bulunamadı!")

    payload: Dict[str, Any] = {
        "chat_id": hedef_chat,
        "text": metin,
        "parse_mode": "HTML",
    }

    if butonlar:
        payload["reply_markup"] = json.dumps({"inline_keyboard": butonlar})

    res = _istek("sendMessage", data=payload)
    return res.get("message_id", 0)


def gorsel_gonder(
    gorsel_yolu: Path,
    caption: str = "",
    chat_id: Optional[str] = None,
    butonlar: Optional[List[List[Dict[str, str]]]] = None,
) -> int:
    """Tekil görseli başlığı ve butonlarıyla gruba gönderir."""
    _, varsayilan_chat_id = get_token_ve_chat_id()
    hedef_chat = chat_id or varsayilan_chat_id

    payload: Dict[str, Any] = {
        "chat_id": hedef_chat,
        "caption": caption[:1024],
        "parse_mode": "HTML",
    }
    if butonlar:
        payload["reply_markup"] = json.dumps({"inline_keyboard": butonlar})

    with open(gorsel_yolu, "rb") as f:
        files = {"photo": f}
        res = _istek("sendPhoto", data=payload, files=files)

    return res.get("message_id", 0)


def video_gonder(
    video_yolu: Path,
    caption: str = "",
    chat_id: Optional[str] = None,
    butonlar: Optional[List[List[Dict[str, str]]]] = None,
) -> int:
    """Reels MP4 videosunu önizleme ve onay butonlarıyla gruba gönderir."""
    _, varsayilan_chat_id = get_token_ve_chat_id()
    hedef_chat = chat_id or varsayilan_chat_id

    payload: Dict[str, Any] = {
        "chat_id": hedef_chat,
        "caption": caption[:1024],
        "parse_mode": "HTML",
        "supports_streaming": True,
    }
    if butonlar:
        payload["reply_markup"] = json.dumps({"inline_keyboard": butonlar})

    with open(video_yolu, "rb") as f:
        files = {"video": f}
        res = _istek("sendVideo", data=payload, files=files)

    return res.get("message_id", 0)


def onay_istegi_gonder(paylasim_id: int) -> int:
    """
    Veritabanındaki paylaşım kaydını okur ve formatına göre
    (görsel post veya Reels videosu) Telegram grubuna onay butonlarıyla iletir.
    """
    kayit = db.paylasim_getir(paylasim_id)
    if not kayit:
        raise ValueError(f"Paylaşım bulunamadı: ID {paylasim_id}")

    kategori = kayit["kategori"].upper()
    format_tipi = kayit["format"]
    caption = kayit.get("caption") or ""
    baslik = kayit.get("baslik") or ""

    # Telegram Önizleme Başlığı
    ozet_metin = (
        f"🕌 <b>EZAN PLUS YENİ İÇERİK ONAYI</b>\n\n"
        f"📌 <b>Kategori:</b> #{kategori} ({format_tipi})\n"
        f"📖 <b>Başlık/Kaynak:</b> {kayit.get('kaynak') or baslik}\n\n"
        f"📝 <b>Açıklama:</b>\n"
        f"<i>{caption[:350]}...</i>\n\n"
        f"👇 <b>Lütfen yayını onaylayın veya iptal edin:</b>"
    )

    butonlar = [
        [
            {"text": "✅ Onayla ve Yayınla", "callback_data": f"onay_{paylasim_id}"},
            {"text": "❌ İptal Et", "callback_data": f"red_{paylasim_id}"},
        ]
    ]

    # Medya Gönderimi
    if format_tipi == "reels_9_16" and kayit.get("video_yolu"):
        video_p = Path(kayit["video_yolu"])
        msg_id = video_gonder(video_p, caption=ozet_metin, butonlar=butonlar)
    elif kayit.get("gorsel_yollari") and len(kayit["gorsel_yollari"]) > 0:
        gorsel_p = Path(kayit["gorsel_yollari"][0])
        msg_id = gorsel_gonder(gorsel_p, caption=ozet_metin, butonlar=butonlar)
    else:
        msg_id = mesaj_gonder(ozet_metin, butonlar=butonlar)

    # Veritabanını güncelle
    db.durum_guncelle(paylasim_id, yeni_durum="onay_bekliyor", telegram_mesaj_id=msg_id)
    return msg_id


def callback_cevapla(callback_query_id: str, metin: str = "", alert: bool = False):
    """Butona tıklandığında Telegram bildirim baloncuğu gösterir."""
    try:
        _istek("answerCallbackQuery", data={
            "callback_query_id": callback_query_id,
            "text": metin,
            "show_alert": alert
        })
    except Exception as e:
        log.warning(f"answerCallbackQuery hatası: {e}")


def caption_guncelle(chat_id: str | int, message_id: int, yeni_caption: str):
    """Medya mesajının başlığını günceller."""
    try:
        _istek("editMessageCaption", data={
            "chat_id": chat_id,
            "message_id": message_id,
            "caption": yeni_caption[:1024],
            "parse_mode": "HTML"
        })
    except Exception as e:
        log.warning(f"editMessageCaption hatası: {e}")


def yayinla_hepsi(paylasim_id: int) -> Dict[str, Any]:
    """
    Onaylanan içeriği Instagram, Threads ve Facebook'ta eş zamanlı yayınlar.
    """
    kayit = db.paylasim_getir(paylasim_id)
    if not kayit:
        raise ValueError(f"Paylaşım ID bulunamadı: {paylasim_id}")

    format_tipi = kayit["format"]
    caption = kayit.get("caption") or ""
    video_yolu = kayit.get("video_yolu")
    gorsel_yollari = kayit.get("gorsel_yollari") or []
    gorsel_yolu = gorsel_yollari[0] if gorsel_yollari else None

    sonuclar = {}

    # 1. Instagram Yayınla
    try:
        if format_tipi == "reels_9_16" and video_yolu:
            log.info(f"Instagram'a Reels yükleniyor: {video_yolu}")
            ig_res = instagram.instagram_reels_paylas(video_yolu, caption)
            sonuclar["instagram"] = ig_res.get("id")
        elif gorsel_yolu:
            log.info(f"Instagram'a Görsel yükleniyor: {gorsel_yolu}")
            ig_res = instagram.instagram_gorsel_paylas(gorsel_yolu, caption)
            sonuclar["instagram"] = ig_res.get("id")
    except Exception as e:
        log.error(f"Instagram yayınlama hatası: {e}")
        sonuclar["instagram_hata"] = str(e)

    # 1b. Instagram Story Yayınla
    try:
        if format_tipi == "reels_9_16" and video_yolu:
            log.info(f"Instagram Story (Video) yükleniyor: {video_yolu}")
            story_res = instagram.instagram_story_paylas(video_yolu, is_video=True)
            sonuclar["instagram_story"] = story_res.get("id")
        elif gorsel_yolu:
            log.info(f"Instagram Story (Görsel) yükleniyor: {gorsel_yolu}")
            story_res = instagram.instagram_story_paylas(gorsel_yolu, is_video=False)
            sonuclar["instagram_story"] = story_res.get("id")
    except Exception as e:
        log.error(f"Instagram Story yayınlama hatası: {e}")
        sonuclar["instagram_story_hata"] = str(e)

    # 2. Threads Yayınla
    try:
        if gorsel_yolu:
            log.info("Threads'e görselli gönderi yükleniyor...")
            th_res = threads.threads_gorsel_paylas(gorsel_yolu, caption)
            sonuclar["threads"] = th_res.get("id")
        else:
            log.info("Threads'e metin gönderisi yükleniyor...")
            th_res = threads.threads_metin_paylas(caption)
            sonuclar["threads"] = th_res.get("id")
    except Exception as e:
        log.error(f"Threads yayınlama hatası: {e}")
        sonuclar["threads_hata"] = str(e)

    # 3. Facebook Sayfası Yayınla
    try:
        log.info("Facebook Sayfasına paylaşım yapılıyor...")
        fb_res = instagram.facebook_post_paylas(caption, gorsel_yolu=gorsel_yolu)
        sonuclar["facebook"] = fb_res.get("id")
    except Exception as e:
        log.error(f"Facebook sayfa yayınlama hatası: {e}")
        sonuclar["facebook_hata"] = str(e)

    # 4. YouTube Shorts Yayınla (Video varsa ve YouTube yetkilendirmesi hazırsa)
    if format_tipi == "reels_9_16" and video_yolu:
        try:
            from . import youtube
            if youtube.CLIENT_SECRET_DOSYASI.exists() or youtube.TOKEN_DOSYASI.exists():
                log.info(f"YouTube Shorts'a yükleniyor: {video_yolu}")
                baslik = kayit.get("baslik") or "Günün Ayeti • Ezan Plus"
                yt_res = youtube.youtube_shorts_yukle(
                    video_yolu=video_yolu,
                    baslik=baslik,
                    aciklama=caption,
                )
                sonuclar["youtube"] = yt_res.get("video_id")
                sonuclar["youtube_url"] = yt_res.get("url")
        except Exception as e:
            log.error(f"YouTube Shorts yayınlama hatası: {e}")
            sonuclar["youtube_hata"] = str(e)

    # Veritabanı güncelle
    db.durum_guncelle(
        paylasim_id,
        yeni_durum="yayinlandi",
        instagram_post_id=sonuclar.get("instagram"),
        youtube_post_id=sonuclar.get("youtube"),
    )
    return sonuclar


def tek_sefer_dinle(offset: int = 0) -> int:
    """
    Telegram'daki bekleyen güncellemeleri (buton tıklamalarını) kontrol eder,
    onay veya ret varsa anında işler. Yeni offset döner.
    """
    token, _ = get_token_ve_chat_id()
    url = TABAN_URL.format(token=token, metot="getUpdates")
    try:
        res = requests.get(url, params={"offset": offset, "timeout": 2}, timeout=5)
        res_json = res.json()
        if not res_json.get("ok"):
            return offset

        updates = res_json.get("result", [])
        for u in updates:
            u_id = u["update_id"]
            offset = max(offset, u_id + 1)

            cq = u.get("callback_query")
            if not cq:
                continue

            cq_id = cq["id"]
            data = cq.get("data", "")
            msg = cq.get("message", {})
            chat_id = msg.get("chat", {}).get("id")
            msg_id = msg.get("message_id")

            if data.startswith("onay_"):
                paylasim_id = int(data.split("_")[1])
                callback_cevapla(cq_id, "✅ İçerik onaylandı, yayınlanıyor! Lütfen bekleyin...", alert=True)
                caption_guncelle(chat_id, msg_id, "⏳ <b>YAYINLANIYOR...</b>\n\nİçerik Instagram, Threads ve Facebook'a aktarılıyor...")

                sonuclar = yayinla_hepsi(paylasim_id)

                yt_durum = "—"
                if "youtube" in sonuclar:
                    yt_durum = f"✅ Yayınlandı (<a href='{sonuclar.get('youtube_url', '')}'>İzle</a>)"
                elif "youtube_hata" in sonuclar:
                    yt_durum = "❌ Hata"

                basari_metni = (
                    f"🎉 <b>İÇERİK BAŞARIYLA YAYINLANDI!</b>\n\n"
                    f"• <b>Instagram Reels/Gönderi:</b> {'✅ Yayınlandı' if 'instagram' in sonuclar else '❌ Hata'}\n"
                    f"• <b>Instagram Story:</b> {'✅ Yayınlandı' if 'instagram_story' in sonuclar else '❌ Hata'}\n"
                    f"• <b>Threads (@ezanplusapp):</b> {'✅ Yayınlandı' if 'threads' in sonuclar else '❌ Hata'}\n"
                    f"• <b>Facebook Sayfası:</b> {'✅ Yayınlandı' if 'facebook' in sonuclar else '❌ Hata'}\n"
                    f"• <b>YouTube Shorts:</b> {yt_durum}\n\n"
                    f"⏰ <i>Zaman: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</i>"
                )
                caption_guncelle(chat_id, msg_id, basari_metni)

            elif data.startswith("red_"):
                paylasim_id = int(data.split("_")[1])
                callback_cevapla(cq_id, "❌ İçerik iptal edildi.", alert=False)
                db.durum_guncelle(paylasim_id, yeni_durum="iptal_edildi")
                caption_guncelle(chat_id, msg_id, "❌ <b>BU İÇERİK İPTAL EDİLDİ</b>\n\nYayınlanmadan arşivlendi.")

    except Exception as e:
        log.error(f"Telegram dinleme hatası: {e}")

    return offset
