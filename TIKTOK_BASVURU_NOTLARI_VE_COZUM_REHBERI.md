# TikTok for Developers Başvuru İncelemesi & Çözüm Rehberi
> **Proje:** Ezan Plus Bot (App ID: `7681671159805020181`)  
> **Durum:** Production - Not Approved (Düzeltme & Yeniden Gönderim Gerekiyor)  
> **Tarih:** 11 Eylül 2026

---

## 1. Gelen Yanıt ve Denetçi Notu

TikTok denetim ekibi başvuruyu inceledi ve **sadece tek bir alanı** güncelleyerek tekrar göndermenizi talep etti:

* **Eksik / Hatalı Alan:** `Website URL`
* **Denetçinin Resmi Notu:**
  > *"Your externally facing website must be fully developed and cannot be a landing or login page. If it is a login page, you must provide a test account and password in the Apply Reason field."*

---

## 2. Denetçi Tam Olarak Ne İstiyor? (Sorunun Kaynağı)

Denetçi başvuru formunda girdiğiniz `Website URL` adresine gitmiş ve şunlardan biriyle karşılaşmış:

1. **Sadece Giriş Formu (Login Page) Gördü:**  
   Siteniz bir web paneli/uygulaması ise ve giriş yapmadan içerisi görünmüyorsa, denetçi içerideki TikTok entegrasyonunu, arayüzü ve ürün fonksiyonlarını test edememiş. Bu yüzden içeri girebilmek için sizden **test hesabı (kullanıcı adı & şifre)** istiyor.
2. **Veya Basit / Boş Landing Page Gördü:**  
   Siteniz tek sayfalık, "yakında açılıyor" tarzı veya tam bitmemiş bir sayfa ise, TikTok politikaları gereği "tamamen geliştirilmiş bir ürün sitesi" olmadığı için reddedilmiş.

---

## 3. Adım Adım Çözüm ve Resubmit Planı

### Adım 1: Düzenleme Moduna Geçin
* Portalın sağ üst köşesinde yer alan **`Return to Draft`** butonuna tıklayın. Form yeniden düzenlenebilir hale gelecektir.

### Adım 2: Durumunuza Uygun Yolu Uygulayın

#### Seçenek A: Siteniz bir Web Uygulaması / Panel ise (En Olası Durum)
Eğer siteniz login gerektiren bir web paneliyse:
1. Panelinizde denetçiye özel bir **test kullanıcısı** oluşturun (örnek: `reviewer@ezanplus.com` / `TikTokReview2026!`).
2. Bu hesapla giriş yapıldığında TikTok paylaşım/otomasyon ekranları ve panel özellikleri açıkça görülebilmeli.
3. Formdaki **`Apply Reason` (Başvuru Nedeni)** alanına aşağıdaki İngilizce şablonu kopyalayıp ekleyin:

```text
--- TEST CREDENTIALS FOR TIKTOK REVIEWER ---
Website URL: https://siteniz.com/login
Test Username / Email: reviewer@ezanplus.com
Test Password: TikTokReview2026!

Note: Please use the test account above to log in to our web application. Once logged in, you will be able to access the dashboard, view the TikTok Content Posting integration, configure video posts, and test the full end-to-end user workflow.
--------------------------------------------
```

#### Seçenek B: Siteniz bir Tanıtım / Landing Page ise
* Siteniz sadece giriş ekranı değilse; Ezan Plus'ın ne olduğunu anlatan, özelliklerini, mobil uygulama/panel ekran görüntülerini, App Store bağlantılarını, iletişim bilgilerini ve footer'da Gizlilik Politikası / Kullanım Şartları linklerini içeren **eksiksiz ve çalışan** bir web sitesi sunun.
* Sayfanın SSL (HTTPS) sertifikalı olduğundan ve gizli sekmede hatasız açıldığından emin olun.

---

## 4. Daha Önceki Görselden Tespit Edilen Diğer Kritik Noktalar

Madem formu tekrar `Draft` moduna alıp düzenleyeceksiniz, ileride yeni bir ret yememek için şu noktalara da dikkat edin:

1. **Uygulama Adındaki "Bot" Kelimesi (`Ezan Plus Bot`):**  
   * "Bot", "Scraper", "Automator" gibi kelimeler TikTok, Meta ve Google incelemelerinde otomatik spam filtresine takılır.
   * `video.publish` (doğrudan video yayınlama) izni istenirken bot kelimesi risklidir. Mümkünse adı `Ezan Plus Web` veya `Ezan Plus App` olarak güncellemek güveni artırır.
2. **Content Posting API - Business Verification (`Apply` Butonu):**  
   * `Direct Post` özelliğini kullanmak için TikTok ilerleyen aşamada tüzel kişilik/şirket doğrulaması (vergi levhası vb.) talep edebilir.
3. **Demo Videosu Linki:**  
   * Demo video linkinizin (YouTube Unlisted, Google Drive vb.) gizli pencerede şifresiz/izinsiz doğrudan oynatılabildiğinden emin olun.
   * Videoda OAuth onay ekranının ve videonun TikTok'ta yayınlandığının gösterilmesi şarttır.

---

## 5. Yeniden Gönderim (Resubmit)
Yukarıdaki düzenlemeleri tamamladıktan sonra:
1. `Website URL` alanını kontrol edin.
2. `Apply Reason` kutusuna test hesabı bilgilerini girin.
3. **`Submit for Review` / `Resubmit`** butonuna basarak başvuruyu yeniden gönderin.
4. Düzeltilmiş başvurular genellikle ilk başvuruya göre çok daha hızlı (1-3 iş günü) sonuçlanır.
