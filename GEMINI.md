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
* **Kelime Zaman Damgası Normalizasyonu & Enterpolasyon (`kelime_zamanlarini_hizala` & `ayet_kelime_zamanlari_getir`):**
  - **İlk Kelime Başlangıç Garantisi (`segments[0][1]` Tabanı):** QuranCDN sûre zaman dosyalarında tanımlanan `timestamp_from`, sûre geneli için kaba bir imleçtir ve âyetin ilk kelimesinin gerçek telaffuz başlangıcından (`segments[0][1]`) 1.7 saniyeye kadar sapabilir (örn. Sebe' 13'te 1.675 sn fark). `ayet_kelime_zamanlari_getir` motoru, `segments` mevcut olduğunda âyetin başlangıç tabanını (`ayah_start`) istisnasız ilk segmentin başlangıcına (`segments[0][1]`) kilitler. Bu sayede ilk kelimelerin 0 saniyeye ezilmesi veya zamanlamanın sesin 1.5 - 2 saniye önden gitmesi mimari olarak tamamen engellenmiştir.
  - **Segment Enterpolasyonu:** QuranCDN segment sayıları ile Kur'an metnindeki kelime sayıları farklılık gösterse dahi (örn. Nisâ 5'te hafızın nefes tekrarı nedeniyle 40 segmente karşılık 39 kelime) zaman damgaları kümülatif zaman enterpolasyonu ile 1:1 kelime sayısına eşitlenir; kelime sapması, sayacın erken durması veya indisin donması önlenir.
* **Arapça ve Latin Okunuş 1:1 Eşleme Standardı (`turkce_okunus_hizala` & Gemini AI):**
  - Gemini AI'nin ürettiği `latin_kelimeler` dizisindeki eleman sayısı Arapça kelime sayısıyla (`len(ar_kelimeler)`) **istisnasız 1:1 eşit** olmak zorundadır.
  - **Şemsî/Kamerî Harf ve Hece Koruma:** `es-sufehâe`, `er-rahmân` veya `el-kitâb` gibi birleşik okunuşlarda "es" hecesinin bir durak (pause/"es vermek") zannedilip ayrılması kesinlikle yasaktır (`harfi_tarifler = {"es", "el", "al", "er", ...}`). Dizi boyutları eşit olduğunda (`len(tr_list) == len(ar_list)`) 1:1 dizilim doğrudan korunur.
  - İki dilli dizilim ayrık bağlaçlarda (`ve`, `fe`, `bi`, `li`) ve birleşik lafızlarda (`entes-semîul`) Arapça karşılığına göre dinamik olarak dengelenir. Sıfır indis kayması ve sıfır boş kelime güvencesiyle son kelime tilavetin bittiği ana kadar tam senkron kırmızı kalır.
* **Çift Katmanlı Karaoke & Kontrast Hiyerarşisi (V12.3 Mimarisi):**
  - **Simetrik 3 Durumlu Renk Mimarisi (Arapça & Latin Bütünlüğü):**
    * *1. Henüz Okunmamış (Bekleyen) Kelimeler:* Zarif Açık Arduvaz Grisi (`#94A3B8`). Arka planda sırasını bekler; ekranda yeşil/koyu renk karmaşası oluşturmaz, aktif kelimenin öne çıkması için zemin hazırlar.
    * *2. Şu An Okunan (Aktif) Kelime:* Amiri 700 Bold / Manrope 800 Bold + Canlı Kırmızı (`#C0392B`). Arapça'da sağdan sola, Latin okunuşta soldan sağa akan dinamik kırmızı dolum (loading) efekti. Çevresi silik tonda olduğu için ekranda anında spot ışığı gibi parlar.
    * *3. Okunmuş (Biten) Kelimeler:* Asil Antik Koyu Mürekkep (`#182230`). Okunup tamamlanan kelimeler tokluk kazanarak kalıcı bir sükunetle eşlik eder.
  - **Latin Okunuş Ferah Tipografi Standardı:** Latin okunuş puntosu `pt_okunus = max(32, int(pt_ar * 0.44))` formülü ile heybetli, okunaklı ve Arapça hatla dengeli boyuta çekilmiştir. Satır genişliğini denetleyen otomatik auto-fit mekanizması sayesinde uzun kelimelerde satırdan taşma veya çakışma %100 engellenir.
  - Okunan kelimeye odaklanılırken meal ve tefekkür bölümü kartın alt kısmında huzurlu bir şekilde eşlik eder.
* **Otomatik Zaman Tespiti & Sıfır Gecikme Garantisi (`reels_videosu_uret`):**
  - Fonksiyon çağrısında `kelime_zamanlari` parametresi aktarılmasa dahi `ses_yolu` dosya adından (`002127.mp3` -> Sûre 2, Âyet 127) veya `sure_ayet` başlığından ("Bakara Sûresi, 127. Âyet") sûre ve âyet otomatik çözümlenir; `ayet_kelime_zamanlari_getir` ile yerel tescilli zaman damgaları çekilir. Mekanik sentetik dilimlemeye düşüş mimari olarak engellenmiştir.
  - **1-Tabanlı İndeks Otomatik Normalizasyonu:** Dışarıdan 1-tabanlı gelen segment dizileri otomatik tespit edilerek 0-tabanlıya dönüştürülür.
  - **Yayın Standardı İnce Karaoke Avansı (`t_eval = t_sec + 0.05`):** Şeyh Mişari'nin konsonant ve ses vuruşlarında kelimenin tam hece anında parlaması ve insan algı refleksini karşılamak için 50 ms (~1.5 kare) ince görsel avans uygulanır; sıfır gecikme hissi ve mükemmel vuruş yakalanır.

### D. Uzun Ayet Çoklu Sayfa Geçiş Motoru & Dinamik Flex Mizanpaj
* **Otomatik Tetikleme:** 14 kelimeye kadar olan âyetler (Bakara 127 gibi) tek sayfada ferahça sunulur. 15 kelime ve üzerini aştığında metni sıkıştırmak yerine otomatik olarak çoklu sayfaya bölünür (`sayfa_sayisi = math.ceil(toplam_kelime / 14)`).
* **Akıllı Secavend & Nefes Odaklı Sayfa Bölücü (`akilli_sayfa_araliklari`):** Metni körlemesine matematiksel ortadan (örn. 14 / 2 = 7) bölmek kesinlikle yasaktır. Kur'an secavend durak işaretleri (`ۚ ۖ ۗ ۘ ۙ ۛ ۜ`), hafızın ses dosyasındaki doğal nefes duraklama pencereleri (ses dalgası durak süresi) ve sayfa denge skoru birlikte ağırlıklandırılarak âyetin manevi ve tilavet ahengine göre en kusursuz durak noktasından bölünür.
* **Sayfa İndis Bütünlüğü (Arapça & Latin Eşzamanlı Dilimleme):** Çok sayfalı âyetlerde Arapça ve Latin dizileri sayfalara birebir aynı indeks aralığıyla (`ar_kelimeler[s:e]`, `tr_kelimeler[s:e]`) bölünür. Arapça bir kelimenin 1. sayfada, Türkçe okunuşunun ise 2. sayfada kalması (veya sesin görüntüden önce 2. sayfaya fırlaması) mimari olarak imkansızdır.
* **Akıllı Cümle & Meal Bölücü (`akilli_meal_parcala` / `_meal_parcala`):** 
  - Arapça sayfa oranına göre mealin karşılık gelen bölgesinde en mantıklı cümle bitişini arar.
  - Öncelik Hiyerarşisi: Cümle sonları (`.!?`) ➔ Güçlü ayraçlar (`:;—`) ➔ Virgül ve nefes yerleri (`,`).
  - **Bold Blok Koruma Standardı:** Asla `**bold**` vurgu bloklarının içinden (örn. `**Ey Rabbimiz, bizden kabul buyur**`) bölünemez; tırnak veya parantez bütünlüğü parçalanamaz.
  - **Sıfır Yıldız (`**`) Garantisi:** Kart ve video motorunda `parse_markdown_bold` katmanı yetim veya kapanmamış `**` / `*` işaretlerini ayıklar ve stili bold'a dönüştürür; ekranda çıplak markdown syntax'ı belirmesi %100 imkansızdır.
* **Dinamik Flex Mizanpaj:**
  - *Üste Dayalı Tilavet (`Y = 484`):* Arapça satır yüksekliği `96px` (66pt ferah font), Türkçe okunuş ile arasında `24px` nefes payı bırakılır. 4 satırlık metinlerde dahi çakışma ve taşma imkansızdır.
  - *Alta Dayalı Günün Hikmeti & Tefekkür (`Y = 1566 - tef_h - 16`):* `_tefekkur_yukseklik_hesapla` formülü ile hesaplanan tefekkür bloğu kartın alt sınırına dayalıdır. Çok sayfalı geçişlerde Sayfa 1 ve Sayfa 2'de milimetrik olarak aynı pikselde sabitlenir; geçişte sıfır ghosting (çift görüntü) ve sıfır titreme sağlanır.
  - *Orta Flex Alan (Meal & Ayraç):* Tilavet bitişi ile tefekkür başlangıcı arasındaki kalan serbest dikey boşluk hesaplanarak Türkçe meal ve altın ayraç dikeyde ortalanır (`pad_ust = int(serbest_bosluk * 0.42)`).
* **Sinematik Erime (Crossfade) & Zaman Odaklı Sayfa Seçimi:** Sayfa sonlarında hafızın nefes aralığında 0.45 saniyelik pürüzsüz `Image.blend` erimesi gerçekleşir.
  - *Zaman Odaklı Kilitleme:* Kare döngüsünde aktif sayfa (`active_p`), `aktif_idx` kelime sayacına göre değil; kesin olarak `gecisler` zaman pencerelerine göre (`t_sec < t_s` / `t_sec > t_e`) belirlenir. Bu sayede hafızın nefes duraklamalarında veya ses gecikmelerinde Sayfa 2'den tekrar Sayfa 1'e geri sıçrama (ghosting/snapback/freeze) tamamen engellenmiştir.
* **Kesintisiz Animasyon:** Ekolayzır ses dalgaları ve alt ilerleme çubuğu 30 FPS hızında kesintisiz akmaya devam eder.

### E. Dinamik Tipografi Ölçeklendirme Tavanları (V12.2 Mimarisi)
* **Arapça Hat Dinamik Tavanı (`pt_ar`):**
  - *Tek Satır Ultra-Kısa Âyetler (İhlâs 1, Kevser 1 vb.):* Kartın üst alanındaki ferahlığı heybetle doldurmak için **138pt** devasa hat kullanılır.
  - *Çok Satırlı Âyetler:* Mizanpaj sıkışmasını ve Türkçe okunuşla çakışmayı önlemek için katı tavan **114pt** ile sınırlandırılmıştır (`ar_len < 35` için 114pt; `< 55` için 96pt; `< 90` için 78pt; uzun metinlerde 66pt).
* **Türkçe Meal & Mixed Bold Standardı:**
  - *Ters Orantılı Punto:* Ultra kısa meallerde **66pt**, kısa meallerde **58pt**, orta meallerde **50pt - 44pt**, uzun meallerde **38pt**.
  - *Mixed Bold Tipografi (`wrap_mixed_tokens`):* Vurgulanan kelimeler Ibarra Real Nova Bold (700 weight, `#111827`) ile; diğer kısımlar Regular (400 weight, `#1C1917`) ile çizilir.
* **Akıllı Noktalama & Tırnak Regexi:** `noktalama_regex = re.compile(r'^([,\.;:!?\)’”"]+)(.*)$')` kuralı sayesinde tek/çift tırnaklar ve noktalama işaretleri önceki kelimeye yapışık kalır; satır başlarında sarkan noktalama veya ayrık tırnak hatası oluşmaz.

### F. Türkçe Hadis ve Dua Stüdyo Ses Motoru (Fish Audio S2.1 Mimarisi)
* **Motor & Modül:** `src/uretim/ses.py` (`turkce_tts_uret`, `turkce_fonetik_temizle`, `turkce_kelime_zamanlari_getir`).
* **Varsayılan Kurumsal Ses:** **Mazlum Kiper** (`a6d624c6b8de45d2b89eb0da9a691872`). Usta tiyatrocu ve efsanevi belgesel spikeri ses rengi; sentetik yapaylıktan tamamen arınmış, tok, vakur ve derin bir manevi otorite sunar.
* **Hız Standartı (`hiz = 0.9`):** Hadis ve dua metinlerinin vakarını, akıcılığını ve tefekkür derinliğini korumak için konuşma hızı `0.9x` olarak tescillenmiştir.
* **Akıllı Fonetik & Kısaltma Genişletme Standartları (`turkce_kisaltmalari_genislet` & `turkce_fonetik_temizle` & `dua_fonetik_ve_es_hazirla`):**
  - **Sıfır "Hetz" Garantisi & Kısaltma Genişletme:** `Hz.` veya `Hz` kısaltması spikerin İngilizce/mekanik olarak "hetz" veya "h-z" okumasını engellemek amacıyla istisnasız **"Hazreti"** olarak genişletilir (`Hz. Peygamber` ➔ `Hazreti Peygamber`, `Hz. Âişe` ➔ `Hazreti Âişe`).
  - **Hürmet ve Salavat Lafızları:**
    * `(s.a.v.)`, `s.a.v.`, `(sav)`, `(s.a.s.)` ➔ `sallallahu aleyhi vesellem`
    * `(r.a.)`, `r.a.`, `(ra)`, `(r.anh)` ➔ `radıyallahu anh` (ve ekli `radıyallahu anhâ` / `anhüm` / `anhüma`)
    * `(a.s.)`, `a.s.`, `(as)` ➔ `aleyhisselam`
    * `(c.c.)`, `c.c.`, `(cc)` ➔ `celle celaluhu`
    * `(k.v.)` ➔ `kerremallahu vecheh`, `(k.s.)` ➔ `kaddesallahu sırrah`, `(rh.a.)` ➔ `rahmetullahi aleyh`
    * `vb.` ➔ `ve benzeri`, `vs.` ➔ `ve saire`, `bkz.` ➔ `bakınız`
  - **Ses ve Altyazı 1:1 Bütünlüğü:** Kısaltmalar hem TTS sese hem de ekrandaki meal mizanpajına (`multipage.py`) aynı anda yansıtılır; seslendirilen ile ekrandaki kelime sayısı ve sırası 1:1 eşlenerek karaoke indis kayması ve metin uyuşmazlığı %100 önlenir.
  - **Şapkalı Harf Koruması:** `â`, `î`, `û` harfleri korunur; Fish Audio S2.1 modelinin uzun ünlüleri (`takvâ`, `hidâyet`, `ahlâk`) vakur ve asil şekilde uzatarak okuması sağlanır.
  - **Es ve Nefes Durakları:** Dualarda seslendirmenin kalbe dokunması için nida ve münacat öbeklerinden sonra otomatik virgül durakları eklenir (`dua_fonetik_ve_es_hazirla`).
  - Markdown kalın/italik işaretleri (`**`, `*`) temizlenir.
* **Kelime Kelime Senkron Saniye Zaman Damgaları (`/v1/tts/stream/with-timestamp`):**
  - Ses üretimi Fish Audio SSE akış API'si üzerinden gerçekleştirilir.
  - Üretilen MP3 ses dosyası ile eşzamanlı olarak `.json` formatında her kelimenin kesin başlangıç ve bitiş saniye zaman damgaları yerel diske kaydedilir (`data/sesler/hadis/{id}_{hash}.json` / `data/sesler/dua/{id}_{hash}.json`).
* **Metin Hash'li Kesin Önbellek Garantisi:**
  - Ses ve zaman dosyaları `metin_hash` özetini içerir (`{id}_{hash}.mp3`). Metin veya hız değiştiğinde ses %100 sıfırdan tescillenir; ses-metin uyumsuzluğu mimari olarak imkansızdır.
* **Sıfır Bozuk Glif Garantisi (`arapca_glif_temizle`):**
  - Amiri fontunda karşılığı bulunmayan tüm Latin noktalama işaretleri (`:`, `-`, `?`, tırnaklar) temizlenir veya resmi Arapça Unicode karşılıklarına (`،`, `؛`, `؟`) dönüştürülür; dikey dikdörtgen (tofu kutusu) oluşması %100 engellenmiştir.

### G. V20 Çok Sayfalı Hadis ve Dua Dinamik Video Motoru (`src/uretim/multipage.py`)
* **100% Video Formatı:** Hadis ve Dua içerikleri yalnızca V20 Çok Sayfalı Dinamik Video olarak üretilir; statik kart formatı terk edilmiştir.
* **1080x1920 (9:16) Tam Dikey 30 FPS MP4:** Instagram Reels, Story, YouTube Shorts ve TikTok için standart dikey format.
* **100% Bold Serif Meal Tipografisi:** Türkçe meal metninin tamamı istisnasız `IbarraRealNova 700 Bold` ağırlığında işlenir. Soldan sağa akıcı renk dolumu (`#C0392B` Hadis / `#B45309` Dua) ile spot ışığı gibi takip edilir.
* **Çok Sayfalı Sinematik Erime (0.45s Crossfade):** 14 kelimeyi aşan veya çok cümleli içeriklerde metinler otomatik olarak sayfalara bölünür. Sayfalar arasında 0.45 saniyelik `Image.blend` erimesi uygulanır; aktif sayfa seçimi zaman damgası pencerelerine kilitlidir.
* **1:1 Arapça Hat & Türkçe Bütünlüğü:** Videoda okunan Türkçe metnin Arapça karşılığı sayfa sayfa 1:1 eşlenir; Arapça hat eksik kalmaz.
* **Telifsiz Ulvi Ney Fon Müziği & Sıfır Gecikme Senkronizasyonu:**
  - *Sahih Hadis:* Solo Segâh Ney Taksim (`assets/audio/fon/ney_segah.mp3`, 2.9s güçlü melodi başlangıç ofseti).
  - *Günün Duası:* Solo Ferahfezâ Ney Taksim (`assets/audio/fon/ney_ferahfeza.mp3`, 2.6s güçlü melodi başlangıç ofseti).
  - Miksaj oranı `volume=0.48` (2x dolgun tını) seviyesinde olup, video başlar başlamaz `0.15s` hızlı atak ile ney nağmesi ve spiker sesi aynı anda başlar; kapanışta `1.2s fade-out` uygulanır.
* **Kur'an Tilaveti Meal Alanı Kırmızı Degrade Keten Bandı & Hero Meal Koruma Standardı:** Ayet videolarında Türkçe meal birincil okuma (hero) öğesidir; meal 3 veya daha fazla satıra uzadığında meal fontu küçültülmez, bunun yerine Arapça alanı ve dikey boşlukları (`MIN_VERTICAL_GAP`, `gap_ar_tr`) dinamik olarak daraltılarak (3 satırda tavan 92pt, 4+ satırda 80pt) meale ferah alan açılır. Kırmızı keten bandın katı bölgesi (`solid_top` .. `solid_bottom`), mealin kaç satır olduğuna (`meal_blok_h`) göre dinamik olarak büyüyüp küçülür; metin satırları istisnasız %100 katı kırmızı alanın içinde kalır ve degrade geçişine asla taşmaz. Bant ile tefekkür çizgisi arasına altın odak elması yerleştirilir.
* **Bağımsız Alt İlerleme Çubuğu:** $Y=1858$ koordinatında video boyunca kesintisiz akan ilerleme çubuğu.
* **Telegram Botu & Otomasyon Erişimi:**
  - `/hadis`: V20 dinamik hadis videosu üretir.
  - `/dua`: V20 dinamik dua videosu üretir.
  - `/ayet`: 9:16 Kur'an Tilaveti videosu üretir (kırmızı meal bantlı).
  - CLI: `python -m src.otomasyon hadis` / `python -m src.otomasyon dua` / `python -m src.otomasyon reels`.

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

### B. V20 Sahih Hadis Kartı (`hadis_karti_ciz`) — Sisli Adaçayı Zümrüdü Mimarisi
1. **Sabit Soft Pastel Zemin (Sisli Adaçayı Zümrüdü):**
   - Merkez `(34, 66, 52)` (`#224234`) ➔ Dış kenar `(18, 40, 32)` (`#122820`) organik radyal gradyan parşömen dokusu.
   - Keten zemin bandı, Cosine tül degrade ve altın odak elmasları.
2. **Taç Başlık Standardı:**
   - Sabit, vakur ve taşma yapmayan Nebevî taç başlık: **`“ Resûlullah (s.a.v.) Buyurdu ”`** (Lora Bold 34pt 9:16 / 28pt 4:5 + auto-fit güvencesi).
   - Sahabi râvisi taç başlığa eklenmez; ilmî usule uygun olarak alt kaynak bloğunda yer alır (`{KAYNAK} • RÂVİ: {RAVİ}`).
3. **Arapça Hat & Mixed Bold Tipografi:**
   - Kısa metinlerde 142pt (9:16) / 120pt (4:5) heybetli Uthmani hat ve Latin okunuş.
   - Hero Türkçe meal: Keten bandı içinde Ibarra Real Nova Mixed Bold tipografi (`#1B4D38` bold, `#1C1917` regular).
4. **Birebir Eşitlenmiş Alt Hiyerarşi & İndirin Butonu:**
   - 1. Satır: Tefekkür Notu (Lora Italic `#FFF5F2`).
   - 2. Satır: Kaynak ve Râvi (`#EADBC8` Manrope Bold All-caps).
   - 3. Satır: Beyaz Ezan Plus CTA Butonu ($Y_{nav1}=1770$ 9:16 / $1254$ 4:5, alt ilerleme çubuğu ile 16px net nefes payı).
   - Tefekkür ve Kaynak bloğu, Keten bandı altı ile CTA butonu arasında dikeyde dinamik ortalanır.

### C. V20 Günün Duası Kartı (`dua_karti_ciz`) — Selçuklu Petrol Zümrüdü Mimarisi
1. **Sabit Soft Pastel Zemin (Selçuklu Petrol Zümrüdü):**
   - Merkez `(14, 48, 50)` (`#0E3032`) ➔ Dış kenar `(6, 26, 28)` (`#061A1C`) organik radyal gradyan parşömen dokusu.
   - Keten zemin bandı, Cosine tül degrade ve narin dua eden eller filigranı.
2. **Taç Başlık Standardı:**
   - Dua başlığı veya künyesi: **`“ {dua_basligi} ”`** (Lora Bold 34pt 9:16 / 28pt 4:5 + auto-fit güvencesi).
3. **Arapça Hat & Mixed Bold Tipografi:**
   - Heybetli Uthmani hat ve Şampanya Altın Latin okunuş.
   - Hero Türkçe anlam: Keten bandı içinde Ibarra Real Nova Mixed Bold tipografi (`#0F4144` bold, `#1C1917` regular).
4. **Birebir Eşitlenmiş Alt Hiyerarşi (Sıfır Çift Kaynak Hatası):**
   - 1. Satır: Fazilet Notu (Lora Italic `#FFF5F2`, içinde kaynak tekrarı olmadan saf edebi not).
   - 2. Satır: Kaynak Künyesi (`#EADBC8` Manrope Bold All-caps).
   - 3. Satır: Beyaz Ezan Plus CTA Butonu ($Y_{nav1}=1770$ 9:16 / $1254$ 4:5).
   - Hadis kartı ile milimetrik aynı dikey hiza, öğe sırası ve nefes payı standardı.

### D. V17 Kur'an Sözlüğü & İslamî Kavram Kartı (`kelime_karti_ciz`)
- **Yalınlık & Editoryal Duruş:** Ağır kutular ve çerçeveler terk edilmiş; nefes alan ferah, asil bir editoryal sayfa hissi benimsenmiştir.
- **Renk Standartları:** Ezan Plus Soft Kırmızı zemin (`#AA2228` merkez ➔ `#7E1016` dış vignette), Saf Beyaz (`#FFFFFF`) hero başlık, İpeksi Beyaz (`#FFF8EE`) hat, Şampanya Altın (`#FDE6BA`) rozet, ayraç ve alıntı detayları.
- **Tipografi Hiyerarşisi & Akıllı Çoklu Satır Desteği:** 
  * Tek satırlı kavramlarda 172pt (9:16) / 130pt (4:5) Saf Beyaz Lora Bold Türkçe kavram.
  * 2 satırlı kavramlarda (*Sıla-i Rahim*, *Emr-i bi'l-Ma'rûf*) dikey sıkışmayı önlemek için otomatik **138pt (9:16) / 104pt (4:5)** puntoya ve **148pt (9:16) / 116pt (4:5)** Arapça hatta geçiş yapılır. 3 satırlı kavramlarda **118pt (9:16) / 88pt (4:5)** kullanılır.
  * Lügat anlamı arkasında zarif saten altın filigran tırnak işareti (`“`).
- **Kesin Safe Area & CTA Çarpışma Kilidi:** 
  * Türkçe kelime alt tabanından Arapça hattın en üst noktasına: `68px` (9:16) / `42-46px` (4:5) net görsel mesafe.
  * Arapça kasralardan okunuş/kök satırına: `56px` (9:16) / `38-42px` (4:5) net emniyet mesafesi.
  * **Ayet Referansı Güvenlik Kilidi:** Âyet referansı metni, CTA indirme butonu üzerinden en az `34px - 44px` güvenli pay bırakılarak akış içinde kilitlenir; alıntı metni ile referans arasında en az `22px - 30px` nefes payı garanti edilir. Uzun metinlerde otomatik auto-fit döngüsü devreye girerek font ve satır aralıklarını milimetrik ölçekler, butona çarpma imkansızdır.
- **Taban CTA:** Alt kısımda logo, "Ezan Plus • Ücretsiz İndirin" ve vektörel App Store & Google Play Store indirme barı.

### E. V16 Ayet-i Kerime Görsel Kartı (`ayet_karti_ciz`)
- Video dışındaki tekil görsel paylaşımlar için V16 standartlarına eşitlenmiş Mushaf kartı.
- **Dinamik Ink Clearance Standardı:** `MIN_VERTICAL_GAP = 28px` (9:16) / `24px` (4:5) ile çok satırlı âyetlerde sıfır hareke çakışması, yetim kelime önleme ve dengeli satır dağılımı.
- `#1B4332` İslam Yeşili Baskerville Bold 42pt rozet, sıcak parşömen taç ("Allah Teâlâ şöyle buyuruyor:"), Uthmani hat, mixed bold meal ve hikmet notu.
- Ultra kısa ayetlerde **66pt (9:16)** / **62pt (4:5)** meal ve **114pt (9:16)** / **98pt (4:5)** Uthmani hat ölçeklendirmesi.

---

## 4. Çoklu Platform Yayın Protokolleri (`src/platformlar/`)

Tek bir onay ile tüm büyük sosyal medya kanallarına eş zamanlı ve formata duyarlı yayın yapılır:

```
                  ┌───────────────► 1. Instagram Reels / Post (Video: 9:16 | Görsel: 4:5)
                  ├───────────────► 2. Instagram Story (Dedicated 1080x1920 Tam Ekran)
[Ezan Plus Motoru]├───────────────► 3. Threads (@ezanplusapp Zincir Gönderi + 4:5 Görsel)
                  ├───────────────► 4. Facebook Sayfası (Video: Facebook Reels | Görsel: 4:5 Post)
                  ├───────────────► 5. YouTube Shorts (Ezan Plus Kanalı + 9:16 Video)
                  └───────────────► 6. TikTok (@ezanplusapp - Taslak/Inbox veya Direct Post)
```

1. **Format Duyarlı Dağıtım (`src/telegram/yonetici.py`):**
   - Görsel paylaşımlarda (`gorsel_yollari = [p_4_5, p_9_16]`), Instagram Feed, Threads ve Facebook'a kareye yakın mükemmel akış formatı olan **4:5 (`gorsel_yollari[0]`)** gönderilir.
   - Dikey video paylaşımlarında (`reels_9_16`), Instagram'a Reels + Story, YouTube'a Shorts, Threads'e Video, **Facebook'a Facebook Reels (`facebook_reels_paylas`)** ve TikTok'a Taslak/Direct Video aktarılır.
   - Instagram Story paylaşımında kırpılma olmadan kusursuz görünmesi için doğrudan **9:16 dikey kart (`gorsel_yollari[1]`)** yüklenir.
2. **Güvenilir CDN Medya Barındırma Katmanı (`gecici_medya_yukle`):**
   - Meta Graph API doğrudan yerel dosya kabul etmediği için (`image_url` parametresi) yüksek hızlı geçici CDN katmanı kullanılır.
   - `tmpfiles.org/dl/` doğrudan indirme yerine HTML sayfası döndürdüğü ve 100+ saniye timeout verdiği için mimariden tamamen çıkarılmıştır.
   - **Birincil CDN:** `catbox.moe` (özel User-Agent ile doğrudan dosya yükleme).
   - **İkincil / Yüksek Hızlı Yedek CDN:** `litterbox.catbox.moe` (72 saatlik doğrudan medya CDN'i, Meta Graph API ile 3-4 saniyede işlenir).
   - Tüm HTTP isteklerinde standart masaüstü tarayıcı `User-Agent` başlığı kullanılarak CDN bot engellemeleri aşılmıştır.
3. **Instagram Reels, Feed & Story (`meta.py`):**
   - Meta Graph API v22.0 üzerinden `RUPLOAD_URL` ile iki adımlı Reels ve Story yayın protokolü.
   - **Container Hazırlık Yoklaması (Readiness Polling):** Feed ve Story container'ları oluşturulduktan sonra `media_publish` çağrılmadan önce `status_code == 'FINISHED'` olana kadar maksimum 15 iterasyon (4'er saniye, toplam 60 saniye) yoklama yapılır; `ERROR` durumunda işlem erken durdurulur.
   - **Story Takibi ve Yayından Kaldırma:** Story ID'si veritabanında `instagram_story_post_id` sütununda saklanır; `/kaldir` tetiklendiğinde Meta API üzerinden hem Feed hem Story silinir.
4. **Threads Zincir Gönderi (`threads.py`):** 500 karakter sınırı `metni_parcala()` algoritması ile aşılır; 450 karakterlik mantıklı parçalar halinde ana post altına `(1/3)`, `(2/3)` zincirleme eklenir.
5. **Facebook Sayfası (`meta.py`):** Dikey videolarda `/{page_id}/video_reels` uç noktası üzerinden `description=caption` ile tam açıklamalı **Facebook Reels**; tekil görsel postlarda `/{page_id}/photos` ile 4:5 fotoğraf postu yayınlanır.
6. **YouTube Shorts (`youtube.py`):** Google YouTube Data API v3 OAuth 2.0 ile dikey video (#Shorts).
7. **TikTok (`tiktok.py`):** TikTok Content Posting API v2 ile **Taslak / Gelen Kutusu (Inbox Mode - `/v2/post/publish/inbox/video/init/`)** modu varsayılandır; video kullanıcının TikTok mobil uygulamasına doğrudan taslak olarak aktarılır. Destekleyen onaylı hesaplarda Direct Post moduna geçilebilir.

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
| **6** | **22:00** | 19:00 | **İslamî Kavram / Kelime** | 4:5 Feed + 9:16 Story | Gece tefekkürü, Kur'an kavramı. Otomatik yayınlanır (onay beklemez, Telegram'a detay kartı ve 'Yayından Kaldır' iletilir). |

```
[Cloudflare Edge Cron] (11:30, 13:45, 16:30, 18:45, 20:30, 22:00 TSİ)
       │ (0 ms Gecikme, Global Dağıtık Ağ)
       ▼
[GitHub Actions Webhook] (repository_dispatch: gunluk_reels / hadis / dua / kelime)
       │
[Ubuntu Bulut Runner]
       ├─► 1. İlgili DB'den (Kur'an, Hadis, Dua, Kelime) tescilli metni çek
       ├─► 2. Medyayı render et (Reels için MP4 video, Kartlar için 4:5 + 9:16 PNG)
       ├─► 3. Kalite Kontrolü & Self-Healing Doğrulaması (src/denetleyici.py)
       ├─► 4. Yayınlama & Onay Ayrımı:
       │     • Kur'an Reels (1, 3, 5) & Kelime (6): Onaysız DOĞRUDAN YAYINLA! ➔ Telegram'a 'Yayından Kaldır' kartı at.
       │     • Hadis (2) & Dua (4): Telegram'a "✅ Onayla / ❌ İptal Et" butonlarıyla ilet (45 dk bekleme).
       └─► 5. Yayın geçmişini ve külliyatı git push ile depoya kaydet
```

### A. Cloudflare Worker Zamanlayıcı (`worker/`)
* **Canlı Servis:** `https://ezan-plus-tetikleyici.ezanplus.workers.dev`
* **Zamanlayıcı:** `worker/wrangler.toml` dosyasında 6 adet cron tanımlıdır (`30 8 * * *`, `45 10 * * *`, `30 13 * * *`, `45 15 * * *`, `30 17 * * *`, `0 19 * * *`).
* **Akıllı Dispatcher:** Worker, tetiklenme saatine göre `event_type` belirler (`gunluk_reels`, `gunluk_hadis`, `gunluk_dua`, `gunluk_kelime`).
* **Esnek Manuel Tetikleme Endpoint'i:**
  👉 `https://ezan-plus-tetikleyici.ezanplus.workers.dev/tetikle?tur=reels` (veya `hadis`, `dua`, `kelime`)
  Query parametreleri: `tur`, `tema`, `auto=true` (otomatik yayın).

### B. GitHub Actions Bulut İş Akışı (`.github/workflows/gunluk_reels.yml`)
* **Tekil Yetkili Tetikleyici:** 6 zamanlanmış slot için zamanlama Cloudflare Worker (`repository_dispatch`) üzerinden 0 ms gecikmeyle yönetilir. GitHub Actions'ın dahili `schedule` cron'u, GitHub altyapısındaki 15-30 dakikalık gecikmeler nedeniyle mükerrer üretime (çift tetiklemeye) yol açtığı için devre dışı bırakılmıştır.
* `workflow_dispatch` üzerinden GitHub UI'dan tek tıkla `tur` (reels, hadis, dua, kelime, ayet) seçilerek tetiklenebilir.
* Üretim tamamlandıktan sonra yayın geçmişi ve güncellenen veritabanları (`data/yayin_gecmisi.json`, `data/dualar/dualar.json`, `data/kelimeler/kelimeler.json`, `data/kuran/kuran.db`, `data/hadisler/hadisler.db`) otomatik olarak depoya `git push` yapılır.

### C. 4 Kategoride Birleşik Mükerrerlik Önleme & Külliyat Arşiv Mimarisi
Ezan Plus sosyal medya yayınlarında içeriklerin (Âyet, Hadis, Dua, Kelime) kısa aralıklarla tekrar etmesi mimari olarak kesin biçimde engellenmiştir:

1. **Âyet Mükerrerlik Çözümü (`ayet_anahtari_cozumle` & `gunun_ayetini_sec`):**
   - Geçmiş kayıtlarda yer alan `"9:53"` anahtarları veya `"Tevbe Sûresi • 53. Âyet"` / `"Bakara 127"` gibi insan-okunur etiketler `ayet_anahtari_cozumle` ile sûre ve âyet numaralarına `(sure_no, ayet_no)` ayrıştırılır.
   - SQL sorgusu dışlama listesindeki sûre/âyet ikililerini doğrudan `(sure_no = ? AND ayet_no = ?)` şartıyla eler.
   - Seçim motoru öncelikle `paylasim_sayisi = 0` olan hiç paylaşılmamış âyetleri rastgele getirir. Tüm havuz tükenmeden daha önce paylaşılmış bir âyet asla seçilemez.
2. **Yayın Anında Otomatik Külliyat İşaretleme (`durum_guncelle`):**
   Bir paylaşımın durumu `"yayinlandi"` olduğunda tüm 4 kategorinin birincil veri kaynaklarında sayaçlar anında artırılır:
   - **Âyet:** `kuran_db.ayeti_paylasildi_isaretle(sure_no, ayet_no)` ➔ `kuran.db`'de `paylasim_sayisi += 1` ve `son_paylasim_tarihi` işlenir.
   - **Hadis:** `hadis_db.hadisi_paylasildi_isaretle_metin(turkce_metin)` ➔ `hadisler.db`'de `paylasim_sayisi += 1` ve `son_paylasim_tarihi` işlenir.
   - **Dua:** `dua_db.duayi_paylasildi_isaretle_baslik(baslik)` ➔ `dualar.json`'da `paylasildi_mi: true`, `paylasim_sayisi += 1` ve `son_paylasim_tarihi` kaydedilir.
   - **Kelime:** `kelime_db.kelimeyi_paylasildi_isaretle(kelime)` ➔ `kelimeler.json`'da `paylasildi_mi: true` ve `paylasim_sayisi += 1` güncellenir.
3. **CI/CD Ephemeral Runner Kalıcılık Senkronizasyonu (`gunluk_reels.yml`):**
   GitHub Actions bulut ortamında çalışan sanal makineler geçicidir (ephemeral). Veritabanı sayaçlarının sıfırlanmasını önlemek için iş akışı sonunda `data/kuran/kuran.db` ve `data/hadisler/hadisler.db` dosyaları `git add` ile commit edilip depoya geri push edilir.
4. **Külliyat ve Arşiv Kapasitesi:**
   - **Kur'an Âyetleri (`data/kuran/kuran.db`):** 6.236 âyet (Reels formatına uygun 4-25 kelimelik 4.476 âyet; günde 3 tilavet slotuyla ~4 yıl sıfır tekrar).
   - **Sahih Hadisler (`data/hadisler/hadisler.db`):** 1.900 hadis (Riyâzü's-Sâlihîn; günde 1 hadis slotuyla ~5.2 yıl sıfır tekrar).
   - **Günün Duası (`data/dualar/dualar.json`):** 20 özel dua (8 manevi ruh haline göre; paylaşılmamışlar önceliklidir).
   - **Kur'an Sözlüğü / Kelime (`data/kelimeler/kelimeler.json`):** 15 temel kavram (el-Müfredât külliyatı; paylaşılmamışlar önceliklidir).

---

## 6. Telegram İki Yönlü Komut & Yönetim Sistemi (`src/telegram/`)

Telegram botu sadece pasif bir onay aracı değil, iki yönlü interaktif bir yönetim terminalidir.

### A. Kayıtlı Bot Menüsü Komutları (`setMyCommands`)
Bot başlatıldığında Telegram arayüzündeki `/` menüsüne aşağıdaki komutlar otomatik olarak kaydedilir (`komutlari_kaydet`):
* `/ayet` — Yeni Kur'an tilaveti veya ayet kartı taslağı oluşturur.
* `/hadis` — Riyâzü's-Sâlihîn külliyatından yeni bir sahih hadis kartı üretir.
* `/dua` — 8 farklı manevi kategoriden günün duası kartını üretir.
* `/kelime` — Kur'an'dan önemli bir İslami kavram / kelime kartı üretir (otomatik yayınlanır).
* `/durum` — Veritabanı ve yayın istatistiklerini gösterir.
* `/yardim` — Tüm komutları ve kullanım detaylarını listeler.

### B. İleri Seviye Yayın ve Yönetim Komutları
* `/yayinla <PAYLASIM_ID>` — Beklemede olan bir taslağı tüm platformlara anında yayınlar.
* `/kaldir <PAYLASIM_ID>` — Yayınlanmış olan bir içeriği Meta (Instagram/Facebook), Threads ve YouTube'dan anında siler ve veritabanı/yayın geçmişinden temizler.
* `/iptal <PAYLASIM_ID>` — İlgili taslağı yayından kaldırır ve iptal eder.
* `/onar <PAYLASIM_ID>` — Kusurlu veya hata almış bir paylaşımı `src/denetleyici.py` motoru ile otonom onarır.
* `/yeniden_uret <PAYLASIM_ID>` — İlgili içeriği sıfırdan yeniden render eder ve onaya/yayına sunar.
* `/saglik` — Tüm sosyal medya API token'larını (Instagram, Facebook, Threads, YouTube, TikTok) ve bağlantılarını test ederek sağlık durumunu raporlar.
* `/hatalar` — Son paylaşımlarda yaşanan platform veya render hatalarını ayrıntılı listeler.
* `/temizle` — Geçici medya ve önbellek dosyalarını temizler.

### C. Kur'an Tilaveti & Kur'an Sözlüğü Otomatik Yayın & Yayından Kaldırma Güvencesi
* **Otomatik Yayınlama:** Kur'an tilavetleri (11:30, 16:30, 20:30 TSİ) ve Kur'an Sözlüğü (22:00 TSİ) render tamamlandığı anda onay beklemeden doğrudan ilgili kanallara (Reels için Reels+Story+Threads+Facebook+Shorts; Kelime için Feed+Story+Threads+Facebook) otomatik yayınlanır.
* **Telegram Yayın Detay Kartı (`yayin_detay_karti_gonder`):** Yayınlanan medya, platform yayın başarı raporu ve izleme linkleriyle birlikte Telegram grubuna iletilir.
* **"🗑️ Yayından Kaldır" Butonu:** Telegram'a iletilen yayın raporunun altında `[ 🗑️ Yayından Kaldır ]` butonu yer alır. Olası bir durumda tek tıkla içerik tüm platformlardan API aracılığıyla silinir.
* **Onaylı Kartlar:** Hadis (13:45 TSİ) ve Dua (18:45 TSİ) kartları ise "✅ Onayla / ❌ İptal Et" butonlarıyla onaya sunulur; onaylandıklarında butonları otomatik olarak "🗑️ Yayından Kaldır"a dönüşür.

### D. Dinleme & Yanıt Mimarisi
* **Tek Sefer Dinleme (`dinle_ve_bekle`):** Bulut runner'ında onay butonlarını ve yayın sonrası "Yayından Kaldır" butonlarını dinler.
* **Zaman Aşımı Güvenli Kapanış:** Hadis veya Dua taslaklarında 45 dakika boyunca onay/ret verilmediğinde, Telegram mesajı `⏰ ONAY SÜRESİ DOLDU (45 Dakika)` olarak güncellenir ve onay butonları kaldırılarak yerine `[ 🔄 Sıfırdan Yeniden Üret ]` butonu yerleştirilir. Böylece süresi geçmiş/kapanmış bulut oturumuna basılıp sonsuz spinner hatası alınması engellenir.
* **Sürekli Dinleme Daemon (`surekli_dinle`):** Yerel veya sunucu ortamında sürekli çalışarak gelen her komuta ve buton tıklamasına 2 saniyelik yoklama aralığıyla kesintisiz yanıt verir.
* **KATI KURAL — Çift Bot / HTTP 409 Çakışma Önleme:** Telegram Bot API tekil `getUpdates` kuralına tabidir. Yerel geliştirme ortamında `python -m src.telegram.bot` arka planda yetim (orphaned daemon) olarak çalışırsa GitHub Actions bulut runner'ı ile çakışır (HTTP 409 Conflict) veya yerel boş/eski veritabanıyla butonları yakalayıp sonsuz askıya alır. Yerel daemon geliştirme haricinde daima kapatılmalıdır; bulut runner tek yetkili onay ve yayın orkestratörüdür.
* **Hata Yakalama & Tekrar Dene Güvencesi:** Onay butonuna basıldığında platformlardan herhangi birinde ağ/token hatası oluşursa mesaj sonsuza kadar "Yayınlanıyor..." olarak asılı kalmaz. `_gorev_onay` fonksiyonunda try/except ile yakalanıp hata detayları Telegram mesajına yazılır ve altına `[ 🔄 Tekrar Dene ]` inline butonu eklenir.


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
│   ├── ezanplus.db                # SQLite içerik ve yayın kayıtları (Story, Facebook, YouTube post ID şeması)
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
│   ├── ses_getir.py               # EveryAyah ses indirme & ses süresi yöneticisi
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

## 7. Hata Teşhis, Eyleme Geçirilebilir Çözüm Butonları ve CDN Güvenilirlik Mimarisi

İçerik üretimi veya 6 platformlu yayın akışında herhangi bir aksaklık yaşandığında (ağ kesintisi, CDN engeli, Meta API zaman aşımı vb.) operasyonel körlüğü önlemek ve doğrudan Telegram arayüzünden müdahale edebilmek için kapsamlı bir teşhis ve telafi mimarisi uygulanmıştır:

### A. Kök Sebep Teşhis Motoru (`src/hata_bildir.py`)
* **Hata Kataloğu (`KATALOG`):** Karşılaşılan hatalar düzenli ifadelerle taranarak anında teşhis edilir:
  - `CDN_UPLOAD_FAIL`: Geçici CDN barındırma sunucularına ulaşılamadı.
  - `IG_TIMEOUT_MEDIA`: Instagram sunucuları medyayı çekerken zaman aşımına uğradı.
  - `META_TOKEN_EXPIRED`: Meta API jetonunun süresi doldu veya yetki geçersiz.
  - `META_RATE_LIMIT`: Meta API geçici istek sınırı (429) uyguladı.
  - `TELEGRAM_TIMEOUT`: Telegram botu medyayı yüklerken zaman aşımına uğradı.
  - `SQLITE_LOCKED`: Veritabanı anlık olarak kilitlendi.
  - `GEMINI_QUOTA_EXCEEDED`: Gemini API günlük ücretsiz istek limiti tükendi.
  - `GEMINI_JSON_SYNTAX_ERROR`: Gemini AI modelinin Türkçe tırnak veya sözdizimi nedeniyle bozuk JSON üretmesi (otomatik self-healing ile 2. denemede RFC-8259 uyarı promptuyla telafi edilir).
  - `THREADS_MEDIA_NOT_FOUND`: Meta Threads sunucuları arasındaki replikasyon gecikmesi nedeniyle container ID'nin anlık bulunamaması (Subcode 4279009 / Code 24 - 3 denemeli backoff ile aşılır).
  - `RENDER_FFMPEG_FAIL`: FFmpeg video birleştirme veya ses zaman damgası enterpolasyonunda aksaklık.
  - `PYTHON_SCOPE_ERROR` / `PYTHON_TYPE_ERROR`: Kod yürütme kapsamı veya tip uyumsuzluğu.
* **LLM JSON Self-Healing & Hata Dayanıklılığı (`src/uretim/ai.py`):**
  - `_json_onar`: Sondaki yetim virgülleri (`,\s*([\]}]) -> \1`), markdown bloklarını ve bozuk tırnakları regex ile temizler.
  - `_json_ayikla`: `strict=False` moduyla kaçışsız kontrol karakterlerine tolerans gösterir.
  - `_gemini_cagir_json`: JSON ayrıştırma hatasında bekleyip Gemini'ye hatayı içeren düzeltme promptu göndererek 2. denemede geçerli JSON alır; workflow çökmesini %100 önler.
* **Threads Container Hazırlık Yoklaması & Replika Telafisi (`src/platformlar/threads.py`):**
  - `_threads_container_yayinla`: Zincir gönderi yanıtlarında ve medya gönderilerinde container `status == 'FINISHED'` olana kadar 2 saniyede bir yoklama yapar.
  - Meta Error 24 / Subcode 4279009 (`Media Not Found`) yakalandığında 3 saniye ve 6 saniye üssel gecikmeyle 3 defaya kadar tekrar dener; zincir yanıtlarının kesilmesini engeller.
* **Telegram İdempotent Güncelleme (`src/telegram/bot.py`):**
  - Telegram `message is not modified` 400 uyarısı hata fırlatmak yerine zararsız no-op (DEBUG seviyesi) olarak yutulur.
* **Sade Türkçe Raporlama Standardı:** Teknik hata metinleri yerine kullanıcıya 4 net bölüm sunulur:
  1. **🔍 NE OLDU?** (Durumun sade özeti)
  2. **💡 NEDEN?** (Arka plandaki teknik kök sebep)
  3. **🛠️ ÇÖZÜM / NE YAPILMALI?** (Atılması gereken somut adım)
  4. **📄 HAM HATA İZİ:** (Geliştirici için 450 karakterlik filtrelenmiş traceback)
* **Kalıcı Telemetri Logu:** Tüm hatalar otomatik olarak `data/hata_kayitlari.jsonl` (tarih, paylasim_id, nerede, teşhis) ve `data/son_hata.txt` dosyalarına işlenir.

### B. Çok Katmanlı CDN Güvenilirlik Mimarisi (`gecici_medya_yukle`)
Meta Graph API (Instagram & Threads) yerel dosya kabul etmeyip doğrudan genel HTTP/HTTPS URL şartı koştuğu için 4 kademeli CDN mimarisi devreye alınmıştır:
1. **1. Öncelik — Uguu.se (`https://uguu.se/upload`):** Yüksek hızlı, doğrudan dosya linki, datacenter IP engelleri bulunmayan birincil CDN servisi.
2. **2. Öncelik — Catbox.moe (`https://catbox.moe/user/api.php`):** Doğrudan dosya CDN servisi.
3. **3. Öncelik — Litterbox (`https://litterbox.catbox.moe`):** 72 saatlik geçici doğrudan dosya CDN'i.
4. **4. Öncelik — ImgBB API (`https://api.imgbb.com/1/upload`):** Çoklu anahtar desteği ile kalıcı görsel CDN yedeği.

### C. Dinamik Telafi Butonları & Mükerrer Paylaşım Koruması (`telafi_butonlari_kur` & `yayinla_telafi`)
* **Kısmi Başarı / Hata Raporlama:** Bir paylaşımda bazı platformlar başarılı olup bazıları başarısız olduğunda Telegram raporu `⚠️ [KATEGORİ] — KISMİ BAŞARI / DİKKAT` başlığıyla güncellenir.
* **Dinamik Buton Matrisi:**
  - `[ 🔄 Başarısız Tüm Kanalları Tekrar Dene ]` (`telafi_hepsi_<id>`): Sadece başarısız olan kanalları sırayla yeniden yayınlar.
  - **Kanal Bazlı Tekil Butonlar:** Yalnızca başarısız olan kanallar için buton üretilir (`[ 🔄 📸 Instagram ]`, `[ 🔄 📱 Story ]`, `[ 🔄 🧵 Threads ]`, `[ 🔄 📘 Facebook ]`).
  - `[ 🔍 Hata Teşhisi & Çözüm Rehberi ]` (`teshis_<id>`): Tek tıkla ilgili paylaşımın kök sebep teşhis kartını ve çözüm önerilerini ekrana getirir.
  - `[ 🗑️ Yayından Kaldır ]` (`kaldir_<id>`): Yayınlanan kanallardan içeriği geri çeker.
* **Mükerrer Paylaşım Koruması (`yayinla_telafi`):** Yeniden deneme tetiklendiğinde veritabanında (`paylasimlar`) daha önce başarılı olmuş platformlar (örn. Facebook ID'si mevcutsa) tespit edilerek atlanır; Facebook'ta çift post oluşması mimari olarak %100 engellenir. Sadece eksik platformlar tamamlanır ve DB kaydı güncellenir.

### D. Telegram Teşhis ve Çözüm Komutları
* `/hata`: Sistemde kaydedilen en son hatanın teşhis kartını ve aksiyon butonlarını getirir.
* `/hatalar`: Son 5 sistem hatasını özet liste olarak gösterir ve her biri için tek tık onarım butonları sunar.
* `/onar <id>`: Kalite kontrolünden veya mizanpaj denetiminden geçemeyen içeriği `otomatik_onar` motoruyla otonom tamir eder.
* `/yeniden_uret <id>`: Belirtilen paylaşımı tescilli külliyatından sıfırdan yeniden üretir (AI promptu ve medya render'ı yenilenir, eski kayıt arşivlenir).
* `/tekrar <id>`: Belirtilen paylaşım ID'sinde başarısız kalan platformları anında yeniden dener.
* `/saglik` (veya `/test`): Yerel SQLite veritabanları (`kuran.db`, `hadisler.db`, `ezanplus.db`), Gemini AI API, Meta Graph API, Threads API, YouTube API ve depolama durumunu denetler; renk kodlu sağlık karnesi sunar.
* `/temizle`: `data/cikti/` altındaki geçici render artıklarını (`temp_*`, `*.tmp`), yetim ses listelerini temizler ve SQLite WAL checkpoint'ini diskle senkronize eder.

### E. İçerik Üretim Dayanıklılık ve Troubleshooting Standartları
* **AI Latin Okunuş 1:1 Hizalama Güvencesi (`src/uretim/ai.py`):** Gemini AI modelinin ürettiği token sayısı Arapça kelime sayısından farklı olsa dahi `turkce_okunus_hizala` fonksiyonu ile otomatik dengelenir; eksik token veya dizi taşması mimari olarak imkansızdır.
* **Video Kanca Başlıkları Taşma Emniyeti (`src/uretim/video.py`):** Reels video üst başlıkları (`video_baslik_satir1` ve `video_baslik_satir2`) $1080$px ekran genişliğini aşmayacak şekilde dinamik auto-fit algoritmasıyla ölçeklenir; ekrandan taşma veya kesilme önlenmiştir.
* **Kart Şablonları CTA Çarpışma Kilidi (`src/uretim/kart.py`):** Hadis, Dua ve Kelime kartlarında ultra uzun metinlerde dahi kaynak rozeti alt App Store/Play Store CTA indirme butonunun üst sınırına (`max_badge_bottom`) kilitlenir; buton üzerine binme engellenmiştir.
* **Boş Metin Toleransı (`src/uretim/kart.py`):** Kavram veya hadis metinlerinde boş/hatalı değer gelmesi durumunda `ValueError: max() arg is an empty sequence` hatası vermez; kurumsal editoryal fallback devreye girer.
* **SQLite Kaynak ve Kilit Güvenliği (`src/db.py`, `src/kuran_db.py`, `src/hadis_db.py`):** Tüm veritabanı bağlantıları `@contextmanager` ile sarmalanarak işlem bitiminde `finally: con.close()` garantisi verilmiştir. SQLite bağlantı sızıntıları ve kilitlenme riskleri (`SQLITE_LOCKED`) %100 ortadan kaldırılmıştır.
* **FFmpeg Güvenli Render & Çöp Toplama (`src/uretim/video.py`):** Video birleştirme aşamasında olası hatalarda `subprocess.CalledProcessError` stderr çıktısı Türkçe anlaşılır mesajla yükseltilir ve `finally:` bloğuyla geçici sessiz MP4 dosyaları diskten temizlenir.
* **EveryAyah Ses İndirme Toleransı (`src/uretim/ses.py`):** Ağ gecikmelerine karşı 2 denemeli üssel bekleme ile EveryAyah ses dosyaları güvenle indirilir.

### F. Daily Brief Mimarisinden Aktarılan Güvenilirlik ve Dayanıklılık Standartları
1. **Mükerrer Yayın Kilidi (`src/telegram/yonetici.py` — Ders 1u):**
   `yayinla_hepsi()` çağrıldığında kaydın durumu `"yayinlandi"` ise ve platform post ID'leri mevcutsa körlemesine tekrar paylaşım yapılmaz; doğrudan `yayinla_telafi(paylasim_id, hedef_kanal="hepsi")` süzgecine aktarılarak sadece eksik kanallar tamamlanır.
2. **Cevapsız Telegram Callback Koruması (`src/telegram/bot.py` — Ders 127):**
   Tanınmayan, süresi dolmuş veya eski buton tıklamalarında Telegram istemcisinde sonsuz dönen spinner (yükleme simgesi) oluşmasını engellemek için `callback_cevapla` ile kullanıcıya anında bilgilendirme yapılır.
3. **Threads 60 Günlük Jeton Yenileme (`src/platformlar/threads.py` — Ders 217):**
   `jetonu_yenile()` fonksiyonu ile `https://graph.threads.net/refresh_access_token` uç noktası üzerinden 60 günlük süresi dolmadan önce uzun ömürlü token otomatik yenilenir.
4. **Meta Multi-CDN Fallback & Alt Kod Ayrıştırma (`src/platformlar/meta.py` — Ders 171, 1e, 1aa):**
   Meta Graph API geçici medya işleme hatalarında subcode `2207003` ve `2207052` tespit edilerek başarısız olan CDN dışlanır (`haric_cdnler`); Catbox, Litterbox ve Uguu arasında 3 turlu otomatik geçiş yapılır.
5. **Headless CI Koruması (YouTube & TikTok — Ders 108, 110, 112):**
   GitHub Actions bulut ortamında terminal etkileşimli olmadığı için (`sys.stdin.isatty() == False`), runner'ı sonsuz `input()` veya `run_local_server()` döngüsüne sokmak yerine açık `RuntimeError` yükseltilir. YouTube OAuth konsolunda "Testing" (7 günlük token ömrü) ile "In production" ayrımı hata günlüğünde net teşhis edilir.
6. **TikTok Başlık ve Etiket Formatlayıcı (`src/platformlar/tiktok.py` — Ders 113):**
   `baslik_ve_etiketleri_birlestir()` fonksiyonu ile TikTok'un tekil `title` alanında manşet metni korunur; 2000 karakter sınırı aşılırsa hashtagler sondan dinamik düşürülür.
7. **Türkçe Karakter Destekli Hashtag Normalizasyonu (`src/uretim/ai.py` & `src/denetleyici.py` — Ders 114, 115):**
   `_etiket_anahtari()` fonksiyonu `çğıöşüâîû` harflerini sadeleştirerek `#şükür` ile `#sukur` veya `#duâ` ile `#dua` etiketlerinin mükerrer basılmasını önler; `#ezanplus` daima 1. sıraya kilitlenir ve toplam etiket sayısı katı 5 ile sınırlandırılır.
8. **GitHub Actions CI/CD Dayanıklılığı (`.github/workflows/gunluk_reels.yml` — Ders 1m, 1q):**
   `git pull --rebase origin main || (git rebase --abort || true)` koruması, detached HEAD durumunda doğrudan branch referansı için `git push origin HEAD:main` ve iptal edilen iş akışlarında anlık Telegram uyarısı (`if: cancelled()`).

---

## 8. Gelecek Yol Haritası ve Planlanan Geliştirmeler

1. **Farklı İçerik Türlerinin Genişletilmesi:**
   * ✅ **Hadis-i Şerif Serisi:** Riyâzü's-Sâlihîn'den 1.900 sahih hadis DB entegrasyonu tamamlandı.
   * ✅ **Günün Duası:** 8 manevi ruh haline göre dua DB entegrasyonu tamamlandı.
   * ✅ **Günün Kelimesi / Kavramı:** Kur'an kavramları DB entegrasyonu tamamlandı.
   * **Günün Zikri & Esmaü'l Hüsna:** Anlamı, ebced değeri ve faziletiyle 99 Esma serisi eklenebilir.
2. **Telegram İki Yönlü Komut Menüsü:**
   * ✅ Telegram arayüzüne `/ayet`, `/hadis`, `/dua`, `/kelime`, `/durum`, `/hata`, `/yardim` komut menüsü kaydedildi.
   * ✅ Arka planda `/yayinla <id>`, `/tekrar <id>`, `/iptal <id>` ve `/kaldir <id>` komut desteği tamamlandı.
3. **Yayın Öncesi Kalite & Otomatik Onarım Güvencesi:**
   * ✅ Mizanpaj çakışması, boyut hatası, yasaklı bot ifadesi ve eksik etiket taraması tamamlandı.
   * ✅ Otomatik onarım döngüsü (`otomatik_onar`) ile hataları yayından önce düzelten self-healing mimarisi tamamlandı.
4. **Hata Teşhis ve Dayanıklı Dağıtım:**
   * ✅ Çok katmanlı CDN katmanı (Uguu + Catbox + Litterbox + ImgBB) devreye alındı.
   * ✅ Telegram interaktif teşhis ve telafi butonları devreye alındı.
5. **TikTok Uygulama İncelemesi (App Review):**
   * TikTok Developer Portal'daki inceleme tamamlandığında tek tıkla token alınacak ve TikTok da tam otomatik yayın zincirine bağlanacaktır.
