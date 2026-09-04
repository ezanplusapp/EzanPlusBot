from pathlib import Path
from src.ayar import KOK_DIZIN
from src import db, telegram_bot

video_yolu = KOK_DIZIN / "data" / "cikti" / "reels_29_64_v9_mushaf_duzeni.mp4"
kapak_yolu = video_yolu.with_suffix(".png")

sure_ayet = "Ankebût Sûresi • 64. Âyet"
turkce_meal = "Bu dünya hayatı sadece bir eğlence ve oyundan ibarettir. Ahiret yurdu ise işte asıl hayat odur. Keşke bilselerdi!"
arapca_metin = "وَمَا هَٰذِهِ الْحَيَاةُ الدُّنْيَا إِلَّا لَهْوٌ وَلَعِبٌ ۚ وَإِنَّ الدَّارَ الْآخِرَةَ لَهِيَ الْحَيَوَANُ ۚ لَوْ كَانُوا يَعْلَمُونَ"
tefekkur = "Gelip geçici telaşlar ve kederler içinde boğulurken, asıl durağımızın ahiret olduğunu sık sık unutuyoruz. Bu ayet, gözümüzde büyüttüğümüz dünya dertlerinin bir sahneden ibaret olduğunu hatırlatarak kalbimize sonsuz bir ferahlık ve teslimiyet sunuyor."

caption = """🌿 'Bu dünya hayatı sadece bir eğlence ve oyundan ibarettir...' (Ankebût, 64)

Koşuşturmacaların ve bitmeyen telaşların içinde bazen asıl gayemizi unutuyoruz. Kalbini ferahlat, bu dünyanın bir durak olduğunu hatırla.

Sen bu ayeti okuyunca ne hissediyorsun? Yorumlarda buluşalım 🤲

#ezanplus #kuran #ayet #ankebut #huzur #tevekkul #namaz #islam #dua"""

paylasim_id = db.paylasim_ekle(
    kategori="ayet",
    format_tipi="reels_9_16",
    turkce_metin=turkce_meal,
    baslik=sure_ayet,
    arapca_metin=arapca_metin,
    kaynak=sure_ayet,
    tefekkur=tefekkur,
    caption=caption,
    video_yolu=str(video_yolu),
    gorsel_yollari=[str(kapak_yolu)],
    ses_yolu="assets/audio/029064.mp3",
    durum="taslak"
)

print(f"Yeni paylaşım eklendi, ID: {paylasim_id}")
print("Telegram'a onay isteği gönderiliyor...")
telegram_bot.onay_istegi_gonder(paylasim_id)
print("Telegram'a başarıyla iletildi!")
