"""
bot_servis.py — Arka Planda Sürekli Çalışan Telegram Onay Dinleyicisi
Telegram grubundan gelen 'Onayla' veya 'İptal' buton tıklamalarını
kesintisiz dinler ve yayın işlemlerini anında tetikler.
"""

import logging
import time
from src import telegram_bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("bot_servis")

def main():
    log.info("Ezan Plus Telegram onay servisi başlatıldı (Sürekli Dinleme)...")
    offset = 0
    while True:
        try:
            offset = telegram_bot.tek_sefer_dinle(offset)
        except Exception as e:
            log.error(f"Döngü hatası: {e}")
        time.sleep(2)

if __name__ == "__main__":
    main()
