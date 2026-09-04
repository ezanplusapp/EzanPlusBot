"""
Karaoke / Canlı Kelime Vurgulu Reels Testi
Ayet meali ses ilerledikçe kelime kelime altın sarısı / kırmızı renkle parlar.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from src.ayar import KOK_DIZIN
from src.sablon_ciz import font_al, arapca_hazirla, arapca_satirla, metin_satirla, yuvarlak_kose_ciz, rozet_ciz, FONT_ARAPCA, FONT_BASLIK, FONT_UI

CIKTI = KOK_DIZIN / "data" / "cikti" / "karaoke_tasarim_test.png"
IKONLAR = KOK_DIZIN / "assets" / "icons"

W, H = 1080, 1920

# Kurumsal Renkler
BG_KREM = "#F4F1EA"
KIRMIZI = "#C0392B"
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

# 2. ÜSTTE BÜYÜK VE ORTALI LOGO & UYGULAMA ADI (Kullanıcının 2. isteği)
logo_yolu = IKONLAR / "logo.png"
logo_boyut = 96
logo_x = (W - logo_boyut) // 2
logo_y = 70

if logo_yolu.exists():
    logo = Image.open(logo_yolu).convert("RGBA")
    logo = logo.resize((logo_boyut, logo_boyut), Image.Resampling.LANCZOS)
    maske = Image.new("L", (logo_boyut, logo_boyut), 0)
    draw_m = ImageDraw.Draw(maske)
    draw_m.rounded_rectangle([0, 0, logo_boyut, logo_boyut], radius=24, fill=255)
    im.paste(logo, (logo_x, logo_y), maske)

# Logo Altında Ortalı Ezan Plus ve Slogan
font_marka = font_al(FONT_UI, 38, agirlik=800)
bbox_m = draw.textbbox((0, 0), "Ezan Plus", font=font_marka)
mw = bbox_m[2] - bbox_m[0]
draw.text(((W - mw) // 2, logo_y + 104), "Ezan Plus", font=font_marka, fill=METIN_ANA)

font_alt = font_al(FONT_UI, 19, agirlik=600)
slogan = "GÜNLÜK İBADET VE HUZUR REHBERİN"
bbox_alt = draw.textbbox((0, 0), slogan, font=font_alt)
aw = bbox_alt[2] - bbox_alt[0]
draw.text(((W - aw) // 2, logo_y + 150), slogan, font=font_alt, fill=METIN_MUTED)

# 3. İÇERİKLE İLGİLİ DİNAMİK BAŞLIK (Kullanıcının 1. isteği)
# Ankebût 45 için içerikle doğrudan bağlantılı manevi başlık
b_y = 265
font_baslik = font_al(FONT_UI, 46, agirlik=800)

satir1 = "Namaz, kötülüklerden alıkoyan"
bbox_s1 = draw.textbbox((0, 0), satir1, font=font_baslik)
draw.text(((W - (bbox_s1[2] - bbox_s1[0])) // 2, b_y), satir1, font=font_baslik, fill=METIN_ANA)

satir2 = "en güçlü kalkandır."
bbox_s2 = draw.textbbox((0, 0), satir2, font=font_baslik)
draw.text(((W - (bbox_s2[2] - bbox_s2[0])) // 2, b_y + 58), satir2, font=font_baslik, fill=KIRMIZI)

# 4. MERKEZİ KART
kx1 = 64
ky1 = 415
kx2 = W - 64
ky2 = 1630

# Gölge ve Beyaz Kart
for g in range(8, 0, -2):
    yuvarlak_kose_ciz(draw, (kx1 - g, ky1 - g, kx2 + g, ky2 + g), radius=40 + g, dolgu="#EAE5D8")
yuvarlak_kose_ciz(draw, (kx1, ky1, kx2, ky2), radius=40, dolgu=KART_BG, kenarlik=KART_KENARLIK, kenarlik_kalinlik=2)

# Kart Üst Bilgisi
c_y = ky1 + 36
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

c_y += 52
draw.line([(kx1 + 44, c_y), (kx2 - 44, c_y)], fill="#F1ECE1", width=2)
c_y += 40

genislik = (kx2 - kx1) - 88

# ARAPÇA AYET METNİ (Daha büyük ve ferah)
arapca_metin = "اتْلُ مَا أُوحِيَ إِلَيْكَ مِنَ الْكِتَابِ وَأَقِمِ الصَّلَاةَ ۖ إِنَّ الصَّلَاةَ تَنْهَىٰ عَنِ الْفَحْشَاءِ وَالْمُنكَرِ"
font_ar = font_al(FONT_ARAPCA, 52)
ar_satirlar = arapca_satirla(arapca_metin, font_ar, genislik, draw)
for s in ar_satirlar:
    bbox = draw.textbbox((0, 0), s, font=font_ar)
    sw = bbox[2] - bbox[0]
    draw.text(((W - sw) // 2, c_y), s, font=font_ar, fill=ISLAM_YESILI)
    c_y += 80

c_y += 24
draw.line([(W // 2 - 80, c_y), (W // 2 + 80, c_y)], fill=ALTIN, width=2)
draw.ellipse([W // 2 - 5, c_y - 4, W // 2 + 5, c_y + 6], fill=ALTIN)
c_y += 44

# TÜRKÇE MEAL — CANLI KARAOKE KELİME VURGUSU TESTİ (Kullanıcının 5. isteği)
meal = "Sana vahyedilen kitabı oku ve namazı dosdoğru kıl. Şüphesiz ki namaz, insanı hayasızlıktan ve kötülükten alıkoyar..."
kelimeler = meal.split()
# Örnek: Seslendirmede o an 'namazı' kelimesinde olduğumuzu varsayalım (örnek kelime indexi: 6)
aktif_kelime_idx = 6

font_meal = font_al(FONT_BASLIK, 42, agirlik=600)

# Kelimeleri satırlara yerleştir ve aktif kelimeyi parlak ALTIN / KIRMIZI ile çiz
satirlar = []
mevcut = []
for k in kelimeler:
    if draw.textbbox((0, 0), " ".join(mevcut + [k]), font=font_meal)[2] <= genislik:
        mevcut.append(k)
    else:
        satirlar.append(mevcut)
        mevcut = [k]
if mevcut:
    satirlar.append(mevcut)

k_sayac = 0
for satir_kelimeleri in satirlar:
    # Satır genişliğini hesapla
    satir_str = " ".join(satir_kelimeleri)
    satir_w = draw.textbbox((0, 0), satir_str, font=font_meal)[2]
    cur_x = (W - satir_w) // 2

    for kelime in satir_kelimeleri:
        kw = draw.textbbox((0, 0), kelime, font=font_meal)[2]

        if k_sayac == aktif_kelime_idx:
            # O AN OKUNAN KELİME: Arkasında hafif parlak altın kutu ve koyu kırmızı/altın metin!
            yuvarlak_kose_ciz(draw, (cur_x - 6, c_y - 4, cur_x + kw + 6, c_y + 48), radius=10, dolgu="#FEF3C7")
            draw.text((cur_x, c_y), kelime, font=font_meal, fill=KIRMIZI)
        elif k_sayac < aktif_kelime_idx:
            # Daha önce okunmuş kelimeler: Tok koyu siyah
            draw.text((cur_x, c_y), kelime, font=font_meal, fill=METIN_ANA)
        else:
            # Henüz okunmamış kelimeler: Hafif gri/soluk
            draw.text((cur_x, c_y), kelime, font=font_meal, fill="#64748B")

        # Boşluk genişliği
        bosluk_w = draw.textbbox((0, 0), " ", font=font_meal)[2]
        cur_x += kw + bosluk_w
        k_sayac += 1

    c_y += 62

# 5. YENİ FERAH VE ZARİF TEFEKKÜR KARTI (Kullanıcının 4. isteği: Yeşil tonu değiştirildi)
# Ağır koyu yeşil yerine ferah nane-zümrüt zemin (#ECFDF5) ve canlı yeşil (#059669) aksan
esma_y1 = ky2 - 310
esma_y2 = ky2 - 36
esma_x1 = kx1 + 36
esma_x2 = kx2 - 36

# Ferah zemin
yuvarlak_kose_ciz(draw, (esma_x1, esma_y1, esma_x2, esma_y2), radius=28, dolgu="#F0FDF4", kenarlik="#DCFCE7", kenarlik_kalinlik=2)
# Sol zümrüt aksan çizgisi
draw.rounded_rectangle([esma_x1, esma_y1, esma_x1 + 8, esma_y2], radius=4, fill=CANLI_YESIL)

font_esma_baslik = font_al(FONT_UI, 21, agirlik=700)
draw.text((esma_x1 + 32, esma_y1 + 24), "GÜNÜN HİKMETİ & TEFEKKÜRÜ", font=font_esma_baslik, fill=CANLI_YESIL)

tef_metin = "Namaz sadece bir ibadet değil; günün karmaşasında ruhu arındıran, insanı kötülükten ve günahtan koruyan ilahi bir sığınaktır."
font_tef = font_al(FONT_UI, 24, agirlik=500)
tef_satirlar = metin_satirla(tef_metin, font_tef, (esma_x2 - esma_x1) - 64, draw)
ty = esma_y1 + 68
for s in tef_satirlar:
    draw.text((esma_x1 + 32, ty), s, font=font_tef, fill=METIN_ANA)
    ty += 36

# 6. ALT BAR
bar_x1 = 64
bar_x2 = W - 64
bar_y = 1670
yuvarlak_kose_ciz(draw, (bar_x1, bar_y, bar_x2, bar_y + 10), radius=5, dolgu="#E2E8F0")
dolu_w = int((bar_x2 - bar_x1) * 0.45)
yuvarlak_kose_ciz(draw, (bar_x1, bar_y, bar_x1 + dolu_w, bar_y + 10), radius=5, dolgu=KIRMIZI)
draw.ellipse([bar_x1 + dolu_w - 9, bar_y - 4, bar_x1 + dolu_w + 9, bar_y + 14], fill=ALTIN, outline="#FFFFFF", width=3)

nav_x1 = (W - 580) // 2
nav_x2 = nav_x1 + 580
nav_y1 = 1730
nav_y2 = 1810
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
print("Karaoke tasarım testi kaydedildi:", CIKTI)
