"""
src/telegram/yonetici.py — Çoklu Platform Yayın Dağıtım Yöneticisi
Telegram'dan onaylanan içerikleri eş zamanlı ve hataya dayanıklı olarak
Instagram Reels + Story, Threads, Facebook Sayfası, YouTube Shorts ve TikTok'a iletir.
"""

from __future__ import annotations

import concurrent.futures
import logging
import os
from pathlib import Path
import threading
from typing import Any, Callable, Dict, List, Optional

from .. import db
from ..platformlar import meta, threads, youtube, tiktok, r2

log = logging.getLogger(__name__)


def _kanal_izin_var_mi(kanal: str, kanallar: Optional[Any]) -> bool:
    """Belirtilen kanalın yayın izni olup olmadığını denetler."""
    if kanallar is None:
        return True
    if isinstance(kanallar, dict):
        if kanal in kanallar:
            return bool(kanallar[kanal])
        if kanal == "instagram" and "ig" in kanallar:
            return bool(kanallar["ig"])
        if kanal == "instagram_story" and "story" in kanallar:
            return bool(kanallar["story"])
        if kanal == "facebook" and "fb" in kanallar:
            return bool(kanallar["fb"])
        if kanal == "youtube" and ("yt" in kanallar or "shorts" in kanallar):
            return bool(kanallar.get("youtube", kanallar.get("yt", kanallar.get("shorts"))))
        if kanal == "tiktok" and "tt" in kanallar:
            return bool(kanallar["tt"])
        return True
    if isinstance(kanallar, (list, set, tuple)):
        k_set = {str(x).lower().strip() for x in kanallar}
        if kanal in k_set:
            return True
        if kanal == "instagram" and ("ig" in k_set or "reels" in k_set or "feed" in k_set):
            return True
        if kanal == "instagram_story" and "story" in k_set:
            return True
        if kanal == "facebook" and "fb" in k_set:
            return True
        if kanal == "youtube" and ("yt" in k_set or "shorts" in k_set):
            return True
        if kanal == "tiktok" and "tt" in k_set:
            return True
        return False
    return True


def yayinla_hepsi(
    paylasim_id: int,
    oncesinde_onayla: bool = True,
    kanallar: Optional[Any] = None,
    durum_cb: Optional[Callable[[int, int, str, Dict[str, str]], None]] = None,
) -> Dict[str, Any]:
    """
    Onaylanan içeriği Instagram, Threads, Facebook, YouTube ve TikTok'ta eş zamanlı yayınlar.
    Canlı durum callback'i (durum_cb) verilmişse adım adım ilerleme ve platform durumlarını bildirir.
    """
    kayit = db.paylasim_getir(paylasim_id)
    if not kayit:
        raise ValueError(f"Paylaşım ID bulunamadı: {paylasim_id}")

    # Daily Brief Ders 1u: Mükerrer Yayın Kilidi (Botun yayınladığını unutmasını önleme)
    # Eğer bu içerik zaten 'yayinlandi' durumundaysa ve en az bir platform kimliği varsa,
    # sıfırdan tüm ağlara yeniden basmak yerine yalnızca eksik/başarısız platformları telafi et.
    if kayit.get("durum") == "yayinlandi":
        mevcut_idler = [
            kayit.get("instagram_post_id"),
            kayit.get("threads_post_id"),
            kayit.get("facebook_post_id"),
            kayit.get("youtube_post_id"),
            kayit.get("tiktok_post_id"),
        ]
        if any(mevcut_idler):
            log.warning(
                f"⚠️ Paylaşım #{paylasim_id} zaten 'yayinlandi' durumunda! "
                "Mükerrer yayını önlemek için doğrudan telafi kontrolüne yönlendiriliyor..."
            )
            if durum_cb is not None:
                return yayinla_telafi(paylasim_id, hedef_kanal="hepsi", durum_cb=durum_cb)
            return yayinla_telafi(paylasim_id, hedef_kanal="hepsi")

    # Yayın Öncesi Son Güvenlik & Kalite Kapısı
    if oncesinde_onayla:
        from .. import denetleyici
        denetim = denetleyici.denetle_paylasim(paylasim_id)
        if not denetim.gecerli:
            log.warning(f"Yayın Öncesi Denetim: Paylaşım #{paylasim_id} için otomatik onarım deneniyor...")
            onarildi, duzeltmeler = denetleyici.otomatik_onar(paylasim_id)
            if onarildi:
                denetim = denetleyici.denetle_paylasim(paylasim_id)
                log.info(f"Paylaşım #{paylasim_id} yayın öncesi başarıyla onarıldı: {duzeltmeler}")
                kayit = db.paylasim_getir(paylasim_id)
            else:
                hata_metni = "\n".join(f"• {h}" for h in denetim.hatalar)
                log.critical(f"Yayın Öncesi Kalite Kontrolü Başarısız! Paylaşım #{paylasim_id} yayını durduruldu:\n{hata_metni}")
                db.durum_guncelle(paylasim_id, yeni_durum="iptal_edildi", hata_mesaji=hata_metni)
                from . import bot as telegram_bot
                telegram_bot.mesaj_gonder(denetim.formatli_rapor())
                return {"hata": "Kalite kontrolünden geçemedi ve onarılamadı", "hatalar": denetim.hatalar}

    format_tipi = kayit["format"]
    caption = kayit.get("caption") or ""
    video_yolu = kayit.get("video_yolu")
    gorsel_yollari = kayit.get("gorsel_yollari") or []
    gorsel_yolu = gorsel_yollari[0] if gorsel_yollari else None
    story_gorseli = gorsel_yollari[1] if len(gorsel_yollari) > 1 else gorsel_yolu

    sonuclar: Dict[str, Any] = {}

    # Hedef kanalları belirle ve canlı ilerleme durum tablosunu hazırla
    hedef_kanallar: List[str] = []
    if _kanal_izin_var_mi("tiktok", kanallar) and ((format_tipi == "reels_9_16" and video_yolu) or gorsel_yollari):
        hedef_kanallar.append("tiktok")
    if _kanal_izin_var_mi("instagram", kanallar):
        hedef_kanallar.append("instagram")
    if _kanal_izin_var_mi("instagram_story", kanallar):
        hedef_kanallar.append("instagram_story")
    if _kanal_izin_var_mi("threads", kanallar):
        hedef_kanallar.append("threads")
    if _kanal_izin_var_mi("facebook", kanallar):
        hedef_kanallar.append("facebook")
    if format_tipi == "reels_9_16" and video_yolu and _kanal_izin_var_mi("youtube", kanallar):
        hedef_kanallar.append("youtube")

    toplam_adim = max(1, len(hedef_kanallar))
    durum_haritasi: Dict[str, str] = {k: "⏱️ Sırada" for k in hedef_kanallar}
    adim_sayac = 0
    _lock = threading.Lock()

    def _bildir(k: str, durum: str, increment: bool = False):
        nonlocal adim_sayac
        with _lock:
            if increment:
                adim_sayac = min(toplam_adim, adim_sayac + 1)
            durum_haritasi[k] = durum
            snap_harita = dict(durum_haritasi)
            snap_adim = adim_sayac
        if durum_cb:
            try:
                durum_cb(snap_adim, toplam_adim, k, snap_harita)
            except Exception as e_cb:
                log.debug(f"durum_cb hatası ({k}): {e_cb}")

    # Cloudflare R2 Ön Yükleme (Anycast CDN ile Meta ve Threads indirme sürelerini sıfıra indirir)
    r2_video_url = None
    r2_gorsel_url = None
    if r2.r2_hazir_mi():
        try:
            if format_tipi == "reels_9_16" and video_yolu and Path(video_yolu).exists():
                r2_res = r2.r2ye_yukle(video_yolu, alt_klasor="video", zaman_asimi=30)
                r2_video_url = r2_res.get("url")
            elif gorsel_yolu and Path(gorsel_yolu).exists():
                r2_res = r2.r2ye_yukle(gorsel_yolu, alt_klasor="sosyal", zaman_asimi=20)
                r2_gorsel_url = r2_res.get("url")
        except Exception as e_r2:
            log.debug(f"Cloudflare R2 ön yükleme uyarısı: {e_r2}")

    # Paralel Platform Görevleri
    def _is_tiktok():
        _bildir("tiktok", "⏳ Yükleniyor...")
        try:
            key = os.getenv("TIKTOK_CLIENT_KEY")
            if key and tiktok.TOKEN_DOSYASI.exists():
                baslik = kayit.get("baslik") or "Ezan Plus"
                if format_tipi == "reels_9_16" and video_yolu:
                    log.info(f"TikTok'a yükleniyor (Paralel Dağıtım Video): {video_yolu}")
                    tt_res = tiktok.tiktok_video_yukle(
                        video_yolu=video_yolu,
                        baslik=baslik,
                        aciklama=caption,
                        taslak_modu=True,
                    )
                elif gorsel_yollari:
                    log.info(f"TikTok Fotoğraf Moduna yükleniyor (Paralel Dağıtım Foto): {gorsel_yollari}")
                    tt_res = tiktok.tiktok_foto_yukle(
                        gorsel_yollari=gorsel_yollari,
                        baslik=baslik,
                        aciklama=caption,
                        taslak_modu=True,
                    )
                else:
                    tt_res = {}
                with _lock:
                    sonuclar["tiktok"] = tt_res.get("publish_id")
                durum_etiketi = "📥 Taslakta" if tt_res.get("mod") == "inbox" else "✅ Yayında"
                _bildir("tiktok", durum_etiketi, increment=True)
            else:
                _bildir("tiktok", "⏭️ Atlandı (API Kapalı)", increment=True)
        except Exception as e:
            log.error(f"TikTok yayınlama hatası: {e}")
            with _lock:
                sonuclar["tiktok_hata"] = str(e)
            _bildir("tiktok", "❌ Hata", increment=True)

    def _is_instagram():
        _bildir("instagram", "⏳ Yükleniyor...")
        try:
            if format_tipi == "reels_9_16" and video_yolu:
                log.info(f"Instagram'a Reels yükleniyor (Paralel Dağıtım): {video_yolu}")
                ig_res = meta.instagram_reels_paylas(video_yolu, caption)
                with _lock:
                    sonuclar["instagram"] = ig_res.get("id")
            elif gorsel_yolu:
                log.info(f"Instagram'a Görsel Feed (4:5) yükleniyor (Paralel Dağıtım): {gorsel_yolu}")
                ig_res = meta.instagram_gorsel_paylas(gorsel_yolu, caption)
                with _lock:
                    sonuclar["instagram"] = ig_res.get("id")
            if sonuclar.get("instagram"):
                _bildir("instagram", "✅ Yayında", increment=True)
            else:
                _bildir("instagram", "❌ Hata", increment=True)
        except Exception as e:
            log.error(f"Instagram yayınlama hatası: {e}")
            with _lock:
                sonuclar["instagram_hata"] = str(e)
            _bildir("instagram", "❌ Hata", increment=True)

    def _is_story():
        _bildir("instagram_story", "⏳ Yükleniyor...")
        try:
            if format_tipi == "reels_9_16" and video_yolu:
                log.info(f"Instagram Story (Video) yükleniyor (Paralel Dağıtım): {video_yolu}")
                story_res = meta.instagram_story_paylas(video_yolu, is_video=True)
                with _lock:
                    sonuclar["instagram_story"] = story_res.get("id")
            elif story_gorseli:
                log.info(f"Instagram Story (Özel 9:16 Görsel) yükleniyor (Paralel Dağıtım): {story_gorseli}")
                story_res = meta.instagram_story_paylas(story_gorseli, is_video=False)
                with _lock:
                    sonuclar["instagram_story"] = story_res.get("id")
            if sonuclar.get("instagram_story"):
                _bildir("instagram_story", "✅ Yayında", increment=True)
            else:
                _bildir("instagram_story", "❌ Hata", increment=True)
        except Exception as e:
            log.error(f"Instagram Story yayınlama hatası: {e}")
            with _lock:
                sonuclar["instagram_story_hata"] = str(e)
            _bildir("instagram_story", "❌ Hata", increment=True)

    def _is_threads():
        _bildir("threads", "⏳ Yükleniyor...")
        if threads.threads_aktif_mi():
            try:
                log.info("Threads'e zincir gönderi yükleniyor (Paralel Dağıtım)...")
                if format_tipi == "reels_9_16" and video_yolu:
                    th_res = threads.threads_zincir_paylas(caption, video_url_veya_yolu=r2_video_url or video_yolu)
                elif gorsel_yolu:
                    th_res = threads.threads_zincir_paylas(caption, gorsel_url_veya_yolu=r2_gorsel_url or gorsel_yolu)
                else:
                    th_res = threads.threads_zincir_paylas(caption)
                with _lock:
                    sonuclar["threads"] = th_res.get("id")
                    sonuclar["threads_parca_sayisi"] = th_res.get("toplam_parca", 1)
                _bildir("threads", "✅ Yayında", increment=True)
            except Exception as e:
                log.error(f"Threads yayınlama hatası: {e}")
                with _lock:
                    sonuclar["threads_hata"] = str(e)
                _bildir("threads", "❌ Hata", increment=True)
        else:
            log.info("Threads API jetonu tanımlı değil veya geçersiz; Threads yayını atlandı.")
            _bildir("threads", "⏭️ Atlandı (API Kapalı)", increment=True)

    def _is_facebook():
        _bildir("facebook", "⏳ Yükleniyor...")
        try:
            if format_tipi == "reels_9_16" and video_yolu:
                log.info(f"Facebook Sayfasına Reels yükleniyor (Paralel Dağıtım): {video_yolu}")
                fb_res = meta.facebook_reels_paylas(video_yolu, caption=caption)
                with _lock:
                    sonuclar["facebook"] = fb_res.get("id") or fb_res.get("video_id")
            else:
                log.info("Facebook Sayfasına görsel/metin postu yükleniyor (Paralel Dağıtım)...")
                fb_res = meta.facebook_post_paylas(caption, gorsel_yolu=gorsel_yolu)
                with _lock:
                    sonuclar["facebook"] = fb_res.get("id")
            if sonuclar.get("facebook"):
                _bildir("facebook", "✅ Yayında", increment=True)
            else:
                _bildir("facebook", "❌ Hata", increment=True)
        except Exception as e:
            log.error(f"Facebook sayfa yayınlama hatası: {e}")
            with _lock:
                sonuclar["facebook_hata"] = str(e)
            _bildir("facebook", "❌ Hata", increment=True)

    def _is_youtube():
        _bildir("youtube", "⏳ Yükleniyor...")
        try:
            if youtube.CLIENT_SECRET_DOSYASI.exists() or youtube.TOKEN_DOSYASI.exists():
                log.info(f"YouTube Shorts'a yükleniyor (Paralel Dağıtım): {video_yolu}")
                baslik = kayit.get("baslik") or "Günün Ayeti • Ezan Plus"
                yt_res = youtube.youtube_shorts_yukle(
                    video_yolu=video_yolu,
                    baslik=baslik,
                    aciklama=caption,
                )
                with _lock:
                    sonuclar["youtube"] = yt_res.get("video_id")
                    sonuclar["youtube_url"] = yt_res.get("url")
                _bildir("youtube", "✅ Yayında", increment=True)
            else:
                _bildir("youtube", "⏭️ Atlandı (Yetki Yok)", increment=True)
        except Exception as e:
            log.error(f"YouTube Shorts yayınlama hatası: {e}")
            with _lock:
                sonuclar["youtube_hata"] = str(e)
            _bildir("youtube", "❌ Hata", increment=True)

    kanal_islevleri = {
        "tiktok": _is_tiktok,
        "instagram": _is_instagram,
        "instagram_story": _is_story,
        "threads": _is_threads,
        "facebook": _is_facebook,
        "youtube": _is_youtube,
    }

    gorevler = [kanal_islevleri[k] for k in hedef_kanallar if k in kanal_islevleri]
    if gorevler:
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(6, len(gorevler))) as executor:
            futures = [executor.submit(fn) for fn in gorevler]
            concurrent.futures.wait(futures)


    # Veritabanı güncelle
    hatalar = [v for k, v in sonuclar.items() if k.endswith("_hata")]
    db.durum_guncelle(
        paylasim_id,
        yeni_durum="yayinlandi",
        hata_mesaji="; ".join(hatalar) if hatalar else None,
        instagram_post_id=sonuclar.get("instagram"),
        instagram_story_post_id=sonuclar.get("instagram_story"),
        youtube_post_id=sonuclar.get("youtube"),
        tiktok_post_id=sonuclar.get("tiktok"),
        threads_post_id=sonuclar.get("threads"),
        facebook_post_id=sonuclar.get("facebook"),
    )
    return sonuclar


def yayinla_telafi(
    paylasim_id: int,
    hedef_kanal: str = "hepsi",
    durum_cb: Optional[Callable[[int, int, str, Dict[str, str]], None]] = None,
) -> Dict[str, Any]:
    """
    Kısmi veya başarısız yayınları telafi eder.
    Zaten yayınlanmış platformları (id'si mevcut olanları) KORUR ve atlar;
    yalnızca eksik/başarısız olan veya hedef_kanal olarak belirtilen platformları yeniden yayınlar.
    Canlı durum callback'i (durum_cb) verilmişse adım adım ilerleme durumunu bildirir.
    """
    kayit = db.paylasim_getir(paylasim_id)
    if not kayit:
        raise ValueError(f"Paylaşım ID bulunamadı: {paylasim_id}")

    format_tipi = kayit["format"]
    caption = kayit.get("caption") or ""
    video_yolu = kayit.get("video_yolu")
    gorsel_yollari = kayit.get("gorsel_yollari") or []
    gorsel_yolu = gorsel_yollari[0] if gorsel_yollari else None
    story_gorseli = gorsel_yollari[1] if len(gorsel_yollari) > 1 else gorsel_yolu

    # Mevcut başarı durumlarını koru
    sonuclar: Dict[str, Any] = {}
    if kayit.get("instagram_post_id"):
        sonuclar["instagram"] = kayit["instagram_post_id"]
    if kayit.get("instagram_story_post_id"):
        sonuclar["instagram_story"] = kayit["instagram_story_post_id"]
    if kayit.get("threads_post_id"):
        sonuclar["threads"] = kayit["threads_post_id"]
    if kayit.get("facebook_post_id"):
        sonuclar["facebook"] = kayit["facebook_post_id"]
    if kayit.get("youtube_post_id"):
        sonuclar["youtube"] = kayit["youtube_post_id"]
    if kayit.get("tiktok_post_id"):
        sonuclar["tiktok"] = kayit["tiktok_post_id"]

    hedef = hedef_kanal.lower().strip()
    yeni_basarili: List[str] = []

    # Telafi edilecek kanalları belirle
    telafi_kanallar: List[str] = []
    if (hedef in ("hepsi", "tiktok", "tt")) and ((format_tipi == "reels_9_16" and video_yolu) or gorsel_yollari) and not sonuclar.get("tiktok"):
        telafi_kanallar.append("tiktok")
    if (hedef in ("hepsi", "instagram", "ig")) and not sonuclar.get("instagram"):
        telafi_kanallar.append("instagram")
    if (hedef in ("hepsi", "instagram_story", "story")) and not sonuclar.get("instagram_story"):
        telafi_kanallar.append("instagram_story")
    if (hedef in ("hepsi", "threads")) and not sonuclar.get("threads") and threads.threads_aktif_mi():
        telafi_kanallar.append("threads")
    if (hedef in ("hepsi", "facebook", "fb")) and not sonuclar.get("facebook"):
        telafi_kanallar.append("facebook")
    if format_tipi == "reels_9_16" and video_yolu and (hedef in ("hepsi", "youtube", "yt")) and not sonuclar.get("youtube"):
        telafi_kanallar.append("youtube")

    toplam_adim = max(1, len(telafi_kanallar))
    durum_haritasi: Dict[str, str] = {k: "⏱️ Sırada" for k in telafi_kanallar}
    adim_sayac = 0
    _lock = threading.Lock()

    def _bildir(k: str, durum: str, increment: bool = False):
        nonlocal adim_sayac
        with _lock:
            if increment:
                adim_sayac = min(toplam_adim, adim_sayac + 1)
            durum_haritasi[k] = durum
            snap_harita = dict(durum_haritasi)
            snap_adim = adim_sayac
        if durum_cb:
            try:
                durum_cb(snap_adim, toplam_adim, k, snap_harita)
            except Exception as e_cb:
                log.debug(f"telafi durum_cb hatası ({k}): {e_cb}")

    # Cloudflare R2 Ön Yükleme (Anycast CDN ile Meta ve Threads için)
    r2_video_url = None
    r2_gorsel_url = None
    if r2.r2_hazir_mi():
        try:
            if format_tipi == "reels_9_16" and video_yolu and Path(video_yolu).exists():
                r2_res = r2.r2ye_yukle(video_yolu, alt_klasor="video", zaman_asimi=30)
                r2_video_url = r2_res.get("url")
            elif gorsel_yolu and Path(gorsel_yolu).exists():
                r2_res = r2.r2ye_yukle(gorsel_yolu, alt_klasor="sosyal", zaman_asimi=20)
                r2_gorsel_url = r2_res.get("url")
        except Exception as e_r2:
            log.debug(f"Cloudflare R2 ön yükleme uyarısı (Telafi): {e_r2}")

    # Paralel Telafi Görevleri
    def _telafi_tiktok():
        _bildir("tiktok", "⏳ Yükleniyor...")
        try:
            key = os.getenv("TIKTOK_CLIENT_KEY")
            if key and tiktok.TOKEN_DOSYASI.exists():
                log.info(f"Telafi: TikTok yükleniyor (#{paylasim_id})...")
                baslik = kayit.get("baslik") or "Ezan Plus"
                if format_tipi == "reels_9_16" and video_yolu:
                    tt_res = tiktok.tiktok_video_yukle(video_yolu=video_yolu, baslik=baslik, aciklama=caption, taslak_modu=True)
                elif gorsel_yollari:
                    tt_res = tiktok.tiktok_foto_yukle(gorsel_yollari=gorsel_yollari, baslik=baslik, aciklama=caption, taslak_modu=True)
                else:
                    tt_res = {}
                with _lock:
                    sonuclar["tiktok"] = tt_res.get("publish_id")
                    yeni_basarili.append("tiktok")
                    sonuclar.pop("tiktok_hata", None)
                durum_etiketi = "📥 Taslakta" if tt_res.get("mod") == "inbox" else "✅ Yayında"
                _bildir("tiktok", durum_etiketi, increment=True)
            else:
                _bildir("tiktok", "⏭️ Atlandı (API Kapalı)", increment=True)
        except Exception as e:
            log.error(f"Telafi TikTok hatası (#{paylasim_id}): {e}")
            with _lock:
                sonuclar["tiktok_hata"] = str(e)
            _bildir("tiktok", "❌ Hata", increment=True)

    def _telafi_instagram():
        _bildir("instagram", "⏳ Yükleniyor...")
        try:
            if format_tipi == "reels_9_16" and video_yolu:
                log.info(f"Telafi: Instagram'a Reels yükleniyor (#{paylasim_id}): {video_yolu}")
                ig_res = meta.instagram_reels_paylas(video_yolu, caption)
                with _lock:
                    sonuclar["instagram"] = ig_res.get("id")
            elif gorsel_yolu:
                log.info(f"Telafi: Instagram'a Görsel Feed (4:5) yükleniyor (#{paylasim_id}): {gorsel_yolu}")
                ig_res = meta.instagram_gorsel_paylas(gorsel_yolu, caption)
                with _lock:
                    sonuclar["instagram"] = ig_res.get("id")
            if sonuclar.get("instagram"):
                with _lock:
                    yeni_basarili.append("instagram")
                    sonuclar.pop("instagram_hata", None)
                _bildir("instagram", "✅ Yayında", increment=True)
            else:
                _bildir("instagram", "❌ Hata", increment=True)
        except Exception as e:
            log.error(f"Telafi Instagram hatası (#{paylasim_id}): {e}")
            with _lock:
                sonuclar["instagram_hata"] = str(e)
            _bildir("instagram", "❌ Hata", increment=True)

    def _telafi_story():
        _bildir("instagram_story", "⏳ Yükleniyor...")
        try:
            if format_tipi == "reels_9_16" and video_yolu:
                log.info(f"Telafi: Instagram Story (Video) yükleniyor (#{paylasim_id}): {video_yolu}")
                story_res = meta.instagram_story_paylas(video_yolu, is_video=True)
                with _lock:
                    sonuclar["instagram_story"] = story_res.get("id")
            elif story_gorseli:
                log.info(f"Telafi: Instagram Story (9:16 Görsel) yükleniyor (#{paylasim_id}): {story_gorseli}")
                story_res = meta.instagram_story_paylas(story_gorseli, is_video=False)
                with _lock:
                    sonuclar["instagram_story"] = story_res.get("id")
            if sonuclar.get("instagram_story"):
                with _lock:
                    yeni_basarili.append("instagram_story")
                    sonuclar.pop("instagram_story_hata", None)
                _bildir("instagram_story", "✅ Yayında", increment=True)
            else:
                _bildir("instagram_story", "❌ Hata", increment=True)
        except Exception as e:
            log.error(f"Telafi Story hatası (#{paylasim_id}): {e}")
            with _lock:
                sonuclar["instagram_story_hata"] = str(e)
            _bildir("instagram_story", "❌ Hata", increment=True)

    def _telafi_threads():
        _bildir("threads", "⏳ Yükleniyor...")
        try:
            log.info(f"Telafi: Threads gönderisi yükleniyor (#{paylasim_id})...")
            if format_tipi == "reels_9_16" and video_yolu:
                th_res = threads.threads_zincir_paylas(caption, video_url_veya_yolu=r2_video_url or video_yolu)
            elif gorsel_yolu:
                th_res = threads.threads_zincir_paylas(caption, gorsel_url_veya_yolu=r2_gorsel_url or gorsel_yolu)
            else:
                th_res = threads.threads_zincir_paylas(caption)
            with _lock:
                sonuclar["threads"] = th_res.get("id")
                sonuclar["threads_parca_sayisi"] = th_res.get("toplam_parca", 1)
                yeni_basarili.append("threads")
                sonuclar.pop("threads_hata", None)
            _bildir("threads", "✅ Yayında", increment=True)
        except Exception as e:
            log.error(f"Telafi Threads hatası (#{paylasim_id}): {e}")
            with _lock:
                sonuclar["threads_hata"] = str(e)
            _bildir("threads", "❌ Hata", increment=True)

    def _telafi_facebook():
        _bildir("facebook", "⏳ Yükleniyor...")
        try:
            if format_tipi == "reels_9_16" and video_yolu:
                log.info(f"Telafi: Facebook Reels yükleniyor (#{paylasim_id})...")
                fb_res = meta.facebook_reels_paylas(video_yolu, caption=caption)
                with _lock:
                    sonuclar["facebook"] = fb_res.get("id") or fb_res.get("video_id")
            else:
                log.info(f"Telafi: Facebook postu yükleniyor (#{paylasim_id})...")
                fb_res = meta.facebook_post_paylas(caption, gorsel_yolu=gorsel_yolu)
                with _lock:
                    sonuclar["facebook"] = fb_res.get("id")
            with _lock:
                yeni_basarili.append("facebook")
                sonuclar.pop("facebook_hata", None)
            _bildir("facebook", "✅ Yayında", increment=True)
        except Exception as e:
            log.error(f"Telafi Facebook hatası (#{paylasim_id}): {e}")
            with _lock:
                sonuclar["facebook_hata"] = str(e)
            _bildir("facebook", "❌ Hata", increment=True)

    def _telafi_youtube():
        _bildir("youtube", "⏳ Yükleniyor...")
        try:
            if youtube.CLIENT_SECRET_DOSYASI.exists() or youtube.TOKEN_DOSYASI.exists():
                log.info(f"Telafi: YouTube Shorts yükleniyor (#{paylasim_id})...")
                baslik = kayit.get("baslik") or "Günün Ayeti • Ezan Plus"
                yt_res = youtube.youtube_shorts_yukle(video_yolu=video_yolu, baslik=baslik, aciklama=caption)
                with _lock:
                    sonuclar["youtube"] = yt_res.get("video_id")
                    sonuclar["youtube_url"] = yt_res.get("url")
                    yeni_basarili.append("youtube")
                    sonuclar.pop("youtube_hata", None)
                _bildir("youtube", "✅ Yayında", increment=True)
            else:
                _bildir("youtube", "⏭️ Atlandı (Yetki Yok)", increment=True)
        except Exception as e:
            log.error(f"Telafi YouTube hatası (#{paylasim_id}): {e}")
            with _lock:
                sonuclar["youtube_hata"] = str(e)
            _bildir("youtube", "❌ Hata", increment=True)

    telafi_haritasi = {
        "tiktok": _telafi_tiktok,
        "instagram": _telafi_instagram,
        "instagram_story": _telafi_story,
        "threads": _telafi_threads,
        "facebook": _telafi_facebook,
        "youtube": _telafi_youtube,
    }

    t_gorevler = [telafi_haritasi[k] for k in telafi_kanallar if k in telafi_haritasi]
    if t_gorevler:
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(6, len(t_gorevler))) as executor:
            futures = [executor.submit(fn) for fn in t_gorevler]
            concurrent.futures.wait(futures)

    # Veritabanı güncelle
    kalan_hatalar = [v for k, v in sonuclar.items() if k.endswith("_hata")]
    db.durum_guncelle(
        paylasim_id,
        yeni_durum="yayinlandi",
        hata_mesaji="; ".join(kalan_hatalar) if kalan_hatalar else None,
        instagram_post_id=sonuclar.get("instagram"),
        instagram_story_post_id=sonuclar.get("instagram_story"),
        youtube_post_id=sonuclar.get("youtube"),
        tiktok_post_id=sonuclar.get("tiktok"),
        threads_post_id=sonuclar.get("threads"),
        facebook_post_id=sonuclar.get("facebook"),
    )
    sonuclar["yeni_basarili"] = yeni_basarili
    return sonuclar


def yayindan_kaldir(paylasim_id: int) -> Dict[str, Any]:
    """
    Daha önce yayınlanmış bir içeriği tüm platformlardan (Meta, YouTube, Threads)
    ve sistem veritabanından / yayın geçmişinden siler.
    """
    kayit = db.paylasim_getir(paylasim_id)
    if not kayit:
        raise ValueError(f"Silinecek paylaşım bulunamadı: ID {paylasim_id}")

    sonuclar: Dict[str, bool] = {}

    # 1. Instagram / Facebook (Meta Graph API)
    ig_id = kayit.get("instagram_post_id")
    if ig_id:
        try:
            log.info(f"Instagram Feed'den içerik siliniyor: {ig_id}")
            sonuclar["instagram"] = meta.medyayi_sil(ig_id)
        except Exception as e:
            log.error(f"Instagram silme hatası ({ig_id}): {e}")
            sonuclar["instagram"] = False

    ig_story_id = kayit.get("instagram_story_post_id")
    if ig_story_id:
        try:
            log.info(f"Instagram Story'den içerik siliniyor: {ig_story_id}")
            sonuclar["instagram_story"] = meta.medyayi_sil(ig_story_id)
        except Exception as e:
            log.error(f"Instagram Story silme hatası ({ig_story_id}): {e}")
            sonuclar["instagram_story"] = False

    fb_id = kayit.get("facebook_post_id")
    if fb_id:
        try:
            log.info(f"Facebook'tan içerik siliniyor: {fb_id}")
            sonuclar["facebook"] = meta.medyayi_sil(fb_id)
        except Exception as e:
            log.error(f"Facebook silme hatası ({fb_id}): {e}")
            sonuclar["facebook"] = False

    # 2. YouTube Shorts
    yt_id = kayit.get("youtube_post_id")
    if yt_id:
        try:
            log.info(f"YouTube'dan video siliniyor: {yt_id}")
            sonuclar["youtube"] = youtube.videoyu_sil(yt_id)
        except Exception as e:
            log.error(f"YouTube silme hatası ({yt_id}): {e}")
            sonuclar["youtube"] = False

    # 3. Threads
    th_id = kayit.get("threads_post_id")
    if th_id:
        try:
            log.info(f"Threads'ten gönderi siliniyor: {th_id}")
            sonuclar["threads"] = threads.gonderiyi_sil(th_id)
        except Exception as e:
            log.error(f"Threads silme hatası ({th_id}): {e}")
            sonuclar["threads"] = False

    # 4. Veritabanını ve JSON yayın geçmişini güncelle
    db.durum_guncelle(paylasim_id, yeni_durum="yayindan_kaldirildi")
    log.info(f"Paylaşım #{paylasim_id} başarıyla yayından kaldırıldı: {sonuclar}")
    return sonuclar

