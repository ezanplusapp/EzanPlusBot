# GEMINI.md — Ezan Plus Sosyal Medya Otomasyon ve Yayın Motoru

Bu belge, **Ezan Plus Sosyal Medya Motoru** projesinin mimari anayasasıdır. Projeyi devralan yapay zeka asistanları ve yazılım geliştiriciler bu belgedeki kurallara, tasarım standartlarına ve mimari ilkelere **istisnasız** uymakla yükümlüdür.

---

## 1. Kullanıcı Profili ve Değişmez Temel İlkeler

- **Proje Sahibi:** Doğukan. Türkçe iletişim kurulur. Kararlı, estetik kalitesi son derece yüksek, hata payı sıfır olan kurumsal çıktılar bekler.
- **Marka Kimliği:** **Ezan Plus** (Ozborn Studio çatısı altında). İslami ibadet, Kur'an tilaveti, namaz vakitleri ve manevi tefekkür odaklı premium bir mobil uygulama ekosistemidir.
- **KATI KURAL — SIFIR "BOT" İBARESİ:**
  * Tüketiciye, sosyal medya platformlarına veya mağazalara yansıyan hiçbir açıklamada, web sayfasında veya paylaşımda **"bot"**, **"otomasyon"**, **"yapay zeka üretimi"** gibi yapay ifadeler yer alamaz.
  * Paylaşılan her içerik Ezan Plus editoryal ekibinin elinden çıkmış gibi zarif, edebi, saygılı ve samimi bir Türkçe ile sunulmalıdır.
- **KATI KURAL — SIFIR HALÜSİNASYON & TESCİLLİ KAYNAK ZORUNLULUĞU:**
  * Hadis ve Ayet mealleri, Arapça orijinal metinler ve kaynak referansları **asla yapay zekaya (Gemini'ye) sıfırdan yazdırılamaz**.
  * **Sahih Hadisler:** Doğrudan yerel tescilli külliyat veritabanından (`data/hadisler/hadisler.db` - Riyâzü's-Sâlihîn 1.900 hadis) çekilir (`src/hadis_db.py`).
  * **Kur'an Âyetleri ve Mealleri:** Doğrudan yerel tescilli Kur'an veritabanından (`data/kuran/kuran.db` - 6.236 âyet, 114 sûre) çekilir (`src/kuran_db.py`). Orijinal Arapça hat Medine Kral Fehd Uthmani metnidir; mealler resmi Elmalılı Hamdi Yazır ve Diyanet İşleri Başkanlığı külliyatıdır.
  * **Gemini AI'nin Sınırı:** Gemini AI yalnızca bu tescilli metinler üzerine edebi transkripsiyon (Latin okunuş), 2 satırlık video başlıkları, "Günün Nebevî Öğüdü / Hikmet Notu" (tefekkür) ve 5 odaklı hashtag'e sahip sosyal medya metni (caption) üretir.
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
* **Resmi Kelime Zaman Damgaları:** 114 sûre ve 6.236 âyetin tamamına ait Mişari Râşid el-Afâsî stüdyo tilavet zaman damgaları (80.537 kelime) yerel repoda `data/zamanlar/sure_{1..114}.json` altında saklanır. Sıfır harici API bağımlılığı ve sıfır gecikmeyle %100 offline çalışır (`ayet_kelime_zamanlari_getir`).
* **Çift Katmanlı Karaoke:**
  - Arapça orijinal lafız ve Türkçe Latin okunuşu 1:1 kelime bazında hizalanır (`turkce_okunus_hizala`).
  - Okunan kelime anında kırmızıya (`#9B1B1B`) boyanır; başından sonuna doğru akan dinamik loading dolum çizgisi akar.
  - Okunan kelimeye odaklanılırken meal ve tefekkür bölümü kartın alt kısmında huzurlu bir şekilde eşlik eder.

### D. Uzun Ayet Çoklu Sayfa Geçiş Motoru & Dinamik Flex Mizanpaj
* **Otomatik Tetikleme:** Ayet 20 kelimeyi aştığında metni sıkıştırmak veya fontu küçültmek yerine otomatik olarak 2 veya 3 sayfaya bölünür (`sayfa_sayisi = math.ceil(toplam_kelime / 18)`).
* **Dinamik Flex Mizanpaj:**
  - *Üste Dayalı Tilavet (`Y = 484`):* Arapça satır yüksekliği `96px` (66pt ferah font), Türkçe okunuş ile arasında `24px` nefes payı bırakılır. 4 satırlık metinlerde dahi çakışma ve taşma imkansızdır.
  - *Alta Dayalı Günün Hikmeti & Tefekkür (`Y = 1566 - tef_h - 16`):* `_tefekkur_yukseklik_hesapla` formülü ile hesaplanan tefekkür bloğu kartın alt sınırına dayalıdır. Çok sayfalı geçişlerde Sayfa 1 ve Sayfa 2'de milimetrik olarak aynı pikselde sabitlenir; geçişte sıfır ghosting (çift görüntü) ve sıfır titreme sağlanır.
  - *Orta Flex Alan (Meal & Ayraç):* Tilavet bitişi ile tefekkür başlangıcı arasındaki kalan serbest dikey boşluk hesaplanarak Türkçe meal ve altın ayraç dikeyde ortalanır (`pad_ust = int(serbest_bosluk * 0.42)`).
* **Akıllı Cümle / Meal Bölücü (`_meal_parcala`):** Türkçe meal rastgele kesilmez; nokta, soru işareti veya virgül gibi doğal durak yerlerinden bölünerek her sayfaya anlam bütünlüğü tam olan kısım yerleştirilir.
* **Sinematik Erime (Crossfade) & Zaman Odaklı Sayfa Seçimi:** Sayfa sonlarında hafızın nefes aralığında 0.45 saniyelik pürüzsüz `Image.blend` erimesi gerçekleşir.
  - *Zaman Odaklı Kilitleme:* Kare döngüsünde aktif sayfa (`active_p`), `aktif_idx` kelime sayacına göre değil; kesin olarak `gecisler` zaman pencerelerine göre (`t_sec < t_s` / `t_sec > t_e`) belirlenir. Bu sayede hafızın nefes duraklamalarında veya ses gecikmelerinde Sayfa 2'den tekrar Sayfa 1'e geri sıçrama (ghosting/snapback/freeze) tamamen engellenmiştir.
  - *Kelime Zaman Damgası Normalizasyonu (`kelime_zamanlarini_hizala`):* QuranCDN segment sayıları ile Kur'an metnindeki kelime sayıları farklılık gösterse dahi (örn. 40 segmente karşılık 39 kelime) zaman damgaları kümülatif zaman enterpolasyonu ile 1:1 kelime sayısına eşitlenir; kelime sapması veya sayacın erken durması önlenir.
* **Kesintisiz Animasyon:** Ekolayzır ses dalgaları ve alt ilerleme çubuğu 30 FPS hızında kesintisiz akmaya devam eder.

### E. Dinamik Tipografi Ölçeklendirme Tavanları (V12.2 Mimarisi)
* **Arapça Hat Dinamik Tavanı (`pt_ar`):**
  - *Tek Satır Ultra-Kısa Âyetler (İhlâs 1, Kevser 1 vb.):* Kartın üst alanındaki ferahlığı heybetle doldurmak için **138pt** devasa hat kullanılır.
  - *Çok Satırlı Âyetler:* Mizanpaj sıkışmasını ve Türkçe okunuşla çakışmayı önlemek için katı tavan **114pt** ile sınırlandırılmıştır (`ar_len < 35` için 114pt; `< 55` için 96pt; `< 90` için 78pt; uzun metinlerde 66pt).
* **Türkçe Meal & Mixed Bold Standardı:**
  - *Ters Orantılı Punto:* Ultra kısa meallerde **66pt**, kısa meallerde **58pt**, orta meallerde **50pt - 44pt**, uzun meallerde **38pt**.
  - *Mixed Bold Tipografi (`wrap_mixed_tokens`):* Vurgulanan kelimeler Ibarra Real Nova Bold (700 weight, `#111827`) ile; diğer kısımlar Regular (400 weight, `#1C1917`) ile çizilir.
* **Akıllı Noktalama & Tırnak Regexi:** `noktalama_regex = re.compile(r'^([,\.;:!?\)’”"]+)(.*)$')` kuralı sayesinde tek/çift tırnaklar ve noktalama işaretleri önceki kelimeye yapışık kalır; satır başlarında sarkan noktalama veya ayrık tırnak hatası oluşmaz.

---

### 3. Görsel Kart Motoru Standartları (V16 Şablon Mimarisi)

Tüm tekil görsel post üretimi `src/uretim/kart.py` motoru üzerinden gerçekleştirilir. Hem 1080x1350 (4:5 Feed) hem de 1080x1920 (9:16 Story / Durum) tam desteklenir. Otomasyon her görsel içerikte **hem 4:5 hem de 9:16** dosyalarını aynı anda üretir (`gorsel_yollari = [p_4_5, p_9_16]`).

### A. Tipografi Standardizasyonu ve Başlık Tutarlılığı
- **Kart Başlık Rozeti (Header Rozet):** Tüm 4 kart türünde (`hadis`, `dua`, `kelime`, `ayet`) kesin olarak **Baskerville Bold 42pt ALL CAPS** standartlaştırılmıştır. (Hadis: `#C02128` Logo Kırmızısı; Ayet: `#1B4332` İslam Yeşili; Dua: Ruh haline özel zümrüt/safir/amber; Kelime: `#1E3A8A` Gece Mavisi).
- **Header Künyesi (Simetrik 3'lü Blok):**
  - *Sol:* 68x68 px yuvarlatılmış köşeli kurumsal Ezan Plus kırmızı logosu.
  - *Orta:* Baskerville Bold 42pt ALL CAPS rozet (70px yükseklik, beyaz yazı, tam ortalanmış).
  - *Sağ:* Sağa yaslı "Ezan Plus" (39pt Lora) ve kategori künyesi (13pt Manrope, örn. "SAHİH HADİS-İ ŞERİF REHBERİ", "KUR'AN-I KERİM TİLAVETİ").
  - *Alt:* Merkezinde altın nokta bulunan zarif ayraç çizgisi.
- **Video Başlık Tutarlılığı (Hook Standardı):** V12 video motorunda video hook başlığı **Lora 44pt/55pt (Serif)** olarak tırnak işaretleriyle (`“ ... ”`) sabitlenmiştir. Eski prototiplerdeki Manrope Sans-serif başlıklar tamamen terk edilmiştir.

### B. V16 Sahih Hadis Kartı (`hadis_karti_ciz`)
1. **Dinamik Serlevha Kutusu (Sıcak Parşömen Taç):**
   - Üst taç: Açık, sıcak fildişi/parşömen (`#F5EFE3`) zemin, 1px zarif ayraç (`#E2D7C3`) ve ortasında altın süsleme (`#C29B38`). "Resûlullah sallallahu aleyhi ve sellem şöyle buyurdu:" metni bordo (`#8B1D24`) Lora Bold.
   - Ölçüler: `box_w = 888px`, `text_max_w = 844px`.
   - Heybetli Arapça Hat: Metin uzunluğuna göre ters orantılı dinamik autofit: Kısa hadislerde **88pt - 114pt** heybetli hat; orta hadislerde **70pt - 86pt**; uzun hadislerde **44pt - 56pt**. Tam harekeli (`delete_harakat: False`).
   - Safe Area Kilidi: Okunuş alt sınırı dinamik ölçülerek `pad_ic_alt = 28-38px` ile kutu altına yapışma engellenir.
2. **Türkçe Hadis Meali (Hero Element & Ters Orantılı Punto):**
   - Kısa hadislerde meal **60pt - 66pt (9:16)** / **56pt - 62pt (4:5)** asil puntoya çıkar; orta hadislerde **48pt - 54pt**, uzun hadislerde **41pt - 42pt**.
   - **Mixed Bold Tipografi (`wrap_mixed_tokens`):** `**bold**` kelimeler Ibarra Real Nova Bold (700 weight, `#111827`) ile, diğer kısımlar Regular (400 weight, `#1C1917`) ile çizilir.
   - **Sıfır Halüsinasyon:** Gemini AI mealin tek bir harfini dahi değiştiremez; `re.sub` metin kontrolüyle sadece vurucu 2-5 kelimelik öğüt bold yapılır.
3. **Dikey Flex Dengeleme:** Kalan serbest boşluk kutu üstü (`%16`), kutu-meal arası (`%48`) ve meal-öğüt arası (`%52`) olarak paylaştırılarak alt tarafta ölü kanyon oluşması önlenir.
4. **Muteber Kaynak Rozeti ve Günün Nebevî Öğüdü:** Taban kutusunda kompakt tefekkür notu ve CTA barı yer alır.

### C. V16 Günün Duası Kartı (`dua_karti_ciz`)
- 8 farklı manevi ruh haline (iç sıkıntısı, kaygı, şükür, şifa, rızık, öfke, tevekkül, tevbe) göre dinamik renk paleti ve fazilet kutusu (`src/dua_db.py`).
- Arapça dua metninde kısa metinlerde **88pt - 114pt (9:16)** / **70pt - 98pt (4:5)** dinamik autofit.
- Türkçe anlamda kısa dualarda **60pt - 66pt (9:16)** / **54pt - 60pt (4:5)** heybetli punto.
- Mixed bold vurgusu ve fazilet/öğüt kutusu (`#111827` koyu kontrast).

### D. V17 Kur'an Sözlüğü & İslamî Kavram Kartı (`kelime_karti_ciz`)
- **Yalınlık & Editoryal Duruş:** Ağır kutular ve çerçeveler terk edilmiş; nefes alan ferah, asil bir editoryal sayfa hissi benimsenmiştir.
- **Renk Standartları:** Ezan Plus Soft Kırmızı zemin (`#AA2228` merkez ➔ `#7E1016` dış vignette), Saf Beyaz (`#FFFFFF`) hero başlık, İpeksi Beyaz (`#FFF8EE`) hat, Şampanya Altın (`#FDE6BA`) rozet, ayraç ve alıntı detayları.
- **Tipografi Hiyerarşisi:** 
  * 172pt (9:16) / 130pt (4:5) Saf Beyaz Lora Bold Türkçe kavram.
  * **Çoklu Satır Desteği & Minimum Taban:** Uzun veya birleşik kavramlarda (*Sıla-i Rahim*, *Emr-i bi'l-Ma'rûf*) fontu küçültmek yerine doğal alt satıra iner (`kelime_basligi_satirla`). Boyut hiçbir durumda **154pt (9:16) / 118pt (4:5)** Sekînet standardının altına düşürülemez.
  * 180pt (9:16) / 142pt (4:5) Amiri Bold Arapça hat.
  * Lügat anlamı arkasında zarif saten altın filigran tırnak işareti (`“`).
- **Safe Area Standardı:** 
  * Türkçe kelime alt tabanından Arapça hattın en üst noktasına: `68px` (9:16) / `46px` (4:5) net görsel mesafe.
  * Arapça kasralardan okunuş/kök satırına: `58px` (9:16) / `42px` (4:5) net emniyet mesafesi (sıfır çakışma).
- **Taban CTA:** Alt kısımda logo, "Ezan Plus • Ücretsiz İndirin" ve vektörel App Store & Google Play Store indirme barı.

### E. V16 Ayet-i Kerime Görsel Kartı (`ayet_karti_ciz`)
- Video dışındaki tekil görsel paylaşımlar için V16 standartlarına eşitlenmiş Mushaf kartı.
- `#1B4332` İslam Yeşili Baskerville Bold 42pt rozet, sıcak parşömen taç ("Allah Teâlâ şöyle buyuruyor:"), Uthmani hat, mixed bold meal ve hikmet notu.
- Ultra kısa ayetlerde **66pt (9:16)** / **62pt (4:5)** meal ve **114pt (9:16)** / **98pt (4:5)** Uthmani hat ölçeklendirmesi.

---

## 4. Çoklu Platform Yayın Protokolleri (`src/platformlar/`)

Tek bir onay ile tüm büyük sosyal medya kanallarına eş zamanlı ve formata duyarlı yayın yapılır:

```
                  ┌───────────────► 1. Instagram Reels / Post (Video: 9:16 | Görsel: 4:5)
                  ├───────────────► 2. Instagram Story (Dedicated 1080x1920 Tam Ekran)
[Ezan Plus Motoru]├───────────────► 3. Threads (@ezanplusapp Zincir Gönderi + 4:5 Görsel)
                  ├───────────────► 4. Facebook Sayfası (Ezan Plus + 4:5 Görsel)
                  ├───────────────► 5. YouTube Shorts (Ezan Plus Kanalı + 9:16 Video)
                  └───────────────► 6. TikTok (@ezanplusapp - Direct Post)
```

1. **Format Duyarlı Dağıtım (`src/telegram/yonetici.py`):**
   - Görsel paylaşımlarda (`gorsel_yollari = [p_4_5, p_9_16]`), Instagram Feed, Threads ve Facebook'a kareye yakın mükemmel akış formatı olan **4:5 (`gorsel_yollari[0]`)** gönderilir.
   - Instagram Story paylaşımında kırpılma olmadan kusursuz görünmesi için doğrudan **9:16 dikey kart (`gorsel_yollari[1]`)** yüklenir.
2. **Instagram Reels & Story (`meta.py`):** Meta Graph API v22.0 üzerinden `RUPLOAD_URL` ile iki adımlı Reels ve Story yayın protokolü.
3. **Threads Zincir Gönderi (`threads.py`):** 500 karakter sınırı `metni_parcala()` algoritması ile aşılır; 450 karakterlik mantıklı parçalar halinde ana post altına `(1/3)`, `(2/3)` zincirleme eklenir.
4. **Facebook Sayfası (`meta.py`):** `FACEBOOK_PAGE_ACCESS_TOKEN` ile süresiz token üzerinden zengin metin ve görselle paylaşım.
5. **YouTube Shorts (`youtube.py`):** Google YouTube Data API v3 OAuth 2.0 ile dikey video (#Shorts).
6. **TikTok (`tiktok.py`):** TikTok Content Posting API v2 ile video paylaşımı.

---

## 5. Günlük 6 Slot Yayın Takvimi, Bulut & Otomasyon Mimarisi

Türkiye sosyal medya etkileşim zirveleri ve manevi vakitler dikkate alınarak **günde 6 defa** tam otomatik üretim ve yayın döngüsü kurgulanmıştır:

| Slot | TSİ (UTC+3) | UTC Saat | İçerik Türü | Medya Formatı | Açıklama |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | **11:30** | 08:30 | **Kur'an Tilaveti** | 1080x1920 Reels | Öğle öncesi manevi tefekkür tilaveti |
| **2** | **13:45** | 10:45 | **Sahih Hadis-i Şerif** | 4:5 Feed + 9:16 Story | Günün Nebevî Öğüdü infografik kartı |
| **3** | **16:30** | 13:30 | **Kur'an Tilaveti** | 1080x1920 Reels | İkindi sonrası Kur'an tilaveti |
| **4** | **18:45** | 15:45 | **Günün Duası** | 4:5 Feed + 9:16 Story | Akşam vakti manevi niyaz ve münacat |
| **5** | **20:30** | 17:30 | **Kur'an Tilaveti** | 1080x1920 Reels | Yatsı vakti tefekkür tilaveti |
| **6** | **22:00** | 19:00 | **İslamî Kavram / Kelime** | 4:5 Feed + 9:16 Story | Gece tefekkürü, Kur'an kavramı |

```
[Cloudflare Edge Cron] (11:30, 13:45, 16:30, 18:45, 20:30, 22:00 TSİ)
       │ (0 ms Gecikme, Global Dağıtık Ağ)
       ▼
[GitHub Actions Webhook] (repository_dispatch: gunluk_reels / hadis / dua / kelime)
       │
[Ubuntu Bulut Runner]
       ├─► 1. İlgili DB'den (Kur'an, Hadis, Dua, Kelime) tescilli metni çek
       ├─► 2. Medyayı render et (Reels için MP4 video, Kartlar için 4:5 + 9:16 PNG)
       ├─► 3. Telegram onay grubuna medyayı ve "Onayla / İptal" butonlarını gönder
       ├─► 4. (45 Dakika Dinleme) Doğukan onayladığında 6 platforma yayınla!
       └─► 5. Yayın geçmişini ve sayaçları git push ile depoya kaydet
```

### A. Cloudflare Worker Zamanlayıcı (`worker/`)
* **Canlı Servis:** `https://ezan-plus-tetikleyici.ezanplus.workers.dev`
* **Zamanlayıcı:** `worker/wrangler.toml` dosyasında 6 adet cron tanımlıdır (`30 8 * * *`, `45 10 * * *`, `30 13 * * *`, `45 15 * * *`, `30 17 * * *`, `0 19 * * *`).
* **Akıllı Dispatcher:** Worker, tetiklenme saatine göre `event_type` belirler (`gunluk_reels`, `gunluk_hadis`, `gunluk_dua`, `gunluk_kelime`).
* **Esnek Manuel Tetikleme Endpoint'i:**
  👉 `https://ezan-plus-tetikleyici.ezanplus.workers.dev/tetikle?tur=reels` (veya `hadis`, `dua`, `kelime`)
  Query parametreleri: `tur`, `tema`, `auto=true` (otomatik yayın).

### B. GitHub Actions Bulut İş Akışı (`.github/workflows/gunluk_reels.yml`)
* 6 zamanlanmış slotu doğrudan dinler ve Worker'dan gelen webhook'ları yakalar.
* `workflow_dispatch` üzerinden GitHub UI'dan tek tıkla `tur` (reels, hadis, dua, kelime, ayet) seçilerek tetiklenebilir.
* Üretim tamamlandıktan sonra yayın geçmişi (`data/yayin_gecmisi.json`, `data/dualar.json`, `data/kelimeler.json`) otomatik olarak depoya `git push` yapılır.

---

## 6. Telegram İki Yönlü Komut & Yönetim Sistemi (`src/telegram/`)

Telegram botu sadece pasif bir onay aracı değil, iki yönlü interaktif bir yönetim terminalidir.

### A. Kayıtlı Bot Menüsü Komutları (`setMyCommands`)
Bot başlatıldığında Telegram arayüzündeki `/` menüsüne aşağıdaki komutlar otomatik olarak kaydedilir (`komutlari_kaydet`):
* `/ayet` — Yeni Kur'an tilaveti veya ayet kartı taslağı oluşturur.
* `/hadis` — Riyâzü's-Sâlihîn külliyatından yeni bir sahih hadis kartı üretir.
* `/dua` — 8 farklı manevi kategoriden günün duası kartını üretir.
* `/kelime` — Kur'an'dan önemli bir İslami kavram / kelime kartı üretir.
* `/durum` — Veritabanı ve yayın istatistiklerini gösterir.
* `/yardim` — Tüm komutları ve kullanım detaylarını listeler.

### B. İleri Seviye Yayın ve Yönetim Komutları
* `/yayinla <PAYLASIM_ID>` — Beklemede olan bir taslağı tüm platformlara anında yayınlar.
* `/kaldir <PAYLASIM_ID>` — Yayınlanmış olan bir içeriği Meta (Instagram/Facebook), Threads ve YouTube'dan anında siler ve veritabanı/yayın geçmişinden temizler.
* `/iptal <PAYLASIM_ID>` — İlgili taslağı yayından kaldırır ve iptal eder.

### C. Kur'an Tilaveti Otomatik Yayın & Yayından Kaldırma Güvencesi
* **Otomatik Yayınlama:** Kur'an tilavetleri (11:30, 16:30, 20:30 TSİ) render tamamlandığı anda onay beklemeden doğrudan tüm kanallara (Instagram Reels & Story, Threads, Facebook, YouTube Shorts) yayınlanır.
* **Telegram Yayın Detay Kartı (`yayin_detay_karti_gonder`):** Yayınlanan video, platform yayın başarı raporu ve izleme linkleriyle birlikte Telegram grubuna iletilir.
* **"🗑️ Yayından Kaldır" Butonu:** Telegram'a iletilen yayın raporunun altında `[ 🗑️ Yayından Kaldır ]` butonu yer alır. Olası bir hata durumunda tek tıkla içerik tüm platformlardan API aracılığıyla silinir.
* **Görsel Kartlar:** Hadis, Dua ve Kelime kartları ise önceden "✅ Onayla / ❌ İptal Et" butonlarıyla onaya sunulur; onaylandıklarında butonları otomatik olarak "🗑️ Yayından Kaldır"a dönüşür.

### D. Dinleme & Yanıt Mimarisi
* **Tek Sefer Dinleme (`dinle_ve_bekle`):** Bulut runner'ında onay butonlarını ve yayın sonrası "Yayından Kaldır" butonlarını dinler.
* **Sürekli Dinleme Daemon (`surekli_dinle`):** Yerel veya sunucu ortamında sürekli çalışarak gelen her komuta ve buton tıklamasına 2 saniyelik yoklama aralığıyla kesintisiz yanıt verir.

---

## 7. Yayın Öncesi Kalite Kapısı & Kendi Kendini Onaran (Self-Healing) Motor (`src/denetleyici.py`)

Ezan Plus yayın ekosisteminde **"sıfır hata"**, **"sıfır mizanpaj çakışması"** ve **"sıfır sahte/yapay içerik"** anayasal zorunluluktur. Bu amaçla medya render edildikten sonra ve herhangi bir platforma veya Telegram onayına sunulmadan önce iki aşamalı bir denetim ve otomatik onarım döngüsü devreye girer:

```
[İçerik Üretimi (Reels / Kart)] 
              │
              ▼
    [1. Kalite Denetimi] ──► GEÇERLİ ──────────────────────┐
              │                                            │
           HATALI                                          ▼
              ▼                                   [Onaya Sun / Yayınla]
    [otomatik_onar(id)]                                    ▲
      • Yasaklı Bot İfadelerini Temizle                    │
      • Tescilli DB (Kur'an/Hadis) ile Eşitle              │
      • Mizanpaj Çakışmasında 76pt ile Yeniden Render Et    │
      • Bozuk/Eksik 4:5 ve 9:16 Şablonları Yeniden Çiz     │
              │                                            │
              ▼                                            │
    [2. Doğrulama Geçişi] ──► ONARILDI ────────────────────┘
              │
          BAŞARISIZ
              ▼
   [Yayını Durdur + DB İptal + Telegram'a Kritik Rapor]
```

### A. 4 Katmanlı Kalite Kapısı (`denetle_paylasim`)
1. **Medya Boyut ve Çözünürlük Doğrulaması (`denetle_gorsel_dosyalari`, `denetle_video_dosyasi`):**
   - Video: Kesin olarak $1080 \times 1920$ px, MP4 container, geçerli süre ($> 1.0$ sn) ve ses akışı varlığı.
   - Görseller: Hem 4:5 Feed ($1080 \times 1350$ px) hem de 9:16 Story ($1080 \times 1920$ px) dosyalarının fiziksel olarak üretilmiş ve sağlam olduğu doğrulanır.
2. **KATI KURAL — %100 Tescilli Metin & Sıfır Halüsinasyon (`denetle_tescilli_kaynak`):**
   - Kur'an âyetleri yerel `kuran.db` tescilli Elmalılı veya Diyanet meali ile harfi harfine karşılaştırılır.
   - Hadis-i şerifler yerel `hadisler.db` Riyâzü's-Sâlihîn metni ile birebir doğrulanır. Uyuşmazlık durumunda alarm verilir.
3. **KATI KURAL — Yasaklı Bot ve Yapay İfade Taraması (`YASAKLI_IFADELER`):**
   - Açıklama (caption), başlık ve tefekkür metinlerinde `"bot"`, `"yapay zeka"`, `"otomasyon"`, `"ai üretimi"`, `"chatgpt"`, `"midjourney"` kelimeleri taranır. Tek bir eşleşme dahi içeriğin yayınına engeldir.
   - Açıklama metninde `#ezanplus` ve manevi etiketlerin varlığı şart koşulur.
4. **Reels Dikey Mizanpaj & Çakışma Güvenliği (`denetle_reels_mizanpaj`):**
   - Tilavet bloğunun (Arapça + Türkçe Latin okunuş) alt sınırı ile tefekkür/meal başlangıcı arasındaki net dikey serbest alan ölçülür (`serbest_alan_px = tef_y - tr_bitis_y`).
   - `serbest_alan_px < 10px` ise metinlerin birbirine binme/çakışma riski nedeniyle mizanpaj doğrudan geçersiz sayılır.

### B. Otomatik Kendi Kendini Onarma Mekanizması (`otomatik_onar`)
Sistem bir hata bulduğunda yayını derhal çöpe atmak yerine otonom düzeltme adımlarını uygular:
1. **Caption & Etiket Telafisi:** Yasaklı kelimeleri sessizce ayıklar; eksik açıklama varsa tescilli metinden zarif edebi formatta oluşturur ve `#ezanplus` etiketlerini ekler.
2. **Külliyat Senkronizasyonu:** Gemini'nin meale yaptığı herhangi bir sözcük değişikliğini tescilli `kuran.db` / `hadisler.db` kayıtlarıyla ezerek %100 orijinal metne döndürür.
3. **Mizanpaj Taşma Çözümü:** Dikey çakışma durumunda veya metin eşitlendiğinde Arapça font tavanını 76pt güvenlik sınırına çekerek videoyu arka planda sıfırdan yeniden üretir.
4. **Şablon Re-render:** Eksik veya bozuk kartları doğru punto ve oranlarla (hem 4:5 hem 9:16) yeniden çizer.
5. **İkinci Doğrulama:** Yapılan onarımlar sonrası post tekrar `denetle_paylasim` kapısından geçirilir. Başarılı ise yayın kesintisiz devam eder; onarılamazsa DB'de `iptal_edildi` olarak işaretlenir ve Telegram'a rapor iletilir.

---

## 8. Dizin ve Modül Yapısı

```
EzanPlusBot/
├── .github/
│   └── workflows/
│       └── gunluk_reels.yml       # 6 slotlu GitHub Actions üretim & yayın workflow'u
├── worker/
│   ├── wrangler.toml              # 6 zamanlı Cloudflare Worker Cron Trigger ayarları
│   └── index.js                   # Akıllı GitHub API webhook tetikleyicisi
├── assets/
│   ├── fonts/                     # Amiri, Lora, Manrope, Ibarra, Baskerville fontları
│   ├── audio/                     # İndirilen ve yedek ses dosyaları
│   └── icons/                     # Marka logoları ve vektörler
├── web/
│   ├── index.html, terms.html     # Meta / TikTok doğrulama ve yasal sayfalar
├── data/
│   ├── kuran/
│   │   └── kuran.db               # Tescilli Kur'an DB (6.236 ayet, Uthmani hat, Elmalılı + Diyanet meal, FTS5)
│   ├── hadisler/
│   │   └── hadisler.db            # Tescilli Riyâzü's-Sâlihîn DB (1.900 sahih hadis)
│   ├── dualar.json                # 20 seçkin Kur'an ve Nebevî dua koleksiyonu
│   ├── kelimeler.json             # 15 temel Kur'anî kavram ve kelime koleksiyonu
│   ├── ezanplus.db                # SQLite içerik ve yayın kayıtları
│   ├── yayin_gecmisi.json         # Paylaşım ve tekrarı önleme kayıtları
│   ├── zamanlar/                  # 114 sûrenin (6.236 âyet) resmi kelime zaman damgaları (sure_1..114.json)
│   ├── cikti/                     # Render edilen MP4 ve PNG çıktıları
│   └── onbellek/                  # İndirilen tilavet sesleri
├── scripts/
│   ├── build_kuran_db.py          # Kur'an veritabanı inşa aracı
│   ├── download_all_timings.py    # 114 sûre resmi kelime zaman damgaları indirici
│   └── tiktok_yetki.py            # TikTok yetkilendirme aracı
├── tests/
│   ├── test_kuran_db.py           # Kur'an DB ve arama testleri
│   ├── test_denetleyici.py        # Yayın öncesi kalite kapısı & otomatik onarım testleri
│   ├── test_komutlar_ve_otomasyon.py # Otomasyon, komutlar ve DB birim testleri
│   └── prototipler/               # Geliştirme sürecindeki test ve deneme scriptleri
├── src/                           # Çekirdek Python Paketi
│   ├── __init__.py
│   ├── ayar.py                    # Yapılandırma, yollar, renkler ve sabitler
│   ├── db.py                      # SQLite veritabanı yönetim modülü
│   ├── kuran_db.py                # Tescilli Kur'an DB sorgulama ve seçim motoru
│   ├── hadis_db.py                # Tescilli Sahih Hadis DB yönetim motoru
│   ├── dua_db.py                  # Tescilli Dualar yönetim motoru
│   ├── kelime_db.py               # Tescilli İslamî Kelimeler yönetim motoru
│   ├── denetleyici.py             # Yayın öncesi kalite kontrol & otomatik onarım motoru
│   ├── otomasyon.py               # Günlük 6 slot orkestrasyon motoru & CLI
│   │
│   ├── uretim/                    # İçerik ve Medya Üretim Katmanı
│   │   ├── __init__.py
│   │   ├── ai.py                  # Gemini AI ayet, meal, tefekkür promptları
│   │   ├── ses.py                 # EveryAyah ses indirme & kelime senkronu
│   │   ├── kart.py                # V16 Infografik kart motoru (Hadis, Dua, Kelime, Ayet)
│   │   └── video.py               # 1080x1920 V12 Reels karaoke render motoru
│   │
│   ├── platformlar/               # Sosyal Medya API Dağıtım Katmanı
│   │   ├── __init__.py
│   │   ├── meta.py                # Instagram Reels, Story (9:16) & Facebook Page (4:5)
│   │   ├── threads.py             # Threads akıllı zincir gönderileri
│   │   ├── youtube.py             # YouTube Shorts API yükleyici
│   │   └── tiktok.py              # TikTok Direct Post API
│   │
│   └── telegram/                  # Telegram Onay & Yönetim Katmanı
│       ├── __init__.py
│       ├── bot.py                 # İki yönlü komut menüsü, önizleme kartı, getUpdates
│       └── yonetici.py            # Çoklu platform ve format duyarlı yayın dağıtımı
│
├── GEMINI.md                      # Bu anayasa belgesi
├── config.yaml                    # Proje ve şablon ayarları
├── requirements.txt               # Python bağımlılıkları
└── .env                           # API anahtarları ve token'lar (asla git'e girmez)
```

---

## 9. Gelecek Geliştirme Yol Haritası (Sıradaki Adımlar)

1. **Farklı İçerik Türlerinin Genişletilmesi:**
   * ✅ **Hadis-i Şerif Serisi:** Riyâzü's-Sâlihîn'den 1.900 sahih hadis DB entegrasyonu tamamlandı.
   * ✅ **Günün Duası:** 8 manevi ruh haline göre dua DB entegrasyonu tamamlandı.
   * ✅ **Günün Kelimesi / Kavramı:** Kur'an kavramları DB entegrasyonu tamamlandı.
   * **Günün Zikri & Esmaü'l Hüsna:** Anlamı, ebced değeri ve faziletiyle 99 Esma serisi eklenebilir.
2. **Telegram İki Yönlü Komut Menüsü:**
   * ✅ Telegram arayüzüne `/ayet`, `/hadis`, `/dua`, `/kelime`, `/durum`, `/yardim` komut menüsü kaydedildi.
   * ✅ Arka planda `/yayinla <id>` ve `/iptal <id>` komut desteği tamamlandı.
3. **Yayın Öncesi Kalite & Otomatik Onarım Güvencesi:**
   * ✅ Mizanpaj çakışması, boyut hatası, yasaklı bot ifadesi ve eksik etiket taraması tamamlandı.
   * ✅ Otomatik onarım döngüsü (`otomatik_onar`) ile hataları yayından önce düzelten self-healing mimarisi tamamlandı.
4. **TikTok Uygulama İncelemesi (App Review):**
   * TikTok Developer Portal'daki inceleme tamamlandığında tek tıkla token alınacak ve TikTok da tam otomatik yayın zincirine bağlanacaktır.
