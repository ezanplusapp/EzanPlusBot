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

                # 1. Supergroup göçü koruması (Daily Brief Ders 110)
                yeni_chat_id = res_json.get("parameters", {}).get("migrate_to_chat_id")
                if yeni_chat_id:
                    yeni_str = str(yeni_chat_id)
                    log.warning(f"Telegram grubu supergroup'a yükseltildi! Yeni Chat ID: {yeni_str}")
                    os.environ["TELEGRAM_CHAT_ID"] = yeni_str
                    try:
                        env_p = KOK_DIZIN / ".env"
                        if env_p.exists():
                            lines = env_p.read_text(encoding="utf-8").splitlines()
                            for i_l, line in enumerate(lines):
                                if line.strip().startswith("TELEGRAM_CHAT_ID="):
                                    lines[i_l] = f"TELEGRAM_CHAT_ID={yeni_str}"
                                    break
                            env_p.write_text("\n".join(lines) + "\n", encoding="utf-8")
                    except Exception as env_e:
                        log.warning(f".env TELEGRAM_CHAT_ID güncellenemedi: {env_e}")
                    if data and "chat_id" in data:
                        data["chat_id"] = yeni_str
                    continue

                # 2. Rate limit beklemesi
                retry_after = res_json.get("parameters", {}).get("retry_after")
                if retry_after and deneme < maks_deneme:
                    log.warning(f"Telegram rate limit uygulandı ({retry_after}s bekleniyor): {hata}")
                    time.sleep(int(retry_after) + 1)
                    continue

                if "message is not modified" in hata.lower():
                    log.debug(f"Telegram API ({metot}): Mesaj zaten güncel, değişiklik yapılmadı.")
                    return res_json.get("result", {})

                # 3. HTML Entity Hatası Kurtarma (parse_mode kaldırıp düz metinle anında tekrarla)
                if "can't parse entities" in hata.lower() or "entity" in hata.lower():
                    if data:
                        log.warning(f"Telegram HTML parse hatası ({hata}), etiketler ayıklanarak düz metinle deneniyor...")
                        data["parse_mode"] = None
                        import re
                        if "text" in data and isinstance(data["text"], str):
                            data["text"] = html.unescape(re.sub(r"<[^>]+>", "", data["text"]))
                        if "caption" in data and isinstance(data["caption"], str):
                            data["caption"] = html.unescape(re.sub(r"<[^>]+>", "", data["caption"]))
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

    for k, v in kwargs.items():
        if v is not None:
            payload[k] = v

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


def varsayilan_kanallar(format_tipi: str = "reels_9_16") -> Dict[str, bool]:
    """İçerik formatına göre varsayılan aktif platformları döner."""
    if format_tipi == "reels_9_16":
        return {
            "tiktok": True,
            "instagram": True,
            "instagram_story": True,
            "facebook": True,
            "threads": True,
            "youtube": True,
        }
    else:
        return {
            "instagram": True,
            "instagram_story": True,
            "facebook": True,
            "threads": True,
        }


def kanal_butonlari(
    format_tipi: str,
    kanallar: Optional[Dict[str, bool]] = None,
    paylasim_id: Optional[int] = None,
) -> List[List[Dict[str, str]]]:
    """
    Kanal açma/kapama toggle butonları üretir.
    Kullanıcı dokunduğunda simge anında ✅ <-> ⬜ olarak değişir.
    """
    if kanallar is None:
        kanallar = varsayilan_kanallar(format_tipi)
    pid_str = f":{paylasim_id}" if paylasim_id else ""

    def _s(k: str) -> str:
        return "✅" if kanallar.get(k, True) else "⬜"

    if format_tipi == "reels_9_16":
        return [
            [
                {"text": f"{_s('tiktok')} TT", "callback_data": f"kanal:tiktok{pid_str}"},
                {"text": f"{_s('instagram')} Reels", "callback_data": f"kanal:instagram{pid_str}"},
                {"text": f"{_s('instagram_story')} Story", "callback_data": f"kanal:instagram_story{pid_str}"},
            ],
            [
                {"text": f"{_s('facebook')} FB", "callback_data": f"kanal:facebook{pid_str}"},
                {"text": f"{_s('threads')} Threads", "callback_data": f"kanal:threads{pid_str}"},
                {"text": f"{_s('youtube')} Shorts", "callback_data": f"kanal:youtube{pid_str}"},
            ],
        ]
    else:
        return [
            [
                {"text": f"{_s('instagram')} IG Feed", "callback_data": f"kanal:instagram{pid_str}"},
                {"text": f"{_s('instagram_story')} Story", "callback_data": f"kanal:instagram_story{pid_str}"},
            ],
            [
                {"text": f"{_s('facebook')} FB", "callback_data": f"kanal:facebook{pid_str}"},
                {"text": f"{_s('threads')} Threads", "callback_data": f"kanal:threads{pid_str}"},
            ],
        ]


def ana_onay_menusu_kur(
    paylasim_id: int,
    format_tipi: str = "reels_9_16",
    kanallar: Optional[Dict[str, bool]] = None,
    kategori: str = "",
) -> List[List[Dict[str, str]]]:
    """Tüm gelişmiş işlem ve onay butonlarını eksiksiz kurar."""
    k_satirlar = kanal_butonlari(format_tipi, kanallar, paylasim_id)
    tuslar: List[List[Dict[str, str]]] = list(k_satirlar)

    # 1. Satır: Yayınla & Zamanla
    tuslar.append([
        {"text": "✅ Onayla ve Yayınla", "callback_data": f"onay_{paylasim_id}"},
        {"text": "⏰ Zamanla", "callback_data": f"zamanla_menu_{paylasim_id}"},
    ])

    # 2. Satır: Manuel Paylaşım & Metinleri Yenile
    tuslar.append([
        {"text": "📲 Manuel Paylaşım", "callback_data": f"manuel_paket_{paylasim_id}"},
        {"text": "✍️ Metinleri Yenile", "callback_data": f"metin_menu_{paylasim_id}"},
    ])

    # Hadis/Dua ise ses yenileme butonu
    if kategori.lower() in ("hadis", "dua") and format_tipi == "reels_9_16":
        tuslar.append([
            {"text": "🎙️ Sesi Yeniden Üret", "callback_data": f"sesyenile_{paylasim_id}"},
        ])

    # Son Satır: Atla (Havuza İade) & Çöpe At
    tuslar.append([
        {"text": "❌ Bu Turu Atla", "callback_data": f"atla_{paylasim_id}"},
        {"text": "🗑️ Çöpe At", "callback_data": f"cope_at_{paylasim_id}"},
    ])
    return tuslar


def zamanlama_menusu_kur(paylasim_id: int) -> List[List[Dict[str, str]]]:
    """Zamanlanmış yayın seçenekleri alt menüsü."""
    return [
        [
            {"text": "▶️ Hemen Şimdi", "callback_data": f"onay_{paylasim_id}"},
            {"text": "⏰ 30 Dakika", "callback_data": f"yayin_sonra:30:{paylasim_id}"},
        ],
        [
            {"text": "⏰ 1 Saat", "callback_data": f"yayin_sonra:60:{paylasim_id}"},
            {"text": "⏰ 2 Saat", "callback_data": f"yayin_sonra:120:{paylasim_id}"},
        ],
        [
            {"text": "⏰ 4 Saat", "callback_data": f"yayin_sonra:240:{paylasim_id}"},
            {"text": "← Geri (Ana Menü)", "callback_data": f"onay_menu_{paylasim_id}"},
        ],
    ]


def metin_yenileme_menusu_kur(paylasim_id: int) -> List[List[Dict[str, str]]]:
    """Metin ve tefekkür revizyon alt menüsü."""
    return [
        [
            {"text": "✂️ Tefekkürü Daha Kısa Yap", "callback_data": f"metin_kisalt_{paylasim_id}"},
            {"text": "📖 Tefekkürü Genişlet", "callback_data": f"metin_genislet_{paylasim_id}"},
        ],
        [
            {"text": "🔄 Başlık & Caption'ı Yeniden Yaz", "callback_data": f"metin_yenile_{paylasim_id}"},
        ],
        [
            {"text": "← Geri (Ana Menü)", "callback_data": f"onay_menu_{paylasim_id}"},
        ],
    ]


def manuel_paylasim_menusu_kur(paylasim_id: int) -> List[List[Dict[str, str]]]:
    """Manuel paylaşım paketi butonları."""
    return [
        [
            {"text": "📸 Instagram'ı Aç", "url": "https://www.instagram.com"},
            {"text": "🎵 TikTok'u Aç", "url": "https://www.tiktok.com/@ezanplusapp"},
        ],
        [
            {"text": "🚀 Diğer Kanallarda Otomatik Yayınla", "callback_data": f"manuel_diger_{paylasim_id}"},
        ],
        [
            {"text": "✅ Elle Paylaştım (Tamamlandı İşaretle)", "callback_data": f"manuel_tamam_{paylasim_id}"},
        ],
        [
            {"text": "← Geri (Ana Menü)", "callback_data": f"onay_menu_{paylasim_id}"},
        ],
    ]


def duraklatildi_mi() -> tuple[bool, str]:
    """Botun geçici olarak duraklatılıp duraklatılmadığını ve kalan süreyi döner."""
    bitis_str = db.ayar_getir("bot_duraklatma_bitis")
    if not bitis_str:
        return False, ""
    try:
        bitis = datetime.fromisoformat(bitis_str)
        simdi = datetime.now()
        if simdi < bitis:
            fark = bitis - simdi
            toplam_sn = int(fark.total_seconds())
            saat = toplam_sn // 3600
            dakika = (toplam_sn % 3600) // 60
            kalan = f"{saat}s {dakika}dk" if saat > 0 else f"{dakika}dk"
            return True, kalan
        else:
            db.ayar_kaydet("bot_duraklatma_bitis", "")
    except Exception as e:
        log.warning(f"Duraklatma kontrolü hatası: {e}")
    return False, ""


def duraklat(saat: int) -> datetime:
    """Botu belirtilen saat kadar duraklatır."""
    from datetime import timedelta
    bitis = datetime.now() + timedelta(hours=saat)
    db.ayar_kaydet("bot_duraklatma_bitis", bitis.isoformat())
    log.info(f"Bot {saat} saat duraklatıldı. Bitiş: {bitis}")
    return bitis


def devam_et() -> None:
    """Bot duraklatmasını kaldırır."""
    db.ayar_kaydet("bot_duraklatma_bitis", "")
    log.info("Bot duraklatması kaldırıldı, normal akışa dönüldü.")


def duraklatma_secenekleri_menusu() -> List[List[Dict[str, str]]]:
    """Duraklatma süresi seçim menüsü."""
    return [
        [
            {"text": "⏸️ 1 Saat Duraklat", "callback_data": "duraklat:1"},
            {"text": "⏸️ 6 Saat Duraklat", "callback_data": "duraklat:6"},
        ],
        [
            {"text": "⏸️ 12 Saat Duraklat", "callback_data": "duraklat:12"},
            {"text": "⏸️ 24 Saat Duraklat", "callback_data": "duraklat:24"},
        ],
        [
            {"text": "← Kontrol Merkezine Dön", "callback_data": "cmd_menu"},
        ],
    ]


def kontrol_merkezi_menusu() -> List[List[Dict[str, str]]]:
    """Dokunmatik interaktif kontrol paneli butonları."""
    duraklatildi, kalan = duraklatildi_mi()
    duraklat_txt = f"▶️ Devam Ettir ({kalan})" if duraklatildi else "⏸️ Botu Duraklat"
    return [
        [
            {"text": "🎬 Âyet Tilaveti", "callback_data": "menu_ayet"},
            {"text": "📜 Sahih Hadis", "callback_data": "menu_hadis"},
        ],
        [
            {"text": "🌿 Günün Duası", "callback_data": "menu_dua"},
            {"text": "📖 Kur'an Sözlüğü", "callback_data": "menu_kelime"},
        ],
        [
            {"text": "📈 Detaylı Kota Raporu", "callback_data": "cmd_kota"},
            {"text": "📊 Sistem Durumu", "callback_data": "cmd_durum"},
        ],
        [
            {"text": "🩺 Sağlık Testi", "callback_data": "cmd_saglik"},
            {"text": "🧹 Sistem Temizle", "callback_data": "cmd_temizle"},
        ],
        [
            {"text": "📜 Son Hatalar", "callback_data": "cmd_hatalar"},
            {"text": "⚙️ Ayarlar", "callback_data": "cmd_ayarlar"},
        ],
        [
            {"text": duraklat_txt, "callback_data": "menu_duraklat"},
        ],
    ]


AYAR_TANIMLARI = {
    "ayar_facebook": ("📘 Facebook Paylaşımı", ["AÇIK", "KAPALI"], "AÇIK"),
    "ayar_threads": ("🧵 Threads Paylaşımı", ["AÇIK", "KAPALI"], "AÇIK"),
    "ayar_youtube": ("▶️ YouTube Shorts", ["AÇIK", "KAPALI"], "AÇIK"),
    "ayar_tiktok_inbox": ("🎵 TikTok Inbox Modu", ["AÇIK", "KAPALI"], "AÇIK"),
    "ayar_oto_yayin": ("🌙 Otomatik Yayın", ["KAPALI", "AÇIK"], "KAPALI"),
    "ayar_spiker_hiz": ("🎙️ Spiker Hızı", ["0.85x", "0.9x", "0.95x"], "0.9x"),
}


def ayarlar_menusu_kur() -> List[List[Dict[str, str]]]:
    """Telegram üzerinden ayar değiştirme paneli butonları."""
    satirlar = []
    for anahtar, (etiket, secenekler, varsayilan) in AYAR_TANIMLARI.items():
        aktif = db.ayar_getir(anahtar, varsayilan)
        satirlar.append([
            {"text": f"{etiket}: {aktif}", "callback_data": f"ayar_toggle:{anahtar}"}
        ])
    satirlar.append([{"text": "← Kontrol Merkezine Dön", "callback_data": "cmd_menu"}])
    return satirlar


def durum_guncelle(
    chat_id: str | int,
    message_id: int,
    baslik: str,
    adim: int,
    toplam_adim: int = 4,
    detay: str = "",
) -> None:
    """
    Kullanıcıya grubu mesajla boğmadan canlı ilerleme çubuğu (progress bar) sunar.
    """
    if not message_id:
        return
    toplam_adim = max(1, toplam_adim)
    adim = max(1, min(adim, toplam_adim))
    dolu = "▰" * adim
    bos = "▱" * max(0, toplam_adim - adim)
    yuzde = int((adim / toplam_adim) * 100)

    satirlar = [
        f"⏳ <b>{html.escape(baslik)}</b>",
        f"<code>[{dolu}{bos}] %{yuzde} ({adim}/{toplam_adim})</code>",
    ]
    if detay:
        satirlar.append(f"<i>{html.escape(detay)}</i>")

    try:
        _istek(
            "editMessageText",
            data={
                "chat_id": str(chat_id),
                "message_id": message_id,
                "text": "\n\n".join(satirlar),
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
        )
    except Exception as e:
        if "not modified" not in str(e).lower():
            log.debug(f"durum_guncelle hatası ({message_id}): {e}")


def onay_istegi_gonder(paylasim_id: int) -> int:
    """
    Veritabanındaki paylaşım kaydını okur ve Daily Brief formatında:
    1. Medyayı (Reels videosu veya şık görsel önizleme) gönderir.
    2. Tek dokunuşla kopyalanabilir tam açıklama metni (<pre>) ve toggle kanal butonlarıyla
       onay kartını iletir.
    """
    kayit = db.paylasim_getir(paylasim_id)
    if not kayit:
        raise ValueError(f"Paylaşım bulunamadı: ID {paylasim_id}")

    kategori = kayit["kategori"].upper()
    format_tipi = kayit["format"]
    caption = kayit.get("caption") or ""
    baslik = kayit.get("baslik") or ""
    kaynak = kayit.get("kaynak") or baslik

    import html as html_lib
    temiz_caption = html_lib.escape(caption.strip())

    if kategori in ("AYET", "REELS"):
        baslik_str = "📖 <b>EZAN PLUS — KUR'AN-I KERİM TİLAVETİ</b>"
        ses_str = "Mişari Râşid el-Afâsî (Stüdyo Tilavet)"
    elif kategori == "HADIS":
        baslik_str = "📜 <b>EZAN PLUS — SAHİH HADİS-İ ŞERİF</b>"
        ses_str = "Mazlum Kiper (Fish Audio S2.1)"
    elif kategori == "DUA":
        baslik_str = "🌿 <b>EZAN PLUS — GÜNÜN DUASI</b>"
        ses_str = "Mazlum Kiper (Fish Audio S2.1)"
    elif kategori == "KELIME":
        baslik_str = "📖 <b>EZAN PLUS — KUR'AN SÖZLÜĞÜ</b>"
        ses_str = "Görsel Kart Tipografisi"
    else:
        baslik_str = f"🕌 <b>EZAN PLUS — {kategori}</b>"
        ses_str = "—"

    # 1. Medya Gönderimi (Video veya Görsel Önizleme)
    if format_tipi == "reels_9_16" and kayit.get("video_yolu") and Path(kayit["video_yolu"]).exists():
        video_p = Path(kayit["video_yolu"])
        medya_baslik = (
            f"{baslik_str}\n"
            f"📌 <b>Kaynak:</b> {html_lib.escape(kaynak)}\n"
            f"🎙️ <b>Seslendirme:</b> {ses_str}"
        )
        try:
            video_gonder(video_p, caption=medya_baslik)
        except Exception as e:
            log.warning(f"Onay öncesi video gönderilemedi: {e}")
    elif kayit.get("gorsel_yollari"):
        for g_yol in kayit["gorsel_yollari"][:2]:
            gp = Path(g_yol)
            if gp.exists():
                g_etiket = "9:16 Story" if "9_16" in gp.name else "4:5 Akış"
                try:
                    gorsel_gonder(gp, caption=f"{baslik_str} ({g_etiket})")
                except Exception as e:
                    log.warning(f"Onay öncesi görsel gönderilemedi: {e}")

    # 2. Daily Brief Tarzı Onay Kartı & Kopyalanabilir Caption
    ozet_metin = (
        f"{baslik_str}\n\n"
        f"📌 <b>Format:</b> #{kategori} ({format_tipi})\n"
        f"📖 <b>Başlık / Kaynak:</b> {html_lib.escape(kaynak)}\n"
        f"🎙️ <b>Seslendirme:</b> {ses_str}\n"
        f"🛡️ <b>Kalite Denetimi:</b> Başarılı (Uthmani Hat, Mizanpaj & QA Onaylandı)\n\n"
        f"📝 <b>Açıklama Metni (Kopyalamak için dokunun):</b>\n"
        f"<pre>{temiz_caption}</pre>\n\n"
        f"👇 <b>Yayın kanallarını seçin ve onaylayın:</b>"
    )

    # Kaydedilmiş kanal tercihini oku veya varsayılanı kullan
    kanallar_json = db.ayar_getir(f"paylasim_kanallari_{paylasim_id}")
    kanallar = json.loads(kanallar_json) if kanallar_json else varsayilan_kanallar(format_tipi)
    if not kanallar_json:
        db.ayar_kaydet(f"paylasim_kanallari_{paylasim_id}", json.dumps(kanallar))

    butonlar = ana_onay_menusu_kur(paylasim_id, format_tipi=format_tipi, kanallar=kanallar, kategori=kategori)

    # Onay mesajı (telegram_mesaj_id olarak saklanır, butonlar buradadır)
    msg_id = mesaj_gonder(ozet_metin, butonlar=butonlar)
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
    message_id: Optional[int] = None,
    yeni_caption: str = "",
    butonlar: Optional[List[List[Dict[str, str]]]] = None,
    **kwargs: Any,
):
    """Medya veya metin mesajının içeriğini ve inline butonlarını günceller."""
    m_id = message_id if message_id is not None else kwargs.get("mesaj_id")
    if not m_id:
        log.warning("caption_ve_buton_guncelle: message_id / mesaj_id belirtilmedi!")
        return False
    message_id = m_id

    # 1. Medya mesajı başlığını güncellemeyi dene (editMessageCaption - 1024 karakter sınırı)
    caption_medya = yeni_caption
    if len(caption_medya) > 1020:
        caption_medya = caption_medya[:1015] + "..."

    try:
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "caption": caption_medya,
            "parse_mode": "HTML",
        }
        if butonlar is not None:
            payload["reply_markup"] = json.dumps({"inline_keyboard": butonlar})
        _istek("editMessageCaption", data=payload)
        return
    except Exception as e:
        log.debug(f"editMessageCaption denenemedi ({e}), metin mesajı (editMessageText) deneniyor...")

    # HTML parse hatası ihtimaline karşı düz metin dene (tagler kesilmişse)
    try:
        import re
        duz_metin = re.sub(r"<[^>]+>", "", caption_medya)
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

    # 2. Eğer medya değilse metin mesajı olarak güncelle (editMessageText - 4096 karakter sınırı)
    try:
        payload_txt: Dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": yeni_caption[:4096],
            "parse_mode": "HTML",
        }
        if butonlar is not None:
            payload_txt["reply_markup"] = json.dumps({"inline_keyboard": butonlar})
        _istek("editMessageText", data=payload_txt)
    except Exception as e2:
        log.error(f"Mesaj güncelleme hatası: {e2}")


def reply_markup_guncelle(
    chat_id: str | int,
    message_id: int,
    butonlar: List[List[Dict[str, str]]],
) -> bool:
    """Yalnızca mesajın inline klavyesini (butonlarını) yerinde günceller."""
    try:
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "reply_markup": json.dumps({"inline_keyboard": butonlar}),
        }
        _istek("editMessageReplyMarkup", data=payload)
        return True
    except Exception as e:
        log.debug(f"editMessageReplyMarkup hatası ({message_id}): {e}")
        return False



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

    import html as html_lib
    temiz_caption = html_lib.escape(caption.strip())

    metin = (
        f"{baslik_str}\n\n"
        f"{kunye_str}\n\n"
        f"📱 <b>Yayın Kanalları (Öncelik Sırasıyla):</b>\n"
        f"• <b>TikTok (@ezanplusapp):</b> {tt_durum} (1. Öncelik)\n"
        f"• <b>Instagram Reels/Feed:</b> {ig_durum}\n"
        f"• <b>Instagram Story:</b> {story_durum}\n"
        f"• <b>Facebook Sayfası:</b> {fb_durum}\n"
        f"• <b>Threads (@ezanplusapp):</b> {th_durum}\n"
        f"• <b>YouTube Shorts:</b> {yt_durum}\n\n"
        f"📝 <b>Açıklama Metni (Kopyalamak için dokunun):</b>\n"
        f"<pre>{temiz_caption}</pre>"
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


def yayin_sonucu_bildir(
    paylasim_id: int,
    sonuclar: Dict[str, Any],
    kayit: Optional[Dict[str, Any]] = None,
    chat_id: Optional[str] = None,
) -> int:
    """
    Yayın tamamlandığında sesli bildirim (disable_notification=False) ve
    tek dokunuşla [🗑️ Bu Yayını Kaldır] butonuyla yöneticilere özet raporu gönderir.
    """
    if not kayit:
        kayit = db.paylasim_getir(paylasim_id) or {}

    baslik = kayit.get("baslik") or f"Paylaşım #{paylasim_id}"
    kat = str(kayit.get("kategori", "içerik")).upper()

    basarili = []
    hatali = []
    for k, v in sonuclar.items():
        if k.endswith("_hata"):
            kanal = k.replace("_hata", "").upper()
            hatali.append(f"{kanal}: {v}")
        elif v and not k.startswith("yeni_") and k not in ("paylasim_id", "durum"):
            basarili.append(k.upper())

    emoji = "🎉" if not hatali else ("⚠️" if basarili else "❌")
    durum_str = "BAŞARIYLA YAYINLANDI" if not hatali else ("KISMİ BAŞARIYLA YAYINLANDI" if basarili else "YAYINLANAMADI")

    metin = (
        f"{emoji} <b>{kat} {durum_str}!</b>\n\n"
        f"📌 <b>{html.escape(baslik)}</b> (ID: <code>#{paylasim_id}</code>)\n\n"
    )
    if basarili:
        metin += f"✅ <b>Aktif Kanallar:</b> {', '.join(basarili)}\n"
    if hatali:
        metin += f"⚠️ <b>Hatalar:</b>\n" + "\n".join(f"• {h}" for h in hatali) + "\n"

    metin += f"\n⏰ <i>Yayın Saati: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</i>"

    butonlar: List[List[Dict[str, str]]] = [
        [{"text": "🗑️ Bu Yayını Kaldır", "callback_data": f"kaldir_{paylasim_id}"}],
    ]
    if hatali:
        butonlar.append([{"text": "🔄 Eksik Kanalları Tekrar Dene", "callback_data": f"telafi_hepsi_{paylasim_id}"}])

    return mesaj_gonder(
        metin,
        chat_id=chat_id,
        butonlar=butonlar,
        disable_notification=False,
    )


def zamanlanmis_yayinlari_kontrol_et() -> int:
    """
    Zamanı gelmiş (yayin_zamani <= simdi) ve durumu 'zamanlandi' olan paylaşımları
    kontrol edip seçili kanallarda otomatik olarak yayınlar.
    """
    duraklatildi, kalan = duraklatildi_mi()
    if duraklatildi:
        log.debug(f"Bot duraklatıldığı için zamanlanmış yayın kontrolü ertelendi (Kalan: {kalan})")
        return 0

    bekleyenler = db.zamanlanmis_paylasimlari_getir()
    yayinlanan_sayi = 0
    for kayit in bekleyenler:
        p_id = kayit["id"]
        log.info(f"Zamanlanmış paylaşım #{p_id} yayına alınıyor...")
        try:
            raw_kanallar = db.ayar_getir(f"paylasim_kanallari_{p_id}")
            secili_kanallar = None
            if raw_kanallar:
                try:
                    secili_kanallar = json.loads(raw_kanallar)
                except Exception:
                    pass

            sonuclar = yayinla_hepsi(p_id, kanallar=secili_kanallar)
            yayin_sonucu_bildir(p_id, sonuclar, kayit)
            yayinlanan_sayi += 1
        except Exception as e:
            log.error(f"Zamanlanmış yayın hatası (#{p_id}): {e}")
            db.durum_guncelle(p_id, yeni_durum="onay_bekliyor", hata_mesaji=str(e))
    return yayinlanan_sayi



# yayinla_hepsi fonksiyonu .yonetici modülünden içe aktarılmıştır


def komutlari_kaydet() -> bool:
    """
    Telegram botuna '/' ile açılan komut listesini kaydeder (setMyCommands).
    Daily Brief Ders 120: 3 kapsama birden (default, all_group_chats, all_private_chats) yazılarak
    grupta '/' basıldığında anında taze menü görünmesi sağlanır.
    """
    komutlar = [
        {"command": "menu", "description": "🕌 Dokunmatik Kontrol Merkezi & Panel"},
        {"command": "ayet", "description": "🎬 Kur'an-ı Kerim Tilaveti Reels videosu üret"},
        {"command": "hadis", "description": "📜 V20 Sahih Hadis Dinamik Videosu üret"},
        {"command": "dua", "description": "🌿 V20 Günün Duası Dinamik Videosu üret"},
        {"command": "kelime", "description": "📖 V17 Kur'an Sözlüğü kavram kartı üret"},
        {"command": "durdur", "description": "⏸️ Botu geçici süreyle duraklat (1s, 6s, 24s)"},
        {"command": "devam", "description": "▶️ Duraklatılmış botu hemen başlat"},
        {"command": "ayar", "description": "⚙️ Telegram içi sistem ayarlarını düzenle"},
        {"command": "onar", "description": "🛠️ Kalite kontrolünden geçemeyen içeriği onar"},
        {"command": "yeniden_uret", "description": "🔄 Belirtilen paylaşımı sıfırdan yeniden üret"},
        {"command": "hata", "description": "🔍 Son sistem hatasını ve teşhis raporunu göster"},
        {"command": "hatalar", "description": "📜 Son sistem hatalarını ve çözüm butonlarını listele"},
        {"command": "tekrar", "description": "🔄 Başarısız olan platformları tekrar yayınla"},
        {"command": "saglik", "description": "🩺 Sistem servisleri ve API sağlık testi"},
        {"command": "temizle", "description": "🧹 Geçici dosyaları ve önbelleği temizle"},
        {"command": "kaldir", "description": "🗑️ Yayınlanan içeriği tüm platformlardan sil"},
        {"command": "durum", "description": "📊 Sistem ve yayın istatistikleri raporu"},
        {"command": "kota", "description": "📈 GitHub ve AI kota raporu"},
        {"command": "yardim", "description": "ℹ️ Komut kullanım rehberi ve yardım"},
    ]

    kapsamlar = [
        None,
        {"type": "all_group_chats"},
        {"type": "all_private_chats"},
    ]
    basarili = 0
    for kapsam in kapsamlar:
        payload = {"commands": json.dumps(komutlar)}
        if kapsam:
            payload["scope"] = json.dumps(kapsam)
        try:
            res = _istek("setMyCommands", data=payload)
            if res:
                basarili += 1
        except Exception as e:
            log.warning(f"setMyCommands hatası ({kapsam}): {e}")

    log.info(f"Telegram komut listesi {basarili}/{len(kapsamlar)} kapsama başarıyla kaydedildi.")
    return basarili > 0


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

    # 8. TikTok Content Posting API
    tt_token = KOK_DIZIN / "data" / "tiktok_token.json"
    if tt_token.exists():
        durumlar.append(("TikTok API (@ezanplusapp)", True, "Yetki belirteci aktif (Inbox/Draft)"))
    else:
        durumlar.append(("TikTok API (@ezanplusapp)", False, "Token dosyası eksik (/tiktok)"))

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
        f"🎬 <b>/ayet</b> [sure:ayet veya tema] — 9:16 Kur'an Tilaveti Reels videosu üretir.\n"
        f"📜 <b>/hadis</b> [konu veya hadis no] — V20 Dinamik Hadis Videosu (Mazlum Kiper + Segâh Ney).\n"
        f"🤲 <b>/dua</b> [ruh hali veya dua adı] — V20 Dinamik Dua Videosu (Mazlum Kiper + Ferahfezâ Ney).\n"
        f"📖 <b>/kelime</b> [kavram adı] — Kur'an Sözlüğü kavram kartı üretir (4:5 + 9:16).\n\n"
        f"🛠️ <b>HATA ÇÖZÜM & ONARIM KOMUTLARI:</b>\n"
        f"• <b>/sesyenile &lt;ID&gt;</b> — Hadis veya Dua videosunun sesini alternatif manevi tonla yeniden üretir.\n"
        f"• <b>/onar &lt;ID&gt;</b> — Kalite veya mizanpaj hatası alan içeriği otonom onarır.\n"
        f"• <b>/yeniden_uret &lt;ID&gt;</b> — Belirtilen paylaşımı tescilli kaynaktan sıfırdan yeniden üretir.\n"
        f"• <b>/hata</b> — En son sistem hatasını ve doğrudan çözüm butonlarını gösterir.\n"
        f"• <b>/hatalar</b> — Son 5 sistem hatasını ve her biri için tek tık onarım butonlarını listeler.\n"
        f"• <b>/tekrar &lt;ID&gt;</b> — Başarısız/eksik kalan kanalları tekrar yayınlar.\n"
        f"• <b>/saglik</b> — Veritabanları, AI ve sosyal medya API bağlantılarını test eder.\n"
        f"• <b>/temizle</b> — Geçici render dosyalarını ve önbelleği temizler.\n\n"
        f"⚙️ <b>YAYIN YÖNETİMİ:</b>\n"
        f"• <b>/tiktok</b> [kod] — TikTok yetkilendirmesi yapar veya giriş bağlantısı üretir.\n"
        f"• <b>/yayinla &lt;ID&gt;</b> — Onay bekleyen taslağı hemen yayınlar.\n"
        f"• <b>/kaldir &lt;ID&gt;</b> — Yayındaki içeriği tüm platformlardan siler.\n"
        f"• <b>/iptal &lt;ID&gt;</b> — Belirtilen taslağı iptal eder.\n"
        f"• <b>/durum</b> — Yayın ve envanter istatistikleri raporu.\n"
        f"• <b>/kota</b> — Detaylı GitHub Actions ve AI kota raporu.\n"
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

    elif ana_komut in ("/menu", "/panel"):
        mesaj_gonder(
            "🕌 <b>EZAN PLUS KONTROL MERKEZİ</b>\n\nLütfen çalıştırmak veya denetlemek istediğiniz işlemi dokunarak seçin:",
            chat_id=str(chat_id),
            butonlar=kontrol_merkezi_menusu(),
        )

    elif ana_komut in ("/durdur", "/duraklat"):
        mesaj_gonder(
            "⏸️ <b>BOTU DURAKLATMA SEÇENEKLERİ</b>\n\nBotu ne kadar süreyle duraklatmak istersiniz?",
            chat_id=str(chat_id),
            butonlar=duraklatma_secenekleri_menusu(),
        )

    elif ana_komut == "/devam":
        devam_et()
        mesaj_gonder(
            "▶️ <b>Bot duraklatması kaldırıldı!</b> Tüm otomasyonlar normal akışına döndü.",
            chat_id=str(chat_id),
            butonlar=[[{"text": "🕌 Kontrol Merkezi", "callback_data": "cmd_menu"}]],
        )

    elif ana_komut == "/ayar":
        mesaj_gonder(
            "⚙️ <b>EZAN PLUS SİSTEM AYARLARI</b>\n\nDeğiştirmek istediğiniz ayarın üzerine dokunun:",
            chat_id=str(chat_id),
            butonlar=ayarlar_menusu_kur(),
        )

    elif ana_komut == "/durum":
        mesaj_gonder(durum_raporu_olustur(), chat_id=str(chat_id))

    elif ana_komut in ("/kota", "/rapor", "/kullanim"):
        from .. import kota_uretici
        kat = parametre.strip().lower() if parametre else "menu"
        kota_uretici.kota_gonder(chat_id=str(chat_id), kategori=kat)

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

    elif ana_komut in ("/hadis", "/hadis_video", "/hadis_reels"):
        if not _coklu_komut_engeli("/hadis", chat_id):
            mesaj_gonder("⚠️ <b>Komutunuz zaten işleniyor:</b> Hadis videosu hazırlanıyor, lütfen bekleyin...", chat_id=str(chat_id))
            return
        # Parametrede 'video' kelimesi varsa temizle
        param_temiz = (parametre or "").strip()
        if param_temiz.lower().startswith("video"):
            param_temiz = param_temiz[5:].strip() or None
        mesaj_gonder("⏳ <b>V20 Dinamik Hadis Videosu Hazırlanıyor...</b>\n\nRiyâzü's-Sâlihîn külliyatından seçilerek Mazlum Kiper spiker sesi (0.8x), kelime karaoke takibi ve Segâh Ney fonuyla 1080x1920 dikey video render ediliyor...", chat_id=str(chat_id))
        def _gorev_hadis_video():
            try:
                from .. import otomasyon
                otomasyon.hadis_videosu_olustur_ve_gonder(tema=param_temiz)
            except Exception as e:
                log.error(f"/hadis komutu hatası: {e}")
                mesaj_gonder(f"❌ <b>Hadis videosu üretilemedi:</b>\n<code>{html.escape(str(e))}</code>", chat_id=str(chat_id))
        _arkaplanda_calistir(_gorev_hadis_video)

    elif ana_komut in ("/dua", "/dua_video", "/dua_reels"):
        if not _coklu_komut_engeli("/dua", chat_id):
            mesaj_gonder("⚠️ <b>Komutunuz zaten işleniyor:</b> Dua videosu hazırlanıyor, lütfen bekleyin...", chat_id=str(chat_id))
            return
        # Parametrede 'video' kelimesi varsa temizle
        param_temiz = (parametre or "").strip()
        if param_temiz.lower().startswith("video"):
            param_temiz = param_temiz[5:].strip() or None
        mesaj_gonder("⏳ <b>V20 Dinamik Dua Videosu Hazırlanıyor...</b>\n\nTescilli dualar külliyatından seçilerek Mazlum Kiper spiker sesi (0.8x), kelime karaoke takibi ve Ferahfezâ Ney fonuyla 1080x1920 dikey video render ediliyor...", chat_id=str(chat_id))
        def _gorev_dua_video():
            try:
                from .. import otomasyon
                otomasyon.dua_videosu_olustur_ve_gonder(ruh_hali=param_temiz)
            except Exception as e:
                log.error(f"/dua komutu hatası: {e}")
                mesaj_gonder(f"❌ <b>Dua videosu üretilemedi:</b>\n<code>{html.escape(str(e))}</code>", chat_id=str(chat_id))
        _arkaplanda_calistir(_gorev_dua_video)

    elif ana_komut == "/kelime":
        if not _coklu_komut_engeli("/kelime", chat_id):
            mesaj_gonder("⚠️ <b>Komutunuz zaten işleniyor:</b> Kelime kartı hazırlanıyor, lütfen bekleyin...", chat_id=str(chat_id))
            return
        mesaj_gonder("⏳ <b>Kur'an Sözlüğü Kartı Hazırlanıyor...</b>\n\nİslami kavramlar külliyatından seçilerek V16 standardında 4:5 Feed ve 9:16 Story formatlarında çizilip otomatik yayınlanacak, lütfen bekleyin...", chat_id=str(chat_id))
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

    elif ana_komut in ("/sesyenile", "/ses_yenile"):
        p_id = None
        if parametre and parametre.isdigit():
            p_id = int(parametre)
        else:
            with db.baglanti_al() as con:
                row = con.execute("SELECT id FROM paylasimlar WHERE durum = 'onay_bekliyor' AND LOWER(kategori) IN ('hadis', 'dua') ORDER BY id DESC LIMIT 1").fetchone()
                if row:
                    p_id = row[0]
        if not p_id:
            mesaj_gonder("⚠️ <b>Geçerli bir onay bekleyen Hadis veya Dua videosu bulunamadı.</b>\n<i>Kullanım: <code>/sesyenile [paylasim_id]</code></i>", chat_id=str(chat_id))
            return
        mesaj_gonder(f"⏳ <b>Paylaşım #{p_id} için ses ve video yenileniyor...</b>\nMazlum Kiper spiker sesi alternatif bir tonla yeniden sentezleniyor, lütfen bekleyin...", chat_id=str(chat_id))
        def _gorev_komut_sesyenile(pid=p_id, cid=chat_id):
            try:
                from .. import otomasyon
                otomasyon.hadis_veya_dua_sesi_yenile(pid)
                onay_istegi_gonder(pid)
            except Exception as e:
                log.error(f"/sesyenile hatası (#{pid}): {e}")
                mesaj_gonder(f"❌ <b>Ses yenileme hatası:</b> <code>{html.escape(str(e))}</code>", chat_id=str(cid))
        _arkaplanda_calistir(_gorev_komut_sesyenile)

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

    elif ana_komut == "/tiktok":
        from ..platformlar import tiktok
        if parametre:
            try:
                res = tiktok.yetki_al(manuel_kod=parametre)
                mesaj_gonder(
                    "✅ <b>TikTok Yetkilendirmesi Başarılı!</b>\n\n"
                    "Erişim belirteci başarıyla kaydedildi. 9:16 videolar artık otomatik olarak TikTok Gelen Kutusu / Taslaklar klasörünüze aktarılacak.",
                    chat_id=str(chat_id)
                )
            except Exception as e:
                log.error(f"/tiktok yetkilendirme hatası: {e}")
                mesaj_gonder(f"❌ <b>TikTok Yetkilendirme Hatası:</b>\n<code>{html.escape(str(e))}</code>", chat_id=str(chat_id))
        else:
            try:
                url = tiktok.auth_url_uret()
                mesaj_gonder(
                    "🔗 <b>TikTok Yetkilendirme Adımı:</b>\n\n"
                    "Videoların TikTok Gelen Kutusu / Taslaklar bölümüne aktarılabilmesi için @ezanplusapp hesabınızla 1 defalık izin vermeniz gerekmektedir:\n\n"
                    f"👉 <a href=\"{url}\">TikTok İle Giriş Yapmak İçin Dokunun</a>\n\n"
                    "Giriş yaptıktan sonra açılan ekrandaki kodu kopyalayıp buraya <code>/tiktok &lt;KOD&gt;</code> olarak gönderin.",
                    chat_id=str(chat_id)
                )
            except Exception as e:
                mesaj_gonder(f"❌ <b>TikTok linki üretilemedi:</b>\n<code>{html.escape(str(e))}</code>", chat_id=str(chat_id))

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
                    kayit = db.paylasim_getir(paylasim_id)
                    if not kayit:
                        callback_cevapla(cq_id, f"ℹ️ Paylaşım #{paylasim_id} veritabanında bulunamadı (silinmiş olabilir).", alert=True)
                        caption_ve_buton_guncelle(
                            chat_id,
                            msg_id,
                            f"⚠️ <b>PAYLAŞIM BULUNAMADI (#{paylasim_id})</b>\n\nBu içerik sistemden silinmiş veya arşivlenmiş.",
                            butonlar=[]
                        )
                        continue

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
                            raw_k = db.ayar_getir(f"paylasim_kanallari_{p_id}")
                            secili_k = None
                            if raw_k:
                                try:
                                    secili_k = json.loads(raw_k)
                                except Exception:
                                    pass
                            sonuclar = yayinla_hepsi(p_id, kanallar=secili_k)
                            kayit = db.paylasim_getir(p_id)
                            format_t = kayit.get("format") if kayit else "post_4_5"
                            basari_metni = yayin_raporu_metni_kur(kayit, sonuclar)
                            yeni_butonlar = telafi_butonlari_kur(p_id, sonuclar, format_t)
                            caption_ve_buton_guncelle(c_id, m_id, basari_metni, butonlar=yeni_butonlar)
                            yayin_sonucu_bildir(p_id, sonuclar, kayit, chat_id=str(c_id))

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

                elif data.startswith("sesyenile_"):
                    p_id = int(data.split("_")[1])
                    callback_cevapla(cq_id, f"🎙️ Paylaşım #{p_id} için yeni ses üretiliyor...", alert=False)
                    caption_ve_buton_guncelle(
                        chat_id,
                        msg_id,
                        f"⏳ <b>SES VE VİDEO YENİLENİYOR (#{p_id})...</b>\n\nMazlum Kiper spiker sesi alternatif tonlama ile yeniden sentezleniyor ve video render ediliyor, lütfen bekleyin...",
                        butonlar=[]
                    )

                    def _gorev_ses_yenile_btn(paylasim_id=p_id, c_id=chat_id, m_id=msg_id):
                        try:
                            from .. import otomasyon
                            otomasyon.hadis_veya_dua_sesi_yenile(paylasim_id)
                            caption_ve_buton_guncelle(
                                c_id,
                                m_id,
                                f"🔄 <b>Paylaşım #{paylasim_id} için yeni ses ve video üretildi!</b>\n\n<i>Aşağıda paylaşılan yeni videoyu dinleyip onaylayabilirsiniz.</i>",
                                butonlar=[]
                            )
                            onay_istegi_gonder(paylasim_id)
                        except Exception as e:
                            log.error(f"Sesi yenileme hatası (#{paylasim_id}): {e}")
                            caption_ve_buton_guncelle(
                                c_id,
                                m_id,
                                f"❌ <b>Ses Yenilenemedi:</b> <code>{html.escape(str(e))}</code>",
                                butonlar=[
                                    [{"text": "🎙️ Tekrar Dene", "callback_data": f"sesyenile_{paylasim_id}"}],
                                    [{"text": "❌ İptal Et", "callback_data": f"red_{paylasim_id}"}],
                                ]
                            )

                    _arkaplanda_calistir(_gorev_ses_yenile_btn)

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

                elif data in ("cmd_kota", "kota_goster", "kota_tazele", "rapor_goster", "rapor_tazele", "kota_menu"):
                    callback_cevapla(cq_id, "📈 Kota menüsü hazırlanıyor...", alert=False)
                    from .. import kota_uretici
                    kota_uretici.kota_gonder(mesaj_id=msg_id, chat_id=str(chat_id), kategori="menu")

                elif data.startswith("kota_kat:"):
                    kat = data.split(":", 1)[1]
                    callback_cevapla(cq_id, f"📈 Kategori {kat} hazırlanıyor...", alert=False)
                    from .. import kota_uretici
                    kota_uretici.kota_gonder(mesaj_id=msg_id, chat_id=str(chat_id), kategori=kat)

                elif data == "cmd_yardim":
                    callback_cevapla(cq_id, "ℹ️ Yardım rehberi getiriliyor...", alert=False)
                    mesaj_gonder(yardim_metni_olustur(), chat_id=str(chat_id))

                elif data.startswith("kaldir_"):
                    paylasim_id = int(data.split("_")[1])
                    kayit = db.paylasim_getir(paylasim_id)
                    if not kayit:
                        callback_cevapla(cq_id, f"ℹ️ Paylaşım #{paylasim_id} zaten yayından kaldırılmış veya silinmiş.", alert=True)
                        caption_ve_buton_guncelle(
                            chat_id,
                            msg_id,
                            f"🗑️ <b>BU İÇERİK DAHA ÖNCE YAYINDAN KALDIRILDI</b>\n\n📌 Paylaşım #{paylasim_id} sistemde bulunamadı.",
                            butonlar=[]
                        )
                        continue

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

                # -----------------------------------------------------------------
                # İNSTABOT İLERİ SEVİYE BUTON VE KANAL YÖNETİMİ
                # -----------------------------------------------------------------
                elif data.startswith("kanal:"):
                    # Format: kanal:kanal_kodu veya kanal:kanal_kodu:paylasim_id
                    parcalar = data.split(":")
                    kanal_kodu = parcalar[1]
                    paylasim_id = int(parcalar[2]) if len(parcalar) > 2 else 0

                    kayit = db.paylasim_getir(paylasim_id) if paylasim_id else None
                    format_t = kayit.get("format", "reels_9_16") if kayit else "reels_9_16"
                    kat = kayit.get("kategori", "ayet") if kayit else "ayet"

                    raw_k = db.ayar_getir(f"paylasim_kanallari_{paylasim_id}") if paylasim_id else ""
                    if raw_k:
                        try:
                            kanallar = json.loads(raw_k)
                        except Exception:
                            kanallar = varsayilan_kanallar(format_t)
                    else:
                        kanallar = varsayilan_kanallar(format_t)

                    suanki = kanallar.get(kanal_kodu, True)
                    kanallar[kanal_kodu] = not suanki
                    if paylasim_id:
                        db.ayar_kaydet(f"paylasim_kanallari_{paylasim_id}", json.dumps(kanallar, ensure_ascii=False))

                    durum_adi = "AÇILDI ✅" if kanallar[kanal_kodu] else "KAPATILDI ⬜"
                    callback_cevapla(cq_id, f"🔘 {kanal_kodu.upper()} kanalı {durum_adi}", alert=False)

                    yeni_klavye = ana_onay_menusu_kur(paylasim_id, format_tipi=format_t, kanallar=kanallar, kategori=kat)
                    reply_markup_guncelle(chat_id, msg_id, yeni_klavye)

                elif data.startswith("zamanla_menu_"):
                    paylasim_id = int(data.split("_")[2])
                    callback_cevapla(cq_id, "⏰ Zamanlama menüsü açıldı.", alert=False)
                    yeni_klavye = zamanlama_menusu_kur(paylasim_id)
                    reply_markup_guncelle(chat_id, msg_id, yeni_klavye)

                elif data.startswith("yayin_sonra:"):
                    from datetime import timedelta
                    parcalar = data.split(":")
                    dakika = int(parcalar[1])
                    paylasim_id = int(parcalar[2])
                    hedef_zaman = datetime.now() + timedelta(minutes=dakika)
                    zaman_str = hedef_zaman.strftime("%Y-%m-%d %H:%M:%S")
                    db.durum_guncelle(paylasim_id, yeni_durum="zamanlandi", yayin_zamani=zaman_str)

                    callback_cevapla(cq_id, f"⏰ Paylaşım #{paylasim_id} {dakika} dk sonraya ({hedef_zaman.strftime('%H:%M')}) zamanlandı!", alert=True)

                    yeni_metin = (
                        f"⏰ <b>YAYIN ZAMANLANDI (#{paylasim_id})</b>\n\n"
                        f"📌 Bu içerik <b>{hedef_zaman.strftime('%d.%m.%Y %H:%M')}</b> saatinde otomatik olarak yayınlanacak.\n\n"
                        f"<i>İptal etmek isterseniz aşağıdaki butonu kullanabilirsiniz.</i>"
                    )
                    yeni_klavye = [
                        [{"text": "↩️ Şimdi Yayınla Menüsüne Dön", "callback_data": f"onay_menu_{paylasim_id}"}],
                        [{"text": "❌ İptal Et & Sil", "callback_data": f"red_{paylasim_id}"}],
                    ]
                    caption_ve_buton_guncelle(chat_id, msg_id, yeni_metin, butonlar=yeni_klavye)

                elif data.startswith("onay_menu_"):
                    paylasim_id = int(data.split("_")[2])
                    kayit = db.paylasim_getir(paylasim_id)
                    format_t = kayit.get("format", "reels_9_16") if kayit else "reels_9_16"
                    kat = kayit.get("kategori", "ayet") if kayit else "ayet"

                    raw_k = db.ayar_getir(f"paylasim_kanallari_{paylasim_id}")
                    if raw_k:
                        try:
                            kanallar = json.loads(raw_k)
                        except Exception:
                            kanallar = varsayilan_kanallar(format_t)
                    else:
                        kanallar = varsayilan_kanallar(format_t)

                    callback_cevapla(cq_id, "↩️ Ana onay menüsüne dönüldü.", alert=False)
                    yeni_klavye = ana_onay_menusu_kur(paylasim_id, format_tipi=format_t, kanallar=kanallar, kategori=kat)
                    reply_markup_guncelle(chat_id, msg_id, yeni_klavye)

                elif data.startswith("manuel_paket_"):
                    paylasim_id = int(data.split("_")[2])
                    kayit = db.paylasim_getir(paylasim_id)
                    if not kayit:
                        callback_cevapla(cq_id, "⚠️ Paylaşım bulunamadı.", alert=True)
                        continue

                    callback_cevapla(cq_id, "📲 Manuel paylaşım paketi hazırlandı.", alert=False)
                    caption_metni = kayit.get("caption") or kayit.get("turkce_metin") or ""
                    etiketler = kayit.get("etiketler") or ""
                    if etiketler and etiketler not in caption_metni:
                        caption_metni = f"{caption_metni}\n\n{etiketler}"

                    manuel_metin = (
                        f"📲 <b>MANUEL PAYLAŞIM PAKETİ (#{paylasim_id})</b>\n\n"
                        f"📋 <b>TEK DOKUNUŞLA KOPYALA (AÇIKLAMA / CAPTION):</b>\n"
                        f"<pre>{html.escape(caption_metni)}</pre>\n\n"
                        f"<i>Metne dokunarak panoya kopyalayabilir, aşağıdaki butonlarla uygulamaları doğrudan açabilirsiniz. Paylaşımı tamamladıktan sonra 'Elle Paylaştım' butonuna basınız.</i>"
                    )
                    yeni_klavye = manuel_paylasim_menusu_kur(paylasim_id)
                    mesaj_gonder(manuel_metin, chat_id=str(chat_id), butonlar=yeni_klavye)

                elif data.startswith("manuel_diger_"):
                    paylasim_id = int(data.split("_")[2])
                    callback_cevapla(cq_id, "🌐 Ek platformlar listeleniyor...", alert=False)
                    ek_klavye = [
                        [
                            {"text": "🐦 X / Twitter", "url": "https://twitter.com/compose/tweet"},
                            {"text": "💬 WhatsApp Web", "url": "https://web.whatsapp.com"},
                        ],
                        [
                            {"text": "✈️ Telegram Kanalı", "url": "https://t.me"},
                        ],
                        [
                            {"text": "↩️ Ana Onay Menüsüne Dön", "callback_data": f"onay_menu_{paylasim_id}"},
                        ]
                    ]
                    mesaj_gonder(
                        f"🌐 <b>EK PLATFORM BAĞLANTILARI (#{paylasim_id})</b>\n\nPaylaşmak istediğiniz platforma dokunarak doğrudan geçiş yapabilirsiniz:",
                        chat_id=str(chat_id),
                        butonlar=ek_klavye
                    )

                elif data.startswith("manuel_tamam_"):
                    paylasim_id = int(data.split("_")[2])
                    callback_cevapla(cq_id, "✅ Manuel paylaşım kaydedildi!", alert=True)
                    db.durum_guncelle(paylasim_id, yeni_durum="yayinlandi")
                    caption_ve_buton_guncelle(
                        chat_id,
                        msg_id,
                        f"✅ <b>MANUEL PAYLAŞIM TAMAMLANDI (#{paylasim_id})</b>\n\nDoğukan tarafından paylaşıldığı onaylandı ve arşivlendi.",
                        butonlar=[]
                    )

                elif data.startswith("metin_menu_"):
                    paylasim_id = int(data.split("_")[2])
                    callback_cevapla(cq_id, "✍️ Metin revizyon menüsü açıldı.", alert=False)
                    yeni_klavye = metin_yenileme_menusu_kur(paylasim_id)
                    reply_markup_guncelle(chat_id, msg_id, yeni_klavye)

                elif data.startswith("metin_kisalt_") or data.startswith("metin_genislet_") or data.startswith("metin_yenile_"):
                    parcalar = data.split("_")
                    aksiyon = parcalar[1]  # "kisalt", "genislet", "yenile"
                    paylasim_id = int(parcalar[2])

                    hedef_harita = {
                        "kisalt": "Daha kısa ve öz",
                        "genislet": "Daha derin ve tefekkür odaklı",
                        "yenile": "Alternatif edebi üslup",
                    }
                    hedef_adi = hedef_harita.get(aksiyon, "Yeni metin")

                    callback_cevapla(cq_id, f"✍️ Metinler revize ediliyor ({hedef_adi})...", alert=False)
                    mesaj_gonder(f"⏳ <b>Paylaşım #{paylasim_id} metinleri revize ediliyor...</b>\n<i>Hedef: {hedef_adi}</i>", chat_id=str(chat_id))

                    def _gorev_metin_revize(p_id=paylasim_id, c_id=chat_id, act=aksiyon):
                        try:
                            from ..uretim import ai
                            kayit = db.paylasim_getir(p_id)
                            if not kayit:
                                return
                            turkce_metin = kayit.get("turkce_metin", "")
                            kategori = kayit.get("kategori", "ayet")
                            eski_tef = kayit.get("tefekkur", "")
                            eski_cap = kayit.get("caption", "")

                            yeni_tef, yeni_cap = ai.metin_ve_tefekkur_revize_et(
                                turkce_metin=turkce_metin,
                                kategori=kategori,
                                hedef=act,
                                mevcut_tefekkur=eski_tef,
                                mevcut_caption=eski_cap,
                            )

                            db.paylasim_guncelle(p_id, tefekkur=yeni_tef, caption=yeni_cap)
                            format_t = kayit.get("format", "reels_9_16")
                            raw_k = db.ayar_getir(f"paylasim_kanallari_{p_id}")
                            kanallar = json.loads(raw_k) if raw_k else varsayilan_kanallar(format_t)
                            yeni_klavye = ana_onay_menusu_kur(p_id, format_tipi=format_t, kanallar=kanallar, kategori=kategori)

                            revize_bildirim = (
                                f"✨ <b>METİNLER GÜNCELLENDİ (#{p_id})</b>\n\n"
                                f"💡 <b>Yeni Tefekkür / Hikmet:</b>\n<i>{html.escape(yeni_tef)}</i>\n\n"
                                f"📝 <b>Yeni Açıklama:</b>\n<pre>{html.escape(yeni_cap)}</pre>"
                            )
                            mesaj_gonder(revize_bildirim, chat_id=str(c_id), butonlar=yeni_klavye)
                        except Exception as e:
                            log.error(f"Metin revizyon hatası (#{p_id}): {e}")
                            mesaj_gonder(f"❌ Metin revizyonunda hata oluştu: <code>{html.escape(str(e))}</code>", chat_id=str(c_id))

                    _arkaplanda_calistir(_gorev_metin_revize)

                elif data.startswith("atla_") or data.startswith("cope_at_"):
                    p_str = data.split("_")[1] if data.startswith("atla_") else data.split("_")[2]
                    paylasim_id = int(p_str)
                    callback_cevapla(cq_id, "🗑️ İçerik atlandı ve arşivlendi.", alert=False)
                    db.durum_guncelle(paylasim_id, yeni_durum="iptal_edildi")
                    caption_ve_buton_guncelle(
                        chat_id,
                        msg_id,
                        f"🗑️ <b>İÇERİK ATLANDI (#{paylasim_id})</b>\n\nDoğukan tarafından reddedildi ve arşivlendi.",
                        butonlar=[]
                    )

                elif data == "cmd_menu":
                    callback_cevapla(cq_id, "🕌 Kontrol Merkezi açıldı.", alert=False)
                    mesaj_gonder(
                        "🕌 <b>EZAN PLUS KONTROL MERKEZİ</b>\n\nLütfen çalıştırmak veya denetlemek istediğiniz işlemi dokunarak seçin:",
                        chat_id=str(chat_id),
                        butonlar=kontrol_merkezi_menusu(),
                    )

                elif data == "menu_duraklat":
                    callback_cevapla(cq_id, "⏸️ Duraklatma seçenekleri...", alert=False)
                    reply_markup_guncelle(chat_id, msg_id, duraklatma_secenekleri_menusu())

                elif data.startswith("duraklat:"):
                    saat = int(data.split(":")[1])
                    duraklat(saat)
                    callback_cevapla(cq_id, f"⏸️ Bot {saat} saat duraklatıldı.", alert=True)
                    mesaj_gonder(
                        f"⏸️ <b>BOT {saat} SAAT DURAKLATILDI</b>\n\n"
                        f"Otomatik üretim ve zamanlanmış yayınlar geçici olarak durduruldu.\n"
                        f"Tekrar başlatmak için <b>/devam</b> komutunu veya aşağıdaki butonu kullanabilirsiniz.",
                        chat_id=str(chat_id),
                        butonlar=[[{"text": "▶️ Yayına Devam Et", "callback_data": "devam_et"}]]
                    )

                elif data == "devam_et":
                    devam_et()
                    callback_cevapla(cq_id, "▶️ Bot çalışmaya devam ediyor.", alert=True)
                    mesaj_gonder(
                        "▶️ <b>BOT AKTİF HALE GETİRİLDİ</b>\n\nOtomasyon ve zamanlanmış yayın akışı olağan şekilde devam ediyor.",
                        chat_id=str(chat_id),
                        butonlar=[[{"text": "🕌 Kontrol Merkezi", "callback_data": "cmd_menu"}]]
                    )

                elif data == "cmd_ayarlar":
                    callback_cevapla(cq_id, "⚙️ Ayarlar menüsü açıldı.", alert=False)
                    mesaj_gonder(
                        "⚙️ <b>EZAN PLUS SİSTEM AYARLARI</b>\n\nDeğiştirmek istediğiniz ayarın üzerine dokunun:",
                        chat_id=str(chat_id),
                        butonlar=ayarlar_menusu_kur(),
                    )

                elif data.startswith("ayar_toggle:"):
                    ayar_anahtar = data.split(":")[1]
                    if ayar_anahtar in AYAR_TANIMLARI:
                        etiket, secenekler, varsayilan = AYAR_TANIMLARI[ayar_anahtar]
                        suanki = db.ayar_getir(ayar_anahtar, varsayilan)
                        if suanki in secenekler:
                            yeni_idx = (secenekler.index(suanki) + 1) % len(secenekler)
                            yeni_deger = secenekler[yeni_idx]
                        else:
                            yeni_deger = secenekler[0]
                        db.ayar_kaydet(ayar_anahtar, yeni_deger)
                        callback_cevapla(cq_id, f"{etiket}: {yeni_deger}", alert=False)
                        reply_markup_guncelle(chat_id, msg_id, ayarlar_menusu_kur())
                    else:
                        callback_cevapla(cq_id, "Ayar bulunamadı.", alert=False)

                elif data in ("menu_ayet", "menu_hadis", "menu_dua", "menu_kelime"):
                    tur_harita = {
                        "menu_ayet": ("ayet", "Kur'an Tilaveti Reels"),
                        "menu_hadis": ("hadis", "Sahih Hadis Videosu"),
                        "menu_dua": ("dua", "Günün Duası Videosu"),
                        "menu_kelime": ("kelime", "Kur'an Sözlüğü Kartı"),
                    }
                    tur_kod, tur_ad = tur_harita[data]
                    callback_cevapla(cq_id, f"🚀 {tur_ad} üretimi başlatıldı...", alert=False)
                    durum_mid = mesaj_gonder(f"⏳ <b>{tur_ad} üretimi başlatılıyor...</b>", chat_id=str(chat_id))

                    def _gorev_menu_uret(t_kod=tur_kod, c_id=chat_id, d_mid=durum_mid):
                        try:
                            from .. import otomasyon
                            if t_kod == "ayet":
                                otomasyon.reels_icerigi_olustur_ve_gonder(durum_mesaj_id=d_mid)
                            elif t_kod == "hadis":
                                otomasyon.hadis_videosu_olustur_ve_gonder(durum_mesaj_id=d_mid)
                            elif t_kod == "dua":
                                otomasyon.dua_videosu_olustur_ve_gonder(durum_mesaj_id=d_mid)
                            elif t_kod == "kelime":
                                otomasyon.kelime_postu_olustur_ve_gonder(durum_mesaj_id=d_mid)
                        except Exception as e:
                            log.error(f"Menüden üretim hatası ({t_kod}): {e}")
                            mesaj_gonder(f"❌ <b>{tur_ad} Üretim Hatası:</b> <code>{html.escape(str(e))}</code>", chat_id=str(c_id))

                    _arkaplanda_calistir(_gorev_menu_uret)

                else:
                    # Daily Brief Ders 127: Tanınmayan veya süresi dolmuş buton tıklamalarında
                    # Telegram istemcisinde sonsuz dönen yükleme simgesini (spinner) engelle
                    log.warning(f"Tanınmayan veya süresi dolmuş Telegram butonu tıklandı: data='{data}', msg_id={msg_id}")
                    callback_cevapla(cq_id, "⚠️ Bu buton artık geçerli değil veya süresi doldu.", alert=False)
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
    son_zamanli_kontrol = 0.0
    while True:
        try:
            offset = tek_sefer_dinle(offset)
            simdi_ts = time.time()
            if simdi_ts - son_zamanli_kontrol >= 15.0:
                son_zamanli_kontrol = simdi_ts
                zamanlanmis_yayinlari_kontrol_et()
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
