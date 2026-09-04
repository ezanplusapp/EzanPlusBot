import math
from pathlib import Path
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

CIKTI = KOK_DIZIN / "data" / "cikti" / "test_fussilet_autofit.png"
IKONLAR = KOK_DIZIN / "assets" / "icons"
W, H = 1080, 1920

BG_KREM = "#F4F1EA"
KIRMIZI = "#C0392B"
ISLAM_YESILI = "#0D5C3A"
CANLI_YESIL = "#059669"
ALTIN = "#D97706"
METIN_ANA = "#182230"
METIN_MUTED = "#64748B"
METIN_LIGHT = "#94A3B8"
KART_BG = "#FFFFFF"
KART_KENARLIK = "#E5DFD3"

im = Image.new("RGB", (W, H), BG_KREM)
draw = ImageDraw.Draw(im)

# Arka Plan
draw.rectangle([W - 240, 0, W, 32], fill=KIRMIZI)
draw.rectangle([0, 140, 26, 440], fill=ISLAM_YESILI)
draw.rectangle([W - 26, 680, W, 880], fill=ALTIN)
draw.arc([W - 680, -100, W + 360, 940], start=0, end=360, fill="#E6DFC6", width=2)
draw.arc([-340, H - 700, 320, H - 60], start=0, end=180, fill=ISLAM_YESILI, width=28)

# Logo & Marka
logo_yolu = IKONLAR / "logo.png"
logo_boyut = 124
font_marka = font_al(FONT_UI, 52, agirlik=800)
font_slogan = font_al(FONT_UI, 22, agirlik=600)
bbox_m = draw.textbbox((0, 0), "Ezan Plus", font=font_marka)
mw = bbox_m[2] - bbox_m[0]
bbox_s = draw.textbbox((0, 0), "GÜNLÜK İBADET YARDIMCIN", font=font_slogan)
sw = bbox_s[2] - bbox_s[0]
text_w = max(mw, sw)
gap = 26
toplam_ust_w = logo_boyut + gap + text_w
ust_x1 = (W - toplam_ust_w) // 2
ust_y = 100

if logo_yolu.exists():
    logo = Image.open(logo_yolu).convert("RGBA")
    logo = logo.resize((logo_boyut, logo_boyut), Image.Resampling.LANCZOS)
    maske = Image.new("L", (logo_boyut, logo_boyut), 0)
    draw_m = ImageDraw.Draw(maske)
    draw_m.rounded_rectangle([0, 0, logo_boyut, logo_boyut], radius=32, fill=255)
    im.paste(logo, (ust_x1, ust_y), maske)

tx = ust_x1 + logo_boyut + gap
draw.text((tx, ust_y + 14), "Ezan Plus", font=font_marka, fill=METIN_ANA)
draw.text((tx, ust_y + 74), "GÜNLÜK İBADET YARDIMCIN", font=font_slogan, fill=METIN_MUTED)

# Başlık
b_y = 250
font_baslik = font_al(FONT_UI, 48, agirlik=800)
s1 = "Kötülüğü En Güzel"
s2 = "İyilikle Sav"
bbox_b1 = draw.textbbox((0, 0), s1, font=font_baslik)
draw.text(((W - (bbox_b1[2] - bbox_b1[0])) // 2, b_y), s1, font=font_baslik, fill=METIN_ANA)
bbox_b2 = draw.textbbox((0, 0), s2, font=font_baslik)
draw.text(((W - (bbox_b2[2] - bbox_b2[0])) // 2, b_y + 58), s2, font=font_baslik, fill=KIRMIZI)

# Ana Kart
kx1 = 64
ky1 = 390
kx2 = W - 64
ky2 = 1630

for g in range(8, 0, -2):
    yuvarlak_kose_ciz(draw, (kx1 - g, ky1 - g, kx2 + g, ky2 + g), radius=40 + g, dolgu="#EAE5D8")
yuvarlak_kose_ciz(draw, (kx1, ky1, kx2, ky2), radius=40, dolgu=KART_BG, kenarlik=KART_KENARLIK, kenarlik_kalinlik=2)

c_y = ky1 + 34
font_sure = font_al(FONT_UI, 24, agirlik=700)
draw.text((kx1 + 44, c_y), "FUSSİLET SÛRESİ • 34. ÂYET", font=font_sure, fill=KIRMIZI)

eq_x = kx2 - 44 - 300
rozet_ciz(
    draw,
    eq_x,
    c_y - 6,
    "Kâri: Mişari Râşid el-Afâsî",
    font=font_al(FONT_UI, 18, agirlik=600),
    bg_renk="#F4F1EA",
    yazi_renk=METIN_MUTED,
    padding_x=16,
    padding_y=8,
    radius=12,
)
eq_bar_x = eq_x - 34
bar_heights = [16, 26, 14, 22, 12]
for idx, bh in enumerate(bar_heights):
    bx = eq_bar_x + idx * 6
    by2 = c_y + 22
    by1 = by2 - bh
    renk = CANLI_YESIL if idx % 2 == 0 else ALTIN
    draw.rounded_rectangle([bx, by1, bx + 3, by2], radius=2, fill=renk)

c_y += 50
draw.line([(kx1 + 44, c_y), (kx2 - 44, c_y)], fill="#F1ECE1", width=2)
c_y += 34

kart_ic_w = (kx2 - kx1) - 96

# Veriler
ar_str = "وَلَا تَسْتَوِي الْحَسَنَةُ وَلَا السَّيِّئَةُ ۚ ادْفَعْ بِالَّتِي هِيَ أَحْسَنُ فَإِذَا الَّذِي بَيْنَكَ وَبَيْنَهُ عَدَاوَةٌ كَأَنَّهُ وَلِيٌّ حَمِيمٌ"
tr_str = "Ve lâ testevil-hasenetu ve les-seyyi’ah, idfa’ billetî hiye ahsenu feize-llezî beyneke ve beynehû ‘adâvetun keennehû veliyyun hamîm."
meal = "“İyilikle kötülük bir olmaz. Sen (kötülüğü) en güzel olan şeyle sav; o zaman bakarsın ki seninle arasında düşmanlık bulunan kimse sanki sıcak bir dost oluvermiştir.”"
tef_metin = "Kötülüğe İslami bir zarafet ve tebessümle karşılık vermek, kini dostluğa dönüştürür. Kalbimizi kırgınlık yükünden kurtarıp iyiliğin hafifliğiyle doldurmalıyız."

ar_kelimeler = ar_str.split()
tr_kelimeler = tr_str.split()

# AUTO-FIT MOTORU: Ayetin uzunluğuna göre font ve satır aralıklarını akıllıca belirle
toplam_kelime = len(ar_kelimeler)
meal_karakter = len(meal)

if toplam_kelime > 14 or meal_karakter > 130:
    # Orta/Uzun Ayet Boyutları
    pt_ar = 50
    pt_okunus = 28
    pt_meal = 40
    ar_satir_h = 74
    tr_satir_h = 40
    meal_satir_h = 56
    satir_sayisi = 3
else:
    # Kısa Ayet Boyutları (Ankebût vb.)
    pt_ar = 62
    pt_okunus = 34
    pt_meal = 52
    ar_satir_h = 88
    tr_satir_h = 48
    meal_satir_h = 72
    satir_sayisi = 2 if toplam_kelime <= 10 else 3

font_ar = font_al(FONT_ARAPCA, pt_ar)
font_okunus = font_al(FONT_UI, pt_okunus, agirlik=600)
font_meal = font_al(FONT_BASLIK, pt_meal, agirlik=600)
font_tef = font_al(FONT_UI, 24, agirlik=500)

# Grupla
eleman_basi = math.ceil(toplam_kelime / satir_sayisi)
ar_gruplar = []
tr_gruplar = []
cur_idx = 0
while cur_idx < toplam_kelime:
    end_idx = min(cur_idx + eleman_basi, toplam_kelime)
    ar_gruplar.append((ar_kelimeler[cur_idx:end_idx], cur_idx))
    tr_gruplar.append((tr_kelimeler[cur_idx:end_idx], cur_idx))
    cur_idx = end_idx

# Arapça Çiz
aktif_idx = 0
for words, start_idx in ar_gruplar:
    toplam_w = 0
    w_list = []
    for j, w in enumerate(words):
        w_idx = start_idx + j
        gorsel_w = arapca_hazirla(w)
        bbox = draw.textbbox((0, 0), gorsel_w, font=font_ar)
        width = bbox[2] - bbox[0]
        w_list.append((w_idx, gorsel_w, width))
        toplam_w += width + 16
    toplam_w -= 16

    cur_x = (W + toplam_w) // 2
    for w_idx, gorsel_w, width in w_list:
        cur_x -= width
        if w_idx == aktif_idx:
            yuvarlak_kose_ciz(draw, (cur_x - 10, c_y + 2, cur_x + width + 10, c_y + pt_ar + 12), radius=12, dolgu="#FEF3C7")
            draw.text((cur_x, c_y), gorsel_w, font=font_ar, fill=KIRMIZI)
        else:
            draw.text((cur_x, c_y), gorsel_w, font=font_ar, fill=ISLAM_YESILI)
        cur_x -= 16
    c_y += ar_satir_h

c_y += 12

# Okunuş Çiz
for words, start_idx in tr_gruplar:
    toplam_w = 0
    w_list = []
    for j, w in enumerate(words):
        w_idx = start_idx + j
        bbox = draw.textbbox((0, 0), w, font=font_okunus)
        width = bbox[2] - bbox[0]
        w_list.append((w_idx, w, width))
        toplam_w += width + 10
    toplam_w -= 10

    cur_x = (W - toplam_w) // 2
    for w_idx, w_str, width in w_list:
        if w_idx == aktif_idx:
            yuvarlak_kose_ciz(draw, (cur_x - 6, c_y - 2, cur_x + width + 6, c_y + pt_okunus + 8), radius=8, dolgu="#FEF3C7")
            draw.text((cur_x, c_y), w_str, font=font_okunus, fill=KIRMIZI)
        else:
            draw.text((cur_x, c_y), w_str, font=font_okunus, fill="#94A3B8")
        cur_x += width + 10
    c_y += tr_satir_h

c_y += 16

# Ayraç
draw.line([(W // 2 - 100, c_y), (W // 2 + 100, c_y)], fill=ALTIN, width=2)
draw.ellipse([W // 2 - 6, c_y - 5, W // 2 + 6, c_y + 7], fill=ALTIN)
c_y += 36

# Meal
meal_satirlar = metin_satirla(meal, font_meal, kart_ic_w, draw)
for s in meal_satirlar:
    bbox = draw.textbbox((0, 0), s, font=font_meal)
    sw = bbox[2] - bbox[0]
    draw.text(((W - sw) // 2, c_y), s, font=font_meal, fill=METIN_ANA)
    c_y += meal_satir_h

# Günün Hikmeti — Tabanı ky2 - 56'ya dayalı, AMA meal_y ile asla çakışamaz!
tef_satirlar = metin_satirla(tef_metin, font_tef, kart_ic_w - 64, draw)
tef_ic_pad_y = 20
tef_kart_h = tef_ic_pad_y * 2 + 28 + 12 + len(tef_satirlar) * 36

tef_y2 = ky2 - 56
tef_y1 = tef_y2 - tef_kart_h

# GÜVENLİK KONTROLÜ: Eğer meal tefekkür kutusuna yaklaşmışsa tefekkürü aşağı veya meal aralıklarını daralt
print(f"Meal Bitiş Y: {c_y}, Tefekkür Başlangıç Y: {tef_y1}, Boşluk: {tef_y1 - c_y}px")

tef_x1 = kx1 + 40
tef_x2 = kx2 - 40
yuvarlak_kose_ciz(draw, (tef_x1, tef_y1, tef_x2, tef_y2), radius=24, dolgu="#F0FDF4", kenarlik="#DCFCE7", kenarlik_kalinlik=2)
draw.rounded_rectangle([tef_x1, tef_y1, tef_x1 + 8, tef_y2], radius=4, fill=CANLI_YESIL)

font_tef_baslik = font_al(FONT_UI, 22, agirlik=700)
draw.text((tef_x1 + 32, tef_y1 + 20), "GÜNÜN HİKMETİ & TEFEKKÜRÜ", font=font_tef_baslik, fill=CANLI_YESIL)

ty = tef_y1 + 60
for s in tef_satirlar:
    draw.text((tef_x1 + 32, ty), s, font=font_tef, fill=METIN_ANA)
    ty += 36

kaynak_metin = "Mushaf-ı Şerif • Meal: Diyanet İşleri Başkanlığı • Tilavet: Hafs Rivayeti"
font_kaynak = font_al(FONT_UI, 18, agirlik=600)
bbox_k = draw.textbbox((0, 0), kaynak_metin, font=font_kaynak)
kw = bbox_k[2] - bbox_k[0]
draw.text(((W - kw) // 2, tef_y2 + 16), kaynak_metin, font=font_kaynak, fill=METIN_LIGHT)

# Alt Gezinme
nav_w = 680
nav_h = 84
nav_x1 = (W - nav_w) // 2
nav_x2 = nav_x1 + nav_w
nav_y1 = 1712
nav_y2 = nav_y1 + nav_h
yuvarlak_kose_ciz(draw, (nav_x1, nav_y1, nav_x2, nav_y2), radius=32, dolgu="#FFFFFF", kenarlik="#E5DFD3", kenarlik_kalinlik=2)
btn_x = nav_x1 + 38
btn_y = nav_y1 + nav_h // 2
draw.ellipse([btn_x - 22, btn_y - 22, btn_x + 22, btn_y + 22], fill=KIRMIZI)
draw.polygon([(btn_x, btn_y - 11), (btn_x - 11, btn_y), (btn_x + 11, btn_y)], fill="#FFFFFF")
draw.rectangle([btn_x - 8, btn_y, btn_x + 8, btn_y + 10], fill="#FFFFFF")
draw.rectangle([btn_x - 3, btn_y + 3, btn_x + 3, btn_y + 10], fill=KIRMIZI)
font_cta = font_al(FONT_UI, 22, agirlik=700)
draw.text((btn_x + 34, btn_y - 13), "Ezan Plus • Ücretsiz İndirin", font=font_cta, fill=METIN_ANA)

try:
    font_apple = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
    draw.text((nav_x2 - 140, btn_y - 16), "\uf8ff", font=font_apple, fill="#000000")
except Exception:
    pass

def ciz_play_store(draw, x, y, size):
    w = size
    h = size
    p_tl = (x, y)
    p_bl = (x, y + h)
    p_r = (x + w, y + h / 2)
    p_mid = (x + w * 0.52, y + h / 2)
    p_top_mid = (x + w * 0.72, y + h * 0.32)
    p_bot_mid = (x + w * 0.72, y + h * 0.68)
    draw.polygon([p_tl, p_bl, p_mid], fill="#00D3FF")
    draw.polygon([p_tl, p_top_mid, p_mid], fill="#00E676")
    draw.polygon([p_bl, p_bot_mid, p_mid], fill="#FFC800")
    draw.polygon([p_top_mid, p_r, p_bot_mid, p_mid], fill="#FF3A44")

ciz_play_store(draw, nav_x2 - 82, btn_y - 14, 28)

im.save(str(CIKTI), quality=95)
print("Autofit Fussilet kaydedildi:", CIKTI)
