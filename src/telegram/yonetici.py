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
    db.durum_guncelle(
        paylasim_id,
        yeni_durum="yayinlandi",
        instagram_post_id=sonuclar.get("instagram"),
        youtube_post_id=sonuclar.get("youtube"),
        tiktok_post_id=sonuclar.get("tiktok"),
        threads_post_id=sonuclar.get("threads"),
        facebook_post_id=sonuclar.get("facebook"),
    )
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
            log.info(f"Instagram'dan içerik siliniyor: {ig_id}")
            sonuclar["instagram"] = meta.medyayi_sil(ig_id)
        except Exception as e:
            log.error(f"Instagram silme hatası ({ig_id}): {e}")
            sonuclar["instagram"] = False

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

