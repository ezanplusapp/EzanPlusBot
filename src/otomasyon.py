"""
otomasyon.py — Ezan Plus Sosyal Medya Otomasyon ve Orkestrasyon Motoru
Gemini AI ile içerik üretir, görsel/video şablonlarını çizer, veritabanına kaydeder
ve Telegram grubuna onay butonuyla iletir.
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import db
from .uretim import ai as icerik_uret
from .uretim import kart as sablon_ciz
from .uretim import ses as ses_getir
from .uretim import video as video_motoru
from .ayar import KOK_DIZIN, get_env
from .telegram import bot as telegram_bot

log = logging.getLogger(__name__)


def otomatik_yayinla_ve_raporla(paylasim_id: int, durum_mesaj_id: Optional[int] = None) -> Dict[str, Any]:
    """
    İnstabot parite standardında canlı yayın dağıtımı ve raporlaması yapar.
    Ayrı mesaj atmak yerine tek bir canlı mesajı gerçek zamanlı günceller (0.8s throttling ve canlı butonlar).
    """
    _, chat_id = telegram_bot.get_token_ve_chat_id()
    kayit = db.paylasim_getir(paylasim_id) or {}
    b_str = kayit.get("baslik") or f"Paylaşım #{paylasim_id}"
    f_tip = kayit.get("format", "reels_9_16")
    t_start = time.time()

    canli_mid = durum_mesaj_id
    if not canli_mid and chat_id:
        canli_mid = telegram_bot.mesaj_gonder(
            f"⏳ <b>YAYIN DAĞITIMI BAŞLATILIYOR (#{paylasim_id})...</b>\nLütfen bekleyin...",
            chat_id=str(chat_id)
        )

    _son_edit = [0.0]
    def _oto_yayin_cb(adim: int, toplam_adim: int, aktif_kanal: str, durumlar: Dict[str, str]):
        if not canli_mid or not chat_id:
            return
        now = time.time()
        if (adim < toplam_adim) and (now - _son_edit[0] < 0.8):
            time.sleep(max(0.0, 0.8 - (now - _son_edit[0])))
        _son_edit[0] = time.time()

        live_txt = telegram_bot.yayin_durum_metni_olustur(
            paylasim_id=paylasim_id,
            adim=adim,
            toplam_adim=toplam_adim,
            durum_haritasi=durumlar,
            baslik=b_str,
            baslangic_ts=t_start,
            format_tipi=f_tip,
        )
        live_btns = telegram_bot.canli_yayin_butonlari_kur(durumlar)
        telegram_bot.caption_ve_buton_guncelle(chat_id, canli_mid, live_txt, butonlar=live_btns)

    sonuclar = telegram_bot.yayinla_hepsi(paylasim_id, durum_cb=_oto_yayin_cb)
    gecen_sure = time.time() - t_start

    # Canlı ilerleme metin mesajını temizle
    if canli_mid and chat_id:
        try:
            telegram_bot.mesaj_sil(chat_id, canli_mid)
        except Exception as e_sil:
            log.debug(f"Canlı ilerleme mesajı silinemedi: {e_sil}")

    # Nihai videoyu/görseli ve açıklamayı içeren detay kartını Telegram grubuna ilet
    try:
        telegram_bot.yayin_detay_karti_gonder(paylasim_id, sonuclar, dagitim_suresi=gecen_sure)
    except Exception as e_detay:
        log.error(f"Yayın detay kartı gönderilemedi (#{paylasim_id}): {e_detay}")
        basari_metni = telegram_bot.yayin_raporu_metni_kur(kayit, sonuclar, dagitim_suresi=gecen_sure)
        yeni_butonlar = telegram_bot.telafi_butonlari_kur(paylasim_id, sonuclar, f_tip)
        if chat_id:
            telegram_bot.mesaj_gonder(basari_metni, chat_id=str(chat_id), butonlar=yeni_butonlar)

    return sonuclar


def reels_icerigi_olustur_ve_gonder(
    tema: Optional[str] = None,
    auto_publish: bool = True,
    durum_mesaj_id: Optional[int] = None,
) -> int:
    """
    1. Gemini ile ayet içeriği üretir.
    2. EveryAyah üzerinden sesini indirir.
    3. 1080x1920 dikey Reels videosunu oluşturur.
    4. SQLite veritabanına kaydeder.
    5. Telegram 'Ezan Plus Onay' grubuna onay butonlarıyla iletir.
    """
    _, chat_id = telegram_bot.get_token_ve_chat_id()
    if durum_mesaj_id and chat_id:
        telegram_bot.durum_guncelle(chat_id, durum_mesaj_id, "Kur'an Tilaveti Reels", 1, 4, "Âyet ve meal tescilli kaynaktan alınıyor...")

    log.info("1/5: Gemini AI ile Reels için ayet içeriği üretiliyor...")
    icerik = icerik_uret.ayet_icerigi_uret(tema=tema)

    sure_no = int(icerik.get("sure_no", 94))
    ayet_no = int(icerik.get("ayet_no", 5))
    sure_ayet_etiket = icerik.get("sure_ayet_etiket", f"{sure_no}. Sure, {ayet_no}. Ayet")
    turkce_meal = icerik.get("turkce_meal", "")
    arapca_metin = icerik.get("arapca_metin", "")
    caption = icerik.get("instagram_caption", "")

    if durum_mesaj_id and chat_id:
        telegram_bot.durum_guncelle(chat_id, durum_mesaj_id, "Kur'an Tilaveti Reels", 2, 4, f"Mişari Alafasy tilaveti indiriliyor ({sure_no}:{ayet_no})...")

    log.info(f"2/5: Ayet sesi indiriliyor (Sure: {sure_no}, Ayet: {ayet_no})...")
    try:
        ses_yolu = ses_getir.ayet_sesi_indir(sure_no, ayet_no)
    except Exception as e:
        log.warning(f"Ayet sesi indirilemedi ({e}), yedek ses deneniyor...")
        # Eğer belirtilen ayet sesinde sorun çıkarsa İnşirah 5-6 yedek kullanılır
        ses_yolu = ses_getir.sure_aralik_indir(94, 5, 6, "insirah_5_6.mp3")

    if durum_mesaj_id and chat_id:
        telegram_bot.durum_guncelle(chat_id, durum_mesaj_id, "Kur'an Tilaveti Reels", 3, 4, "1080x1920 dikey video ve karaoke render ediliyor...")

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
        latin_kelimeler=icerik.get("latin_kelimeler"),
    )

    if durum_mesaj_id and chat_id:
        telegram_bot.durum_guncelle(chat_id, durum_mesaj_id, "Kur'an Tilaveti Reels", 4, 4, "Kalite kontrolü yapılıyor ve yayınlanıyor...")

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

    # 4.5/5: Yayın Öncesi Kalite, Taşma & Boyut Denetimi
    from . import denetleyici
    denetim = denetleyici.denetle_paylasim(paylasim_id)
    if not denetim.gecerli:
        log.warning(f"Reels #{paylasim_id} kalite denetiminde eksikler tespit etti, otomatik onarım deneniyor...")
        onarildi, duzeltmeler = denetleyici.otomatik_onar(paylasim_id)
        if onarildi:
            denetim = denetleyici.denetle_paylasim(paylasim_id)
            log.info(f"Reels #{paylasim_id} başarıyla otomatik onarıldı ve doğrulandı! Düzeltmeler: {duzeltmeler}")
        else:
            hata_metni = "\n".join(f"• {h}" for h in denetim.hatalar)
            log.critical(f"Reels #{paylasim_id} kalite denetiminden GEÇEMEDİ ve onarılamadı:\n{hata_metni}")
            db.durum_guncelle(paylasim_id, yeni_durum="iptal_edildi", hata_mesaji=hata_metni)
            telegram_bot.mesaj_gonder(denetim.formatli_rapor())
            raise RuntimeError(f"Yayın öncesi kalite kontrolü başarısız oldu: {denetim.hatalar}")

    log.info(f"🛡️ Kalite kontrolü BAŞARILI: {denetim.metrikler}")

    if auto_publish:
        log.info("5/5: Kur'an tilaveti otomatik olarak canlı takiple yayınlanıyor...")
        sonuclar = otomatik_yayinla_ve_raporla(paylasim_id, durum_mesaj_id=durum_mesaj_id)
        log.info(f"Reels tilaveti başarıyla yayınlandı ve Telegram'a raporlandı! Paylaşım ID: {paylasim_id}")
    else:
        if durum_mesaj_id and chat_id:
            telegram_bot.mesaj_sil(chat_id, durum_mesaj_id)
        telegram_bot.onay_istegi_gonder(paylasim_id)
        log.info(f"Reels #{paylasim_id} Telegram grubuna onaya sunuldu!")

    return paylasim_id


def gorsel_icerik_olustur_ve_gonder(
    kategori: str = "kelime",
    tema: Optional[str] = None,
    format_tipi: str = "4:5",
    auto_publish: bool = True,
    durum_mesaj_id: Optional[int] = None,
) -> int:
    """
    4:5 (Feed) ve 9:16 (Story) formatlarında tescilli görsel post üretip Telegram grubuna onay için gönderir.
    Sistemde yalnızca Kur'an Sözlüğü (kelime) görsel kart formatında üretilir.
    Ayet, Hadis ve Dua içerikleri resmi standart olarak video motorlarına yönlendirilir.
    auto_publish=True olduğunda onay beklemeden doğrudan tüm platformlara yayınlar.
    """
    if kategori in ("ayet", "kuran"):
        log.info("Ayet içeriği için statik kart formatı kaldırılmıştır. 9:16 Kur'an Tilaveti Reels videosuna yönlendiriliyor...")
        return reels_icerigi_olustur_ve_gonder(tema=tema, auto_publish=auto_publish, durum_mesaj_id=durum_mesaj_id)
    elif kategori == "hadis":
        log.info("Hadis içeriği için statik kart formatı kaldırılmıştır. 9:16 V20 Dinamik Hadis videosuna yönlendiriliyor...")
        return hadis_videosu_olustur_ve_gonder(tema=tema, auto_publish=auto_publish, durum_mesaj_id=durum_mesaj_id)
    elif kategori == "dua":
        log.info("Dua içeriği için statik kart formatı kaldırılmıştır. 9:16 V20 Dinamik Dua videosuna yönlendiriliyor...")
        return dua_videosu_olustur_ve_gonder(ruh_hali=tema, auto_publish=auto_publish, durum_mesaj_id=durum_mesaj_id)

    _, chat_id = telegram_bot.get_token_ve_chat_id()
    if durum_mesaj_id and chat_id:
        telegram_bot.durum_guncelle(chat_id, durum_mesaj_id, f"{kategori.capitalize()} Kartı", 1, 3, "Tescilli metin ve anlam hazırlanıyor...")

    dosya_eki = int(time.time())
    format_etiketi = format_tipi.replace(":", "_")
    gorsel_yollari: List[str] = []

    if kategori == "kelime":
        icerik = icerik_uret.kelime_icerigi_uret(kelime_tr=tema)
        kavram_adi = icerik.get("kelime_tr", "Kur'an Sözlüğü")
        arapca_kelime = icerik.get("kelime_ar", "")
        kok = icerik.get("kok", "")
        lugat_anlami = icerik.get("lugat_anlami", "")
        ayet_ornek = icerik.get("kuran_boyutu", "")
        ayet_referans = icerik.get("ayet_ref", "")
        hikmet_notu = icerik.get("hayat_dersi", "")
        caption = icerik.get("instagram_caption", "")
        kaynak = f"Kur'an Sözlüğü • {kavram_adi}"
        turkce = lugat_anlami
        arapca = arapca_kelime
        tefekkur = hikmet_notu

        gorsel_4_5 = sablon_ciz.kelime_karti_ciz(
            kelime_tr=kavram_adi,
            kelime_ar=arapca_kelime,
            okunus=icerik.get("okunus", ""),
            kok=kok,
            lugat_anlami=lugat_anlami,
            kuran_boyutu=ayet_ornek,
            hayat_dersi=hikmet_notu,
            ayet_ref=ayet_referans,
            cikti_dosya_adi=f"kelime_4_5_{dosya_eki}.png",
            format_tipi="4:5",
            palet="yakut_kirmizi",
        )
        gorsel_9_16 = sablon_ciz.kelime_karti_ciz(
            kelime_tr=kavram_adi,
            kelime_ar=arapca_kelime,
            okunus=icerik.get("okunus", ""),
            kok=kok,
            lugat_anlami=lugat_anlami,
            kuran_boyutu=ayet_ornek,
            hayat_dersi=hikmet_notu,
            ayet_ref=ayet_referans,
            cikti_dosya_adi=f"kelime_9_16_{dosya_eki}.png",
            format_tipi="9:16",
            palet="yakut_kirmizi",
        )
        gorsel_yollari = [str(gorsel_4_5), str(gorsel_9_16)]

    else:
        raise ValueError(f"Bilinmeyen içerik kategorisi: {kategori}")

    paylasim_id = db.paylasim_ekle(
        kategori=kategori,
        format_tipi=f"post_{format_etiketi}",
        turkce_metin=turkce,
        baslik=kaynak,
        arapca_metin=arapca,
        kaynak=kaynak,
        tefekkur=tefekkur,
        caption=caption,
        gorsel_yollari=gorsel_yollari,
        durum="taslak",
    )

    # Yayın Öncesi Kalite & Güvenlik Denetimi
    from . import denetleyici
    denetim = denetleyici.denetle_paylasim(paylasim_id)
    if not denetim.gecerli:
        log.warning(f"Görsel post #{paylasim_id} kalite denetiminde eksikler tespit etti, otomatik onarım deneniyor...")
        onarildi, duzeltmeler = denetleyici.otomatik_onar(paylasim_id)
        if onarildi:
            denetim = denetleyici.denetle_paylasim(paylasim_id)
            log.info(f"Görsel post #{paylasim_id} başarıyla otomatik onarıldı ve doğrulandı! Düzeltmeler: {duzeltmeler}")
        else:
            hata_metni = "\n".join(f"• {h}" for h in denetim.hatalar)
            log.critical(f"Görsel post #{paylasim_id} kalite denetiminden GEÇEMEDİ ve onarılamadı:\n{hata_metni}")
            db.durum_guncelle(paylasim_id, yeni_durum="iptal_edildi", hata_mesaji=hata_metni)
            telegram_bot.mesaj_gonder(denetim.formatli_rapor())
            raise RuntimeError(f"Yayın öncesi kalite kontrolü başarısız oldu: {denetim.hatalar}")

    log.info(f"🛡️ Kalite kontrolü BAŞARILI: {denetim.metrikler}")

    if auto_publish:
        log.info(f"Görsel post ({kategori.upper()}) doğrudan tüm platformlara canlı takiple yayınlanıyor...")
        sonuclar = otomatik_yayinla_ve_raporla(paylasim_id, durum_mesaj_id=durum_mesaj_id)
        log.info(f"{kategori.upper()} postu başarıyla yayınlandı ve Telegram'a raporlandı! Paylaşım ID: {paylasim_id}")
    else:
        if durum_mesaj_id and chat_id:
            telegram_bot.mesaj_sil(chat_id, durum_mesaj_id)
        telegram_bot.onay_istegi_gonder(paylasim_id)
        log.info(f"Görsel post ({kategori.upper()} Çift Format 4:5 + 9:16) hazırlandı ve onaya sunuldu! Paylaşım ID: {paylasim_id}")
    return paylasim_id


def hadis_videosu_olustur_ve_gonder(
    tema: Optional[str] = None,
    auto_publish: bool = True,
    durum_mesaj_id: Optional[int] = None,
) -> int:
    """
    Riyâzü's-Sâlihîn hadisinden V20 Çok Sayfalı Dinamik Video üretir:
    - 100% Bold Ibarra Real Nova Türkçe meal karaoke takibi.
    - Arka planda telifsiz Segâh Ney fon müziği.
    - Çok sayfalı 0.45s sinematik crossfade geçişi.
    - Telegram grubuna videolu onay butonuyla iletir.
    """
    _, chat_id = telegram_bot.get_token_ve_chat_id()
    if durum_mesaj_id and chat_id:
        telegram_bot.durum_guncelle(chat_id, durum_mesaj_id, "V20 Hadis Videosu", 1, 4, "Riyâzü's-Sâlihîn külliyatından hadis taranıyor...")

    dosya_eki = int(time.time())
    log.info("1/5: Tescilli külliyattan Sahih Hadis içeriği seçiliyor...")
    icerik = icerik_uret.hadis_icerigi_uret(tema=tema)

    hadis_id = icerik.get("hadis_id")
    turkce_metin = icerik.get("hadis_metni", "")
    from .uretim.ses import hadis_metninden_kaynaklari_temizle, turkce_metin_harf_duzelt
    turkce_metin = turkce_metin_harf_duzelt(hadis_metninden_kaynaklari_temizle(turkce_metin))
    kaynak_ravi = icerik.get("kaynak_ravi", "Hadis-i Şerif")
    tefekkur_notu = icerik.get("tefekkur_notu")
    caption = icerik.get("instagram_caption", "")
    arapca_metin = icerik.get("arapca_metin")
    arapca_okunus = icerik.get("arapca_okunus")
    ravi = icerik.get("ravi")

    spiker_adi = "Adam" if get_env("ELEVENLABS_API_KEY") else "Mazlum Kiper"
    if durum_mesaj_id and chat_id:
        telegram_bot.durum_guncelle(chat_id, durum_mesaj_id, "V20 Hadis Videosu", 2, 4, f"{spiker_adi} sesi ve kelime zamanları üretiliyor...")

    log.info(f"2/5: {spiker_adi} spiker sesi ve kelime zaman damgaları üretiliyor ({kaynak_ravi})...")
    ses_id_etiketi = f"hadis_{hadis_id}" if hadis_id else f"hadis_{dosya_eki}"
    ses_yolu = ses_getir.turkce_tts_uret(
        metin=turkce_metin,
        kategori="hadis",
        icerik_id=ses_id_etiketi,
        ton_promptu="[vakur, manevi ve sakin bir tefekkür tonuyla]",
        zaman_damgasi_al=True
    )

    words_data = ses_getir.turkce_kelime_zamanlari_getir(ses_yolu)
    log.info(f"Kelime zaman damgaları yüklendi: {len(words_data)} kelime")

    if durum_mesaj_id and chat_id:
        telegram_bot.durum_guncelle(chat_id, durum_mesaj_id, "V20 Hadis Videosu", 3, 4, "1080x1920 video, Segâh Ney ve karaoke render ediliyor...")

    log.info("3/5: V20 Çok Sayfalı Dinamik Hadis Videosu render ediliyor...")
    video_yolu = video_motoru.hadis_videosu_uret(
        hadis_metni=turkce_metin,
        kaynak_ref=kaynak_ravi,
        ses_yolu=ses_yolu,
        words_data=words_data,
        arapca_metin=arapca_metin,
        arapca_okunus=arapca_okunus,
        ravi=ravi,
        tefekkur_notu=tefekkur_notu,
        cikti_yolu=KOK_DIZIN / "data" / "cikti" / f"hadis_video_{dosya_eki}.mp4",
        ney_volume=0.48
    )

    if durum_mesaj_id and chat_id:
        telegram_bot.durum_guncelle(chat_id, durum_mesaj_id, "V20 Hadis Videosu", 4, 4, "Kalite kontrolü yapılıyor ve onaya sunuluyor...")

    log.info("4/5: Veritabanına kayıt ekleniyor...")
    paylasim_id = db.paylasim_ekle(
        kategori="hadis",
        format_tipi="reels_9_16",
        turkce_metin=turkce_metin,
        baslik=kaynak_ravi,
        arapca_metin=arapca_metin,
        kaynak=kaynak_ravi,
        tefekkur=tefekkur_notu,
        caption=caption,
        video_yolu=str(video_yolu),
        gorsel_yollari=[str(video_yolu.with_suffix(".png"))],
        ses_yolu=str(ses_yolu),
        durum="taslak",
    )

    if hadis_id:
        from . import hadis_db
        hadis_db.hadisi_paylasildi_isaretle(hadis_id)

    # Kalite Denetimi
    from . import denetleyici
    denetim = denetleyici.denetle_paylasim(paylasim_id)
    if not denetim.gecerli:
        log.warning(f"Hadis Videosu #{paylasim_id} kalite denetiminde eksikler tespit etti, otomatik onarım deneniyor...")
        onarildi, duzeltmeler = denetleyici.otomatik_onar(paylasim_id)
        if onarildi:
            denetim = denetleyici.denetle_paylasim(paylasim_id)
            log.info(f"Hadis Videosu #{paylasim_id} onarıldı: {duzeltmeler}")
        else:
            hata_metni = "\n".join(f"• {h}" for h in denetim.hatalar)
            log.critical(f"Hadis Videosu #{paylasim_id} kalite denetiminden GEÇEMEDİ:\n{hata_metni}")
            db.durum_guncelle(paylasim_id, yeni_durum="iptal_edildi", hata_mesaji=hata_metni)
            telegram_bot.mesaj_gonder(denetim.formatli_rapor())
            raise RuntimeError(f"Yayın öncesi kalite kontrolü başarısız oldu: {denetim.hatalar}")

    log.info(f"🛡️ Kalite kontrolü BAŞARILI: {denetim.metrikler}")

    if auto_publish:
        log.info(f"Hadis Videosu #{paylasim_id} otomatik olarak tüm platformlara canlı takiple yayınlanıyor...")
        sonuclar = otomatik_yayinla_ve_raporla(paylasim_id, durum_mesaj_id=durum_mesaj_id)
        log.info(f"Hadis Videosu #{paylasim_id} başarıyla yayınlandı ve Telegram'a raporlandı!")
    else:
        if durum_mesaj_id and chat_id:
            telegram_bot.mesaj_sil(chat_id, durum_mesaj_id)
        telegram_bot.onay_istegi_gonder(paylasim_id)
        log.info(f"Hadis Videosu #{paylasim_id} Telegram grubuna onaya sunuldu!")
    return paylasim_id


def dua_videosu_olustur_ve_gonder(
    ruh_hali: Optional[str] = None,
    auto_publish: bool = True,
    durum_mesaj_id: Optional[int] = None,
) -> int:
    """
    Tescilli Dua külliyatından V20 Çok Sayfalı Dinamik Video üretir:
    - 100% Bold Ibarra Real Nova Türkçe meal karaoke takibi (Kehribar ton).
    - Arka planda telifsiz Ferahfezâ Ney fon müziği.
    - Çok sayfalı 0.45s sinematik crossfade geçişi.
    - Telegram grubuna videolu onay butonuyla iletir.
    """
    _, chat_id = telegram_bot.get_token_ve_chat_id()
    if durum_mesaj_id and chat_id:
        telegram_bot.durum_guncelle(chat_id, durum_mesaj_id, "V20 Dua Videosu", 1, 4, "Tescilli dualar külliyatından dua taranıyor...")

    dosya_eki = int(time.time())
    log.info("1/5: Tescilli külliyattan Günün Duası içeriği seçiliyor...")
    icerik = icerik_uret.dua_icerigi_uret(ruh_hali=ruh_hali)

    baslik = icerik.get("dua_basligi", "Günün Duası")
    from .uretim.ses import turkce_metin_harf_duzelt
    turkce_anlam = turkce_metin_harf_duzelt(icerik.get("turkce_anlam", ""))
    arapca_metin = icerik.get("arapca_metin")
    arapca_okunus = icerik.get("arapca_okunus")
    fazilet = icerik.get("fazilet_notu") or icerik.get("okunus_veya_fazilet")
    if fazilet and "•" in fazilet:
        parcalar = fazilet.split("•", 1)
        if len(parcalar[0].strip()) < 45:
            fazilet = parcalar[1].strip()
    kaynak_ref = icerik.get("kaynak_ref") or baslik
    caption = icerik.get("instagram_caption", "")

    spiker_adi = "Adam" if get_env("ELEVENLABS_API_KEY") else "Mazlum Kiper"
    if durum_mesaj_id and chat_id:
        telegram_bot.durum_guncelle(chat_id, durum_mesaj_id, "V20 Dua Videosu", 2, 4, f"{spiker_adi} sesi ve kelime zamanları üretiliyor...")

    log.info(f"2/5: {spiker_adi} spiker sesi ve kelime zaman damgaları üretiliyor ({baslik})...")
    ses_yolu = ses_getir.turkce_tts_uret(
        metin=turkce_anlam,
        kategori="dua",
        icerik_id=f"dua_{dosya_eki}",
        ton_promptu="[huzurlu, samimi ve ulvi bir dua tonuyla]",
        zaman_damgasi_al=True
    )

    words_data = ses_getir.turkce_kelime_zamanlari_getir(ses_yolu)
    log.info(f"Kelime zaman damgaları yüklendi: {len(words_data)} kelime")

    if durum_mesaj_id and chat_id:
        telegram_bot.durum_guncelle(chat_id, durum_mesaj_id, "V20 Dua Videosu", 3, 4, "1080x1920 video, Ferahfezâ Ney ve karaoke render ediliyor...")

    log.info("3/5: V20 Çok Sayfalı Dinamik Dua Videosu render ediliyor...")
    video_yolu = video_motoru.dua_videosu_uret(
        turkce_anlam=turkce_anlam,
        dua_basligi=baslik,
        ses_yolu=ses_yolu,
        words_data=words_data,
        arapca_metin=arapca_metin,
        arapca_okunus=arapca_okunus,
        tefekkur_notu=fazilet,
        kaynak_ref=kaynak_ref,
        cikti_yolu=KOK_DIZIN / "data" / "cikti" / f"dua_video_{dosya_eki}.mp4",
        ney_volume=0.48
    )

    if durum_mesaj_id and chat_id:
        telegram_bot.durum_guncelle(chat_id, durum_mesaj_id, "V20 Dua Videosu", 4, 4, "Kalite kontrolü yapılıyor ve onaya sunuluyor...")

    log.info("4/5: Veritabanına kayıt ekleniyor...")
    paylasim_id = db.paylasim_ekle(
        kategori="dua",
        format_tipi="reels_9_16",
        turkce_metin=turkce_anlam,
        baslik=baslik,
        arapca_metin=arapca_metin,
        kaynak=kaynak_ref,
        tefekkur=fazilet,
        caption=caption,
        video_yolu=str(video_yolu),
        gorsel_yollari=[str(video_yolu.with_suffix(".png"))],
        ses_yolu=str(ses_yolu),
        durum="taslak",
    )

    # Kalite Denetimi
    from . import denetleyici
    denetim = denetleyici.denetle_paylasim(paylasim_id)
    if not denetim.gecerli:
        log.warning(f"Dua Videosu #{paylasim_id} kalite denetiminde eksikler tespit etti, otomatik onarım deneniyor...")
        onarildi, duzeltmeler = denetleyici.otomatik_onar(paylasim_id)
        if onarildi:
            denetim = denetleyici.denetle_paylasim(paylasim_id)
            log.info(f"Dua Videosu #{paylasim_id} onarıldı: {duzeltmeler}")
        else:
            hata_metni = "\n".join(f"• {h}" for h in denetim.hatalar)
            log.critical(f"Dua Videosu #{paylasim_id} kalite denetiminden GEÇEMEDİ:\n{hata_metni}")
            db.durum_guncelle(paylasim_id, yeni_durum="iptal_edildi", hata_mesaji=hata_metni)
            telegram_bot.mesaj_gonder(denetim.formatli_rapor())
            raise RuntimeError(f"Yayın öncesi kalite kontrolü başarısız oldu: {denetim.hatalar}")

    log.info(f"🛡️ Kalite kontrolü BAŞARILI: {denetim.metrikler}")

    if auto_publish:
        log.info(f"Dua Videosu #{paylasim_id} otomatik olarak tüm platformlara canlı takiple yayınlanıyor...")
        sonuclar = otomatik_yayinla_ve_raporla(paylasim_id, durum_mesaj_id=durum_mesaj_id)
        log.info(f"Dua Videosu #{paylasim_id} başarıyla yayınlandı ve Telegram'a raporlandı!")
    else:
        if durum_mesaj_id and chat_id:
            telegram_bot.mesaj_sil(chat_id, durum_mesaj_id)
        telegram_bot.onay_istegi_gonder(paylasim_id)
        log.info(f"Dua Videosu #{paylasim_id} Telegram grubuna onaya sunuldu!")

    return paylasim_id


def hadis_veya_dua_sesi_yenile(paylasim_id: int) -> Path:
    """
    Mevcut Hadis veya Dua paylaşımının tescilli metin ve külliyat verisini koruyarak,
    Adam (ElevenLabs / Mazlum Kiper fallback) seslendirmesini alternatif bir manevi ton direktifi ile sıfırdan yeniden üretir,
    videoyu kelime kelime senkronize ederek tekrar render eder.
    """
    import random
    kayit = db.paylasim_getir(paylasim_id)
    if not kayit:
        raise ValueError(f"Paylaşım bulunamadı: ID #{paylasim_id}")

    kategori = kayit.get("kategori", "").lower()
    if kategori not in ("hadis", "dua"):
        raise ValueError(f"Yalnızca Hadis ve Dua video içeriklerinin sesi yenilenebilir. Kategori: {kategori}")

    turkce_metin = kayit.get("turkce_metin", "")
    if kategori == "hadis":
        from .uretim.ses import hadis_metninden_kaynaklari_temizle
        turkce_metin = hadis_metninden_kaynaklari_temizle(turkce_metin)
    baslik = kayit.get("baslik") or ""
    kaynak = kayit.get("kaynak") or baslik
    arapca_metin = kayit.get("arapca_metin")
    arapca_okunus = kayit.get("arapca_okunus")
    tefekkur = kayit.get("tefekkur")
    dosya_eki = int(time.time())

    # Alternatif Manevi Ton Direktifleri (Fish Audio S2.1 için)
    HADIS_TONLARI = [
        "[vakur, manevi ve sakin bir tefekkür tonuyla]",
        "[derin, etkileyici, yavaş ve tane tane bir hitabetle]",
        "[samimi, vakur ve hikmet dolu bir edayla]",
        "[tok, asil ve etkileyici bir spiker ses tonuyla]",
        "[kalbe dokunan, huzurlu ve vakur bir tonda]",
    ]
    DUA_TONLARI = [
        "[huzurlu, samimi ve ulvi bir dua tonuyla]",
        "[kalbe dokunan, içten, duygusal ve yalvarış dolu bir nida ile]",
        "[derin bir huşu, sükunet ve tevazu içinde]",
        "[yavaş, tane tane, vakur ve kalbi titreten bir niyazla]",
        "[içten bir münacat ve teslimiyet edasıyla]",
    ]

    secilen_ton = random.choice(HADIS_TONLARI if kategori == "hadis" else DUA_TONLARI)
    log.info(f"🎙️ Yeniden seslendirme başlatılıyor (#{paylasim_id} - {kategori}). Ton: {secilen_ton}")

    # 1. Yeni ses üret (overwrite=True ve yeni içerik id'si ile önbellek baypas edilir)
    yeni_icerik_id = f"{kategori}_{paylasim_id}_v{dosya_eki}"
    yeni_ses_yolu = ses_getir.turkce_tts_uret(
        metin=turkce_metin,
        kategori=kategori,
        icerik_id=yeni_icerik_id,
        ton_promptu=secilen_ton,
        zaman_damgasi_al=True,
        overwrite=True,
    )

    words_data = ses_getir.turkce_kelime_zamanlari_getir(yeni_ses_yolu)
    log.info(f"Yeni kelime zaman damgaları yüklendi: {len(words_data)} kelime")

    # 2. Videoyu yeniden render et
    if kategori == "hadis":
        yeni_video_yolu = video_motoru.hadis_videosu_uret(
            hadis_metni=turkce_metin,
            kaynak_ref=kaynak,
            ses_yolu=yeni_ses_yolu,
            words_data=words_data,
            arapca_metin=arapca_metin,
            arapca_okunus=arapca_okunus,
            tefekkur_notu=tefekkur,
            cikti_yolu=KOK_DIZIN / "data" / "cikti" / f"hadis_video_{dosya_eki}.mp4",
            ney_volume=0.48,
        )
    else:  # dua
        yeni_video_yolu = video_motoru.dua_videosu_uret(
            turkce_anlam=turkce_metin,
            dua_basligi=baslik or "Günün Duası",
            ses_yolu=yeni_ses_yolu,
            words_data=words_data,
            arapca_metin=arapca_metin,
            arapca_okunus=arapca_okunus,
            tefekkur_notu=tefekkur,
            kaynak_ref=kaynak,
            cikti_yolu=KOK_DIZIN / "data" / "cikti" / f"dua_video_{dosya_eki}.mp4",
            ney_volume=0.48,
        )

    # 3. Veritabanını güncelle
    db.paylasim_guncelle(
        paylasim_id,
        video_yolu=str(yeni_video_yolu),
        ses_yolu=str(yeni_ses_yolu),
        gorsel_yollari=[str(yeni_video_yolu.with_suffix(".png"))],
    )
    log.info(f"✅ Paylaşım #{paylasim_id} yeni ses ve video ile güncellendi: {yeni_video_yolu}")
    return yeni_video_yolu


def hadis_postu_olustur_ve_gonder(
    tema: Optional[str] = None,
    format_tipi: str = "video",
    auto_publish: bool = True,
    durum_mesaj_id: Optional[int] = None,
) -> int:
    """Sahih Hadis-i Şerif V20 Dinamik Videosu üretip doğrudan otomatik yayınlar."""
    return hadis_videosu_olustur_ve_gonder(tema=tema, auto_publish=auto_publish, durum_mesaj_id=durum_mesaj_id)


def dua_postu_olustur_ve_gonder(
    ruh_hali: Optional[str] = None,
    format_tipi: str = "video",
    auto_publish: bool = True,
    durum_mesaj_id: Optional[int] = None,
) -> int:
    """Günün Duası / Manevi Niyaz V20 Dinamik Videosu üretip doğrudan otomatik yayınlar."""
    return dua_videosu_olustur_ve_gonder(ruh_hali=ruh_hali, auto_publish=auto_publish, durum_mesaj_id=durum_mesaj_id)


def kelime_postu_olustur_ve_gonder(
    kavram: Optional[str] = None,
    format_tipi: str = "4:5",
    auto_publish: bool = True,
    durum_mesaj_id: Optional[int] = None,
) -> int:
    """Kur'an Sözlüğü & İslami Kavramlar kartı üretip doğrudan otomatik yayınlar (onay beklemez)."""
    return gorsel_icerik_olustur_ve_gonder(kategori="kelime", tema=kavram, format_tipi=format_tipi, auto_publish=auto_publish, durum_mesaj_id=durum_mesaj_id)


def icerik_olustur_ve_gonder(
    tur: str = "reels",
    tema: Optional[str] = None,
    format_tipi: str = "4:5",
    auto_publish: Optional[bool] = None,
    durum_mesaj_id: Optional[int] = None,
) -> int:
    """
    Belirtilen türe göre (reels, hadis, dua, kelime, ayet) içeriği üretip doğrudan otomatik yayınlar.
    Tüm içerik türleri (Kur'an Tilaveti, Sahih Hadis, Günün Duası, Kur'an Sözlüğü) varsayılan olarak doğrudan otomatik yayınlanır (onay beklemez).
    Telegram grubuna video/kart ile birlikte detaylı yayın raporu ve 'Yayından Kaldır' butonları iletilir.
    """
    tur_temiz = tur.lower().strip()
    if tur_temiz in ("reels", "video", "ayet_video", "ayet"):
        oto = True if auto_publish is None else auto_publish
        return reels_icerigi_olustur_ve_gonder(tema=tema, auto_publish=oto, durum_mesaj_id=durum_mesaj_id)
    elif tur_temiz in ("hadis", "hadis_video", "hadis_reels"):
        oto = True if auto_publish is None else auto_publish
        return hadis_videosu_olustur_ve_gonder(tema=tema, auto_publish=oto, durum_mesaj_id=durum_mesaj_id)
    elif tur_temiz in ("dua", "dua_video", "dua_reels"):
        oto = True if auto_publish is None else auto_publish
        return dua_videosu_olustur_ve_gonder(ruh_hali=tema, auto_publish=oto, durum_mesaj_id=durum_mesaj_id)
    elif tur_temiz in ("kelime", "gorsel", "post"):
        oto = True if auto_publish is None else auto_publish
        return kelime_postu_olustur_ve_gonder(kavram=tema, format_tipi=format_tipi, auto_publish=oto, durum_mesaj_id=durum_mesaj_id)
    else:
        raise ValueError(f"Geçersiz içerik türü: {tur}. Desteklenen 4 resmi format: 'reels' (ayet), 'hadis', 'dua', 'kelime'")


def dinle_ve_bekle(sure_saniye: int = 1800, paylasim_id: Optional[int] = None, yayin_sonrasi: bool = False) -> bool:
    """
    Belirtilen süre boyunca Telegram'daki butonları ve komutları dinler.
    yayin_sonrasi=True ise: İçerik zaten yayınlanmıştır, 'yayindan_kaldirildi' durumu oluşursa erkenden çıkar.
    yayin_sonrasi=False ise: Onay bekleniyordur, 'yayinlandi' veya 'iptal_edildi' olduğunda erkenden çıkar.
    """
    dakika = sure_saniye // 60
    durum_tipi = "Yayından Kaldır butonu" if yayin_sonrasi else "Onay butonları"
    log.info(f"Telegram {durum_tipi} dinleniyor (Maksimum bekleme: {dakika} dakika)...")
    offset = 0
    baslangic = time.time()
    while time.time() - baslangic < sure_saniye:
        offset = telegram_bot.tek_sefer_dinle(offset)
        if paylasim_id:
            kayit = db.paylasim_getir(paylasim_id)
            if kayit:
                durum = kayit.get("durum")
                if yayin_sonrasi:
                    if durum == "yayindan_kaldirildi":
                        log.info(f"Paylaşım #{paylasim_id} kullanıcı tarafından yayından kaldırıldı.")
                        telegram_bot.aktif_isleri_bekle(timeout=30.0)
                        return False
                else:
                    if durum in ("yayinlandi", "iptal_edildi"):
                        log.info(f"Paylaşım #{paylasim_id} '{durum}' durumuna geçti, işlem tamam.")
                        telegram_bot.aktif_isleri_bekle(timeout=30.0)
                        return durum == "yayinlandi"
        time.sleep(2)

    telegram_bot.aktif_isleri_bekle(timeout=10.0)

    if yayin_sonrasi:
        log.info(f"Yayın sonrası kontrol süresi ({dakika} dk) tamamlandı. İçerik yayında kalmaya devam ediyor.")
        return True
    else:
        log.warning(f"Zaman aşımı: {sure_saniye} saniye içinde onay/ret gelmedi.")
        if paylasim_id:
            try:
                kayit = db.paylasim_getir(paylasim_id)
                msg_id = kayit.get("telegram_mesaj_id") if kayit else None
                token, chat_id = telegram_bot.get_token_ve_chat_id()
                if msg_id and chat_id:
                    telegram_bot.caption_ve_buton_guncelle(
                        chat_id=chat_id,
                        mesaj_id=msg_id,
                        yeni_caption=(
                            f"⏰ <b>ONAY SÜRESİ DOLDU ({dakika} Dakika)</b>\n\n"
                            f"Bu içerik için tanınan onay süresi dolduğu için bulut oturumu kapatılmıştır.\n"
                            f"İçeriği sıfırdan yeniden üretip onaya sunmak için aşağıdaki butona basabilirsiniz:"
                        ),
                        butonlar=[[{"text": "🔄 Sıfırdan Yeniden Üret", "callback_data": f"yeniden_uret_{paylasim_id}"}]]
                    )
            except Exception as e:
                log.warning(f"Zaman aşımı Telegram mesajı güncellenemedi: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ezan Plus Sosyal Medya Otomasyon Motoru")
    parser.add_argument("komut", nargs="?", default=None, choices=["reels", "hadis", "dua", "kelime", "ayet"], help="Üretilecek içerik türü: reels (ayet), hadis, dua, kelime")
    parser.add_argument("--tur", choices=["reels", "hadis", "dua", "kelime", "ayet"], default=None, help="İçerik türü")
    parser.add_argument("--format", choices=["4:5", "9:16"], default="4:5", help="Görsel formatı (4:5 feed veya 9:16 story)")
    parser.add_argument("--tema", type=str, default=None, help="Özel tema, sure:ayet veya arama terimi")
    parser.add_argument("--otomatik", action="store_true", help="Onay beklemeden doğrudan yayınla")
    parser.add_argument("--bekleme", type=int, default=1800, help="Onay bekleme süresi (saniye)")
    parser.add_argument("--dinle", action="store_true", help="Sürekli dinleme modunda Telegram botunu çalıştır")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.dinle:
        log.info("Ezan Plus Telegram Dinleyici (Daemon) başlatılıyor...")
        telegram_bot.surekli_dinle()
        sys.exit(0)

    tur = args.komut or args.tur or "reels"
    oto_varsayilan = True
    oto_yayin = True if args.otomatik else oto_varsayilan
    try:
        pid = icerik_olustur_ve_gonder(tur=tur, tema=args.tema, format_tipi=args.format, auto_publish=oto_yayin)
    except Exception as e:
        log.error(f"İçerik üretim hatası ({tur}): {e}")
        from . import hata_bildir
        hata_bildir.bildir(
            baslik=f"{tur.upper()} Otomasyon Hatası",
            hata=e,
            nerede=f"otomasyon.icerik_olustur_ve_gonder({tur})"
        )
        sys.exit(1)

    kayit_son = db.paylasim_getir(pid)
    zaten_yayinlandi = kayit_son and kayit_son.get("durum") == "yayinlandi"

    if zaten_yayinlandi or oto_yayin:
        # Otomatik yayınlanan içeriklerde bekleme süresi boyunca 'Yayından Kaldır' butonu dinlenir
        log.info(f"{tur.upper()} #{pid} yayınlandı. Telegram'dan 'Yayından Kaldır' komutları dinleniyor (Maks: {args.bekleme//60} dk)...")
        dinle_ve_bekle(sure_saniye=args.bekleme, paylasim_id=pid, yayin_sonrasi=True)
    elif args.otomatik:
        log.info(f"Otomatik yayınlama aktif. Paylaşım #{pid} doğrudan yayınlanıyor...")
        try:
            sonuclar = telegram_bot.yayinla_hepsi(pid)
            try:
                telegram_bot.yayin_detay_karti_gonder(pid, sonuclar)
            except Exception as e:
                log.error(f"Paylaşım #{pid} yayınlandı fakat Telegram yayın detay kartı iletilemedi: {e}")
        except Exception as e_yayin:
            log.error(f"Otomatik yayınlama hatası (#{pid}): {e_yayin}")
            from . import hata_bildir
            hata_bildir.bildir(
                baslik=f"Paylaşım #{pid} Otomatik Yayınlama",
                hata=e_yayin,
                nerede="otomasyon.otomatik_yayin",
                paylasim_id=pid
            )
        dinle_ve_bekle(sure_saniye=args.bekleme, paylasim_id=pid, yayin_sonrasi=True)
    else:
        dinle_ve_bekle(sure_saniye=args.bekleme, paylasim_id=pid, yayin_sonrasi=False)


