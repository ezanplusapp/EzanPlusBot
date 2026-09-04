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

KIRMIZI = (192, 57, 43, 255)
GRI_INACTIVE = (148, 163, 184, 255)
KOYU_SPOKEN = (30, 41, 59, 255)

# Test edelim: Latin okunuş "dunyâ" ve Arapça "الدُّنْيَا"
# 4 farklı progress: 0.1, 0.4, 0.7, 1.0

def ciz_akan_kelime_latin(word: str, progress: float):
    # Base RGBA
    w_box = 300
    h_box = 100
    im = Image.new("RGBA", (w_box, h_box), (255, 255, 255, 0))
    
    # 1. Taban gri metin
    draw = ImageDraw.Draw(im)
    bbox = draw.textbbox((0, 0), word, font=font_okunus_bold)
    w_text = bbox[2] - bbox[0]
    h_text = bbox[3] - bbox[1]
    tx = (w_box - w_text) // 2
    ty = (h_box - h_text) // 2
    
    # Gri zemin (okunmamış)
    draw.text((tx, ty), word, font=font_okunus_bold, fill="#94A3B8")
    
    # 2. Kırmızı metin katmanı
    im_red = Image.new("RGBA", (w_box, h_box), (255, 255, 255, 0))
    draw_red = ImageDraw.Draw(im_red)
    draw_red.text((tx, ty), word, font=font_okunus_bold, fill="#C0392B")
    
    # 3. Maske oluştur: progress'e göre soldan sağa yumuşak geçiş
    mask = Image.new("L", (w_box, h_box), 0)
    draw_mask = ImageDraw.Draw(mask)
    
    # Geçiş sınırı
    feather = 20 # 20px yumuşak tüy kenar
    cut_x = tx + int(w_text * progress)
    
    # cut_x'e kadar tam 255
    if cut_x - feather > 0:
        draw_mask.rectangle([0, 0, cut_x - feather, h_box], fill=255)
    
    # feather aralığında gradyan
    for x in range(max(0, cut_x - feather), min(w_box, cut_x + feather)):
        alpha = int(255 * (1.0 - (x - (cut_x - feather)) / (2 * feather)))
        draw_mask.line([(x, 0), (x, h_box)], fill=255 - alpha)
        
    im.paste(im_red, (0, 0), mask)
    return im

for p in [0.0, 0.25, 0.5, 0.75, 1.0]:
    res = ciz_akan_kelime_latin("dunyâ", p)
    res.save(f"data/cikti/test_soft_latin_{int(p*100)}.png")
    print(f"Latin p={p} kaydedildi")
