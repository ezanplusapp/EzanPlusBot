import sys
from pathlib import Path
from typing import List, Tuple
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

IKONLAR = KOK_DIZIN / "assets" / "icons"
CIKTI = KOK_DIZIN / "data" / "cikti" / "ornek_tasarim_v4.png"
W, H = 1080, 1920

# Kurumsal Renk Paleti (Ezan Plus)
BG_KREM = "#F4F1EA"
KIRMIZI = "#C0392B"
KOYU_KIRMIZI = "#962D22"
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

# 1. ARKA PLAN MİMARİSİ
draw.rectangle([W - 240, 0, W, 32], fill=KIRMIZI)
draw.rectangle([0, 140, 26, 440], fill=ISLAM_YESILI)
draw.rectangle([W - 26, 680, W, 880], fill=ALTIN)
draw.arc([W - 680, -100, W + 360, 940], start=0, end=360, fill="#E6DFC6", width=2)
draw.arc([-340, H - 700, 320, H - 60], start=0, end=180, fill=ISLAM_YESILI, width=28)

# 2. ÜST MARKA ALANI (Daha Büyük İkon: 124x124 + İsim & Slogan)
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

# 3. İÇERİKLE İLGİLİ DİNAMİK BAŞLIK
b_y = 250
font_baslik = font_al(FONT_UI, 48, agirlik=800)
s1 = "Namaz, kötülüklerden koruyan"
s2 = "en güçlü kalkandır."
bbox_b1 = draw.textbbox((0, 0), s1, font=font_baslik)
draw.text(((W - (bbox_b1[2] - bbox_b1[0])) // 2, b_y), s1, font=font_baslik, fill=METIN_ANA)
bbox_b2 = draw.textbbox((0, 0), s2, font=font_baslik)
draw.text(((W - (bbox_b2[2] - bbox_b2[0])) // 2, b_y + 58), s2, font=font_baslik, fill=KIRMIZI)

# 4. MERKEZİ KART (Instagram Safe Zone uyumlu: y = 390 to y = 1630)
kx1 = 64
ky1 = 390
kx2 = W - 64
ky2 = 1630

for g in range(8, 0, -2):
    yuvarlak_kose_ciz(draw, (kx1 - g, ky1 - g, kx2 + g, ky2 + g), radius=40 + g, dolgu="#EAE5D8")
yuvarlak_kose_ciz(draw, (kx1, ky1, kx2, ky2), radius=40, dolgu=KART_BG, kenarlik=KART_KENARLIK, kenarlik_kalinlik=2)

# Kart Üst Bar (Sure + İmam/Kâri + Kaynak Bilgisi)
c_y = ky1 + 34
font_sure = font_al(FONT_UI, 24, agirlik=700)
draw.text((kx1 + 44, c_y), "ANKEBÛT SÛRESİ • 45. ÂYET", font=font_sure, fill=KIRMIZI)

# Kâri ve Equalizer Rozeti
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

# Equalizer çubukları
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
c_y += 40

kart_ic_genislik = (kx2 - kx1) - 96  # 856 px güvenli metin genişliği

# Kelimeler
ar_kelimeler = [
    "اتْلُ", "مَا", "أُوحِيَ", "إِلَيْكَ", "مِنَ", "الْكِتَابِ",
    "وَأَقِمِ", "الصَّلَاةَ", "ۖ", "إِنَّ", "الصَّلَاةَ", "تَنْهَىٰ", "عَنِ", "الْفَحْشَاءِ", "وَالْمُنكَرِ"
]
tr_okunus = [
    "Utlu", "mâ", "ûhıye", "ileyke", "minel", "kitâbi",
    "ve", "ekımis-salâte,", "—", "innes-salâte", "tenhâ", "‘anil", "fahşâi", "vel-munker."
]
aktif_idx = 5

# DİNAMİK ARAPÇA VE OKUNUŞ SATIRLAMA (TAŞMAYA KARŞI TAM GÜVENLİ)
font_ar = font_al(FONT_ARAPCA, 62)
font_okunus = font_al(FONT_UI, 34, agirlik=600)

# 3 satıra dengeli bölerek taşmayı %100 önlüyoruz
ar_satirlar_gruplu = [
    (ar_kelimeler[0:6], 0),
    (ar_kelimeler[6:11], 6),
    (ar_kelimeler[11:15], 11),
]

tr_satirlar_gruplu = [
    (tr_okunus[0:6], 0),
    (tr_okunus[6:11], 6),
    (tr_okunus[11:15], 11),
]

# 4A. ARAPÇA BÖLÜMÜ
def arapca_satir_ciz(words: List[str], start_idx: int, y: int):
    toplam_w = 0
    w_list = []
    for i, w in enumerate(words):
        w_idx = start_idx + i
        gorsel_w = arapca_hazirla(w)
        bbox = draw.textbbox((0, 0), gorsel_w, font=font_ar)
        width = bbox[2] - bbox[0]
        w_list.append((w_idx, gorsel_w, width))
        toplam_w += width + 18
    toplam_w -= 18

    cur_x = (W + toplam_w) // 2
    for w_idx, gorsel_w, width in w_list:
        cur_x -= width
        if w_idx == aktif_idx:
            yuvarlak_kose_ciz(draw, (cur_x - 10, y + 2, cur_x + width + 10, y + 76), radius=14, dolgu="#FEF3C7")
            draw.text((cur_x, y), gorsel_w, font=font_ar, fill=KIRMIZI)
        elif w_idx < aktif_idx:
            draw.text((cur_x, y), gorsel_w, font=font_ar, fill=ISLAM_YESILI)
        else:
            draw.text((cur_x, y), gorsel_w, font=font_ar, fill="#2E7D56")
        cur_x -= 18

for words, s_idx in ar_satirlar_gruplu:
    arapca_satir_ciz(words, s_idx, c_y)
    c_y += 88

c_y += 18

# 4B. TÜRKÇE OKUNUŞ BÖLÜMÜ
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

for words, s_idx in tr_satirlar_gruplu:
    okunus_satir_ciz(words, s_idx, c_y)
    c_y += 48

c_y += 24

# Altın Ayraç
draw.line([(W // 2 - 110, c_y), (W // 2 + 110, c_y)], fill=ALTIN, width=2)
draw.ellipse([W // 2 - 7, c_y - 6, W // 2 + 7, c_y + 8], fill=ALTIN)
c_y += 52

# 4C. TÜRKÇE MEAL (52px Serif)
meal = "“Sana vahyedilen kitabı oku ve namazı dosdoğru kıl. Şüphesiz ki namaz, insanı hayasızlıktan ve kötülükten alıkoyar.”"
font_meal = font_al(FONT_BASLIK, 52, agirlik=600)
meal_satirlar = metin_satirla(meal, font_meal, kart_ic_genislik, draw)
for s in meal_satirlar:
    bbox = draw.textbbox((0, 0), s, font=font_meal)
    sw = bbox[2] - bbox[0]
    draw.text(((W - sw) // 2, c_y), s, font=font_meal, fill=METIN_ANA)
    c_y += 72

# 4D. GÜNÜN HİKMETİ & TEFEKKÜRÜ KUTUSU — KARTIN TABANINA GÜVENLİ VE FERAH ŞEKİLDE DAYALI
# Taşmayı kesinlikle önlemek için kartın alt sınırından (ky2) en az 56px yukarıda bitiriyoruz!
tef_metin = "Namaz sadece bir ibadet değil; günün karmaşasında ruhu arındıran, insanı kötülükten ve günahtan koruyan ilahi bir sığınaktır. Her secde kalbi yeniler."
font_tef = font_al(FONT_UI, 26, agirlik=500)
tef_satirlar = metin_satirla(tef_metin, font_tef, kart_ic_genislik - 64, draw)

tef_ic_pad_y = 24
tef_kart_h = tef_ic_pad_y * 2 + 30 + 16 + len(tef_satirlar) * 42

# Taban boşluğu: 56px (ky2 = 1630 -> tef_y2 = 1574)
tef_y2 = ky2 - 56
tef_y1 = tef_y2 - tef_kart_h
tef_x1 = kx1 + 40
tef_x2 = kx2 - 40

yuvarlak_kose_ciz(draw, (tef_x1, tef_y1, tef_x2, tef_y2), radius=24, dolgu="#F0FDF4", kenarlik="#DCFCE7", kenarlik_kalinlik=2)
draw.rounded_rectangle([tef_x1, tef_y1, tef_x1 + 8, tef_y2], radius=4, fill=CANLI_YESIL)

font_tef_baslik = font_al(FONT_UI, 22, agirlik=700)
draw.text((tef_x1 + 32, tef_y1 + 22), "GÜNÜN HİKMETİ & TEFEKKÜRÜ", font=font_tef_baslik, fill=CANLI_YESIL)

ty = tef_y1 + 68
for s in tef_satirlar:
    draw.text((tef_x1 + 32, ty), s, font=font_tef, fill=METIN_ANA)
    ty += 42

# 4E. RESMİ KAYNAK VE MEAL BİLGİSİ (Alt Taban İmzası)
kaynak_metin = "Mushaf-ı Şerif • Meal: Diyanet İşleri Başkanlığı • Tilavet: Hafs Rivayeti"
font_kaynak = font_al(FONT_UI, 18, agirlik=600)
bbox_k = draw.textbbox((0, 0), kaynak_metin, font=font_kaynak)
kw = bbox_k[2] - bbox_k[0]
draw.text(((W - kw) // 2, tef_y2 + 16), kaynak_metin, font=font_kaynak, fill=METIN_LIGHT)

# 5. ALT BÖLÜM (İlerleme Çubuğu + App Store & Google Play İndirme Rozeti)
bar_x1 = 64
bar_x2 = W - 64
bar_y = 1670
yuvarlak_kose_ciz(draw, (bar_x1, bar_y, bar_x2, bar_y + 10), radius=5, dolgu="#E2E8F0")
dolu_w = int((bar_x2 - bar_x1) * 0.40)
yuvarlak_kose_ciz(draw, (bar_x1, bar_y, bar_x1 + dolu_w, bar_y + 10), radius=5, dolgu=KIRMIZI)
draw.ellipse([bar_x1 + dolu_w - 9, bar_y - 4, bar_x1 + dolu_w + 9, bar_y + 14], fill=ALTIN, outline="#FFFFFF", width=3)

# ALT STORE & İNDİRME HAPI (Instagram Reels Safe Zone: y = 1715 .. 1800)
nav_w = 680
nav_h = 84
nav_x1 = (W - nav_w) // 2
nav_x2 = nav_x1 + nav_w
nav_y1 = 1712
nav_y2 = nav_y1 + nav_h

yuvarlak_kose_ciz(draw, (nav_x1, nav_y1, nav_x2, nav_y2), radius=32, dolgu="#FFFFFF", kenarlik="#E5DFD3", kenarlik_kalinlik=2)

# Sol: Kırmızı Ezan Plus logosu / simgesi
btn_x = nav_x1 + 38
btn_y = nav_y1 + nav_h // 2
draw.ellipse([btn_x - 22, btn_y - 22, btn_x + 22, btn_y + 22], fill=KIRMIZI)
draw.polygon([(btn_x, btn_y - 11), (btn_x - 11, btn_y), (btn_x + 11, btn_y)], fill="#FFFFFF")
draw.rectangle([btn_x - 8, btn_y, btn_x + 8, btn_y + 10], fill="#FFFFFF")
draw.rectangle([btn_x - 3, btn_y + 3, btn_x + 3, btn_y + 10], fill=KIRMIZI)

# Metin: "Ezan Plus • Ücretsiz İndirin"
font_cta = font_al(FONT_UI, 22, agirlik=700)
draw.text((btn_x + 34, btn_y - 13), "Ezan Plus • Ücretsiz İndirin", font=font_cta, fill=METIN_ANA)

# Sağ Taraf: Apple ve Google Play İkon Rozetleri
try:
    font_apple = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
    apple_x = nav_x2 - 140
    draw.text((apple_x, btn_y - 16), "\uf8ff", font=font_apple, fill="#000000")
except Exception:
    pass

# Google Play İkon Çizimi (vektörel 4 renkli üçgen)
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

play_x = nav_x2 - 82
ciz_play_store(draw, play_x, btn_y - 14, 28)

CIKTI.parent.mkdir(parents=True, exist_ok=True)
im.save(str(CIKTI), quality=95)
print("Tasarım v4 kaydedildi:", CIKTI)
