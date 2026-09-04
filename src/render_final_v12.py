import os
import sys
import logging
from pathlib import Path

# Loglama
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

from src.ayar import KOK_DIZIN
from src import db, telegram_bot, video_motoru, ses_getir

def main():
    sure_no = 29
    ayet_no = 64
    sure_ayet = "Ankebût Sûresi • 64. Âyet"
    
    # Elmalılı Muhammed Hamdi Yazır sadeleştirilmiş meali
    turkce_meal = "Bu dünya hayatı sadece bir oyun ve oyalanmadan ibarettir. Ahiret yurduna gelince, işte asıl hayat odur. Keşke bilmiş olsalardı."
    arapca_metin = "وَمَا هَٰذِهِ الْحَيَاةُ الدُّنْيَا إِلَّا لَهْوٌ وَلَعِبٌ ۚ وَإِنَّ الدَّارَ الْآخِرَةَ لَهِيَ الْحَيَوَانُ ۚ لَوْ كَانُوا يَعْلَمُونَ"
    arapca_okunus = "Ve mâ hâzihil hayâtud dunyâ illâ lehvun ve le'ıb(un), ve inned dâral âhirete lehiyel hayavân(u), lev kânû ya'lemûn(e)."
    
    video_b1 = "Dünya Hayatı Sadece"
    video_b2 = "Bir Oyun ve Oyalanmadır"
    
    tefekkur = "Gelip geçici telaşlar ve kederler içinde boğulurken, asıl durağımızın <b>ahiret</b> olduğunu sık sık unutuyoruz. Bu ayet, gözümüzde büyüttüğümüz dünya dertlerinin bir sahneden ibaret olduğunu hatırlatarak kalbimize sonsuz bir <b>ferahlık ve teslimiyet</b> sunuyor."
    
    # Instagram/TikTok algoritması için optimize edilmiş, TAM 5 HASHTAG içeren profesyonel caption
    caption = """🌿 Dünyanın bitmek bilmeyen telaşında kalbinin yorulduğunu hissettiğin anlar oluyor mu?

“Bu dünya hayatı sadece bir oyun ve oyalanmadan ibarettir. Ahiret yurduna gelince, işte asıl hayat odur. Keşke bilmiş olsalardı.”
— Ankebût Sûresi, 64 • Elmalılı Hamdi Yazır Meali

Koşuşturmacaların ve geçici kaygıların içinde boğulurken asıl yurdumuzu unutabiliyoruz. Bu ayet, gözümüzde büyüttüğümüz dünya dertlerinin gelip geçici bir sahneden ibaret olduğunu hatırlatarak kalbimize sonsuz bir ferahlık ve teslimiyet sunuyor.

📌 Kalbine hatırlatmak için bu ayeti kaydetmeyi unutma.
🕊️ Huzura vesile olmak için sevdiklerinle paylaş.
💬 Bu ayet bugün senin kalbine nasıl dokundu? Yorumlarda buluşalım.

📲 Namaz vakitleri, Kur’an-ı Kerim ve günlük tefekkürler için Ezan Plus uygulamasını profildeki linkten ücretsiz indirebilirsin.

#ezanplus #ankebut #kuranıkerim #gününayeti #tefekkur"""

    ses_yolu = KOK_DIZIN / "assets" / "audio" / "029064.mp3"
    kelime_zamanlari = ses_getir.ayet_kelime_zamanlari_getir(sure_no, ayet_no)
    
    cikti_adi = "reels_29_64_final_v12.mp4"
    log.info(f"Video üretimi başlıyor: {cikti_adi}")
    
    video_yolu = video_motoru.reels_videosu_uret(
        sure_ayet=sure_ayet,
        turkce_meal=turkce_meal,
        ses_yolu=ses_yolu,
        arapca_metin=arapca_metin,
        arapca_okunus=arapca_okunus,
        video_baslik_satir1=video_b1,
        video_baslik_satir2=video_b2,
        tefekkur_notu=tefekkur,
        hafiz_adi="Mişari Râşid el-Afâsî",
        cikti_adi=cikti_adi,
        kelime_zamanlari=kelime_zamanlari,
    )
    
    kapak_yolu = video_yolu.with_suffix(".png")
    log.info(f"Video hazırlandı: {video_yolu}")
    
    paylasim_id = db.paylasim_ekle(
        kategori="ayet",
        format_tipi="reels_9_16",
        turkce_metin=turkce_meal,
        baslik=f"{sure_ayet} (V12 Elmalılı & Büyük Logo)",
        arapca_metin=arapca_metin,
        kaynak=f"{sure_ayet} • Elmalılı Meali",
        tefekkur=tefekkur,
        caption=caption,
        video_yolu=str(video_yolu),
        gorsel_yollari=[str(kapak_yolu)],
        ses_yolu=str(ses_yolu),
        durum="taslak"
    )
    
    log.info(f"Veritabanına eklendi, Paylaşım ID: {paylasim_id}")
    return paylasim_id, video_yolu

if __name__ == "__main__":
    main()
