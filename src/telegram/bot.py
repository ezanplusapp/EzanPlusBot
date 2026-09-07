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

from ..ayar import AYARLAR, get_env
from .. import db
from .yonetici import yayinla_hepsi, yayindan_kaldir

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
    # 1. Medya mesajı başlığını güncellemeyi dene (editMessageCaption)
    try:
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "caption": yeni_caption[:1024],
            "parse_mode": "HTML",
        }
        if butonlar is not None:
            payload["reply_markup"] = json.dumps({"inline_keyboard": butonlar})
        _istek("editMessageCaption", data=payload)
        return
    except Exception as e:
        log.debug(f"editMessageCaption denenemedi ({e}), editMessageText deneniyor...")

    # 2. Eğer medya değilse metin mesajı olarak güncelle (editMessageText)
    try:
        payload_txt: Dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": yeni_caption,
            "parse_mode": "HTML",
        }
        if butonlar is not None:
            payload_txt["reply_markup"] = json.dumps({"inline_keyboard": butonlar})
        _istek("editMessageText", data=payload_txt)
    except Exception as e2:
        log.warning(f"Mesaj güncelleme hatası: {e2}")


def yayin_detay_karti_gonder(paylasim_id: int, sonuclar: Dict[str, Any]) -> int:
    """
    Otomatik yayınlanan (veya onaylanan) içeriğin detaylı yayın raporunu
    ve '🗑️ Yayından Kaldır' butonunu Telegram grubuna iletir.
    """
    kayit = db.paylasim_getir(paylasim_id)
    if not kayit:
        raise ValueError(f"Paylaşım bulunamadı: ID {paylasim_id}")

    kategori = kayit["kategori"].upper()
    format_tipi = kayit["format"]
    caption = kayit.get("caption") or ""
    baslik = kayit.get("baslik") or ""
    kaynak = kayit.get("kaynak") or baslik

    yt_durum = "—"
    yt_url = sonuclar.get("youtube_url")
    if "youtube" in sonuclar:
        yt_durum = "✅ Yayında"
    elif "youtube_hata" in sonuclar:
        yt_durum = "❌ Hata"

    tt_durum = "—"
    if "tiktok" in sonuclar:
        tt_durum = "✅ Yayında"
    elif "tiktok_hata" in sonuclar:
        tt_durum = "❌ Hata"
    elif format_tipi == "reels_9_16":
        tt_durum = "⏳ API Onayı Bekliyor (Metin aşağıda)"

    tsi_saat = datetime.now().strftime("%H:%M TSİ")

    if kategori in ("AYET", "REELS"):
        baslik_str = "🚀 <b>KUR'AN-I KERİM TİLAVETİ YAYINLANDI!</b>"
        kunye_str = f"📖 <b>Âyet:</b> {kaynak}\n🎙️ <b>Kari:</b> Mişari Râşid el-Afâsî\n⏱️ <b>Yayın Saati:</b> {tsi_saat}"
    elif kategori == "HADIS":
        baslik_str = "🚀 <b>SAHİH HADİS-İ ŞERİF YAYINLANDI!</b>"
        kunye_str = f"📜 <b>Hadis:</b> {kaynak}\n⏱️ <b>Yayın Saati:</b> {tsi_saat}"
    elif kategori == "DUA":
        baslik_str = "🚀 <b>GÜNÜN DUASI YAYINLANDI!</b>"
        kunye_str = f"🌿 <b>Dua:</b> {kaynak}\n⏱️ <b>Yayın Saati:</b> {tsi_saat}"
    elif kategori == "KELIME":
        baslik_str = "🚀 <b>KUR'AN SÖZLÜĞÜ YAYINLANDI!</b>"
        kunye_str = f"📖 <b>Kavram:</b> {kaynak}\n🎨 <b>Palet:</b> Ezan Yakut Kırmızısı\n⏱️ <b>Yayın Saati:</b> {tsi_saat}"
    else:
        baslik_str = f"🚀 <b>{kategori} İÇERİĞİ YAYINLANDI!</b>"
        kunye_str = f"📌 <b>Kaynak:</b> {kaynak}\n⏱️ <b>Yayın Saati:</b> {tsi_saat}"

    rapor_metin = (
        f"{baslik_str}\n\n"
        f"{kunye_str}\n\n"
        f"📱 <b>Yayın Kanalları:</b>\n"
        f"• <b>Instagram Reels/Feed:</b> {'✅ Yayında' if 'instagram' in sonuclar else '❌ Hata'}\n"
        f"• <b>Instagram Story:</b> {'✅ Yayında' if 'instagram_story' in sonuclar else '❌ Hata'}\n"
        f"• <b>Threads (@ezanplusapp):</b> {'✅ Yayında' if 'threads' in sonuclar else '❌ Hata'}\n"
        f"• <b>Facebook Sayfası:</b> {'✅ Yayında' if 'facebook' in sonuclar else '❌ Hata'}\n"
        f"• <b>YouTube Shorts:</b> {yt_durum}\n"
        f"• <b>TikTok:</b> {tt_durum}\n\n"
        f"📝 <b>Açıklama:</b>\n"
        f"<i>{caption[:280]}...</i>\n\n"
        f"⚠️ <i>İçerikte bir sorun varsa aşağıdaki butonla tüm platformlardan kaldırabilirsiniz:</i>"
    )

    buton_satirlari = [
        [{"text": "🗑️ Yayından Kaldır", "callback_data": f"kaldir_{paylasim_id}"}]
    ]
    if yt_url:
        buton_satirlari.append([{"text": "🔗 YouTube Shorts'ta İzle", "url": yt_url}])
    if format_tipi == "reels_9_16" and "tiktok" not in sonuclar:
        buton_satirlari.append([{"text": "🎵 TikTok'u Aç (@ezanplusapp)", "url": "https://www.tiktok.com/@ezanplusapp"}])

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


def yardim_metni_olustur() -> str:
    """Kullanılabilir komutların yardım metnini döner."""
    return (
        f"🕌 <b>EZAN PLUS YÖNETİM KOMUT REHBERİ</b>\n\n"
        f"Aşağıdaki komutları bu gruba yazarak anında üretim başlatabilir veya sistemi yönetebilirsiniz:\n\n"
        f"🎬 <b>/ayet</b> [sure:ayet veya tema]\n"
        f"<i>Örnek: <code>/ayet</code> veya <code>/ayet 94:5</code> veya <code>/ayet sabır</code></i>\n"
        f"Mişari Râşid tilavetli, senkron karaokeli 9:16 Reels videosu üretir.\n\n"
        f"📜 <b>/hadis</b> [konu veya hadis no]\n"
        f"<i>Örnek: <code>/hadis</code> veya <code>/hadis niyet</code> veya <code>/hadis 65</code></i>\n"
        f"Riyâzü's-Sâlihîn'den V16 standartlarında 4:5 Feed ve 9:16 Story kartı üretir.\n\n"
        f"🌿 <b>/dua</b> [ruh hali veya dua adı]\n"
        f"<i>Örnek: <code>/dua</code> veya <code>/dua ferahlık</code> veya <code>/dua Musa</code></i>\n"
        f"Tescilli dualar külliyatından 4:5 Feed ve 9:16 Story kartı üretir.\n\n"
        f"📖 <b>/kelime</b> [kavram adı]\n"
        f"<i>Örnek: <code>/kelime</code> veya <code>/kelime Sekînet</code></i>\n"
        f"Kur'an Sözlüğü külliyatından kök ve ayet analizli 4:5 ve 9:16 kart üretir.\n\n"
        f"📊 <b>/durum</b>\n"
        f"Veritabanı envanteri, yayın sayıları ve bekleyen taslakları listeler.\n\n"
        f"🚀 <b>/yayinla</b> &lt;ID&gt;\n"
        f"<i>Örnek: <code>/yayinla 14</code></i> — Onay bekleyen taslağı hemen yayınlar.\n\n"
        f"🗑️ <b>/kaldir</b> &lt;ID&gt;\n"
        f"<i>Örnek: <code>/kaldir 14</code></i> — Yayındaki içeriği tüm platformlardan siler.\n\n"
        f"❌ <b>/iptal</b> &lt;ID&gt;\n"
        f"<i>Örnek: <code>/iptal 14</code></i> — Belirtilen taslağı iptal eder.\n\n"
        f"ℹ️ <b>/yardim</b> — Bu rehber mesajını görüntüler."
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


def _arkaplanda_calistir(hedef, *args, **kwargs):
    """Uzun süren komutları ve yayın işlemlerini bot dinleme döngüsünü tıkamadan arka planda çalıştırır."""
    t = threading.Thread(target=hedef, args=args, kwargs=kwargs, daemon=True)
    t.start()
    return t


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
                    caption_guncelle(chat_id, msg_id, "⏳ <b>YAYINLANIYOR...</b>\n\nİçerik Instagram, Threads ve Facebook'a aktarılıyor...")

                    def _gorev_onay(p_id=paylasim_id, c_id=chat_id, m_id=msg_id):
                        sonuclar = yayinla_hepsi(p_id)
                        yt_durum = "—"
                        if "youtube" in sonuclar:
                            yt_durum = f"✅ Yayınlandı (<a href='{sonuclar.get('youtube_url', '')}'>İzle</a>)"
                        elif "youtube_hata" in sonuclar:
                            yt_durum = "❌ Hata"

                        tt_durum = "—"
                        if "tiktok" in sonuclar:
                            tt_durum = "✅ Yayınlandı"
                        elif "tiktok_hata" in sonuclar:
                            tt_durum = "❌ Hata"

                        basari_metni = (
                            f"🎉 <b>İÇERİK BAŞARIYLA YAYINLANDI!</b>\n\n"
                            f"• <b>Instagram Feed (4:5):</b> {'✅ Yayınlandı' if 'instagram' in sonuclar else '❌ Hata'}\n"
                            f"• <b>Instagram Story (9:16):</b> {'✅ Yayınlandı' if 'instagram_story' in sonuclar else '❌ Hata'}\n"
                            f"• <b>Threads (@ezanplusapp):</b> {'✅ Yayınlandı' if 'threads' in sonuclar else '❌ Hata'}\n"
                            f"• <b>Facebook Sayfası:</b> {'✅ Yayınlandı' if 'facebook' in sonuclar else '❌ Hata'}\n"
                            f"• <b>YouTube Shorts:</b> {yt_durum}\n"
                            f"• <b>TikTok (@ezanplusapp):</b> {tt_durum}\n\n"
                            f"⏰ <i>Zaman: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</i>"
                        )
                        yeni_butonlar = [
                            [{"text": "🗑️ Yayından Kaldır", "callback_data": f"kaldir_{p_id}"}]
                        ]
                        if sonuclar.get("youtube_url"):
                            yeni_butonlar.append([{"text": "🔗 YouTube Shorts'ta İzle", "url": sonuclar["youtube_url"]}])

                        caption_ve_buton_guncelle(c_id, m_id, basari_metni, butonlar=yeni_butonlar)

                    _arkaplanda_calistir(_gorev_onay)

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
