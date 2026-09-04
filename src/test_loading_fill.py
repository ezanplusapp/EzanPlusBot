import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from src.ayar import KOK_DIZIN
from src.sablon_ciz import font_al, arapca_hazirla, FONT_UI

FONTLAR = KOK_DIZIN / "assets" / "fonts"
font_ar_norm = font_al(FONTLAR / "amiri-400-arabic.ttf", 78)
font_ar_bold = font_al(FONTLAR / "amiri-700-arabic.ttf", 82)
font_okunus_norm = font_al(FONT_UI, 34, agirlik=500)
font_okunus_bold = font_al(FONT_UI, 36, agirlik=800)

KIRMIZI = "#C0392B"
GRI_INACTIVE = "#94A3B8"
KOYU_SPOKEN = "#1E293B"
YESIL_INACTIVE = "#2E7D56"
YESIL_SPOKEN = "#0D5C3A"

def loading_efekti_ciz_latin(draw: ImageDraw.ImageDraw, word: str, mid_x: int, y: int, progress: float):
    """
    Latin kelimeyi (soldan sağa) progress oranında loading gibi doldurur.
    progress: 0.0 (henüz başlamadı) -> 1.0 (tamamlandı)
    """
    fnt = font_okunus_bold
    bbox = draw.textbbox((0, 0), word, font=fnt)
    w_text = bbox[2] - bbox[0]
    h_text = bbox[3] - bbox[1]
    x_start = mid_x - w_text // 2
    
    # 1. Taban: Gri (okunmamış metin)
    draw.text((x_start, y), word, font=fnt, fill=GRI_INACTIVE)
    
    # 2. Doldurulan kısım (Soldan Sağa Loading)
    if progress > 0.0:
        dolum_w = int(w_text * min(1.0, progress))
        # Maske ile tam dolum sınırını kırmızı çiz
        # Pillow'da clip/mask veya bitmap dilimleme:
        # En temiz yöntem: kelimenin dolan kısmını kırmızı olarak tam sınırda çizmek
        # Ya da küçük bir RGBA parçasını paste etmek
        w_crop = max(1, dolum_w)
        img_word = Image.new("RGBA", (w_text + 4, h_text + 10), (0, 0, 0, 0))
        d_word = ImageDraw.Draw(img_word)
        d_word.text((0, 0), word, font=fnt, fill=KIRMIZI)
        
        # Sadece dolum_w kadarını al
        cropped = img_word.crop((0, 0, w_crop, img_word.height))
        draw._image.paste(cropped, (x_start, y), cropped)

def loading_efekti_ciz_arapca(draw: ImageDraw.ImageDraw, word: str, mid_x: int, y: int, progress: float):
    """
    Arapça kelimeyi (sağdan sola) progress oranında loading gibi doldurur.
    progress: 0.0 -> 1.0
    """
    gw = arapca_hazirla(word)
    fnt = font_ar_bold
    bbox = draw.textbbox((0, 0), gw, font=fnt)
    w_text = bbox[2] - bbox[0]
    h_text = bbox[3] - bbox[1]
    x_start = mid_x - w_text // 2
    
    # 1. Taban: Açık yeşil (okunmamış)
    draw.text((x_start, y), gw, font=fnt, fill=YESIL_INACTIVE)
    
    # 2. Doldurulan kısım (Sağdan Sola Loading)
    if progress > 0.0:
        dolum_w = int(w_text * min(1.0, progress))
        w_crop = max(1, dolum_w)
        
        img_word = Image.new("RGBA", (w_text + 4, h_text + 30), (0, 0, 0, 0))
        d_word = ImageDraw.Draw(img_word)
        d_word.text((0, 0), gw, font=fnt, fill=KIRMIZI)
        
        # Arapça sağdan sola aktığı için görselin sağ tarafından crop edilir:
        # crop kutusu: (w_text - w_crop, 0, w_text, height)
        crop_x1 = max(0, img_word.width - w_crop)
        cropped = img_word.crop((crop_x1, 0, img_word.width, img_word.height))
        draw._image.paste(cropped, (x_start + crop_x1, y), cropped)

# Test edelim
canvas = Image.new("RGB", (1080, 400), "#FFFFFF")
draw = ImageDraw.Draw(canvas)

# 4 adım gösterelim: %15, %40, %70, %100
adimlar = [0.15, 0.40, 0.70, 1.0]
for idx, p in enumerate(adimlar):
    mid_x = 135 + idx * 270
    loading_efekti_ciz_arapca(draw, "الدُّنْيَا", mid_x, 60, p)
    loading_efekti_ciz_latin(draw, "dunyâ", mid_x, 220, p)
    draw.text((mid_x - 30, 320), f"%{int(p*100)}", font=font_okunus_norm, fill="#64748B")

out_p = KOK_DIZIN / "data" / "cikti" / "test_loading_adimlar.png"
canvas.save(str(out_p))
print(f"Loading adımları kaydedildi: {out_p}")
