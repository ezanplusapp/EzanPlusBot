"""
scripts/tiktok_yetki.py — TikTok OAuth Yetkilendirme Aracı
Ezan Plus TikTok Direct Post için ilk kez access ve refresh token almak üzere kullanılır.
"""

import sys
from pathlib import Path

# Proje kökünü sys.path'e ekle
KOK_DIZIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK_DIZIN))

from src.tiktok import yetki_al

if __name__ == "__main__":
    kod = sys.argv[1] if len(sys.argv) > 1 else None
    print("🚀 TikTok OAuth Yetkilendirme Başlatılıyor...")
    try:
        token = yetki_al(manuel_kod=kod)
        print("\n✅ TEBRİKLER! TikTok yetkilendirmesi tamamlandı ve data/tiktok_token.json dosyasına kaydedildi.")
    except Exception as e:
        print(f"\n❌ Hata oluştu: {e}")
        sys.exit(1)
