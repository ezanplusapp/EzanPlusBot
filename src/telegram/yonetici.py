"""
src/telegram/yonetici.py — Çoklu Platform Yayın Dağıtım Yöneticisi
Telegram'dan onaylanan içerikleri eş zamanlı ve hataya dayanıklı olarak
Instagram Reels + Story, Threads, Facebook Sayfası, YouTube Shorts ve TikTok'a iletir.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from .. import db
from ..platformlar import meta, threads, youtube, tiktok

log = logging.getLogger(__name__)


def yayinla_hepsi(paylasim_id: int) -> Dict[str, Any]:
    """
    Onaylanan içeriği Instagram, Threads, Facebook, YouTube ve TikTok'ta eş zamanlı yayınlar.
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
            return yayinla_telafi(paylasim_id, hedef_kanal="hepsi")

    # Yayın Öncesi Son Güvenlik & Kalite Kapısı
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

    # 1. Instagram Akış (Reels veya Görsel Feed)
    try:
        if format_tipi == "reels_9_16" and video_yolu:
            log.info(f"Instagram'a Reels yükleniyor: {video_yolu}")
            ig_res = meta.instagram_reels_paylas(video_yolu, caption)
            sonuclar["instagram"] = ig_res.get("id")
        elif gorsel_yolu:
            log.info(f"Instagram'a Görsel Feed (4:5) yükleniyor: {gorsel_yolu}")
            ig_res = meta.instagram_gorsel_paylas(gorsel_yolu, caption)
            sonuclar["instagram"] = ig_res.get("id")
    except Exception as e:
        log.error(f"Instagram yayınlama hatası: {e}")
        sonuclar["instagram_hata"] = str(e)

    # 1b. Instagram Story (Video veya Özel 9:16 Story Görseli)
    try:
        if format_tipi == "reels_9_16" and video_yolu:
            log.info(f"Instagram Story (Video) yükleniyor: {video_yolu}")
            story_res = meta.instagram_story_paylas(video_yolu, is_video=True)
            sonuclar["instagram_story"] = story_res.get("id")
        elif story_gorseli:
            log.info(f"Instagram Story (Özel 9:16 Görsel) yükleniyor: {story_gorseli}")
            story_res = meta.instagram_story_paylas(story_gorseli, is_video=False)
            sonuclar["instagram_story"] = story_res.get("id")
    except Exception as e:
        log.error(f"Instagram Story yayınlama hatası: {e}")
        sonuclar["instagram_story_hata"] = str(e)

    # 2. Threads (Akıllı Parçalanmış Zincir Gönderi)
    if threads.threads_aktif_mi():
        try:
            log.info("Threads'e zincir gönderi yükleniyor...")
            if format_tipi == "reels_9_16" and video_yolu:
                th_res = threads.threads_zincir_paylas(caption, video_url_veya_yolu=video_yolu)
            elif gorsel_yolu:
                th_res = threads.threads_zincir_paylas(caption, gorsel_url_veya_yolu=gorsel_yolu)
            else:
                th_res = threads.threads_zincir_paylas(caption)
            sonuclar["threads"] = th_res.get("id")
            sonuclar["threads_parca_sayisi"] = th_res.get("toplam_parca", 1)
        except Exception as e:
            log.error(f"Threads yayınlama hatası: {e}")
            sonuclar["threads_hata"] = str(e)
    else:
        log.info("Threads API jetonu tanımlı değil veya geçersiz; Threads yayını güvenle atlandı (OAuth 190 riski sıfır).")

    # 3. Facebook Sayfası
    try:
        log.info("Facebook Sayfasına paylaşım yapılıyor...")
        fb_res = meta.facebook_post_paylas(caption, gorsel_yolu=gorsel_yolu)
        sonuclar["facebook"] = fb_res.get("id")
    except Exception as e:
        log.error(f"Facebook sayfa yayınlama hatası: {e}")
        sonuclar["facebook_hata"] = str(e)

    # 4. YouTube Shorts
    if format_tipi == "reels_9_16" and video_yolu:
        try:
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

    # 5. TikTok Direct Post
    if format_tipi == "reels_9_16" and video_yolu:
        try:
            key = os.getenv("TIKTOK_CLIENT_KEY")
            if key and tiktok.TOKEN_DOSYASI.exists():
                log.info(f"TikTok'a yükleniyor: {video_yolu}")
                baslik = kayit.get("baslik") or "Ezan Plus • Günün Ayeti"
                tt_res = tiktok.tiktok_video_yukle(
                    video_yolu=video_yolu,
                    baslik=baslik,
                    aciklama=caption,
                )
                sonuclar["tiktok"] = tt_res.get("publish_id")
        except Exception as e:
            log.error(f"TikTok yayınlama hatası: {e}")
            sonuclar["tiktok_hata"] = str(e)

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


def yayinla_telafi(paylasim_id: int, hedef_kanal: str = "hepsi") -> Dict[str, Any]:
    """
    Kısmi veya başarısız yayınları telafi eder.
    Zaten yayınlanmış platformları (id'si mevcut olanları) KORUR ve atlar;
    yalnızca eksik/başarısız olan veya hedef_kanal olarak belirtilen platformları yeniden yayınlar.
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

    # 1. Instagram Akış (Reels veya Görsel Feed)
    if (hedef in ("hepsi", "instagram", "ig")) and not sonuclar.get("instagram"):
        try:
            if format_tipi == "reels_9_16" and video_yolu:
                log.info(f"Telafi: Instagram'a Reels yükleniyor (#{paylasim_id}): {video_yolu}")
                ig_res = meta.instagram_reels_paylas(video_yolu, caption)
                sonuclar["instagram"] = ig_res.get("id")
            elif gorsel_yolu:
                log.info(f"Telafi: Instagram'a Görsel Feed (4:5) yükleniyor (#{paylasim_id}): {gorsel_yolu}")
                ig_res = meta.instagram_gorsel_paylas(gorsel_yolu, caption)
                sonuclar["instagram"] = ig_res.get("id")
            if sonuclar.get("instagram"):
                yeni_basarili.append("instagram")
                sonuclar.pop("instagram_hata", None)
        except Exception as e:
            log.error(f"Telafi Instagram hatası (#{paylasim_id}): {e}")
            sonuclar["instagram_hata"] = str(e)

    # 2. Instagram Story
    if (hedef in ("hepsi", "instagram_story", "story")) and not sonuclar.get("instagram_story"):
        try:
            if format_tipi == "reels_9_16" and video_yolu:
                log.info(f"Telafi: Instagram Story (Video) yükleniyor (#{paylasim_id}): {video_yolu}")
                story_res = meta.instagram_story_paylas(video_yolu, is_video=True)
                sonuclar["instagram_story"] = story_res.get("id")
            elif story_gorseli:
                log.info(f"Telafi: Instagram Story (9:16 Görsel) yükleniyor (#{paylasim_id}): {story_gorseli}")
                story_res = meta.instagram_story_paylas(story_gorseli, is_video=False)
                sonuclar["instagram_story"] = story_res.get("id")
            if sonuclar.get("instagram_story"):
                yeni_basarili.append("instagram_story")
                sonuclar.pop("instagram_story_hata", None)
        except Exception as e:
            log.error(f"Telafi Story hatası (#{paylasim_id}): {e}")
            sonuclar["instagram_story_hata"] = str(e)

    # 3. Threads
    if (hedef in ("hepsi", "threads")) and not sonuclar.get("threads") and threads.threads_aktif_mi():
        try:
            log.info(f"Telafi: Threads gönderisi yükleniyor (#{paylasim_id})...")
            if format_tipi == "reels_9_16" and video_yolu:
                th_res = threads.threads_zincir_paylas(caption, video_url_veya_yolu=video_yolu)
            elif gorsel_yolu:
                th_res = threads.threads_zincir_paylas(caption, gorsel_url_veya_yolu=gorsel_yolu)
            else:
                th_res = threads.threads_zincir_paylas(caption)
            sonuclar["threads"] = th_res.get("id")
            sonuclar["threads_parca_sayisi"] = th_res.get("toplam_parca", 1)
            yeni_basarili.append("threads")
            sonuclar.pop("threads_hata", None)
        except Exception as e:
            log.error(f"Telafi Threads hatası (#{paylasim_id}): {e}")
            sonuclar["threads_hata"] = str(e)

    # 4. Facebook
    if (hedef in ("hepsi", "facebook", "fb")) and not sonuclar.get("facebook"):
        try:
            log.info(f"Telafi: Facebook postu yükleniyor (#{paylasim_id})...")
            fb_res = meta.facebook_post_paylas(caption, gorsel_yolu=gorsel_yolu)
            sonuclar["facebook"] = fb_res.get("id")
            yeni_basarili.append("facebook")
            sonuclar.pop("facebook_hata", None)
        except Exception as e:
            log.error(f"Telafi Facebook hatası (#{paylasim_id}): {e}")
            sonuclar["facebook_hata"] = str(e)

    # 5. YouTube Shorts
    if format_tipi == "reels_9_16" and video_yolu and (hedef in ("hepsi", "youtube", "yt")) and not sonuclar.get("youtube"):
        try:
            if youtube.CLIENT_SECRET_DOSYASI.exists() or youtube.TOKEN_DOSYASI.exists():
                log.info(f"Telafi: YouTube Shorts yükleniyor (#{paylasim_id})...")
                baslik = kayit.get("baslik") or "Günün Ayeti • Ezan Plus"
                yt_res = youtube.youtube_shorts_yukle(video_yolu=video_yolu, baslik=baslik, aciklama=caption)
                sonuclar["youtube"] = yt_res.get("video_id")
                sonuclar["youtube_url"] = yt_res.get("url")
                yeni_basarili.append("youtube")
                sonuclar.pop("youtube_hata", None)
        except Exception as e:
            log.error(f"Telafi YouTube hatası (#{paylasim_id}): {e}")
            sonuclar["youtube_hata"] = str(e)

    # 6. TikTok
    if format_tipi == "reels_9_16" and video_yolu and (hedef in ("hepsi", "tiktok", "tt")) and not sonuclar.get("tiktok"):
        try:
            key = os.getenv("TIKTOK_CLIENT_KEY")
            if key and tiktok.TOKEN_DOSYASI.exists():
                log.info(f"Telafi: TikTok yükleniyor (#{paylasim_id})...")
                baslik = kayit.get("baslik") or "Ezan Plus • Günün Ayeti"
                tt_res = tiktok.tiktok_video_yukle(video_yolu=video_yolu, baslik=baslik, aciklama=caption)
                sonuclar["tiktok"] = tt_res.get("publish_id")
                yeni_basarili.append("tiktok")
                sonuclar.pop("tiktok_hata", None)
        except Exception as e:
            log.error(f"Telafi TikTok hatası (#{paylasim_id}): {e}")
            sonuclar["tiktok_hata"] = str(e)

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

