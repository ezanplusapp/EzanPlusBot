"""
src/telegram — Ezan Plus Telegram Onay ve Yayın Yönetim Paketi
- bot: Telegram önizleme kartları, inline butonlar, getUpdates dinleyici
- yonetici: Çoklu platform yayın dağıtım orkestrasyonu
"""

from . import bot
from . import yonetici
from .bot import (
    mesaj_gonder,
    gorsel_gonder,
    video_gonder,
    onay_istegi_gonder,
    tek_sefer_dinle,
)
from .yonetici import yayinla_hepsi

__all__ = [
    "bot",
    "yonetici",
    "mesaj_gonder",
    "gorsel_gonder",
    "video_gonder",
    "onay_istegi_gonder",
    "tek_sefer_dinle",
    "yayinla_hepsi",
]
