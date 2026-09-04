"""
Ezan Plus Tam Kurumsal Tasarım — Mükemmel Orantılı & Sıfır Boşluklu Sürüm
"""

from pathlib import Path
from typing import List
from PIL import Image, ImageDraw, ImageFont
from src.ayar import KOK_DIZIN
from src.sablon_ciz import (
    font_al,
    arapca_hazirla,
    metin_satirla,
    yuvarlak_kose_ciz,
    rozet_ciz,
    FONT_ARAPCA,
    FONT_BASLIK,
    FONT_UI,
)

CIKTI = KOK_DIZIN / "data" / "cikti" / "ornek_yeni_tam_tasarim.png"
IKONLAR = KOK_DIZIN / "assets" / "icons"

W, H = 1080, 1920

# Kurumsal Renk Paleti
BG_KREM = "#F4F1EA"
KIRMIZI = "#C0392B"
KOYU_KIRMIZI = "#962D22"
ISLAM_YESILI = "#0D5C3A"
CANLI_YESIL = "#059669"
ALTIN = "#D97706"
METIN_ANA = "#182230"
METIN_MUTED = "#64748B"
KART_BG = "#FFFFFF"
KART_KENARLIK = "#E5DFD3"

im = Image.new("RGB", (W, H), BG_KREM)
draw = ImageDraw.Draw(im)

# 1. ARKA PLAN
draw.rectangle([W - 240, 0, W, 32], fill=KIRMIZI)
draw.rectangle([0, 120, 28, 420], fill=ISLAM_YESILI)
draw.rectangle([W - 28, 700, W, 900], fill=ALTIN)
draw.arc([W - 700, -120, W + 360, 940], start=0, end=360, fill="#E6DFC6", width=2)
draw.arc([-340, H - 720, 320, H - 80], start=0, end=180, fill=ISLAM_YESILI, width=28)

# 2. ÜSTTE YAN YANA VE BÜYÜK LOGO + AD (Ortalı)
logo_yolu = IKONLAR / "logo.png"
logo_boyut = 104

font_marka = font_al(FONT_UI, 44, agirlik=800)
font_slogan = font_al(FONT_UI, 20, agirlik=600)
bbox_m = draw.textbbox((0, 0), "Ezan Plus", font=font_marka)
mw = bbox_m[2] - bbox_m[0]
bbox_s = draw.textbbox((0, 0), "GÜNLÜK İBADET YARDIMCIN", font=font_slogan)
sw = bbox_s[2] - bbox_s[0]

text_w = max(mw, sw)
gap = 20
toplam_ust_w = logo_boyut + gap + text_w
ust_x1 = (W - toplam_ust_w) // 2
ust_y = 80

if logo_yolu.exists():
    logo = Image.open(logo_yolu).convert("RGBA")
    logo = logo.resize((logo_boyut, logo_boyut), Image.Resampling.LANCZOS)
    maske = Image.new("L", (logo_boyut, logo_boyut), 0)
    draw_m = ImageDraw.Draw(maske)
    draw_m.rounded_rectangle([0, 0, logo_boyut, logo_boyut], radius=26, fill=255)
    im.paste(logo, (ust_x1, ust_y), maske)

tx = ust_x1 + logo_boyut + gap
draw.text((tx, ust_y + 10), "Ezan Plus", font=font_marka, fill=METIN_ANA)
draw.text((tx, ust_y + 60), "GÜNLÜK İBADET YARDIMCIN", font=font_slogan, fill=METIN_MUTED)

# 3. İÇERİKLE İLGİLİ VURUCU BAŞLIK
b_y = 215
font_baslik = font_al(FONT_UI, 48, agirlik=800)
satir1 = "Namaz, kötülüklerden koruyan"
bbox_b1 = draw.textbbox((0, 0), satir1, font=font_baslik)
draw.text(((W - (bbox_b1[2] - bbox_b1[0])) // 2, b_y), satir1, font=font_baslik, fill=METIN_ANA)

satir2 = "en güçlü kalkandır."
bbox_b2 = draw.textbbox((0, 0), satir2, font=font_baslik)
draw.text(((W - (bbox_b2[2] - bbox_b2[0])) // 2, b_y + 58), satir2, font=font_baslik, fill=KIRMIZI)

# 4. MERKEZİ KART (Tam Dengeli, Sıfır Boşluklu)
kx1 = 64
ky1 = 360
kx2 = W - 64
ky2 = 1650

for g in range(8, 0, -2):
    yuvarlak_kose_ciz(draw, (kx1 - g, ky1 - g, kx2 + g, ky2 + g), radius=40 + g, dolgu="#EAE5D8")
yuvarlak_kose_ciz(draw, (kx1, ky1, kx2, ky2), radius=40, dolgu=KART_BG, kenarlik=KART_KENARLIK, kenarlik_kalinlik=2)

# Kart Üst Bar (Sure ve Hafız)
c_y = ky1 + 38
font_sure = font_al(FONT_UI, 24, agirlik=700)
draw.text((kx1 + 44, c_y), "ANKEBÛT SÛRESİ • 45. ÂYET", font=font_sure, fill=KIRMIZI)

rozet_ciz(
    draw,
    kx2 - 44 - 260,
    c_y - 6,
    "Mishary Rashid Alafasy",
    font=font_al(FONT_UI, 18, agirlik=600),
    bg_renk="#F4F1EA",
    yazi_renk=METIN_MUTED,
    padding_x=16,
    padding_y=8,
    radius=12,
)

c_y += 54
draw.line([(kx1 + 44, c_y), (kx2 - 44, c_y)], fill="#F1ECE1", width=2)
c_y += 48

genislik = (kx2 - kx1) - 88

# ARAPÇA VE TÜRKÇE OKUNUŞ KELİMELERİ
ar_kelimeler = [
    "اتْلُ", "مَا", "أُوحِيَ", "إِلَيْكَ", "مِنَ", "الْكِتَابِ",
    "وَأَقِمِ", "الصَّلَاةَ", "ۖ", "إِنَّ", "الصَّلَاةَ", "تَنْهَىٰ", "عَنِ", "الْفَحْشَاءِ", "وَالْمُنكَرِ"
]
tr_okunus = [
    "Utlu", "mâ", "ûhıye", "ileyke", "minel", "kitâbi",
    "ve", "ekımis-salâte,", "—", "innes-salâte", "tenhâ", "‘anil", "fahşâi", "vel-munker."
]

aktif_idx = 5

# --- 4A. ARAPÇA BÖLÜMÜ (64px) ---
font_ar = font_al(FONT_ARAPCA, 64)

ar_satir1 = ar_kelimeler[:8]
ar_satir2 = ar_kelimeler[8:]

def arapca_satir_ciz(words: List[str], start_idx: int, y: int):
    toplam_w = 0
    w_list = []
    for i, w in enumerate(words):
        w_idx = start_idx + i
        gorsel_w = arapca_hazirla(w)
        bbox = draw.textbbox((0, 0), gorsel_w, font=font_ar)
        width = bbox[2] - bbox[0]
        w_list.append((w_idx, gorsel_w, width))
        toplam_w += width + 20
    toplam_w -= 20

    cur_x = (W + toplam_w) // 2
    for w_idx, gorsel_w, width in w_list:
        cur_x -= width
        if w_idx == aktif_idx:
            yuvarlak_kose_ciz(draw, (cur_x - 10, y + 2, cur_x + width + 10, y + 78), radius=14, dolgu="#FEF3C7")
            draw.text((cur_x, y), gorsel_w, font=font_ar, fill=KIRMIZI)
        elif w_idx < aktif_idx:
            draw.text((cur_x, y), gorsel_w, font=font_ar, fill=ISLAM_YESILI)
        else:
            draw.text((cur_x, y), gorsel_w, font=font_ar, fill="#2E7D56")
        cur_x -= 20

arapca_satir_ciz(ar_satir1, 0, c_y)
c_y += 98
arapca_satir_ciz(ar_satir2, 8, c_y)
c_y += 114

# --- 4B. TÜRKÇE OKUNUŞU (34px) ---
font_okunus = font_al(FONT_UI, 34, agirlik=600)

tr_satir1 = tr_okunus[:8]
tr_satir2 = tr_okunus[8:]

def okunus_satir_ciz(words: List[str], start_idx: int, y: int):
    toplam_w = 0
    w_list = []
    for i, w in enumerate(words):
        w_idx = start_idx + i
        bbox = draw.textbbox((0, 0), w, font=font_okunus)
        width = bbox[2] - bbox[0]
        w_list.append((w_idx, w, width))
        toplam_w += width + 12
    toplam_w -= 12

    cur_x = (W - toplam_w) // 2
    for w_idx, w_str, width in w_list:
        if w_idx == aktif_idx:
            yuvarlak_kose_ciz(draw, (cur_x - 6, y - 2, cur_x + width + 6, y + 44), radius=10, dolgu="#FEF3C7")
            draw.text((cur_x, y), w_str, font=font_okunus, fill=KIRMIZI)
        elif w_idx < aktif_idx:
            draw.text((cur_x, y), w_str, font=font_okunus, fill=METIN_ANA)
        else:
            draw.text((cur_x, y), w_str, font=font_okunus, fill="#94A3B8")
        cur_x += width + 12

okunus_satir_ciz(tr_satir1, 0, c_y)
c_y += 54
okunus_satir_ciz(tr_satir2, 8, c_y)
c_y += 76

# İnce Altın Ayraç
draw.line([(W // 2 - 110, c_y), (W // 2 + 110, c_y)], fill=ALTIN, width=2)
draw.ellipse([W // 2 - 7, c_y - 6, W // 2 + 7, c_y + 8], fill=ALTIN)
c_y += 68

# --- 4C. TÜRKÇE MEAL (Daha Dolgun & Büyük: 50px Serif) ---
meal = "“Sana vahyedilen kitabı oku ve namazı dosdoğru kıl. Şüphesiz ki namaz, insanı hayasızlıktan ve kötülükten alıkoyar.”"
font_meal = font_al(FONT_BASLIK, 50, agirlik=600)
tr_satirlar = metin_satirla(meal, font_meal, genislik, draw)
for s in tr_satirlar:
    bbox = draw.textbbox((0, 0), s, font=font_meal)
    sw = bbox[2] - bbox[0]
    draw.text(((W - sw) // 2, c_y), s, font=font_meal, fill=METIN_ANA)
    c_y += 72

# --- 4D. GÜNÜN HİKMETİ KARTI (Kartın Altına Tam Oturan Ferah Yerleşim) ---
tef_metin = "Namaz sadece bir ibadet değil; günün karmaşasında ruhu arındıran, insanı kötülükten ve günahtan koruyan ilahi bir sığınaktır."
font_tef = font_al(FONT_UI, 26, agirlik=500)
tef_satirlar = metin_satirla(tef_metin, font_tef, genislik - 64, draw)

tef_kart_h = 240
tef_y2 = ky2 - 36
tef_y1 = tef_y2 - tef_kart_h
tef_x1 = kx1 + 36
tef_x2 = kx2 - 36

yuvarlak_kose_ciz(draw, (tef_x1, tef_y1, tef_x2, tef_y2), radius=28, dolgu="#F0FDF4", kenarlik="#DCFCE7", kenarlik_kalinlik=2)
draw.rounded_rectangle([tef_x1, tef_y1, tef_x1 + 8, tef_y2], radius=4, fill=CANLI_YESIL)

font_tef_baslik = font_al(FONT_UI, 22, agirlik=700)
draw.text((tef_x1 + 32, tef_y1 + 28), "GÜNÜN HİKMETİ & TEFEKKÜRÜ", font=font_tef_baslik, fill=CANLI_YESIL)

ty = tef_y1 + 78
for s in tef_satirlar:
    draw.text((tef_x1 + 32, ty), s, font=font_tef, fill=METIN_ANA)
    ty += 42

# 5. ALT İLERLEME ÇUBUĞU VE GEZİNME HAPI
bar_x1 = 64
bar_x2 = W - 64
bar_y = 1685
yuvarlak_kose_ciz(draw, (bar_x1, bar_y, bar_x2, bar_y + 10), radius=5, dolgu="#E2E8F0")
dolu_w = int((bar_x2 - bar_x1) * 0.40)
yuvarlak_kose_ciz(draw, (bar_x1, bar_y, bar_x1 + dolu_w, bar_y + 10), radius=5, dolgu=KIRMIZI)
draw.ellipse([bar_x1 + dolu_w - 9, bar_y - 4, bar_x1 + dolu_w + 9, bar_y + 14], fill=ALTIN, outline="#FFFFFF", width=3)

nav_x1 = (W - 580) // 2
nav_x2 = nav_x1 + 580
nav_y1 = 1740
nav_y2 = 1820
yuvarlak_kose_ciz(draw, (nav_x1, nav_y1, nav_x2, nav_y2), radius=30, dolgu="#FFFFFF", kenarlik="#E5DFD3", kenarlik_kalinlik=2)

btn_x = nav_x1 + 44
btn_y = nav_y1 + (nav_y2 - nav_y1) // 2
draw.ellipse([btn_x - 26, btn_y - 26, btn_x + 26, btn_y + 26], fill=KIRMIZI)
draw.polygon([(btn_x, btn_y - 13), (btn_x - 13, btn_y), (btn_x + 13, btn_y)], fill="#FFFFFF")
draw.rectangle([btn_x - 9, btn_y, btn_x + 9, btn_y + 12], fill="#FFFFFF")
draw.rectangle([btn_x - 3, btn_y + 4, btn_x + 3, btn_y + 12], fill=KIRMIZI)

draw.text((btn_x + 44, btn_y - 12), "Ezan Plus • App Store & Google Play'de", font=font_al(FONT_UI, 21, agirlik=600), fill=METIN_ANA)

CIKTI.parent.mkdir(parents=True, exist_ok=True)
im.save(str(CIKTI), quality=95)
print("Sıfır boşluklu tam tasarım kaydedildi:", CIKTI)
