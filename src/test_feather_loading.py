from PIL import Image, ImageDraw
from pathlib import Path
from src.ayar import KOK_DIZIN
from src.sablon_ciz import font_al, arapca_hazirla, FONT_UI

FONTLAR = KOK_DIZIN / "assets" / "fonts"
font_ar_bold = font_al(FONTLAR / "amiri-700-arabic.ttf", 82)
font_okunus_bold = font_al(FONT_UI, 36, agirlik=800)

KIRMIZI = "#C0392B"
GRI_INACTIVE = "#94A3B8"
YESIL_INACTIVE = "#2E7D56"

def ciz_loading_feather_latin(draw: ImageDraw.ImageDraw, word: str, mid_x: int, y: int, progress: float):
    fnt = font_okunus_bold
    bbox = draw.textbbox((0, 0), word, font=fnt)
    w_text = bbox[2] - bbox[0]
    h_text = bbox[3] - bbox[1]
    x_start = mid_x - w_text // 2
    
    # 1. Taban gri
    draw.text((x_start, y), word, font=fnt, fill=GRI_INACTIVE)
    
    if progress <= 0.0:
        return
    if progress >= 1.0:
        draw.text((x_start, y), word, font=fnt, fill=KIRMIZI)
        return

    # RGBA kırmızı katman
    pad = 8
    im_red = Image.new("RGBA", (w_text + pad * 2, h_text + pad * 2), (0, 0, 0, 0))
    d_red = ImageDraw.Draw(im_red)
    d_red.text((pad, pad), word, font=fnt, fill=KIRMIZI)

    # Yumuşak geçiş maskesi (Soldan Sağa)
    mask = Image.new("L", im_red.size, 0)
    d_mask = ImageDraw.Draw(mask)
    
    feather = 8
    target_x = pad + int(w_text * progress)
    
    # Tam opak bölge
    if target_x - feather > 0:
        d_mask.rectangle([0, 0, target_x - feather, mask.height], fill=255)
    
    # Yumuşak geçiş bölgesi
    for px in range(max(0, target_x - feather), min(mask.width, target_x + feather)):
        alpha = int(255 * (1.0 - (px - (target_x - feather)) / (2 * feather)))
        d_mask.line([(px, 0), (px, mask.height)], fill=255 - alpha)

    # Maskeyi uygula
    draw._image.paste(im_red, (x_start - pad, y - pad), mask)


def ciz_loading_feather_arapca(draw: ImageDraw.ImageDraw, word: str, mid_x: int, y: int, progress: float):
    gw = arapca_hazirla(word)
    fnt = font_ar_bold
    bbox = draw.textbbox((0, 0), gw, font=fnt)
    w_text = bbox[2] - bbox[0]
    h_text = bbox[3] - bbox[1]
    x_start = mid_x - w_text // 2
    
    # 1. Taban yeşil
    draw.text((x_start, y), gw, font=fnt, fill=YESIL_INACTIVE)
    
    if progress <= 0.0:
        return
    if progress >= 1.0:
        draw.text((x_start, y), gw, font=fnt, fill=KIRMIZI)
        return

    pad = 12
    im_red = Image.new("RGBA", (w_text + pad * 2, h_text + pad * 2), (0, 0, 0, 0))
    d_red = ImageDraw.Draw(im_red)
    d_red.text((pad, pad), gw, font=fnt, fill=KIRMIZI)

    mask = Image.new("L", im_red.size, 0)
    d_mask = ImageDraw.Draw(mask)
    
    feather = 10
    # Arapça sağdan sola dolduğu için:
    # 0.0 -> maske sağ kenarda (width)
    # 1.0 -> maske sol kenara kadar dolu (0)
    target_x = (mask.width - pad) - int(w_text * progress)
    
    # target_x + feather'dan sağa kadar tam opak (255)
    if target_x + feather < mask.width:
        d_mask.rectangle([target_x + feather, 0, mask.width, mask.height], fill=255)
        
    for px in range(max(0, target_x - feather), min(mask.width, target_x + feather)):
        alpha = int(255 * ((px - (target_x - feather)) / (2 * feather)))
        d_mask.line([(px, 0), (px, mask.height)], fill=alpha)

    draw._image.paste(im_red, (x_start - pad, y - pad), mask)


canvas = Image.new("RGB", (1080, 400), "#FFFFFF")
draw = ImageDraw.Draw(canvas)

adimlar = [0.15, 0.40, 0.70, 1.0]
for idx, p in enumerate(adimlar):
    mid_x = 135 + idx * 270
    ciz_loading_feather_arapca(draw, "الدُّنْيَا", mid_x, 60, p)
    ciz_loading_feather_latin(draw, "dunyâ", mid_x, 220, p)
    draw.text((mid_x - 30, 320), f"%{int(p*100)}", font=font_okunus_bold, fill="#64748B")

out_p = KOK_DIZIN / "data" / "cikti" / "test_feather_loading_adimlar.png"
canvas.save(str(out_p))
print(f"Feathered loading adımları kaydedildi: {out_p}")
