"""
src/hata_bildir.py — Ezan Plus Sosyal Medya Hata Teşhis ve Bildirim Motoru

Yayınlama veya içerik üretimi sırasında bir aksaklık yaşandığında:
1. Hatayı katalogla eşleştirir ve kök sebebi tespit eder (NE OLDU, NEDEN, NE YAPILMALI).
2. Hatayı kalıcı olarak data/hata_kayitlari.jsonl ve data/son_hata.txt dosyalarına yazar.
3. Telegram onay grubuna teknik jargon yerine sade Türkçe teşhis kartı ve doğrudan
   aksiyon/çözüm butonları ("🔄 Tekrar Yayınla", "🔄 Başarısızları Dene", "🔍 Teşhis") iletir.
"""

from __future__ import annotations

import html as html_lib
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .ayar import KOK_DIZIN

log = logging.getLogger(__name__)

HATA_LOG_YOLU = KOK_DIZIN / "data" / "hata_kayitlari.jsonl"
SON_HATA_YOLU = KOK_DIZIN / "data" / "son_hata.txt"

# ----------------------------------------------------------------------
# Ezan Plus Genişletilmiş Hata Teşhis Kataloğu
# ----------------------------------------------------------------------
KATALOG: List[Dict[str, str]] = [
    {
        "kod": "CDN_UPLOAD_FAIL",
        "desen": r"Medya hiçbir CDN servisine yüklenemedi|Catbox|Litterbox|uguu|ImgBB|cdn\.upload",
        "ne_oldu": "Görsel veya video dosyası Meta/Threads sunucularının erişebileceği genel CDN adresine yüklenemedi.",
        "neden": "Instagram ve Threads yerel dosya kabul etmeyip genel URL şartı koşar. Geçici barındırma sunucuları (Catbox/Uguu) anlık ağ gecikmesi veya datacenter kısıtlaması yaşadı.",
        "ne_yapilir": "Görseller yerel sistemde hazırdır. Aşağıdaki '🔄 Başarısız Kanalları Tekrar Dene' butonuna basarak yedek CDN üzerinden doğrudan yayını tamamlayabilirsiniz.",
        "eylem": "tekrar_yayinla",
    },
    {
        "kod": "IG_TIMEOUT_MEDIA",
        "desen": r"2207052|2207003|Only photo or video can be accepted",
        "ne_oldu": "Instagram sunucuları medya dosyasını çekerken geçici zaman aşımına uğradı.",
        "neden": "Meta Graph API sunucuları ile görsel sunucusu arasında anlık gecikme oluştu.",
        "ne_yapilir": "Görsel dosyası sağlam. '🔄 Instagram'ı Tekrar Dene' butonuna basarak işlemi hemen tamamlayabilirsiniz.",
        "eylem": "tekrar_yayinla",
    },
    {
        "kod": "META_TOKEN_EXPIRED",
        "desen": r"OAuthException|Error validating access token|Session has expired|Invalid OAuth access token",
        "ne_oldu": "Meta (Instagram / Facebook / Threads) API jetonunun süresi dolmuş veya yetki geçersiz.",
        "neden": "Facebook/Instagram şifresi değişmiş veya 60 günlük uzun ömürlü Page Access Token süresi dolmuş olabilir.",
        "ne_yapilir": "GitHub Secrets ve .env içindeki INSTAGRAM_ACCESS_TOKEN ve FACEBOOK_PAGE_ACCESS_TOKEN yenilenmelidir.",
        "eylem": "yok",
    },
    {
        "kod": "META_RATE_LIMIT",
        "desen": r"Application request limit|throttl|instagram.*429|User request limit reached",
        "ne_oldu": "Meta / Instagram API geçici istek sınırı (Rate Limit) uyguladı.",
        "neden": "Kısa sürede çok sayıda API isteği yapıldı. Bu sınır Meta tarafından genelde 15-30 dakika içinde otomatik kaldırılır.",
        "ne_yapilir": "15 dakika bekledikten sonra '🔄 Tekrar Yayınla' butonuna basınız.",
        "eylem": "tekrar_yayinla",
    },
    {
        "kod": "TELEGRAM_TIMEOUT",
        "desen": r"WEBPAGE_CURL_FAILED|failed to send message #\d+",
        "ne_oldu": "Telegram botu medyayı karşıya yüklerken zaman aşımına uğradı.",
        "neden": "Telegram API sunucuları ile bot arasında anlık paket kaybı veya bağlantı kopması yaşandı.",
        "ne_yapilir": "'🔄 Tekrar Dene' butonu ile mesajı ve butonları yeniden iletebilirsiniz.",
        "eylem": "tekrar_yayinla",
    },
    {
        "kod": "SQLITE_LOCKED",
        "desen": r"database is locked|database table is locked|sqlite3\.OperationalError",
        "ne_oldu": "SQLite veritabanı anlık olarak kilitlendi.",
        "neden": "İki işlem aynı anda veritabanına yazmaya çalıştı.",
        "ne_yapilir": "1-2 saniye bekledikten sonra butona basmak işlemi sorunsuz tamamlayacaktır.",
        "eylem": "tekrar_yayinla",
    },
    {
        "kod": "GEMINI_QUOTA_EXCEEDED",
        "desen": r"KOTASI DOLDU|RESOURCE_EXHAUSTED|429.*(quota|Quota)",
        "ne_oldu": "Gemini API günlük istek kotası doldu.",
        "neden": "Google AI Studio günlük ücretsiz istek limiti tükendi.",
        "ne_yapilir": "Yeni bir GEMINI_API_KEY eklenebilir veya bir sonraki kotanın açılması beklenebilir.",
        "eylem": "yok",
    },
    {
        "kod": "GEMINI_JSON_SYNTAX_ERROR",
        "desen": r"Expecting ',' delimiter|Expecting property name|JSONDecodeError|Unterminated string",
        "ne_oldu": "Gemini AI tarafından üretilen içerik çıktısında JSON formatlama uyuşmazlığı oluştu.",
        "neden": "Yapay zeka modeli metin üretirken tırnak işareti, satır sonu veya virgül kaçışını unuttu.",
        "ne_yapilir": "Kod seviyesinde self-healing devrededir; '🔄 Yeniden Üret ve Hazırla' butonuna basarak temiz bir içerik oluşturabilirsiniz.",
        "eylem": "yeniden_uret",
    },
    {
        "kod": "THREADS_MEDIA_NOT_FOUND",
        "desen": r"Media Not Found|The media with id \d+ cannot be found|Subcode 4279009|4279009",
        "ne_oldu": "Threads sunucuları oluşturulan yanıt container'ını henüz işleyip eşitlemedi.",
        "neden": "Meta Graph API sunucuları arasındaki replikasyon gecikmesi nedeniyle yayınlama isteği henüz hazır olmayan bir medya ID'sine yapıldı.",
        "ne_yapilir": "'🔄 Threads'i Tekrar Dene' butonuna basarak zinciri anında tamamlayabilirsiniz.",
        "eylem": "tekrar_yayinla",
    },
    {
        "kod": "RENDER_FFMPEG_FAIL",
        "desen": r"reels_videosu_uret|ffmpeg|MoviePy|codec|audio.*sync|segment",
        "ne_oldu": "Reels videosu veya stüdyo tilavet sesi birleştirilirken render hatası oluştu.",
        "neden": "FFmpeg işleminde veya ses zaman damgası enterpolasyonunda bir aksaklık yaşandı.",
        "ne_yapilir": "'🔄 Yeniden Üret' butonuna basarak videoyu sıfırdan render edebilirsiniz.",
        "eylem": "yeniden_uret",
    },
    {
        "kod": "PYTHON_SCOPE_ERROR",
        "desen": r"UnboundLocalError|NameError|cannot access local variable|is not defined",
        "ne_oldu": "Kod yürütülürken değişken kapsamı (scope) hatası oluştu.",
        "neden": "Kod düzenlemesinde yerel bir değişken adı tanımlanmadan çağrıldı.",
        "ne_yapilir": "Hata giderildiğinde işlemi tekrar başlatabilirsiniz.",
        "eylem": "tekrar_yayinla",
    },
    {
        "kod": "PYTHON_TYPE_ERROR",
        "desen": r"AttributeError|KeyError|IndexError|TypeError|ValueError",
        "ne_oldu": "İçerik verisi işlenirken beklenmeyen bir format veya alan uyuşmazlığı oluştu.",
        "neden": "Dönen veri sözlüğünde beklenen bir anahtar eksikti ya da tip dönüşümü başarısız oldu.",
        "ne_yapilir": "'🔄 Tekrar Dene' butonuna basabilir veya paylaşım taslağını yenileyebilirsiniz.",
        "eylem": "tekrar_yayinla",
    },
]


def _sadelestir(metin: str) -> str:
    """Fazla boşluk ve satır başlarını temizler."""
    return re.sub(r"\s+", " ", (metin or "")).strip()


def tani(hata: Any) -> Dict[str, Any]:
    """
    Ham hata nesnesini veya hata metnini katalogla eşleştirir.
    Tanınan hata ise sadeleştirilmiş teşhis döner, tanınmazsa dürüstçe ham detayı sunar.
    """
    ham = _sadelestir(str(hata))
    for kayit in KATALOG:
        if re.search(kayit["desen"], ham, re.IGNORECASE):
            return {
                **kayit,
                "tanindi": True,
                "ham": ham,
            }
    return {
        "kod": "GENERIC_ERROR",
        "ne_oldu": "Beklenmeyen bir sistem hatası oluştu.",
        "neden": "Bu hata kataloğa henüz tanımlanmamış yeni bir durum.",
        "ne_yapilir": "Aşağıdaki butonları kullanarak işlemi tekrar deneyebilir veya yöneticiden yardım alabilirsiniz.",
        "eylem": "tekrar_yayinla",
        "tanindi": False,
        "ham": ham,
    }


def hata_kaydet(nerede: str, baslik: str, ham_hata: str, teshis: Dict[str, Any], paylasim_id: Optional[int] = None) -> None:
    """Hatayı kalıcı JSONL loguna ve son_hata.txt dosyasına yazar."""
    try:
        HATA_LOG_YOLU.parent.mkdir(parents=True, exist_ok=True)
        simdi = datetime.now()
        kayit = {
            "tarih": simdi.isoformat(),
            "tarih_tr": simdi.strftime("%d.%m.%Y %H:%M:%S"),
            "paylasim_id": paylasim_id,
            "nerede": nerede,
            "baslik": baslik,
            "ne_oldu": teshis.get("ne_oldu", ""),
            "neden": teshis.get("neden", ""),
            "ne_yapilir": teshis.get("ne_yapilir", ""),
            "eylem": teshis.get("eylem", ""),
            "tanindi": teshis.get("tanindi", False),
            "ham_hata": ham_hata,
        }
        with open(HATA_LOG_YOLU, "a", encoding="utf-8") as f:
            f.write(json.dumps(kayit, ensure_ascii=False) + "\n")

        with open(SON_HATA_YOLU, "w", encoding="utf-8") as f:
            f.write(
                f"[{kayit['tarih_tr']}] (ID #{paylasim_id or '-'}) {nerede} -> {baslik}\n"
                f"NE OLDU: {kayit['ne_oldu']}\n"
                f"NEDEN: {kayit['neden']}\n"
                f"ÇÖZÜM: {kayit['ne_yapilir']}\n\n"
                f"HAM DETAY:\n{ham_hata[:3000]}\n"
            )
    except Exception as e:
        log.warning(f"Hata log dosyasına yazılamadı: {e}")


def son_hata_getir() -> Optional[Dict[str, Any]]:
    """En son kaydedilen hatanın bilgilerini döner."""
    liste = son_hatalari_listele(adet=1)
    return liste[-1] if liste else None


def son_hatalari_listele(adet: int = 5) -> List[Dict[str, Any]]:
    """En son kaydedilen N adet hatayı döner."""
    if not HATA_LOG_YOLU.exists():
        return []
    try:
        with open(HATA_LOG_YOLU, "r", encoding="utf-8") as f:
            satirlar = [s.strip() for s in f if s.strip()]
            son_satirlar = satirlar[-adet:] if len(satirlar) > adet else satirlar
            return [json.loads(s) for s in son_satirlar]
    except Exception as e:
        log.warning(f"Hatalar listelenemedi: {e}")
        return []


def mesaji_kur(baslik: str, teshis: Dict[str, Any], nerede: str = "", paylasim_id: Optional[int] = None) -> str:
    """Telegram için zengin, HTML formatlı ve anlaşılır hata teşhis mesajı kurar."""
    b_esc = html_lib.escape(baslik or "Sistem Hatası")
    n_esc = html_lib.escape(nerede or "Bilinmiyor")
    ne_oldu = html_lib.escape(teshis.get("ne_oldu", "") or "")
    neden = html_lib.escape(teshis.get("neden", "") or "")
    ne_yapilir = html_lib.escape(teshis.get("ne_yapilir", "") or "")
    ham = html_lib.escape(str(teshis.get("ham", ""))[:450] or "")

    satirlar = [
        f"⚠️ <b>EZAN PLUS HATA TEŞHİS RAPORU</b>\n",
        f"📌 <b>İçerik / Başlık:</b> {b_esc}",
    ]
    if paylasim_id:
        satirlar.append(f"🆔 <b>Paylaşım ID:</b> <code>#{paylasim_id}</code>")
    if nerede:
        satirlar.append(f"📍 <b>Konum / Fonksiyon:</b> <code>{n_esc}</code>")

    satirlar.extend([
        "",
        f"🔍 <b>NE OLDU?</b>\n{ne_oldu}",
        "",
        f"💡 <b>NEDEN?</b>\n{neden}",
        "",
        f"🛠️ <b>ÇÖZÜM / NE YAPILMALI?</b>\n{ne_yapilir}",
    ])

    if ham:
        satirlar.extend([
            "",
            f"📄 <b>HAM HATA İZİ:</b>\n<code>{ham}</code>",
        ])

    satirlar.extend([
        "",
        f"⏰ <i>Tespit Zamanı: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</i>",
    ])
    return "\n".join(satirlar)


def hata_butonlari(paylasim_id: Optional[int] = None, eylem: str = "tekrar_yayinla") -> List[List[Dict[str, str]]]:
    """Hataya uygun doğrudan aksiyon butonları üretir."""
    butonlar: List[List[Dict[str, str]]] = []
    if paylasim_id:
        if eylem == "tekrar_yayinla":
            butonlar.append([{"text": "🔄 Başarısız Kanalları Tekrar Dene", "callback_data": f"telafi_hepsi_{paylasim_id}"}])
            butonlar.append([
                {"text": "📸 Instagram", "callback_data": f"telafi_ig_{paylasim_id}"},
                {"text": "📱 Story", "callback_data": f"telafi_story_{paylasim_id}"},
                {"text": "🧵 Threads", "callback_data": f"telafi_threads_{paylasim_id}"},
            ])
            butonlar.append([
                {"text": "🛠️ Otomatik Onar", "callback_data": f"onar_{paylasim_id}"},
                {"text": "🗑️ Yayından Kaldır", "callback_data": f"kaldir_{paylasim_id}"}
            ])
        elif eylem == "yeniden_uret":
            butonlar.append([
                {"text": "🛠️ Otomatik Onar", "callback_data": f"onar_{paylasim_id}"},
                {"text": "🔄 Sıfırdan Yeniden Üret", "callback_data": f"yeniden_uret_{paylasim_id}"},
            ])
            butonlar.append([{"text": "❌ İptal Et", "callback_data": f"red_{paylasim_id}"}])
        else:
            butonlar.append([
                {"text": "🔄 Tekrar Dene", "callback_data": f"telafi_hepsi_{paylasim_id}"},
                {"text": "🛠️ Otomatik Onar", "callback_data": f"onar_{paylasim_id}"},
            ])
    else:
        # paylasim_id yoksa genel sorun giderme butonları sun
        butonlar.append([
            {"text": "🩺 Sistem Sağlık Testi", "callback_data": "cmd_saglik"},
            {"text": "🧹 Geçici Dosyaları Temizle", "callback_data": "cmd_temizle"},
        ])

    butonlar.append([
        {"text": "📊 Sistem Durumu", "callback_data": "cmd_durum"},
        {"text": "📜 Son Hatalar", "callback_data": "cmd_hatalar"},
        {"text": "ℹ️ Yardım", "callback_data": "cmd_yardim"},
    ])
    return butonlar


def bildir(
    baslik: str = "Sistem Hatası",
    hata: Any = None,
    nerede: str = "",
    paylasim_id: Optional[int] = None,
    **kwargs: Any,
) -> bool:
    """
    Hatayı teşhis eder, kalıcı olarak kaydeder ve Telegram grubuna
    aksiyon butonlarıyla birlikte raporlar.
    """
    try:
        from .telegram import bot as telegram_bot

        if hata is None and "hata" in kwargs:
            hata = kwargs["hata"]
        if not nerede and "konum" in kwargs:
            nerede = str(kwargs["konum"])
        if paylasim_id is None and "paylasim_id" in kwargs:
            paylasim_id = kwargs["paylasim_id"]

        teshis = tani(hata if hata is not None else baslik)
        ham_hata = _sadelestir(str(hata if hata is not None else baslik))
        hata_kaydet(nerede, baslik, ham_hata, teshis, paylasim_id=paylasim_id)

        metin = mesaji_kur(baslik, teshis, nerede=nerede, paylasim_id=paylasim_id)
        butonlar = hata_butonlari(paylasim_id, eylem=teshis.get("eylem", "tekrar_yayinla"))

        telegram_bot.mesaj_gonder(metin, butonlar=butonlar, html=True)
        log.info(f"Hata Telegram'a teşhis kartı ve aksiyon butonlarıyla iletildi: {teshis['ne_oldu']}")
        return True
    except Exception as e:
        log.error(f"Hata bildirim mesajı Telegram'a iletilemedi: {e}")
        return False
