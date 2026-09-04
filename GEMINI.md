# GEMINI.md — Ezan Plus Sosyal Medya Otomasyon ve Yayın Motoru

Bu belge, **Ezan Plus Sosyal Medya Motoru** projesinin mimari anayasasıdır. Projeyi devralan yapay zeka asistanları ve yazılım geliştiriciler bu belgedeki kurallara, tasarım standartlarına ve mimari ilkelere **istisnasız** uymakla yükümlüdür.

---

## 1. Kullanıcı Profili ve Değişmez Temel İlkeler

- **Proje Sahibi:** Doğukan. Türkçe iletişim kurulur. Kararlı, estetik kalitesi son derece yüksek, hata payı sıfır olan kurumsal çıktılar bekler.
- **Marka Kimliği:** **Ezan Plus** (Ozborn Studio çatısı altında). İslami ibadet, Kur'an tilaveti, namaz vakitleri ve manevi tefekkür odaklı premium bir mobil uygulama ekosistemidir.
- **KATI KURAL — SIFIR "BOT" İBARESİ:**
  * Tüketiciye, sosyal medya platformlarına veya mağazalara yansıyan hiçbir açıklamada, web sayfasında veya paylaşımda **"bot"**, **"otomasyon"**, **"yapay zeka üretimi"** gibi yapay ifadeler yer alamaz.
  * Paylaşılan her içerik Ezan Plus editoryal ekibinin elinden çıkmış gibi zarif, edebi, saygılı ve samimi bir Türkçe ile sunulmalıdır.
- **Alan Adı ve Web:**
  * Projenin resmi Meta ve TikTok onay web sayfası `web/` dizininde yer alır (`https://ezanplus.ozbornstudio.com`).
  * `terms.html`, `privacy.html` ve marka doğrulama sayfaları aktiftir.

---

## 2. Tasarım & Video Motoru Standartları (V12 Mimarisi)

Tüm dikey video üretimi `src/uretim/video.py` motoru üzerinden gerçekleştirilir.

### A. 1080x1920 (9:16) Tuval & 4:5 Güvenli Alan Mantığı
* **Çözünürlük:** Tam dikey $1080 \times 1920$ px, 30 FPS MP4 formatı.
* **4:5 Akış (Grid) Güvenli Payı:** Üstten ve alttan bırakılan güvenli paylar sayesinde video Instagram profil ızgarasında (Feed) gösterildiğinde hiçbir metin veya logo kırpılmaz; Story, Reels, Shorts ve TikTok'ta tam ekran kusursuz görünür.
* **Kurumsal Renk Paleti:**
  - *Klasik Mushaf Krem Zemin:* `#FBF9F4`
  - *Kart Tabanı:* `#FFFDF9` (Zarif ince kenarlık: `#EAE4D5`)
  - *Marka Kırmızısı (Vurgu & İlerleme):* `#9B1B1B`
  - *İslam Yeşili (Ayet Rozeti & Vurgular):* `#1B4332`
  - *Sıcak Altın / Bal Rengi (Tefekkür):* `#B45309` / `#C29B38`
  - *Antik Koyu Mürekkep (Metin):* `#1C1917`

### B. Tipografi Standartları (`assets/fonts/`)
* **Arapça Hat:** `amiri-700-arabic.ttf` (vurgulu okuma) ve `amiri-400-arabic.ttf`.
* **Türkçe Meal & Tefekkür:** `Lora.ttf` (Zarif editoryal Serif) ve `IbarraRealNova.ttf`.
* **UI, Başlıklar ve Etiketler:** `Manrope.ttf` (Modern geometrik Sans-Serif).
* **Apple & Play Store Vektörleri:** Alt CTA alanında Ezan Plus indirme butonu, kurumsal logolar ve vektörel mağaza ikonları bulunur.

### C. Stüdyo Sesi & Kelime Bazlı Senkron Karaoke
* **Hafız:** Mişari Râşid el-Afâsî (EveryAyah 128kbps stüdyo kaydı).
* **Resmi Kelime Zaman Damgaları:** QuranCDN API'si üzerinden mikrosaniye hassasiyetinde kelime başlangıç/bitiş zamanları çekilir (`ayet_kelime_zamanlari_getir`).
* **Çift Katmanlı Karaoke:**
  - Arapça orijinal lafız ve Türkçe Latin okunuşu 1:1 kelime bazında hizalanır (`turkce_okunus_hizala`).
  - Okunan kelime anında kırmızıya (`#9B1B1B`) boyanır; hemen altında dinamik dolan animasyonlu ilerleme çizgisi akar.
  - Okunan kelimeye odaklanılırken meal ve tefekkür bölümü kartın alt kısmında huzurlu bir şekilde eşlik eder.

---

## 3. Çoklu Platform Yayın Protokolleri (`src/platformlar/`)

Tek bir onay ile 5 büyük sosyal medya kanalına eş zamanlı yayın yapılır:

```
                  ┌───────────────► 1. Instagram Reels (1080x1920)
                  ├───────────────► 2. Instagram Story (1080x1920 Tam Ekran)
[Ezan Plus Motoru]├───────────────► 3. Threads (@ezanplusapp Zincir Gönderi)
                  ├───────────────► 4. Facebook Sayfası (Ezan Plus)
                  ├───────────────► 5. YouTube Shorts (Ezan Plus Kanalı)
                  └───────────────► 6. TikTok (@ezanplusapp - Direct Post)
```

1. **Instagram Reels (`meta.py`):** Meta Graph API v22.0 üzerinden `RUPLOAD_URL` ile iki adımlı (video upload -> publish) doğrudan Reels olarak yüklenir.
2. **Instagram Story (`meta.py`):** Aynı video `media_type: STORIES` parametresiyle profil hikayelerine 24 saatlik tam ekran dikey video olarak aktarılır.
3. **Threads Zincir Gönderi (`threads.py`):**
   - Threads'in 500 karakter sınırı `metni_parcala()` algoritması ile akıllıca aşılır.
   - Ayet ve tefekkür paragraf ve cümle anlam bütünlüğü korunarak 450 karakterlik mantıklı parçalara bölünür.
   - İlk parça video ile birlikte ana post olarak paylaşılır, sonraki parçalar `reply_to_id` ile bu posta zincir olarak eklenir (`(1/3)`, `(2/3)` vb.).
4. **Facebook Sayfası (`meta.py`):** `FACEBOOK_PAGE_ACCESS_TOKEN` kullanılarak süresiz (Never Expires) token ile Ezan Plus resmi sayfasına kapak görseli ve zengin metinle post paylaşılır.
5. **YouTube Shorts (`youtube.py`):** Google YouTube Data API v3 OAuth 2.0 entegrasyonuyla `#Shorts` etiketiyle dikey video olarak kanala yüklenir.
6. **TikTok (`tiktok.py`):** TikTok Content Posting API v2 ile doğrudan hesaba video yüklenir.

---

## 4. Zamanlama, Altyapı ve Bulut Mimarisi

Türkiye sosyal medya etkileşim zirvesi dikkate alınarak **tamamen sıfır maliyetli ve kesintisiz** bir bulut altyapısı kurulmuştur:

```
[Cloudflare Edge Cron] (Her gün 19:45 TSİ - 16:45 UTC)
       │ (0 ms Gecikme, Global Dağıtık Ağ)
       ▼
[GitHub Actions Webhook] (repository_dispatch: gunluk_reels)
       │
[Ubuntu Bulut Runner]
       ├─► 1. Gemini AI ile ayeti seç & metinleri hazırla
       ├─► 2. EveryAyah'tan tilaveti, QuranCDN'den kelime zamanlarını çek
       ├─► 3. FFmpeg ile 1080x1920 V12 Reels videosunu render et
       ├─► 4. Telegram grubuna video ve "Onayla / İptal" butonlarını gönder
       └─► 5. (45 Dakika Dinleme) Doğukan onayladığında 5 platforma yayınla!
```

### A. Cloudflare Worker Zamanlayıcı (`worker/`)
* **Canlı Servis:** `https://ezan-plus-tetikleyici.ezanplus.workers.dev`
* **Neden Kuruldu?** GitHub Actions'ın yerleşik cron zamanlayıcısı yoğun saatlerde 15-45 dakika gecikebilir. Cloudflare Worker dünya çapındaki Edge sunucularıyla her gün **tam 19:45:00** olduğunda GitHub API'sine anlık webhook atar; Actions kuyruğa girmeden anında başlar.
* **Manuel Tetikleme Linki:** Beklemeden anında üretim yaptırmak için:
  👉 `https://ezan-plus-tetikleyici.ezanplus.workers.dev/tetikle`

### B. Telegram Onay & Yönetim Grubu (`src/telegram/`)
* Bot, üretilen videoyu gruba gönderir ve altına `✅ Onayla` ile `❌ İptal Et` inline butonlarını yerleştirir.
* GitHub Actions bulut sunucusu arka planda buton tıklamasını bekler (`dinle_ve_bekle`).
* Sen telefondan **"✅ Onayla"** dediğin an saniyeler içinde tüm platformlara dağıtım başlar ve Telegram mesajı yeşil başarı raporuyla güncellenir.
* Bilgisayarının açık kalmasına veya herhangi bir yerel script çalıştırmana **gerek yoktur**.

---

## 5. Dizin ve Modül Yapısı

```
EzanPlusBot/
├── .github/
│   └── workflows/
│       └── gunluk_reels.yml       # GitHub Actions günlük üretim & yayın workflow'u
├── worker/
│   ├── wrangler.toml              # Cloudflare Worker Cron Trigger ayarları
│   └── index.js                   # Sıfır gecikmeli GitHub API webhook tetikleyicisi
├── assets/
│   ├── fonts/                     # Amiri, Lora, Manrope, Ibarra fontları
│   ├── audio/                     # İndirilen ve yedek ses dosyaları
│   └── icons/                     # Marka logoları ve vektörler
├── web/
│   ├── index.html, terms.html     # Meta / TikTok doğrulama ve yasal sayfalar
├── data/
│   ├── ezanplus.db                # SQLite içerik ve yayın kayıtları
│   ├── cikti/                     # Render edilen MP4 ve PNG çıktıları
│   └── onbellek/                  # İndirilen tilavet sesleri
├── scripts/
│   └── tiktok_yetki.py            # TikTok yetkilendirme aracı
├── tests/
│   └── prototipler/               # Geliştirme sürecindeki test ve deneme scriptleri
├── src/                           # Çekirdek Python Paketi
│   ├── __init__.py
│   ├── ayar.py                    # Yapılandırma, yollar, renkler ve sabitler
│   ├── db.py                      # SQLite veritabanı yönetim modülü
│   ├── otomasyon.py               # Günlük pipeline orkestrasyon motoru & CLI
│   │
│   ├── uretim/                    # İçerik ve Medya Üretim Katmanı
│   │   ├── __init__.py
│   │   ├── ai.py                  # Gemini AI ayet, meal, tefekkür promptları
│   │   ├── ses.py                 # EveryAyah ses indirme & kelime senkronu
│   │   ├── kart.py                # 1080x1350 infografik kart çizici
│   │   └── video.py               # 1080x1920 V12 Reels karaoke render motoru
│   │
│   ├── platformlar/               # Sosyal Medya API Dağıtım Katmanı
│   │   ├── __init__.py
│   │   ├── meta.py                # Instagram Reels, Story & Facebook Page
│   │   ├── threads.py             # Threads akıllı zincir gönderileri
│   │   ├── youtube.py             # YouTube Shorts API yükleyici
│   │   └── tiktok.py              # TikTok Direct Post API
│   │
│   └── telegram/                  # Telegram Onay & Yönetim Katmanı
│       ├── __init__.py
│       ├── bot.py                 # Önizleme kartı, inline butonlar, getUpdates
│       └── yonetici.py            # Çoklu platform yayın dağıtım orkestrasyonu
│
├── GEMINI.md                      # Bu anayasa belgesi
├── config.yaml                    # Proje ve şablon ayarları
├── requirements.txt               # Python bağımlılıkları
└── .env                           # API anahtarları ve token'lar (asla git'e girmez)
```

---

## 6. Gelecek Geliştirme Yol Haritası (Sıradaki Adımlar)

1. **Farklı İçerik Türlerinin Eklenmesi:**
   * **Hadis-i Şerif Serisi:** Riyazü's-Salihin'den sahih hadisler ve ahlak/fazilet odaklı 9:16 kart/videolar.
   * **Günün Duası:** Kur'an'dan peygamber duaları ve Cevşen-ül Kebir niyazları.
   * **Günün Zikri & Esmaü'l Hüsna:** Anlamı, ebced değeri ve faziletiyle zikir serileri.
2. **Telegram İki Yönlü Komut Menüsü:**
   * Bot grubundan `/ayet`, `/hadis`, `/dua` komutlarıyla anında istenen türde taslak ürettirme.
   * `/yayinla <ID>` ile geçmiş bir taslağı tekrar yayına alma.
   * `/durum` ile haftalık istatistik ve yayın raporu sorgulama.
3. **TikTok Uygulama İncelemesi (App Review):**
   * TikTok Developer Portal'daki inceleme tamamlandığında tek tıkla token alınacak ve TikTok da tam otomatik yayın zincirine bağlanacaktır.
