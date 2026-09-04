"""
otomasyon.py — Ezan Plus Sosyal Medya Otomasyon ve Orkestrasyon Motoru
Gemini AI ile içerik üretir, görsel/video şablonlarını çizer, veritabanına kaydeder
ve Telegram grubuna onay butonuyla iletir.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

from . import db
from . import icerik_uret
from . import sablon_ciz
from . import ses_getir
from . import video_motoru
from . import telegram_bot

log = logging.getLogger(__name__)


def reels_icerigi_olustur_ve_gonder(tema: Optional[str] = None) -> int:
    """
    1. Gemini ile ayet içeriği üretir.
    2. EveryAyah üzerinden sesini indirir.
    3. 1080x1920 dikey Reels videosunu oluşturur.
    4. SQLite veritabanına kaydeder.
    5. Telegram 'Ezan Plus Onay' grubuna onay butonlarıyla iletir.
    """
    log.info("1/5: Gemini AI ile Reels için ayet içeriği üretiliyor...")
    icerik = icerik_uret.ayet_icerigi_uret(tema=tema)

    sure_no = int(icerik.get("sure_no", 94))
    ayet_no = int(icerik.get("ayet_no", 5))
    sure_ayet_etiket = icerik.get("sure_ayet_etiket", f"{sure_no}. Sure, {ayet_no}. Ayet")
    turkce_meal = icerik.get("turkce_meal", "")
    arapca_metin = icerik.get("arapca_metin", "")
    caption = icerik.get("instagram_caption", "")

    log.info(f"2/5: Ayet sesi indiriliyor (Sure: {sure_no}, Ayet: {ayet_no})...")
    try:
        ses_yolu = ses_getir.ayet_sesi_indir(sure_no, ayet_no)
    except Exception as e:
        log.warning(f"Ayet sesi indirilemedi ({e}), yedek ses deneniyor...")
        # Eğer belirtilen ayet sesinde sorun çıkarsa İnşirah 5-6 yedek kullanılır
        ses_yolu = ses_getir.sure_aralik_indir(94, 5, 6, "insirah_5_6.mp3")

    log.info(f"3/5: 9:16 Dikey Reels videosu render ediliyor ({sure_ayet_etiket})...")
    dosya_adi = f"reels_{sure_no}_{ayet_no}_{int(time.time())}.mp4"
    # Resmi QuranCDN kelime zaman damgalarını al (Mişari Alafasy stüdyo senkronizasyonu)
    kelime_zamanlari = ses_getir.ayet_kelime_zamanlari_getir(sure_no, ayet_no)
    if kelime_zamanlari:
        log.info(f"Mişari Râşid Alafasy kelime zaman damgaları başarıyla yüklendi: {len(kelime_zamanlari)} kelime")

    video_yolu = video_motoru.reels_videosu_uret(
        sure_ayet=sure_ayet_etiket,
        turkce_meal=turkce_meal,
        ses_yolu=ses_yolu,
        arapca_metin=arapca_metin,
        arapca_okunus=icerik.get("arapca_okunus"),
        video_baslik_satir1=icerik.get("video_baslik_satir1"),
        video_baslik_satir2=icerik.get("video_baslik_satir2"),
        tefekkur_notu=icerik.get("tefekkur_notu"),
        hafiz_adi=icerik.get("hafiz_adi", "Mişari Râşid el-Afâsî"),
        cikti_adi=dosya_adi,
        kelime_zamanlari=kelime_zamanlari,
    )

    log.info("4/5: Veritabanına kayıt ekleniyor...")
    paylasim_id = db.paylasim_ekle(
        kategori="ayet",
        format_tipi="reels_9_16",
        turkce_metin=turkce_meal,
        baslik=sure_ayet_etiket,
        arapca_metin=arapca_metin,
        kaynak=sure_ayet_etiket,
        tefekkur=icerik.get("tefekkur_notu"),
        caption=caption,
        video_yolu=str(video_yolu),
        gorsel_yollari=[str(video_yolu.with_suffix(".png"))],
        ses_yolu=str(ses_yolu),
        durum="taslak",
    )

    log.info("5/5: Telegram grubuna önizleme ve onay butonları gönderiliyor...")
    telegram_bot.onay_istegi_gonder(paylasim_id)

    log.info(f"Reels içeriği hazırlandı ve onaya sunuldu! Paylaşım ID: {paylasim_id}")
    return paylasim_id


def gorsel_icerik_olustur_ve_gonder(kategori: str = "ayet", tema: Optional[str] = None) -> int:
    """
    1080x1350 formatında tekil görsel post üretip Telegram grubuna gönderir.
    """
    dosya_eki = int(time.time())

    if kategori == "ayet":
        icerik = icerik_uret.ayet_icerigi_uret(tema=tema)
        turkce = icerik.get("turkce_meal", "")
        arapca = icerik.get("arapca_metin", "")
        kaynak = icerik.get("sure_ayet_etiket", "Günün Ayeti")
        tefekkur = icerik.get("tefekkur_notu")
        caption = icerik.get("instagram_caption", "")

        gorsel_yolu = sablon_ciz.ayet_karti_ciz(
            sure_ayet=kaynak,
            turkce_meal=turkce,
            arapca_metin=arapca,
            tefekkur_notu=tefekkur,
            cikti_dosya_adi=f"ayet_{dosya_eki}.png",
        )

    elif kategori == "hadis":
        icerik = icerik_uret.hadis_icerigi_uret(tema=tema)
        turkce = icerik.get("hadis_metni", "")
        kaynak = icerik.get("kaynak_ravi", "Hadis-i Şerif")
        tefekkur = icerik.get("tefekkur_notu")
        caption = icerik.get("instagram_caption", "")

        gorsel_yolu = sablon_ciz.hadis_karti_ciz(
            hadis_metni=turkce,
            kaynak=kaynak,
            tefekkur_notu=tefekkur,
            cikti_dosya_adi=f"hadis_{dosya_eki}.png",
        )

    else:  # dua
        icerik = icerik_uret.dua_icerigi_uret(ruh_hali=tema)
        baslik = icerik.get("dua_basligi", "Günün Duası")
        turkce = icerik.get("turkce_anlam", "")
        arapca = icerik.get("arapca_metin")
        kaynak = icerik.get("okunus_veya_fazilet")
        caption = icerik.get("instagram_caption", "")

        gorsel_yolu = sablon_ciz.dua_karti_ciz(
            dua_basligi=baslik,
            turkce_anlam=turkce,
            arapca_metin=arapca,
            kaynak_fazilet=kaynak,
            cikti_dosya_adi=f"dua_{dosya_eki}.png",
        )

    paylasim_id = db.paylasim_ekle(
        kategori=kategori,
        format_tipi="post_4_5",
        turkce_metin=turkce,
        baslik=kaynak,
        arapca_metin=arapca if kategori != "hadis" else None,
        kaynak=kaynak,
        tefekkur=tefekkur if kategori != "dua" else None,
        caption=caption,
        gorsel_yollari=[str(gorsel_yolu)],
        durum="taslak",
    )

    telegram_bot.onay_istegi_gonder(paylasim_id)
    log.info(f"Görsel post hazırlandı ve onaya sunuldu! Paylaşım ID: {paylasim_id}")
    return paylasim_id


def dinle_ve_bekle(sure_saniye: int = 120):
    """
    Belirtilen süre boyunca Telegram'daki onay butonlarına basılmasını bekler.
    """
    log.info(f"Telegram onay butonları dinleniyor ({sure_saniye} saniye)...")
    offset = 0
    baslangic = time.time()
    while time.time() - baslangic < sure_saniye:
        offset = telegram_bot.tek_sefer_dinle(offset)
        time.sleep(2)
