"""
ayar.py — Ezan Plus Bot Yapılandırma Yöneticisi
config.yaml ve .env dosyalarını okur, doğrular ve sisteme sunar.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict
import yaml
from dotenv import load_dotenv

KOK_DIZIN = Path(__file__).resolve().parent.parent
ENV_YOLU = KOK_DIZIN / ".env"
CONFIG_YOLU = KOK_DIZIN / "config.yaml"

# .env yükle
load_dotenv(dotenv_path=ENV_YOLU)


def ayar_yukle() -> Dict[str, Any]:
    """config.yaml dosyasını okur ve sözlük olarak döner."""
    if not CONFIG_YOLU.exists():
        raise FileNotFoundError(f"Yapılandırma dosyası bulunamadı: {CONFIG_YOLU}")

    with open(CONFIG_YOLU, "r", encoding="utf-8") as f:
        ayarlar = yaml.safe_load(f) or {}

    return ayarlar


# Tekil örnek (Singleton gibi)
AYARLAR = ayar_yukle()


def get_renk(renk_adi: str, varsayilan: str = "#000000") -> str:
    """Belirtilen rengi config'den çeker."""
    return AYARLAR.get("renkler", {}).get(renk_adi, varsayilan)


def get_env(anahtar: str, varsayilan: str = "") -> str:
    """Ortam değişkenini döner."""
    return os.getenv(anahtar, varsayilan).strip()
