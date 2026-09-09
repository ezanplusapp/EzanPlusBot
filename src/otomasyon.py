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
from .telegram import bot as telegram_bot

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
        latin_kelimeler=icerik.get("latin_kelimeler"),
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

    log.info("5/5: Kur'an tilaveti otomatik yayınlanıyor ve Telegram'a yayın detay kartı iletiliyor...")
    sonuclar = telegram_bot.yayinla_hepsi(paylasim_id)
    try:
        telegram_bot.yayin_detay_karti_gonder(paylasim_id, sonuclar)
    except Exception as e:
        log.error(f"Reels #{paylasim_id} yayınlandı fakat Telegram yayın detay kartı iletilemedi: {e}")

    log.info(f"Reels tilaveti başarıyla yayınlandı ve Telegram'a raporlandı! Paylaşım ID: {paylasim_id}")
    return paylasim_id


def gorsel_icerik_olustur_ve_gonder(
    kategori: str = "ayet",
    tema: Optional[str] = None,
    format_tipi: str = "4:5",
    auto_publish: bool = False,
) -> int:
    """
    4:5 (Feed) ve 9:16 (Story) formatlarında tescilli görsel post üretip Telegram grubuna onay için gönderir.
    Hadis, Dua ve Kelime kartlarında hem 4:5 hem de 9:16 çıktıları eş zamanlı üretilir.
    auto_publish=True olduğunda onay beklemeden doğrudan tüm platformlara yayınlar.
    """
    dosya_eki = int(time.time())
    format_etiketi = format_tipi.replace(":", "_")
    gorsel_yollari: List[str] = []

    if kategori == "ayet":
        icerik = icerik_uret.ayet_icerigi_uret(tema=tema)
        turkce = icerik.get("turkce_meal", "")
        arapca = icerik.get("arapca_metin", "")
        kaynak = icerik.get("sure_ayet_etiket", "Günün Ayeti")
        tefekkur = icerik.get("tefekkur_notu")
        caption = icerik.get("instagram_caption", "")

        gorsel_4_5 = sablon_ciz.ayet_karti_ciz(
            sure_ayet=kaynak,
            turkce_meal=turkce,
            arapca_metin=arapca,
            tefekkur_notu=tefekkur,
            cikti_dosya_adi=f"ayet_4_5_{dosya_eki}.png",
            format_tipi="4:5",
        )
        gorsel_9_16 = sablon_ciz.ayet_karti_ciz(
            sure_ayet=kaynak,
            turkce_meal=turkce,
            arapca_metin=arapca,
            tefekkur_notu=tefekkur,
            cikti_dosya_adi=f"ayet_9_16_{dosya_eki}.png",
            format_tipi="9:16",
        )
        gorsel_yollari = [str(gorsel_4_5), str(gorsel_9_16)]

    elif kategori == "hadis":
        icerik = icerik_uret.hadis_icerigi_uret(tema=tema)
        turkce = icerik.get("hadis_metni", "")
        kaynak = icerik.get("kaynak_ravi", "Hadis-i Şerif")
        tefekkur = icerik.get("tefekkur_notu")
        caption = icerik.get("instagram_caption", "")
        arapca = icerik.get("arapca_metin")
        okunus = icerik.get("arapca_okunus")
        ravi = icerik.get("ravi")

        gorsel_4_5 = sablon_ciz.hadis_karti_ciz(
            hadis_metni=turkce,
            kaynak_ravi=kaynak,
            tefekkur_notu=tefekkur,
            cikti_dosya_adi=f"hadis_4_5_{dosya_eki}.png",
            format_tipi="4:5",
            arapca_metin=arapca,
            arapca_okunus=okunus,
            ravi=ravi,
        )
        gorsel_9_16 = sablon_ciz.hadis_karti_ciz(
            hadis_metni=turkce,
            kaynak_ravi=kaynak,
            tefekkur_notu=tefekkur,
            cikti_dosya_adi=f"hadis_9_16_{dosya_eki}.png",
            format_tipi="9:16",
            arapca_metin=arapca,
            arapca_okunus=okunus,
            ravi=ravi,
        )
        gorsel_yollari = [str(gorsel_4_5), str(gorsel_9_16)]

        if icerik.get("hadis_id"):
            from . import hadis_db
            hadis_db.hadisi_paylasildi_isaretle(icerik["hadis_id"])

    elif kategori == "dua":
        icerik = icerik_uret.dua_icerigi_uret(ruh_hali=tema)
        baslik = icerik.get("dua_basligi", "Günün Duası")
        turkce = icerik.get("turkce_anlam", "")
        arapca = icerik.get("arapca_metin")
        okunus = icerik.get("arapca_okunus")
        fazilet = icerik.get("okunus_veya_fazilet")
        kaynak = baslik
        tefekkur = fazilet
        caption = icerik.get("instagram_caption", "")

        gorsel_4_5 = sablon_ciz.dua_karti_ciz(
            dua_basligi=baslik,
            turkce_anlam=turkce,
            arapca_metin=arapca,
            arapca_okunus=okunus,
            okunus_veya_fazilet=fazilet,
            cikti_dosya_adi=f"dua_4_5_{dosya_eki}.png",
            format_tipi="4:5",
        )
        gorsel_9_16 = sablon_ciz.dua_karti_ciz(
            dua_basligi=baslik,
            turkce_anlam=turkce,
            arapca_metin=arapca,
            arapca_okunus=okunus,
            okunus_veya_fazilet=fazilet,
            cikti_dosya_adi=f"dua_9_16_{dosya_eki}.png",
            format_tipi="9:16",
        )
        gorsel_yollari = [str(gorsel_4_5), str(gorsel_9_16)]

    elif kategori == "kelime":
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

    if auto_publish or kategori == "kelime":
        log.info(f"Görsel post ({kategori.upper()}) doğrudan tüm platformlara otomatik yayınlanıyor...")
        sonuclar = telegram_bot.yayinla_hepsi(paylasim_id)
        try:
            telegram_bot.yayin_detay_karti_gonder(paylasim_id, sonuclar)
        except Exception as e:
            log.error(f"{kategori.upper()} #{paylasim_id} yayınlandı fakat Telegram yayın detay kartı iletilemedi: {e}")
        log.info(f"{kategori.upper()} postu başarıyla yayınlandı ve Telegram'a raporlandı! Paylaşım ID: {paylasim_id}")
    else:
        telegram_bot.onay_istegi_gonder(paylasim_id)
        log.info(f"Görsel post ({kategori.upper()} Çift Format 4:5 + 9:16) hazırlandı ve onaya sunuldu! Paylaşım ID: {paylasim_id}")
    return paylasim_id


def hadis_postu_olustur_ve_gonder(tema: Optional[str] = None, format_tipi: str = "4:5") -> int:
    """Sahih Hadis-i Şerif kartı üretip Telegram grubuna onay için iletir."""
    return gorsel_icerik_olustur_ve_gonder(kategori="hadis", tema=tema, format_tipi=format_tipi)


def dua_postu_olustur_ve_gonder(ruh_hali: Optional[str] = None, format_tipi: str = "4:5") -> int:
    """Günün Duası / Manevi Niyaz kartı üretip Telegram grubuna onay için iletir."""
    return gorsel_icerik_olustur_ve_gonder(kategori="dua", tema=ruh_hali, format_tipi=format_tipi)


def kelime_postu_olustur_ve_gonder(kavram: Optional[str] = None, format_tipi: str = "4:5", auto_publish: bool = True) -> int:
    """Kur'an Sözlüğü & İslami Kavramlar kartı üretip doğrudan tüm kanallara otomatik yayınlar."""
    return gorsel_icerik_olustur_ve_gonder(kategori="kelime", tema=kavram, format_tipi=format_tipi, auto_publish=auto_publish)


def icerik_olustur_ve_gonder(tur: str = "reels", tema: Optional[str] = None, format_tipi: str = "4:5") -> int:
    """
    Belirtilen türe göre (reels, hadis, dua, kelime, ayet) içeriği üretip Telegram onayına sunar.
    """
    tur_temiz = tur.lower().strip()
    if tur_temiz in ("reels", "video"):
        return reels_icerigi_olustur_ve_gonder(tema=tema)
    elif tur_temiz == "hadis":
        return hadis_postu_olustur_ve_gonder(tema=tema, format_tipi=format_tipi)
    elif tur_temiz == "dua":
        return dua_postu_olustur_ve_gonder(ruh_hali=tema, format_tipi=format_tipi)
    elif tur_temiz == "kelime":
        return kelime_postu_olustur_ve_gonder(kavram=tema, format_tipi=format_tipi, auto_publish=True)
    elif tur_temiz in ("ayet", "gorsel"):
        return gorsel_icerik_olustur_ve_gonder(kategori="ayet", tema=tema, format_tipi=format_tipi)
    else:
        raise ValueError(f"Geçersiz içerik türü: {tur}")


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
    parser.add_argument("komut", nargs="?", default=None, choices=["reels", "ayet", "hadis", "dua", "kelime", "gorsel"], help="Üretilecek içerik türü")
    parser.add_argument("--tur", choices=["reels", "ayet", "hadis", "dua", "kelime", "gorsel"], default=None, help="İçerik türü")
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
    try:
        pid = icerik_olustur_ve_gonder(tur=tur, tema=args.tema, format_tipi=args.format)
    except Exception as e:
        log.error(f"İçerik üretim hatası ({tur}): {e}")
        from . import hata_bildir
        hata_bildir.bildir(
            baslik=f"{tur.upper()} Otomasyon Hatası",
            hata=e,
            nerede=f"otomasyon.icerik_olustur_ve_gonder({tur})"
        )
        sys.exit(1)

    if tur in ("reels", "video", "kelime"):
        # Reels ve Kelime otomatik olarak yayınlandı; bekleme süresi boyunca 'Yayından Kaldır' butonu dinlenir
        log.info(f"{tur.upper()} #{pid} otomatik yayınlandı. Telegram'dan 'Yayından Kaldır' komutları dinleniyor (Maks: {args.bekleme//60} dk)...")
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


