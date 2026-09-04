import logging
from pathlib import Path
from src.ayar import KOK_DIZIN
from src.ses_getir import ayet_kelime_zamanlari_getir
from src.video_motoru import reels_videosu_uret
from src import db
from src import telegram_bot

logging.basicConfig(level=logging.INFO)

sure_no = 29
ayet_no = 64
sure_ayet = "Ankebût Sûresi • 64. Âyet"
turkce_meal = "Bu dünya hayatı sadece bir eğlence ve oyundan ibarettir. Ahiret yurdu ise işte asıl hayat odur. Keşke bilselerdi!"
arapca_metin = "وَمَا هَٰذِهِ الْحَيَاةُ الدُّنْيَا إِلَّا لَهْوٌ وَلَعِبٌ ۚ وَإِنَّ الدَّارَ الْآخِرَةَ لَهِيَ الْحَيَوَانُ ۚ لَوْ كَانُوا يَعْلَمُونَ"
arapca_okunus = "Ve mâ hâzihil hayâtud dunyâ illâ lehvun ve le'ıb(un), ve inned dâral âhirete lehiyel hayavân(u), lev kânû ya'lemûn(e)."
video_b1 = "Dünya Hayatı Sadece"
video_b2 = "Bir Eğlence ve Oyundur"
tefekkur = "Gelip geçici telaşlar ve kederler içinde boğulurken, asıl durağımızın ahiret olduğunu sık sık unutuyoruz. Bu ayet, gözümüzde büyüttüğümüz dünya dertlerinin bir sahneden ibaret olduğunu hatırlatarak kalbimize sonsuz bir ferahlık ve teslimiyet sunuyor."

ses_yolu = KOK_DIZIN / "assets" / "audio" / "029064.mp3"
kelime_zamanlari = ayet_kelime_zamanlari_getir(sure_no, ayet_no)

cikti_adi = "reels_29_64_v9_mushaf_duzeni.mp4"

print("Video render ediliyor...")
video_yolu = reels_videosu_uret(
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

print(f"Video hazır: {video_yolu}")
