"""
src/platformlar — Ezan Plus Çoklu Sosyal Medya Dağıtım Paketi
- meta: Instagram Reels, Video/Görsel Story, Carousel ve Facebook Sayfa paylaşımları
- threads: Threads metin ve akıllı zincir gönderileri
- youtube: YouTube Data API v3 ile 9:16 Shorts video yükleyici
- tiktok: TikTok Content Posting API ile doğrudan video yükleyici
- r2: Cloudflare R2 Object Storage S3 SigV4 medya barındırma motoru
"""

from . import meta
from . import threads
from . import youtube
from . import tiktok
from . import r2

__all__ = ["meta", "threads", "youtube", "tiktok", "r2"]

