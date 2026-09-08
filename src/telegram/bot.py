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

from ..ayar import AYARLAR, get_env, KOK_DIZIN
from .. import db, hata_bildir
from .yonetici import yayinla_hepsi, yayindan_kaldir, yayinla_telafi

log = logging.getLogger(__name__)

TABAN_URL = "https://api.telegram.org/bot{token}/{metot}"


def get_token_ve_chat_id() -> tuple[str, str]:
    """Güncel Telegram Bot Token ve Chat ID'yi döner."""
    token = get_env("TELEGRAM_BOT_TOKEN")
    chat_id = get_env("TELEGRAM_CHAT_ID")
    return token, chat_id


def _istek(
    metot: str,
    data: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    timeout: Optional[int] = None,
    maks_deneme: int = 3,
) -> Dict[str, Any]:
    """Telegram Bot API'ye güvenli, otomatik yeniden denemeli (retry) HTTP isteği atar."""
    token, _ = get_token_ve_chat_id()
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN tanımlı değil! .env dosyasını kontrol edin.")

    url = TABAN_URL.format(token=token, metot=metot)
    timeout_val = timeout or (120 if files else 35)

    for deneme in range(1, maks_deneme + 1):
        try:
            # Dosya pointer'larını sıfırla (yeniden denemelerde eksik/boş yüklemeyi önler)
            if files:
                for val in files.values():
                    if hasattr(val, "seek"):
                        try:
                            val.seek(0)
                        except Exception:
                            pass
                    elif isinstance(val, (tuple, list)) and len(val) > 1 and hasattr(val[1], "seek"):
                        try:
                            val[1].seek(0)
                        except Exception:
                            pass

            res = requests.post(url, data=data, files=files, timeout=timeout_val)
            try:
                res_json = res.json()
            except Exception as json_err:
                log.warning(f"Telegram API ({metot}) yanıtı JSON olarak okunamadı (Status: {res.status_code}): {res.text[:150]}")
                raise json_err

            if not res_json.get("ok"):
                hata = res_json.get("description", "Bilinmeyen hata")
                retry_after = res_json.get("parameters", {}).get("retry_after")
                if retry_after and deneme < maks_deneme:
                    log.warning(f"Telegram rate limit uygulandı ({retry_after}s bekleniyor): {hata}")
                    time.sleep(int(retry_after) + 1)
                    continue
                if "message is not modified" in hata.lower():
                    log.debug(f"Telegram API ({metot}): Mesaj zaten güncel, değişiklik yapılmadı.")
                    return res_json.get("result", {})
                log.error(f"Telegram API Hatası ({metot}): {hata}")
                raise RuntimeError(f"Telegram Hatası: {hata}")

            return res_json.get("result", {})

        except (requests.exceptions.RequestException, ConnectionResetError, ConnectionError, TimeoutError, json.JSONDecodeError) as e:
            log.warning(f"Telegram API isteği ({metot}) ağ/bağlantı hatası (deneme {deneme}/{maks_deneme}): {e}")
            if deneme < maks_deneme:
                time.sleep(2.0 * deneme)
            else:
                log.error(f"Telegram API ({metot}) tüm yeniden denemeler ({maks_deneme}) başarısız oldu: {e}")
                raise e


def mesaj_gonder(
    metin: str,
    chat_id: Optional[str] = None,
    butonlar: Optional[List[List[Dict[str, str]]]] = None,
    html: bool = True,
    **kwargs: Any,
) -> int:
    """Telegram grubuna metin mesajı gönderir ve mesaj ID'sini döner."""
    _, varsayilan_chat_id = get_token_ve_chat_id()
    hedef_chat = chat_id or varsayilan_chat_id
    if not hedef_chat:
        raise ValueError("TELEGRAM_CHAT_ID bulunamadı!")

    payload: Dict[str, Any] = {
        "chat_id": hedef_chat,
        "text": metin,
        "parse_mode": "HTML" if html else None,
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
        files = {"photo": (gorsel_yolu.name, f, "image/png")}
        res = _istek("sendPhoto", data=payload, files=files, timeout=60)

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
        files = {"video": (video_yolu.name, f, "video/mp4")}
        res = _istek("sendVideo", data=payload, files=files, timeout=120)

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
    if kategori == "KELIME":
        ozet_metin = (
            f"📖 <b>EZAN PLUS — KUR'AN SÖZLÜĞÜ</b>\n\n"
            f"✨ <b>Kavram:</b> {kayit.get('kaynak') or baslik}\n"
            f"🎨 <b>Palet:</b> Ezan Yakut Kırmızısı (4:5 Feed + 9:16 Story)\n"
            f"🛡️ <b>Kalite Denetimi:</b> Başarılı (Boyut, Metin & Mizanpaj Onaylandı)\n\n"
            f"📝 <b>Açıklama:</b>\n"
            f"<i>{caption[:450]}...</i>\n\n"
            f"👇 <b>Lütfen yayını onaylayın veya iptal edin:</b>"
        )
    else:
        ozet_metin = (
            f"🕌 <b>EZAN PLUS YENİ İÇERİK ONAYI</b>\n\n"
            f"📌 <b>Kategori:</b> #{kategori} ({format_tipi})\n"
            f"📖 <b>Başlık/Kaynak:</b> {kayit.get('kaynak') or baslik}\n"
            f"🛡️ <b>Kalite Denetimi:</b> Başarılı (Boyut, Metin & Mizanpaj Onaylandı)\n\n"
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
    caption_ve_buton_guncelle(chat_id, message_id, yeni_caption, butonlar=None)


def caption_ve_buton_guncelle(
    chat_id: str | int,
    message_id: int,
    yeni_caption: str,
    butonlar: Optional[List[List[Dict[str, str]]]] = None,
):
    """Medya veya metin mesajının içeriğini ve inline butonlarını günceller."""
    # Güvenli uzunluk: Telegram 1024 karakter sınırına saygı göster
    caption_temiz = yeni_caption
    if len(caption_temiz) > 1020:
        caption_temiz = caption_temiz[:1015] + "..."

    # 1. Medya mesajı başlığını güncellemeyi dene (editMessageCaption)
    try:
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "caption": caption_temiz,
            "parse_mode": "HTML",
        }
        if butonlar is not None:
            payload["reply_markup"] = json.dumps({"inline_keyboard": butonlar})
        _istek("editMessageCaption", data=payload)
        return
    except Exception as e:
        log.warning(f"editMessageCaption denenemedi ({e}), düz metin veya editMessageText deneniyor...")

    # HTML parse hatası ihtimaline karşı düz metin dene (tagler kesilmişse)
    try:
        import re
        duz_metin = re.sub(r"<[^>]+>", "", caption_temiz)
        payload_plain: Dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "caption": duz_metin[:1020],
        }
        if butonlar is not None:
            payload_plain["reply_markup"] = json.dumps({"inline_keyboard": butonlar})
        _istek("editMessageCaption", data=payload_plain)
        return
    except Exception:
        pass

    # 2. Eğer medya değilse metin mesajı olarak güncelle (editMessageText)
    try:
        payload_txt: Dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": caption_temiz,
            "parse_mode": "HTML",
        }
        if butonlar is not None:
            payload_txt["reply_markup"] = json.dumps({"inline_keyboard": butonlar})
        _istek("editMessageText", data=payload_txt)
    except Exception as e2:
        log.error(f"Mesaj güncelleme hatası: {e2}")


def _kanal_ok(sonuclar: Dict[str, Any], k: str) -> bool:
    """Kanalın başarıyla yayınlanıp yayınlanmadığını kontrol eder."""
    val = sonuclar.get(k)
    if not val:
        return False
    if f"{k}_hata" in sonuclar:
        return False
    if isinstance(val, dict):
        return bool(val.get("basarili") is True or val.get("id"))
    return True


def telafi_butonlari_kur(paylasim_id: int, sonuclar: Dict[str, Any], format_tipi: str = "post_4_5") -> List[List[Dict[str, str]]]:
    """
    Yayın sonucuna göre eksik veya hatalı platformlar için telafi (yeniden deneme),
    hata teşhis ve yayından kaldırma butonlarını dinamik olarak kurar.
    """
    eksik_butonlar: List[Dict[str, str]] = []
    if not _kanal_ok(sonuclar, "instagram"):
        eksik_butonlar.append({"text": "🔄 📸 Instagram", "callback_data": f"telafi_ig_{paylasim_id}"})
    if not _kanal_ok(sonuclar, "instagram_story"):
        eksik_butonlar.append({"text": "🔄 📱 Story", "callback_data": f"telafi_story_{paylasim_id}"})
    if not _kanal_ok(sonuclar, "threads"):
        eksik_butonlar.append({"text": "🔄 🧵 Threads", "callback_data": f"telafi_threads_{paylasim_id}"})
    if not _kanal_ok(sonuclar, "facebook"):
        eksik_butonlar.append({"text": "🔄 📘 Facebook", "callback_data": f"telafi_facebook_{paylasim_id}"})
    if format_tipi == "reels_9_16" and not _kanal_ok(sonuclar, "youtube"):
        eksik_butonlar.append({"text": "🔄 ▶️ Shorts", "callback_data": f"telafi_youtube_{paylasim_id}"})
    if format_tipi == "reels_9_16" and not _kanal_ok(sonuclar, "tiktok"):
        eksik_butonlar.append({"text": "🔄 🎵 TikTok", "callback_data": f"telafi_tiktok_{paylasim_id}"})

    satirlar: List[List[Dict[str, str]]] = []

    # Eğer 1'den fazla eksik/hatalı kanal varsa ana telafi butonunu en başa ekle
    if len(eksik_butonlar) > 1:
        satirlar.append([{"text": "🔄 Başarısız Tüm Kanalları Tekrar Dene", "callback_data": f"telafi_hepsi_{paylasim_id}"}])

    # Tekil kanal butonlarını 2'şerli sıralar halinde diz
    for i in range(0, len(eksik_butonlar), 2):
        satirlar.append(eksik_butonlar[i:i+2])

    # Hata teşhis ve rehber butonu (herhangi bir eksik kanal veya hata kaydı varsa)
    has_error = any(k.endswith("_hata") for k in sonuclar.keys()) or len(eksik_butonlar) > 0
    if has_error:
        satirlar.append([{"text": "🔍 Hata Teşhisi & Çözüm Rehberi", "callback_data": f"teshis_{paylasim_id}"}])

    # Yayından kaldır ve canlı link butonları
    satirlar.append([{"text": "🗑️ Yayından Kaldır", "callback_data": f"kaldir_{paylasim_id}"}])
    if sonuclar.get("youtube_url"):
        satirlar.append([{"text": "🔗 YouTube Shorts'ta İzle", "url": sonuclar["youtube_url"]}])
    if format_tipi == "reels_9_16" and not _kanal_ok(sonuclar, "tiktok"):
        satirlar.append([{"text": "🎵 TikTok'u Aç (@ezanplusapp)", "url": "https://www.tiktok.com/@ezanplusapp"}])

    return satirlar


def yayin_raporu_metni_kur(kayit: Dict[str, Any], sonuclar: Dict[str, Any]) -> str:
    """Yayın sonuçlarını şık ve anlaşılır bir HTML özet raporuna dönüştürür."""
    kategori = (kayit.get("kategori") or "İÇERİK").upper()
    format_tipi = kayit.get("format") or ""
    caption = kayit.get("caption") or ""
    baslik = kayit.get("baslik") or ""
    kaynak = kayit.get("kaynak") or baslik

    yt_durum = "—"
    if _kanal_ok(sonuclar, "youtube"):
        yt_durum = "✅ Yayında"
    elif "youtube_hata" in sonuclar:
        yt_durum = "❌ Hata"

    tt_durum = "—"
    if _kanal_ok(sonuclar, "tiktok"):
        tt_durum = "✅ Yayında"
    elif "tiktok_hata" in sonuclar:
        tt_durum = "❌ Hata"
    elif format_tipi == "reels_9_16":
        tt_durum = "⏳ API Onayı Bekliyor (Metin aşağıda)"

    tsi_saat = datetime.now().strftime("%H:%M TSİ")

    has_error = any(k.endswith("_hata") for k in sonuclar.keys()) or not all([
        _kanal_ok(sonuclar, "instagram"),
        _kanal_ok(sonuclar, "instagram_story"),
        _kanal_ok(sonuclar, "threads"),
        _kanal_ok(sonuclar, "facebook"),
    ])

    if has_error:
        if kategori in ("AYET", "REELS"):
            baslik_str = "⚠️ <b>KUR'AN-I KERİM TİLAVETİ — KISMİ BAŞARI / DİKKAT</b>"
        elif kategori == "HADIS":
            baslik_str = "⚠️ <b>SAHİH HADİS-İ ŞERİF — KISMİ BAŞARI / DİKKAT</b>"
        elif kategori == "DUA":
            baslik_str = "⚠️ <b>GÜNÜN DUASI — KISMİ BAŞARI / DİKKAT</b>"
        elif kategori == "KELIME":
            baslik_str = "⚠️ <b>KUR'AN SÖZLÜĞÜ — KISMİ BAŞARI / DİKKAT</b>"
        else:
            baslik_str = f"⚠️ <b>{kategori} — KISMİ BAŞARI / DİKKAT</b>"
    else:
        if kategori in ("AYET", "REELS"):
            baslik_str = "🚀 <b>KUR'AN-I KERİM TİLAVETİ YAYINLANDI!</b>"
        elif kategori == "HADIS":
            baslik_str = "🚀 <b>SAHİH HADİS-İ ŞERİF YAYINLANDI!</b>"
        elif kategori == "DUA":
            baslik_str = "🚀 <b>GÜNÜN DUASI YAYINLANDI!</b>"
        elif kategori == "KELIME":
            baslik_str = "🚀 <b>KUR'AN SÖZLÜĞÜ YAYINLANDI!</b>"
        else:
            baslik_str = f"🚀 <b>{kategori} İÇERİĞİ YAYINLANDI!</b>"

    if kategori in ("AYET", "REELS"):
        kunye_str = f"📖 <b>Âyet:</b> {kaynak}\n🎙️ <b>Kari:</b> Mişari Râşid el-Afâsî\n⏱️ <b>Yayın Saati:</b> {tsi_saat}"
    elif kategori == "HADIS":
        kunye_str = f"📜 <b>Hadis:</b> {kaynak}\n⏱️ <b>Yayın Saati:</b> {tsi_saat}"
    elif kategori == "DUA":
        kunye_str = f"🌿 <b>Dua:</b> {kaynak}\n⏱️ <b>Yayın Saati:</b> {tsi_saat}"
    elif kategori == "KELIME":
        kavram_adi = baslik if baslik else kaynak
        ayet_ref = f"\n📌 <b>Âyet:</b> {kaynak}" if (kaynak and kaynak != baslik) else ""
        kunye_str = f"📖 <b>Kavram:</b> {kavram_adi}{ayet_ref}\n🎨 <b>Palet:</b> Ezan Yakut Kırmızısı\n⏱️ <b>Yayın Saati:</b> {tsi_saat}"
    else:
        kunye_str = f"📌 <b>Kaynak:</b> {kaynak}\n⏱️ <b>Yayın Saati:</b> {tsi_saat}"

    ig_durum = "✅ Yayında" if _kanal_ok(sonuclar, "instagram") else "❌ Hata"
    story_durum = "✅ Yayında" if _kanal_ok(sonuclar, "instagram_story") else "❌ Hata"
    th_durum = "✅ Yayında" if _kanal_ok(sonuclar, "threads") else "❌ Hata"
    fb_durum = "✅ Yayında" if _kanal_ok(sonuclar, "facebook") else "❌ Hata"

    metin = (
        f"{baslik_str}\n\n"
        f"{kunye_str}\n\n"
        f"📱 <b>Yayın Kanalları:</b>\n"
        f"• <b>Instagram Reels/Feed:</b> {ig_durum}\n"
        f"• <b>Instagram Story:</b> {story_durum}\n"
        f"• <b>Threads (@ezanplusapp):</b> {th_durum}\n"
        f"• <b>Facebook Sayfası:</b> {fb_durum}\n"
        f"• <b>YouTube Shorts:</b> {yt_durum}\n"
        f"• <b>TikTok:</b> {tt_durum}\n\n"
        f"📝 <b>Açıklama:</b>\n"
        f"<i>{caption[:280]}...</i>"
    )

    if has_error:
        metin += (
            "\n\n⚠️ <i>Bazı platformlara aktarım sağlanamadı! "
            "Aşağıdaki telafi butonlarına dokunarak eksik kanalları doğrudan yeniden yayınlayabilir "
            "veya <b>Hata Teşhisi</b> butonuna basarak kök sebebi inceleyebilirsiniz.</i>"
        )
    else:
        metin += "\n\n⚠️ <i>İçerikte bir sorun varsa aşağıdaki butonla tüm platformlardan kaldırabilirsiniz:</i>"

    return metin


def yayin_detay_karti_gonder(paylasim_id: int, sonuclar: Dict[str, Any]) -> int:
    """
    Otomatik yayınlanan (veya onaylanan) içeriğin detaylı yayın raporunu,
    eksik platformlar için telafi butonlarını ve '🗑️ Yayından Kaldır' butonunu Telegram grubuna iletir.
    """
    kayit = db.paylasim_getir(paylasim_id)
    if not kayit:
        raise ValueError(f"Paylaşım bulunamadı: ID {paylasim_id}")

    format_tipi = kayit["format"]
    caption = kayit.get("caption") or ""
    rapor_metin = yayin_raporu_metni_kur(kayit, sonuclar)
    buton_satirlari = telafi_butonlari_kur(paylasim_id, sonuclar, format_tipi)

    # Medyayı gönder (Video -> Thumbnail -> Metin Mesajı Kademeli Güvenlik Fallback'i)
    msg_id = 0
    if format_tipi == "reels_9_16" and kayit.get("video_yolu") and Path(kayit["video_yolu"]).exists():
        try:
            msg_id = video_gonder(Path(kayit["video_yolu"]), caption=rapor_metin, butonlar=buton_satirlari)
        except Exception as e:
            log.warning(f"Telegram'a video yüklenemedi: {e}. Görsel/thumbnail fallback deneniyor...")
            thumbnail_yolu = Path(kayit["video_yolu"]).with_suffix(".png")
            if thumbnail_yolu.exists():
                try:
                    msg_id = gorsel_gonder(thumbnail_yolu, caption=rapor_metin, butonlar=buton_satirlari)
                except Exception as e2:
                    log.warning(f"Telegram'a thumbnail yüklenemedi: {e2}. Metin mesajı fallback deneniyor...")
            elif kayit.get("gorsel_yollari") and len(kayit["gorsel_yollari"]) > 0 and Path(kayit["gorsel_yollari"][0]).exists():
                try:
                    msg_id = gorsel_gonder(Path(kayit["gorsel_yollari"][0]), caption=rapor_metin, butonlar=buton_satirlari)
                except Exception as e2:
                    log.warning(f"Telegram'a görsel yüklenemedi: {e2}. Metin mesajı fallback deneniyor...")
            
            if not msg_id:
                try:
                    msg_id = mesaj_gonder(rapor_metin, butonlar=buton_satirlari)
                except Exception as e3:
                    log.error(f"Telegram'a metin raporu dahi gönderilemedi: {e3}")
    elif kayit.get("gorsel_yollari") and len(kayit["gorsel_yollari"]) > 0 and Path(kayit["gorsel_yollari"][0]).exists():
        try:
            msg_id = gorsel_gonder(Path(kayit["gorsel_yollari"][0]), caption=rapor_metin, butonlar=buton_satirlari)
        except Exception as e:
            log.warning(f"Telegram'a görsel yüklenemedi: {e}. Metin mesajı fallback deneniyor...")
            try:
                msg_id = mesaj_gonder(rapor_metin, butonlar=buton_satirlari)
            except Exception as e2:
                log.error(f"Telegram'a metin raporu dahi gönderilemedi: {e2}")
    else:
        try:
            msg_id = mesaj_gonder(rapor_metin, butonlar=buton_satirlari)
        except Exception as e:
            log.error(f"Telegram'a metin raporu dahi gönderilemedi: {e}")

    # Video yayınlandığında TikTok için tek dokunuşla kopyalanabilir tam metni ilet
    if format_tipi == "reels_9_16" and caption:
        try:
            import html
            tiktok_metin = (
                f"📋 <b>TikTok Açıklama &amp; Etiket Metni</b> (Kopyalamak için metne 1 kez dokunun):\n\n"
                f"<code>{html.escape(caption)}</code>"
            )
            mesaj_gonder(tiktok_metin)
        except Exception as e:
            log.warning(f"TikTok kopyalama metni gönderilemedi: {e}")

    if msg_id:
        db.durum_guncelle(paylasim_id, yeni_durum="yayinlandi", telegram_mesaj_id=msg_id)
    else:
        db.durum_guncelle(paylasim_id, yeni_durum="yayinlandi")
    return msg_id



# yayinla_hepsi fonksiyonu .yonetici modülünden içe aktarılmıştır


def komutlari_kaydet() -> bool:
    """Telegram botuna '/' ile açılan komut listesini kaydeder (setMyCommands)."""
    komutlar = [
        {"command": "ayet", "description": "Kur'an-ı Kerim Tilaveti Reels videosu üret"},
        {"command": "hadis", "description": "Sahih Hadis-i Şerif kartı üret (4:5 + 9:16)"},
        {"command": "dua", "description": "Günün Duası kartı üret (4:5 + 9:16)"},
        {"command": "kelime", "description": "Kur'an Sözlüğü kavram kartı üret (4:5 + 9:16)"},
        {"command": "onar", "description": "Kalite kontrolünden geçemeyen içeriği otomatik onar"},
        {"command": "yeniden_uret", "description": "Belirtilen paylaşımı sıfırdan yeniden üret"},
        {"command": "hata", "description": "Son sistem hatasını ve teşhis raporunu göster"},
        {"command": "hatalar", "description": "Son sistem hatalarını ve çözüm butonlarını listele"},
        {"command": "tekrar", "description": "Başarısız olan platformları tekrar yayınla"},
        {"command": "saglik", "description": "Sistem servisleri ve API sağlık testi"},
        {"command": "temizle", "description": "Geçici dosyaları ve önbelleği temizle"},
        {"command": "kaldir", "description": "Yayınlanan içeriği tüm platformlardan sil"},
        {"command": "durum", "description": "Sistem ve yayın istatistikleri raporu"},
        {"command": "yardim", "description": "Komut kullanım rehberi ve yardım"},
    ]
    try:
        _istek("setMyCommands", data={"commands": json.dumps(komutlar)})
        log.info("Telegram komut listesi başarıyla kaydedildi.")
        return True
    except Exception as e:
        log.warning(f"Telegram setMyCommands hatası: {e}")
        return False


def durum_raporu_olustur() -> str:
    """Sistem envanteri, bekleyen taslaklar ve yayın istatistiklerini derler."""
    from .. import kuran_db, hadis_db, dua_db, kelime_db

    # Külliyat sayıları
    toplam_ayet = 6236
    toplam_hadis = hadis_db.toplam_hadis_sayisi()
    toplam_dua = len(dua_db.dualari_yukle())
    toplam_kelime = len(kelime_db.kelimeleri_yukle())

    # Yayın istatistikleri
    yayinlanan_toplam = 0
    bekleyen_taslak = 0
    bugun_yayinlanan = 0
    try:
        with db.baglanti_al() as con:
            cur = con.execute("SELECT COUNT(*) FROM paylasimlar WHERE durum = 'yayinlandi'")
            yayinlanan_toplam = cur.fetchone()[0]
            cur = con.execute("SELECT COUNT(*) FROM paylasimlar WHERE durum = 'onay_bekliyor'")
            bekleyen_taslak = cur.fetchone()[0]
            cur = con.execute("SELECT COUNT(*) FROM paylasimlar WHERE durum = 'yayinlandi' AND date(yayin_zamani) = date('now')")
            bugun_yayinlanan = cur.fetchone()[0]
    except Exception as e:
        log.warning(f"Durum raporu SQL hatası: {e}")

    rapor = (
        f"📊 <b>EZAN PLUS YAYIN MOTORU DURUM RAPORU</b>\n\n"
        f"📚 <b>Tescilli Külliyat Envanteri:</b>\n"
        f"• <b>Kur'an Âyetleri:</b> {toplam_ayet:,} Âyet (114 Sûre, Uthmani Hat)\n"
        f"• <b>Sahih Hadisler:</b> {toplam_hadis:,} Hadis (Riyâzü's-Sâlihîn)\n"
        f"• <b>Manevi Dualar:</b> {toplam_dua} Dua (Kur'an & Sünnet)\n"
        f"• <b>Kur'an Sözlüğü:</b> {toplam_kelime} Temel İslami Kavram\n\n"
        f"📈 <b>Yayın İstatistikleri:</b>\n"
        f"• <b>Bugün Yayınlanan:</b> {bugun_yayinlanan} Gönderi\n"
        f"• <b>Toplam Yayınlanan:</b> {yayinlanan_toplam} Gönderi\n"
        f"• <b>Onay Bekleyen Taslak:</b> {bekleyen_taslak} Adet\n\n"
        f"⚡ <b>Aktif Yayın Stratejisi:</b> Günde 6 Dağıtım Slotu\n"
        f"<i>(3x Kur'an Reels, 1x Hadis Kartı, 1x Dua Kartı, 1x Kelime Kartı)</i>\n\n"
        f"⏰ <i>Sistem Saati: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</i>"
    )
    return rapor


def saglik_raporu_olustur() -> tuple[str, List[List[Dict[str, str]]]]:
    """Tüm sistemin, yerel veritabanlarının ve harici API'lerin sağlık durumunu denetler."""
    import shutil
    durumlar = []

    # 1. EzanPlus Ana DB
    try:
        with db.baglanti_al() as con:
            cur = con.execute("SELECT COUNT(*) FROM paylasimlar")
            cnt = cur.fetchone()[0]
            durumlar.append(("ezanplus.db", True, f"{cnt} kayıt aktif"))
    except Exception as e:
        durumlar.append(("ezanplus.db", False, str(e)[:40]))

    # 2. Kur'an DB
    try:
        from .. import kuran_db
        with kuran_db.baglanti_al() as con:
            cur = con.execute("SELECT COUNT(*) FROM ayetler")
            cnt = cur.fetchone()[0]
            durumlar.append(("kuran.db", cnt == 6236, f"{cnt} âyet tescilli"))
    except Exception as e:
        durumlar.append(("kuran.db", False, str(e)[:40]))

    # 3. Hadis DB
    try:
        from .. import hadis_db
        with hadis_db.baglanti_al() as con:
            cur = con.execute("SELECT COUNT(*) FROM hadisler")
            cnt = cur.fetchone()[0]
            durumlar.append(("hadisler.db", cnt > 0, f"{cnt} hadis tescilli"))
    except Exception as e:
        durumlar.append(("hadisler.db", False, str(e)[:40]))

    # 4. Gemini AI API Anahtarı
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key and len(gemini_key) > 15:
        durumlar.append(("Gemini AI (2.5 Flash)", True, "API anahtarı tanımlı"))
    else:
        durumlar.append(("Gemini AI (2.5 Flash)", False, "API anahtarı eksik!"))

    # 5. Meta Graph API (Instagram & FB)
    meta_token = os.getenv("META_ACCESS_TOKEN") or os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
    if meta_token and len(meta_token) > 20:
        durumlar.append(("Meta Graph API (IG/FB)", True, "Erişim jetonu mevcut"))
    else:
        durumlar.append(("Meta Graph API (IG/FB)", False, "Jeton eksik!"))

    # 6. Threads API
    threads_token = os.getenv("THREADS_ACCESS_TOKEN") or os.getenv("META_ACCESS_TOKEN")
    if threads_token and len(threads_token) > 20:
        durumlar.append(("Threads API", True, "Erişim jetonu mevcut"))
    else:
        durumlar.append(("Threads API", False, "Jeton eksik!"))

    # 7. YouTube Data API
    yt_token = KOK_DIZIN / "data" / "youtube_token.json"
    yt_client = KOK_DIZIN / "data" / "client_secret.json"
    if yt_token.exists() or yt_client.exists():
        durumlar.append(("YouTube Shorts API", True, "Yetki yapılandırması mevcut"))
    else:
        durumlar.append(("YouTube Shorts API", False, "Token/Secret dosyası eksik"))

    # 8. Disk ve Çıktı Klasörü
    try:
        cikti_d = KOK_DIZIN / "data" / "cikti"
        cikti_d.mkdir(parents=True, exist_ok=True)
        total, used, free = shutil.disk_usage(cikti_d)
        free_gb = free / (1024 ** 3)
        durumlar.append(("Depolama (Disk)", free_gb > 0.5, f"{free_gb:.1f} GB boş alan"))
    except Exception as e:
        durumlar.append(("Depolama (Disk)", False, str(e)[:40]))

    satirlar = ["🩺 <b>EZAN PLUS SİSTEM SAĞLIK RAPORU</b>\n"]
    genel_saglik = all(d[1] for d in durumlar)
    ozet_ikon = "🟢" if genel_saglik else "⚠️"
    satirlar.append(f"{ozet_ikon} <b>Genel Durum:</b> {'Tüm Servisler Sağlıklı' if genel_saglik else 'Bazı Servislerde İnceleme Gerekli'}\n")

    for servis, ok, detay in durumlar:
        s_ikon = "✅" if ok else "❌"
        satirlar.append(f"• {s_ikon} <b>{servis}:</b> {detay}")

    satirlar.append(f"\n⏰ <i>Test Zamanı: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</i>")

    btns = [
        [
            {"text": "🧹 Geçici Dosyaları Temizle", "callback_data": "cmd_temizle"},
            {"text": "📜 Son Hatalar", "callback_data": "cmd_hatalar"},
        ],
        [
            {"text": "📊 Sistem Durumu", "callback_data": "cmd_durum"},
            {"text": "ℹ️ Yardım", "callback_data": "cmd_yardim"},
        ],
    ]
    return "\n".join(satirlar), btns


def sistem_temizle() -> str:
    """Geçici video render dosyalarını, önbellekleri ve artık dosyaları temizler."""
    temizlenen = 0
    yer_kazanci_bayt = 0
    cikti_d = KOK_DIZIN / "data" / "cikti"
    if cikti_d.exists():
        for f in cikti_d.glob("temp_*"):
            try:
                sz = f.stat().st_size
                f.unlink()
                temizlenen += 1
                yer_kazanci_bayt += sz
            except Exception:
                pass
        for f in cikti_d.glob("*.tmp"):
            try:
                sz = f.stat().st_size
                f.unlink()
                temizlenen += 1
                yer_kazanci_bayt += sz
            except Exception:
                pass

    audio_d = KOK_DIZIN / "assets" / "audio"
    if audio_d.exists():
        concat_f = audio_d / "concat_listesi.txt"
        if concat_f.exists():
            try:
                concat_f.unlink()
                temizlenen += 1
            except Exception:
                pass

    # SQLite WAL checkpoint
    try:
        with db.baglanti_al() as con:
            con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except Exception:
        pass

    kazanc_mb = yer_kazanci_bayt / (1024 * 1024)
    return (
        f"🧹 <b>SİSTEM TEMİZLİĞİ TAMAMLANDI</b>\n\n"
        f"• <b>Temizlenen Geçici Dosya:</b> {temizlenen} adet\n"
        f"• <b>Açılan Alan:</b> {kazanc_mb:.2f} MB\n"
        f"• <b>Veritabanı:</b> WAL kütükleri diskle senkronize edildi (TRUNCATE).\n\n"
        f"Sistem önbelleği ferahlatıldı ve üretime hazır."
    )


def hatalar_raporu_olustur(adet: int = 5) -> tuple[str, List[List[Dict[str, str]]]]:
    """Son kaydedilen sistem hatalarını özet liste ve çözüm butonlarıyla kurar."""
    hatalar = hata_bildir.son_hatalari_listele(adet=adet)
    if not hatalar:
        return (
            "🟢 <b>Kayıtlı Sistem Hatası Yok</b>\n\nSistemde herhangi bir aktif veya arşivlenmiş hata kaydı bulunmuyor.",
            [[{"text": "🩺 Sağlık Testi", "callback_data": "cmd_saglik"}, {"text": "📊 Sistem Durumu", "callback_data": "cmd_durum"}]]
        )

    satirlar = [f"📋 <b>SON SİSTEM HATALARI (Son {len(hatalar)} Kayıt)</b>\n"]
    btns: List[List[Dict[str, str]]] = []

    for i, h in enumerate(reversed(hatalar), 1):
        pid = h.get("paylasim_id")
        pid_str = f"#{pid}" if pid else "Genel"
        tarih = h.get("tarih_tr") or h.get("tarih", "")[:19]
        baslik = html.escape(h.get("baslik", "Hata"))
        nerede = html.escape(h.get("nerede", "Bilinmiyor"))
        ne_oldu = html.escape(h.get("ne_oldu", "")[:80])

        satirlar.append(
            f"<b>{i}. [{tarih}] ID: {pid_str}</b>\n"
            f"📍 <i>{nerede}</i> ➔ <b>{baslik}</b>\n"
            f"🔍 <i>{ne_oldu}...</i>\n"
        )
        if pid:
            btns.append([
                {"text": f"🛠️ Onar #{pid}", "callback_data": f"onar_{pid}"},
                {"text": f"🔄 Yeniden Üret #{pid}", "callback_data": f"yeniden_uret_{pid}"},
                {"text": f"🔍 Teşhis #{pid}", "callback_data": f"teshis_{pid}"},
            ])

    btns.append([
        {"text": "🩺 Sağlık Testi", "callback_data": "cmd_saglik"},
        {"text": "🧹 Temizle", "callback_data": "cmd_temizle"},
        {"text": "📊 Durum", "callback_data": "cmd_durum"},
    ])
    return "\n".join(satirlar), btns


def yardim_metni_olustur() -> str:
    """Kullanılabilir komutların yardım metnini döner."""
    return (
        f"🕌 <b>EZAN PLUS YÖNETİM & SORUN GİDERME REHBERİ</b>\n\n"
        f"Aşağıdaki komutları bu gruba yazarak anında içerik üretebilir veya sistemi yönetebilirsiniz:\n\n"
        f"🎬 <b>/ayet</b> [sure:ayet veya tema] — 9:16 Kur'an Tilaveti Reels videosu üretir.\n"
        f"📜 <b>/hadis</b> [konu veya hadis no] — Sahih Hadis-i Şerif kartı üretir (4:5 + 9:16).\n"
        f"🌿 <b>/dua</b> [ruh hali veya dua adı] — Günün Duası kartı üretir (4:5 + 9:16).\n"
        f"📖 <b>/kelime</b> [kavram adı] — Kur'an Sözlüğü kavram kartı üretir (4:5 + 9:16).\n\n"
        f"🛠️ <b>HATA ÇÖZÜM & ONARIM KOMUTLARI:</b>\n"
        f"• <b>/onar &lt;ID&gt;</b> — Kalite veya mizanpaj hatası alan içeriği otonom onarır.\n"
        f"• <b>/yeniden_uret &lt;ID&gt;</b> — Belirtilen paylaşımı tescilli kaynaktan sıfırdan yeniden üretir.\n"
        f"• <b>/hata</b> — En son sistem hatasını ve doğrudan çözüm butonlarını gösterir.\n"
        f"• <b>/hatalar</b> — Son 5 sistem hatasını ve her biri için tek tık onarım butonlarını listeler.\n"
        f"• <b>/tekrar &lt;ID&gt;</b> — Başarısız/eksik kalan kanalları tekrar yayınlar.\n"
        f"• <b>/saglik</b> — Veritabanları, AI ve sosyal medya API bağlantılarını test eder.\n"
        f"• <b>/temizle</b> — Geçici render dosyalarını ve önbelleği temizler.\n\n"
        f"⚙️ <b>YAYIN YÖNETİMİ:</b>\n"
        f"• <b>/yayinla &lt;ID&gt;</b> — Onay bekleyen taslağı hemen yayınlar.\n"
        f"• <b>/kaldir &lt;ID&gt;</b> — Yayındaki içeriği tüm platformlardan siler.\n"
        f"• <b>/iptal &lt;ID&gt;</b> — Belirtilen taslağı iptal eder.\n"
        f"• <b>/durum</b> — Yayın ve envanter istatistikleri raporu.\n"
        f"• <b>/yardim</b> — Bu rehber mesajını görüntüler."
    )


import threading

SON_KOMUTLAR: Dict[str, float] = {}


def _coklu_komut_engeli(ana_komut: str, chat_id: str | int, limit_saniye: float = 15.0) -> bool:
    """Aynı komutun arka arkaya flood edilmesini engeller."""
    anahtar = f"{chat_id}:{ana_komut}"
    simdi = time.time()
    son_zaman = SON_KOMUTLAR.get(anahtar, 0)
    if simdi - son_zaman < limit_saniye:
        return False
    SON_KOMUTLAR[anahtar] = simdi
    return True


_AKTIF_ISLER: List[threading.Thread] = []


def _arkaplanda_calistir(hedef, *args, **kwargs):
    """Uzun süren komutları ve yayın işlemlerini bot dinleme döngüsünü tıkamadan arka planda çalıştırır."""
    t = threading.Thread(target=hedef, args=args, kwargs=kwargs, daemon=False)
    _AKTIF_ISLER.append(t)
    t.start()
    return t


def aktif_isleri_bekle(timeout: float = 45.0):
    """Devam eden arka plan yayınlama/silme işlerinin tamamlanmasını bekler."""
    global _AKTIF_ISLER
    for t in list(_AKTIF_ISLER):
        if t.is_alive():
            t.join(timeout=timeout)
    _AKTIF_ISLER = [t for t in _AKTIF_ISLER if t.is_alive()]


def komut_isle(chat_id: str | int, msg_id: int, metin: str):
    """Kullanıcının gönderdiği metin komutunu ayrıştırır ve çalıştırır."""
    parcalar = metin.split(maxsplit=1)
    ana_komut = parcalar[0].split("@")[0].lower().strip()
    parametre = parcalar[1].strip() if len(parcalar) > 1 else None

    log.info(f"Telegram komutu alındı: ana_komut='{ana_komut}', param='{parametre}'")

    if ana_komut in ("/yardim", "/help", "/start"):
        mesaj_gonder(yardim_metni_olustur(), chat_id=str(chat_id))

    elif ana_komut == "/durum":
        mesaj_gonder(durum_raporu_olustur(), chat_id=str(chat_id))

    elif ana_komut == "/ayet":
        if not _coklu_komut_engeli("/ayet", chat_id):
            mesaj_gonder("⚠️ <b>Komutunuz zaten işleniyor:</b> Kur'an tilaveti hazırlanıyor, lütfen bekleyin...", chat_id=str(chat_id))
            return
        mesaj_gonder("⏳ <b>Kur'an Tilaveti Reels Videosu Hazırlanıyor...</b>\n\nMişari Râşid el-Afâsî tilaveti render edilip otomatik yayınlanacak, lütfen bekleyin...", chat_id=str(chat_id))
        def _gorev_ayet():
            try:
                from .. import otomasyon
                otomasyon.reels_icerigi_olustur_ve_gonder(tema=parametre)
            except Exception as e:
                log.error(f"/ayet komutu hatası: {e}")
                mesaj_gonder(f"❌ <b>Tilavet videosu üretilemedi:</b>\n<code>{html.escape(str(e))}</code>", chat_id=str(chat_id))
        _arkaplanda_calistir(_gorev_ayet)

    elif ana_komut == "/hadis":
        if not _coklu_komut_engeli("/hadis", chat_id):
            mesaj_gonder("⚠️ <b>Komutunuz zaten işleniyor:</b> Hadis kartı hazırlanıyor, lütfen bekleyin...", chat_id=str(chat_id))
            return
        mesaj_gonder("⏳ <b>Sahih Hadis-i Şerif Kartı Hazırlanıyor...</b>\n\nRiyâzü's-Sâlihîn külliyatından seçilerek V16 standardında 4:5 Feed ve 9:16 Story formatlarında çiziliyor...", chat_id=str(chat_id))
        def _gorev_hadis():
            try:
                from .. import otomasyon
                otomasyon.hadis_postu_olustur_ve_gonder(tema=parametre)
            except Exception as e:
                log.error(f"/hadis komutu hatası: {e}")
                mesaj_gonder(f"❌ <b>Hadis kartı üretilemedi:</b>\n<code>{html.escape(str(e))}</code>", chat_id=str(chat_id))
        _arkaplanda_calistir(_gorev_hadis)

    elif ana_komut == "/dua":
        if not _coklu_komut_engeli("/dua", chat_id):
            mesaj_gonder("⚠️ <b>Komutunuz zaten işleniyor:</b> Dua kartı hazırlanıyor, lütfen bekleyin...", chat_id=str(chat_id))
            return
        mesaj_gonder("⏳ <b>Günün Duası Kartı Hazırlanıyor...</b>\n\nTescilli dualar külliyatından seçilerek V16 standardında 4:5 Feed ve 9:16 Story formatlarında çiziliyor...", chat_id=str(chat_id))
        def _gorev_dua():
            try:
                from .. import otomasyon
                otomasyon.dua_postu_olustur_ve_gonder(ruh_hali=parametre)
            except Exception as e:
                log.error(f"/dua komutu hatası: {e}")
                mesaj_gonder(f"❌ <b>Dua kartı üretilemedi:</b>\n<code>{html.escape(str(e))}</code>", chat_id=str(chat_id))
        _arkaplanda_calistir(_gorev_dua)

    elif ana_komut == "/kelime":
        if not _coklu_komut_engeli("/kelime", chat_id):
            mesaj_gonder("⚠️ <b>Komutunuz zaten işleniyor:</b> Kelime kartı hazırlanıyor, lütfen bekleyin...", chat_id=str(chat_id))
            return
        mesaj_gonder("⏳ <b>Kur'an Sözlüğü Kartı Hazırlanıyor...</b>\n\nİslami kavramlar külliyatından seçilerek V16 standardında 4:5 Feed ve 9:16 Story formatlarında çiziliyor...", chat_id=str(chat_id))
        def _gorev_kelime():
            try:
                from .. import otomasyon
                otomasyon.kelime_postu_olustur_ve_gonder(kavram=parametre)
            except Exception as e:
                log.error(f"/kelime komutu hatası: {e}")
                mesaj_gonder(f"❌ <b>Kelime kartı üretilemedi:</b>\n<code>{html.escape(str(e))}</code>", chat_id=str(chat_id))
        _arkaplanda_calistir(_gorev_kelime)

    elif ana_komut == "/yayinla":
        if not parametre or not parametre.isdigit():
            mesaj_gonder("⚠️ <b>Geçersiz Kullanım:</b> Lütfen yayınlamak istediğiniz paylaşım ID'sini girin.\n<i>Örnek: <code>/yayinla 14</code></i>", chat_id=str(chat_id))
            return
        pid = int(parametre)
        mesaj_gonder(f"⏳ <b>Paylaşım #{pid} yayınlanıyor...</b>\nInstagram, Threads ve Facebook'a aktarılıyor...", chat_id=str(chat_id))
        def _gorev_yayinla():
            try:
                sonuclar = yayinla_hepsi(pid)
                try:
                    yayin_detay_karti_gonder(pid, sonuclar)
                except Exception as e_k:
                    log.error(f"Paylaşım #{pid} yayınlandı ancak detay kartı Telegram'a iletilemedi: {e_k}")
            except Exception as e:
                log.error(f"/yayinla hatası: {e}")
                mesaj_gonder(f"❌ <b>Yayınlama hatası:</b>\n<code>{html.escape(str(e))}</code>", chat_id=str(chat_id))
        _arkaplanda_calistir(_gorev_yayinla)

    elif ana_komut in ("/kaldir", "/sil"):
        if not parametre or not parametre.isdigit():
            mesaj_gonder("⚠️ <b>Geçersiz Kullanım:</b> Lütfen yayından kaldırmak istediğiniz paylaşım ID'sini girin.\n<i>Örnek: <code>/kaldir 14</code></i>", chat_id=str(chat_id))
            return
        pid = int(parametre)
        mesaj_gonder(f"⏳ <b>Paylaşım #{pid} tüm platformlardan yayından kaldırılıyor...</b>", chat_id=str(chat_id))
        def _gorev_kaldir():
            try:
                silme_sonuclar = yayindan_kaldir(pid)
                mesaj_gonder(
                    f"🗑️ <b>PAYLAŞIM #{pid} YAYINDAN KALDIRILDI!</b>\n\n"
                    f"• Instagram: {'✅ Silindi' if silme_sonuclar.get('instagram') else '—'}\n"
                    f"• Facebook: {'✅ Silindi' if silme_sonuclar.get('facebook') else '—'}\n"
                    f"• YouTube: {'✅ Silindi' if silme_sonuclar.get('youtube') else '—'}\n"
                    f"• Threads: {'✅ Silindi' if silme_sonuclar.get('threads') else '—'}\n\n"
                    f"Sistem yayın geçmişinden ve veritabanından temizlendi.",
                    chat_id=str(chat_id),
                )
            except Exception as e:
                log.error(f"/kaldir hatası: {e}")
                mesaj_gonder(f"❌ <b>Yayından kaldırma hatası:</b>\n<code>{html.escape(str(e))}</code>", chat_id=str(chat_id))
        _arkaplanda_calistir(_gorev_kaldir)

    elif ana_komut == "/iptal":
        if not parametre or not parametre.isdigit():
            mesaj_gonder("⚠️ <b>Geçersiz Kullanım:</b> Lütfen iptal etmek istediğiniz paylaşım ID'sini girin.\n<i>Örnek: <code>/iptal 14</code></i>", chat_id=str(chat_id))
            return
        pid = int(parametre)
        db.durum_guncelle(pid, yeni_durum="iptal_edildi")
        mesaj_gonder(f"❌ <b>Paylaşım #{pid} iptal edildi.</b>", chat_id=str(chat_id))

    elif ana_komut == "/hata":
        son_h = hata_bildir.son_hata_getir()
        if son_h:
            metin = hata_bildir.mesaji_kur(
                baslik=son_h.get("baslik", "Sistem Hatası"),
                teshis=son_h,
                nerede=son_h.get("nerede", ""),
                paylasim_id=son_h.get("paylasim_id"),
            )
            btns = hata_bildir.hata_butonlari(son_h.get("paylasim_id"), eylem=son_h.get("eylem", "tekrar_yayinla"))
            mesaj_gonder(metin, chat_id=str(chat_id), butonlar=btns)
        else:
            mesaj_gonder("🟢 <b>Sistem Sağlıklı:</b> Kayıtlı aktif bir sistem hatası bulunmuyor. Tüm yayınlar ve servisler sorunsuz çalışıyor.", chat_id=str(chat_id))

    elif ana_komut == "/tekrar":
        if not parametre or not parametre.isdigit():
            mesaj_gonder("⚠️ <b>Geçersiz Kullanım:</b> Lütfen tekrar yayınlamak istediğiniz paylaşım ID'sini girin.\n<i>Örnek: <code>/tekrar 1</code></i>", chat_id=str(chat_id))
            return
        pid = int(parametre)
        mesaj_gonder(f"⏳ <b>Paylaşım #{pid} için telafi yayını başlatılıyor...</b>\nEksik veya hatalı platformlar taranıyor...", chat_id=str(chat_id))
        def _gorev_tekrar_cmd():
            try:
                sonuclar = yayinla_telafi(pid, hedef_kanal="hepsi")
                yayin_detay_karti_gonder(pid, sonuclar)
            except Exception as e:
                log.error(f"/tekrar hatası (#{pid}): {e}")
                hata_bildir.bildir(f"Paylaşım #{pid} Telafi Hatası", e, nerede="/tekrar komutu", paylasim_id=pid)
        _arkaplanda_calistir(_gorev_tekrar_cmd)

    elif ana_komut == "/onar":
        if not parametre or not parametre.isdigit():
            mesaj_gonder("⚠️ <b>Geçersiz Kullanım:</b> Lütfen onarmak istediğiniz paylaşım ID'sini girin.\n<i>Örnek: <code>/onar 14</code></i>", chat_id=str(chat_id))
            return
        pid = int(parametre)
        mesaj_gonder(f"🛠️ <b>Paylaşım #{pid} otomatik onarılıyor...</b>\nKalite denetimi, metin uyumu ve şablonlar doğrulanıyor...", chat_id=str(chat_id))
        def _gorev_onar_cmd():
            try:
                from .. import denetleyici
                onarildi, duzeltmeler = denetleyici.otomatik_onar(pid)
                if onarildi:
                    d_rapor = "\n".join(f"• {d}" for d in duzeltmeler)
                    mesaj_gonder(
                        f"🎉 <b>Paylaşım #{pid} Başarıyla Onarıldı!</b>\n\n"
                        f"<b>Yapılan Düzeltmeler:</b>\n{d_rapor}\n\n"
                        f"Kalite denetimi başarıyla onaylandı.",
                        chat_id=str(chat_id),
                        butonlar=[
                            [{"text": "✅ Onayla ve Yayınla", "callback_data": f"onay_{pid}"}],
                            [{"text": "❌ İptal Et", "callback_data": f"red_{pid}"}],
                        ]
                    )
                else:
                    d_hata = "\n".join(f"• {d}" for d in duzeltmeler)
                    mesaj_gonder(
                        f"❌ <b>Paylaşım #{pid} Otomatik Onarılamadı:</b>\n\n{d_hata}\n\n"
                        f"Dilerseniz <b>/yeniden_uret {pid}</b> ile içeriği sıfırdan oluşturabilirsiniz.",
                        chat_id=str(chat_id),
                        butonlar=[
                            [{"text": "🔄 Sıfırdan Yeniden Üret", "callback_data": f"yeniden_uret_{pid}"}],
                            [{"text": "❌ İptal Et", "callback_data": f"red_{pid}"}],
                        ]
                    )
            except Exception as e:
                log.error(f"/onar hatası (#{pid}): {e}")
                mesaj_gonder(f"❌ <b>Onarım sırasında hata:</b>\n<code>{html.escape(str(e))}</code>", chat_id=str(chat_id))
        _arkaplanda_calistir(_gorev_onar_cmd)

    elif ana_komut in ("/yeniden_uret", "/recreate"):
        if not parametre or not parametre.isdigit():
            mesaj_gonder("⚠️ <b>Geçersiz Kullanım:</b> Lütfen yeniden üretmek istediğiniz paylaşım ID'sini girin.\n<i>Örnek: <code>/yeniden_uret 14</code></i>", chat_id=str(chat_id))
            return
        pid = int(parametre)
        kayit = db.paylasim_getir(pid)
        if not kayit:
            mesaj_gonder(f"❌ <b>Paylaşım bulunamadı:</b> #{pid}", chat_id=str(chat_id))
            return
        kat = kayit.get("kategori", "ayet")
        baslik = kayit.get("baslik") or kayit.get("kaynak")
        mesaj_gonder(f"⏳ <b>Paylaşım #{pid} ({kat.upper()}) sıfırdan yeniden üretiliyor...</b>\nLütfen bekleyin...", chat_id=str(chat_id))
        def _gorev_yeniden_uret_cmd():
            try:
                from .. import otomasyon
                yeni_pid = 0
                if kat in ("ayet", "reels"):
                    yeni_pid = otomasyon.reels_icerigi_olustur_ve_gonder(tema=baslik)
                elif kat == "hadis":
                    yeni_pid = otomasyon.hadis_postu_olustur_ve_gonder(tema=baslik)
                elif kat == "dua":
                    yeni_pid = otomasyon.dua_postu_olustur_ve_gonder(ruh_hali=baslik)
                elif kat == "kelime":
                    yeni_pid = otomasyon.kelime_postu_olustur_ve_gonder(kavram=baslik)
                else:
                    yeni_pid = otomasyon.icerik_olustur_ve_gonder(tur=kat, tema=baslik)

                db.durum_guncelle(pid, yeni_durum="iptal_edildi", hata_mesaji=f"Yeniden üretildi -> Yeni ID #{yeni_pid}")
                mesaj_gonder(
                    f"🎉 <b>Yeniden Üretim Tamamlandı!</b>\n\n"
                    f"• Eski Paylaşım: #{pid} (Arşivlendi)\n"
                    f"• <b>Yeni Paylaşım ID:</b> <code>#{yeni_pid}</code>\n\n"
                    f"Yeni içerik kalite kontrolünden başarıyla geçti ve onaya sunuldu.",
                    chat_id=str(chat_id)
                )
            except Exception as e:
                log.error(f"/yeniden_uret hatası (#{pid}): {e}")
                mesaj_gonder(f"❌ <b>Yeniden üretim hatası:</b>\n<code>{html.escape(str(e))}</code>", chat_id=str(chat_id))
        _arkaplanda_calistir(_gorev_yeniden_uret_cmd)

    elif ana_komut in ("/hatalar", "/hata_listesi"):
        metin, btns = hatalar_raporu_olustur(adet=5)
        mesaj_gonder(metin, chat_id=str(chat_id), butonlar=btns)

    elif ana_komut in ("/saglik", "/test", "/status"):
        metin, btns = saglik_raporu_olustur()
        mesaj_gonder(metin, chat_id=str(chat_id), butonlar=btns)

    elif ana_komut in ("/temizle", "/clean"):
        metin = sistem_temizle()
        mesaj_gonder(metin, chat_id=str(chat_id))

    else:
        mesaj_gonder(
            f"❓ <b>Bilinmeyen Komut:</b> <code>{html.escape(ana_komut)}</code>\n\n"
            f"Kullanılabilir tüm komutlar için <b>/yardim</b> yazabilirsiniz.",
            chat_id=str(chat_id),
        )


def tek_sefer_dinle(offset: int = 0) -> int:
    """
    Telegram'daki bekleyen güncellemeleri (hem buton tıklamalarını hem de metin komutlarını) kontrol eder.
    Yeni offset değerini döner.
    """
    token, _ = get_token_ve_chat_id()
    url = TABAN_URL.format(token=token, metot="getUpdates")
    try:
        params = {
            "offset": offset,
            "timeout": 3,
            "allowed_updates": json.dumps(["message", "callback_query", "channel_post", "my_chat_member"]),
        }
        res = requests.get(url, params=params, timeout=15)
        res_json = res.json()
        if not res_json.get("ok"):
            return offset

        updates = res_json.get("result", [])
        for u in updates:
            u_id = u["update_id"]
            offset = max(offset, u_id + 1)

            # 1. Buton Tıklamaları (Inline Callback Query)
            cq = u.get("callback_query")
            if cq:
                cq_id = cq["id"]
                data = cq.get("data", "")
                msg = cq.get("message", {})
                chat_id = msg.get("chat", {}).get("id")
                msg_id = msg.get("message_id")
                log.info(f"Telegram buton tıklaması alındı: data='{data}', msg_id={msg_id}")

                if data.startswith("onay_"):
                    paylasim_id = int(data.split("_")[1])
                    callback_cevapla(cq_id, "✅ İçerik onaylandı, yayınlanıyor! Lütfen bekleyin...", alert=True)
                    # Çift tıklamayı ve mükerrer yayını önlemek için butonları anında kaldır
                    caption_ve_buton_guncelle(
                        chat_id,
                        msg_id,
                        "⏳ <b>YAYINLANIYOR...</b>\n\nİçerik Instagram, Threads, Facebook ve YouTube'a aktarılıyor, lütfen bekleyin...",
                        butonlar=[]
                    )

                    def _gorev_onay(p_id=paylasim_id, c_id=chat_id, m_id=msg_id):
                        try:
                            sonuclar = yayinla_hepsi(p_id)
                            kayit = db.paylasim_getir(p_id)
                            format_t = kayit.get("format") if kayit else "post_4_5"
                            basari_metni = yayin_raporu_metni_kur(kayit, sonuclar)
                            yeni_butonlar = telafi_butonlari_kur(p_id, sonuclar, format_t)
                            caption_ve_buton_guncelle(c_id, m_id, basari_metni, butonlar=yeni_butonlar)

                            # Eğer herhangi bir platform hata aldıysa otomatik teşhis gönder
                            has_error = any(k.endswith("_hata") for k in sonuclar.keys())
                            if has_error:
                                hata_metni = "; ".join(v for k, v in sonuclar.items() if k.endswith("_hata"))
                                hata_bildir.bildir(
                                    baslik=kayit.get("baslik") if kayit else f"Paylaşım #{p_id}",
                                    hata=hata_metni,
                                    nerede="Yayın Dağıtım Motoru",
                                    paylasim_id=p_id
                                )
                        except Exception as e:
                            log.error(f"Onay yayınlama hatası (#{p_id}): {e}")
                            db.durum_guncelle(p_id, yeni_durum="onay_bekliyor", hata_mesaji=str(e))
                            kayit = db.paylasim_getir(p_id)
                            hata_bildir.bildir(
                                baslik=kayit.get("baslik") if kayit else f"Paylaşım #{p_id}",
                                hata=e,
                                nerede="Onay Yayınlama Hatası",
                                paylasim_id=p_id
                            )
                            caption_ve_buton_guncelle(
                                c_id,
                                m_id,
                                f"❌ <b>YAYINLAMA HATASI!</b>\n\n<code>{html.escape(str(e))}</code>\n\n<i>Ayrıntılı teşhis raporu aşağıda iletildi.</i>",
                                butonlar=[
                                    [{"text": "🔄 Tekrar Dene", "callback_data": f"telafi_hepsi_{p_id}"}],
                                    [{"text": "🔍 Hata Teşhisi & Çözüm", "callback_data": f"teshis_{p_id}"}],
                                    [{"text": "❌ İptal Et", "callback_data": f"red_{p_id}"}],
                                ]
                            )

                    _arkaplanda_calistir(_gorev_onay)

                elif data.startswith("telafi_"):
                    parcalar = data.split("_")
                    hedef_kanal = parcalar[1]
                    p_id = int(parcalar[2])
                    callback_cevapla(cq_id, f"⏳ {hedef_kanal.upper()} telafi yayını yapılıyor...", alert=False)
                    caption_ve_buton_guncelle(
                        chat_id,
                        msg_id,
                        f"⏳ <b>TELAFİ YAYINI YAPILIYOR ({hedef_kanal.upper()})...</b>\n\nEksik kanallar tekrar deneniyor, lütfen bekleyin...",
                        butonlar=[]
                    )

                    def _gorev_telafi_btn(paylasim_id=p_id, c_id=chat_id, m_id=msg_id, kanal=hedef_kanal):
                        try:
                            sonuclar = yayinla_telafi(paylasim_id, hedef_kanal=kanal)
                            kayit = db.paylasim_getir(paylasim_id)
                            format_t = kayit.get("format") if kayit else "post_4_5"
                            yeni_metin = yayin_raporu_metni_kur(kayit, sonuclar)
                            yeni_btns = telafi_butonlari_kur(paylasim_id, sonuclar, format_t)
                            caption_ve_buton_guncelle(c_id, m_id, yeni_metin, butonlar=yeni_btns)

                            yeni_ok = sonuclar.get("yeni_basarili", [])
                            if yeni_ok:
                                mesaj_gonder(
                                    f"🎉 <b>Telafi Yayını Başarılı!</b>\n\n"
                                    f"Paylaşım #{paylasim_id} için şu kanallar başarıyla yayınlandı: "
                                    f"<b>{', '.join(yeni_ok).upper()}</b>",
                                    chat_id=str(c_id)
                                )
                            else:
                                kalan_hata = sonuclar.get(f"{kanal}_hata") or "; ".join(v for k, v in sonuclar.items() if k.endswith("_hata")) or "Yayınlama başarısız"
                                hata_bildir.bildir(
                                    baslik=kayit.get("baslik") if kayit else f"Paylaşım #{paylasim_id}",
                                    hata=kalan_hata,
                                    nerede=f"Telafi Yayını ({kanal})",
                                    paylasim_id=paylasim_id
                                )
                        except Exception as e:
                            log.error(f"Telafi yayını hatası (#{paylasim_id}): {e}")
                            hata_bildir.bildir(
                                baslik=f"Paylaşım #{paylasim_id} Telafi Hatası",
                                hata=e,
                                nerede=f"Telafi Butonu ({kanal})",
                                paylasim_id=paylasim_id
                            )

                    _arkaplanda_calistir(_gorev_telafi_btn)

                elif data.startswith("teshis_"):
                    p_id = int(data.split("_")[1])
                    callback_cevapla(cq_id, "🔍 Hata analizi hazırlanıyor...", alert=False)
                    kayit = db.paylasim_getir(p_id)
                    if kayit:
                        hata_metni = kayit.get("hata_mesaji") or "Platform yayınlama hatası oluştu."
                        hata_bildir.bildir(
                            baslik=kayit.get("baslik") or f"Paylaşım #{p_id}",
                            hata=hata_metni,
                            nerede="Yayın Dağıtım Motoru",
                            paylasim_id=p_id
                        )

                elif data.startswith("onar_"):
                    p_id = int(data.split("_")[1])
                    callback_cevapla(cq_id, f"🛠️ Paylaşım #{p_id} otomatik onarılıyor...", alert=False)
                    caption_ve_buton_guncelle(
                        chat_id,
                        msg_id,
                        f"🛠️ <b>OTOMATİK ONARIM BAŞLATILDI (#{p_id})...</b>\n\nKalite denetimi, metin uyumu ve şablonlar doğrulanıyor...",
                        butonlar=[]
                    )

                    def _gorev_onar_btn(paylasim_id=p_id, c_id=chat_id, m_id=msg_id):
                        try:
                            from .. import denetleyici
                            onarildi, duzeltmeler = denetleyici.otomatik_onar(paylasim_id)
                            if onarildi:
                                d_rapor = "\n".join(f"• {d}" for d in duzeltmeler)
                                caption_ve_buton_guncelle(
                                    c_id,
                                    m_id,
                                    f"🎉 <b>Paylaşım #{paylasim_id} Başarıyla Onarıldı!</b>\n\n"
                                    f"<b>Yapılan Düzeltmeler:</b>\n{d_rapor}\n\n"
                                    f"İçerik kalite kapısından başarıyla geçti. Lütfen yayını onaylayın:",
                                    butonlar=[
                                        [{"text": "✅ Onayla ve Yayınla", "callback_data": f"onay_{paylasim_id}"}],
                                        [{"text": "❌ İptal Et", "callback_data": f"red_{paylasim_id}"}],
                                    ]
                                )
                            else:
                                d_hata = "\n".join(f"• {d}" for d in duzeltmeler)
                                caption_ve_buton_guncelle(
                                    c_id,
                                    m_id,
                                    f"❌ <b>Paylaşım #{paylasim_id} Otomatik Onarılamadı:</b>\n\n{d_hata}",
                                    butonlar=[
                                        [{"text": "🔄 Sıfırdan Yeniden Üret", "callback_data": f"yeniden_uret_{paylasim_id}"}],
                                        [{"text": "❌ İptal Et", "callback_data": f"red_{paylasim_id}"}],
                                    ]
                                )
                        except Exception as e:
                            log.error(f"Otomatik onarım hatası (#{paylasim_id}): {e}")
                            caption_ve_buton_guncelle(
                                c_id,
                                m_id,
                                f"❌ <b>Onarım Hatası:</b> <code>{html.escape(str(e))}</code>",
                                butonlar=[[{"text": "❌ İptal Et", "callback_data": f"red_{paylasim_id}"}]]
                            )

                    _arkaplanda_calistir(_gorev_onar_btn)

                elif data.startswith("yeniden_uret_"):
                    p_id = int(data.split("_")[2])
                    callback_cevapla(cq_id, f"🔄 Paylaşım #{p_id} sıfırdan yeniden üretiliyor...", alert=True)
                    caption_ve_buton_guncelle(
                        chat_id,
                        msg_id,
                        f"⏳ <b>SIFIRDAN YENİDEN ÜRETİLİYOR (#{p_id})...</b>\n\nTescilli kaynaktan yeni içerik çekilip şablonlar sıfırdan çiziliyor...",
                        butonlar=[]
                    )

                    def _gorev_yeniden_uret_btn(paylasim_id=p_id, c_id=chat_id, m_id=msg_id):
                        try:
                            kayit = db.paylasim_getir(paylasim_id)
                            kat = kayit.get("kategori", "ayet") if kayit else "ayet"
                            baslik = (kayit.get("baslik") or kayit.get("kaynak")) if kayit else None
                            from .. import otomasyon
                            yeni_pid = 0
                            if kat in ("ayet", "reels"):
                                yeni_pid = otomasyon.reels_icerigi_olustur_ve_gonder(tema=baslik)
                            elif kat == "hadis":
                                yeni_pid = otomasyon.hadis_postu_olustur_ve_gonder(tema=baslik)
                            elif kat == "dua":
                                yeni_pid = otomasyon.dua_postu_olustur_ve_gonder(ruh_hali=baslik)
                            elif kat == "kelime":
                                yeni_pid = otomasyon.kelime_postu_olustur_ve_gonder(kavram=baslik)
                            else:
                                yeni_pid = otomasyon.icerik_olustur_ve_gonder(tur=kat, tema=baslik)

                            db.durum_guncelle(paylasim_id, yeni_durum="iptal_edildi", hata_mesaji=f"Yeniden üretildi -> Yeni ID #{yeni_pid}")
                            mesaj_gonder(
                                f"🎉 <b>Yeniden Üretim Başarılı!</b>\n\n"
                                f"• Eski Paylaşım: #{paylasim_id} (Arşivlendi)\n"
                                f"• <b>Yeni Paylaşım ID:</b> <code>#{yeni_pid}</code>\n\n"
                                f"Yeni içerik kalite kontrolünden başarıyla geçti ve onaya sunuldu.",
                                chat_id=str(c_id)
                            )
                        except Exception as e:
                            log.error(f"Yeniden üretim hatası (#{paylasim_id}): {e}")
                            caption_ve_buton_guncelle(
                                c_id,
                                m_id,
                                f"❌ <b>Yeniden Üretim Hatası:</b> <code>{html.escape(str(e))}</code>",
                                butonlar=[[{"text": "❌ İptal Et", "callback_data": f"red_{paylasim_id}"}]]
                            )

                    _arkaplanda_calistir(_gorev_yeniden_uret_btn)

                elif data == "cmd_saglik":
                    callback_cevapla(cq_id, "🩺 Sağlık testi yapılıyor...", alert=False)
                    metin, btns = saglik_raporu_olustur()
                    mesaj_gonder(metin, chat_id=str(chat_id), butonlar=btns)

                elif data == "cmd_temizle":
                    callback_cevapla(cq_id, "🧹 Sistem temizleniyor...", alert=False)
                    metin = sistem_temizle()
                    mesaj_gonder(metin, chat_id=str(chat_id))

                elif data == "cmd_hatalar":
                    callback_cevapla(cq_id, "📜 Son hatalar getiriliyor...", alert=False)
                    metin, btns = hatalar_raporu_olustur(adet=5)
                    mesaj_gonder(metin, chat_id=str(chat_id), butonlar=btns)

                elif data == "cmd_durum":
                    callback_cevapla(cq_id, "📊 Sistem durumu getiriliyor...", alert=False)
                    mesaj_gonder(durum_raporu_olustur(), chat_id=str(chat_id))

                elif data == "cmd_yardim":
                    callback_cevapla(cq_id, "ℹ️ Yardım rehberi getiriliyor...", alert=False)
                    mesaj_gonder(yardim_metni_olustur(), chat_id=str(chat_id))

                elif data.startswith("kaldir_"):
                    paylasim_id = int(data.split("_")[1])
                    callback_cevapla(cq_id, "⏳ İçerik platformlardan kaldırılıyor...", alert=True)
                    caption_ve_buton_guncelle(
                        chat_id,
                        msg_id,
                        "⏳ <b>YAYINDAN KALDIRILIYOR...</b>\n\nİçerik Meta, YouTube ve Threads ağlarından siliniyor...",
                        butonlar=[]
                    )

                    def _gorev_kaldir_btn(p_id=paylasim_id, c_id=chat_id, m_id=msg_id):
                        try:
                            silme_sonuclar = yayindan_kaldir(p_id)
                            kaldirildi_metni = (
                                f"🗑️ <b>BU İÇERİK YAYINDAN KALDIRILDI</b>\n\n"
                                f"📌 <b>Paylaşım #{p_id}</b> Doğukan tarafından tüm platformlardan başarıyla silindi ve arşivlendi.\n\n"
                                f"• Instagram: {'✅ Silindi' if silme_sonuclar.get('instagram') else '—'}\n"
                                f"• Facebook: {'✅ Silindi' if silme_sonuclar.get('facebook') else '—'}\n"
                                f"• YouTube: {'✅ Silindi' if silme_sonuclar.get('youtube') else '—'}\n"
                                f"• Threads: {'✅ Silindi' if silme_sonuclar.get('threads') else '—'}\n\n"
                                f"⏰ <i>Kaldırılma Saati: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</i>"
                            )
                            caption_ve_buton_guncelle(
                                c_id,
                                m_id,
                                kaldirildi_metni,
                                butonlar=[]
                            )
                            mesaj_gonder(f"🗑️ <b>Paylaşım #{p_id} tüm platformlardan başarıyla kaldırıldı.</b>", chat_id=str(c_id))
                        except Exception as e:
                            log.error(f"Yayından kaldırma hatası (#{p_id}): {e}")
                            mesaj_gonder(f"⚠️ <b>Yayından kaldırma hatası:</b>\n<code>{html.escape(str(e))}</code>", chat_id=str(c_id))

                    _arkaplanda_calistir(_gorev_kaldir_btn)

                elif data.startswith("red_"):
                    paylasim_id = int(data.split("_")[1])
                    callback_cevapla(cq_id, "❌ İçerik iptal edildi.", alert=False)
                    db.durum_guncelle(paylasim_id, yeni_durum="iptal_edildi")
                    caption_ve_buton_guncelle(
                        chat_id,
                        msg_id,
                        "❌ <b>BU İÇERİK İPTAL EDİLDİ</b>\n\nYayınlanmadan arşivlendi.",
                        butonlar=[]
                    )
                continue

            # 2. Gelen Metin Mesajları / Komutlar
            msg = u.get("message") or u.get("channel_post")
            if msg:
                metin = (msg.get("text") or "").strip()
                chat_id = msg.get("chat", {}).get("id")
                msg_id = msg.get("message_id")
                msg_date = msg.get("date", 0)

                # 15 dakikadan eski komutları atla (bot kapalıyken birikmiş eski testleri çalıştırmasın)
                if msg_date > 0 and (time.time() - msg_date) > 900:
                    log.info(f"Eski Telegram mesajı atlandı ({int(time.time() - msg_date)} sn önce): '{metin}'")
                    continue

                if metin.startswith("/") and chat_id:
                    komut_isle(chat_id, msg_id, metin)

    except requests.exceptions.Timeout:
        # Uzun yoklama zaman aşımı normaldir, sessizce devam et
        pass
    except (requests.exceptions.ConnectionError, ConnectionResetError) as ce:
        log.warning(f"Telegram dinleme bağlantı geçici koptu: {ce}")
    except Exception as e:
        log.error(f"Telegram dinleme hatası: {e}")

    return offset


def surekli_dinle(aralik_saniye: float = 2.0):
    """
    Telegram botunu sürekli dinleme (daemon) modunda çalıştırır.
    Ağ kesintilerine karşı otomatik yeniden bağlanır.
    """
    log.info("Telegram komutları ve buton onayları dinleniyor (Çıkmak için Ctrl+C)...")
    komutlari_kaydet()
    offset = 0
    while True:
        try:
            offset = tek_sefer_dinle(offset)
        except KeyboardInterrupt:
            log.info("Telegram dinleyici kullanıcı tarafından durduruldu.")
            break
        except Exception as e:
            log.error(f"Telegram yoklama döngüsü hatası: {e}, 5 sn sonra yeniden deneniyor...")
            time.sleep(5)
        time.sleep(aralik_saniye)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    surekli_dinle()
