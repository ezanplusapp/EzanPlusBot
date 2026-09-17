/**
 * Ezan Plus — Dinamik Vitrin & İnteraktif Modül Motoru
 * - Canlı Namaz Vakti Geri Sayım Sayacı
 * - İnteraktif iPhone 16 Pro Mockup Deneyimi
 * - Şeyh Mişari Râşid Stüdyo Tilavet Çaları
 * - Tescilli Külliyat & Hikmet Rotatoru
 * - QR Kod Modal Yöneticisi
 */

document.addEventListener('DOMContentLoaded', () => {
    initHeaderScroll();
    initSmartDeviceDownload();
    initThreeJsBackground();
    init3dMockupTilt();
    init3dCardTilt();
    initMockupTabs();
    initGalleryCarousel();
    initFaqAccordion();
    initInteractiveDhikr();
    initLivePrayerTimes();
    initQuranShowcase();
    initHadithModule();
    initQrModal();
});

/* ==========================================================================
   Global Metin Sadeleştirme (Arama & Eşleme)
   ========================================================================== */
function normalizeSearchText(str) {
    if (!str) return '';
    return str
        .toLowerCase()
        .replace(/[âäà]/g, 'a')
        .replace(/[îïìı]/g, 'i')
        .replace(/[ûüù]/g, 'u')
        .replace(/[ôöò]/g, 'o')
        .replace(/[ç]/g, 'c')
        .replace(/[ğ]/g, 'g')
        .replace(/[ş]/g, 's')
        .replace(/['’‘\-_\s]/g, '');
}

/* ==========================================================================
   1. Header Scroll Efekti
   ========================================================================== */
function initHeaderScroll() {
    const header = document.querySelector('.site-header');
    if (!header) return;

    window.addEventListener('scroll', () => {
        if (window.scrollY > 40) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    }, { passive: true });
}

/* ==========================================================================
   2. İnteraktif iPhone Mockup Sekmeleri (Gerçek Ekranlar)
   ========================================================================== */
function initMockupTabs() {
    const tabButtons = document.querySelectorAll('.mockup-tab-btn');
    const screens = document.querySelectorAll('.mockup-screen-img, .mockup-screen-content');

    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');

            tabButtons.forEach(b => b.classList.remove('active'));
            screens.forEach(s => s.classList.remove('active'));

            btn.classList.add('active');
            const targetScreen = document.getElementById(`screen-${targetTab}`);
            if (targetScreen) {
                targetScreen.classList.add('active');
            }
        });
    });
}

/* ==========================================================================
   3. İnteraktif Zikirmatik (Haptik / Dokunma Efekti)
   ========================================================================== */
let dhikrCount = 33;
const dhikrPhrases = [
    { ar: "سُبْحَانَ اللَّهِ", tr: "Sübhânallâh", meaning: "Allah her türlü eksiklikten münezzehtir" },
    { ar: "الْحَمْدُ لِلَّهِ", tr: "Elhamdülillâh", meaning: "Hamd ve övgü yalnız Allah'a aittir" },
    { ar: "اللَّهُ أَكْبَرُ", tr: "Allâhu Ekber", meaning: "Allah en büyüktür, yüceler yücesidir" },
    { ar: "لَا إِلٰهَ إِلَّا اللَّهُ", tr: "Lâ ilâhe illallâh", meaning: "Allah'tan başka ilah yoktur" }
];
let currentPhraseIdx = 0;

function initInteractiveDhikr() {
    const dhikrBtn = document.getElementById('dhikrInteractiveBtn');
    const dhikrCountEl = document.getElementById('dhikrCountDisplay');
    const dhikrTitleEl = document.getElementById('dhikrTitleDisplay');
    const dhikrArabicEl = document.getElementById('dhikrArabicDisplay');

    if (!dhikrBtn || !dhikrCountEl) return;

    dhikrBtn.addEventListener('click', () => {
        dhikrCount++;
        dhikrCountEl.textContent = dhikrCount;

        // Titreşim (Mobil destekleyen tarayıcılarda)
        if (navigator.vibrate) {
            navigator.vibrate(25);
        }

        // Her 33'te bir zikri değiştir
        if (dhikrCount % 33 === 0) {
            currentPhraseIdx = (currentPhraseIdx + 1) % dhikrPhrases.length;
            const p = dhikrPhrases[currentPhraseIdx];
            if (dhikrTitleEl) dhikrTitleEl.textContent = p.tr;
            if (dhikrArabicEl) dhikrArabicEl.textContent = p.ar;

            if (navigator.vibrate) {
                navigator.vibrate([40, 60, 40]);
            }
        }
    });
}

/* ==========================================================================
   4. Canlı Namaz Vakitleri & Geri Sayım Sayacı
   ========================================================================== */
const SEHIR_VAKITLERI = {
    "istanbul": { imsak: "05:18", gunes: "06:44", ogle: "13:06", ikindi: "16:38", aksam: "19:18", yatsi: "20:38" },
    "ankara":   { imsak: "05:04", gunes: "06:29", ogle: "12:51", ikindi: "16:23", aksam: "19:03", yatsi: "20:22" },
    "izmir":    { imsak: "05:27", gunes: "06:51", ogle: "13:14", ikindi: "16:47", aksam: "19:26", yatsi: "20:44" },
    "bursa":    { imsak: "05:19", gunes: "06:44", ogle: "13:06", ikindi: "16:39", aksam: "19:18", yatsi: "20:37" },
    "mekke":    { imsak: "04:52", gunes: "06:08", ogle: "12:21", ikindi: "15:44", aksam: "18:24", yatsi: "19:39" },
    "medine":   { imsak: "04:50", gunes: "06:09", ogle: "12:22", ikindi: "15:47", aksam: "18:25", yatsi: "19:42" }
};

const VAKIT_ISIMLERI = [
    { key: "imsak", tr: "İmsak" },
    { key: "gunes", tr: "Güneş" },
    { key: "ogle", tr: "Öğle" },
    { key: "ikindi", tr: "İkindi" },
    { key: "aksam", tr: "Akşam" },
    { key: "yatsi", tr: "Yatsı" }
];

let secilenSehir = "istanbul";

function initLivePrayerTimes() {
    const sehirSelect = document.getElementById('sehirSelect');
    if (sehirSelect) {
        sehirSelect.addEventListener('change', (e) => {
            secilenSehir = e.target.value;
            vakitleriGuncelle();
        });
    }

    vakitleriGuncelle();
    setInterval(vakitleriGuncelle, 1000);
}

function timeToMinutes(timeStr) {
    const [h, m] = timeStr.split(':').map(Number);
    return h * 60 + m;
}

function vakitleriGuncelle() {
    const vakitler = SEHIR_VAKITLERI[secilenSehir] || SEHIR_VAKITLERI["istanbul"];
    const now = new Date();
    const curHours = now.getHours();
    const curMins = now.getMinutes();
    const curSecs = now.getSeconds();
    const nowMinutes = curHours * 60 + curMins;

    // Vakit kutularındaki saatleri yaz
    VAKIT_ISIMLERI.forEach(v => {
        const timeBox = document.getElementById(`vakitTime-${v.key}`);
        if (timeBox) {
            timeBox.textContent = vakitler[v.key];
        }
    });

    // Sıradaki vakti bul
    let siradakiVakit = null;
    let siradakiVakitDakika = 0;
    let oncekiVakit = VAKIT_ISIMLERI[VAKIT_ISIMLERI.length - 1];

    for (let i = 0; i < VAKIT_ISIMLERI.length; i++) {
        const v = VAKIT_ISIMLERI[i];
        const vDk = timeToMinutes(vakitler[v.key]);
        if (vDk > nowMinutes) {
            siradakiVakit = v;
            siradakiVakitDakika = vDk;
            oncekiVakit = i > 0 ? VAKIT_ISIMLERI[i - 1] : VAKIT_ISIMLERI[VAKIT_ISIMLERI.length - 1];
            break;
        }
    }

    // Gece yarısından sonra Yatsı geçmişse sıradaki İmsak'tır (ertesi gün)
    let kalanSaniye = 0;
    if (!siradakiVakit) {
        siradakiVakit = VAKIT_ISIMLERI[0]; // İmsak
        const ertesiImsakDakika = 24 * 60 + timeToMinutes(vakitler["imsak"]);
        kalanSaniye = (ertesiImsakDakika - nowMinutes) * 60 - curSecs;
    } else {
        kalanSaniye = (siradakiVakitDakika - nowMinutes) * 60 - curSecs;
    }

    // Vakit kutularının aktifliğini ayarla
    VAKIT_ISIMLERI.forEach(v => {
        const box = document.getElementById(`prayerBox-${v.key}`);
        if (box) {
            if (v.key === oncekiVakit.key) {
                box.classList.add('active');
                const statusEl = box.querySelector('.prayer-box-status');
                if (statusEl) statusEl.textContent = "Şu Anki Vakit";
            } else {
                box.classList.remove('active');
                const statusEl = box.querySelector('.prayer-box-status');
                if (statusEl) statusEl.textContent = (v.key === siradakiVakit.key) ? "Sıradaki Vakit" : "";
            }
        }
    });

    // Dairesel İlerleme Barı (Circular Progress) Hesapla
    const oncekiDk = timeToMinutes(vakitler[oncekiVakit.key]);
    let hedefDk = timeToMinutes(vakitler[siradakiVakit.key]);
    let simdikiDk = nowMinutes + curSecs / 60;
    
    // Gece geçişi normalizasyonu (Yatsı -> İmsak)
    if (hedefDk <= oncekiDk) {
        hedefDk += 24 * 60;
        if (simdikiDk < oncekiDk) {
            simdikiDk += 24 * 60;
        }
    }
    const toplamSure = hedefDk - oncekiDk;
    const gecenSure = simdikiDk - oncekiDk;
    const progress = Math.min(100, Math.max(0, toplamSure > 0 ? (gecenSure / toplamSure) * 100 : 0));
    
    // SVG çevresi = 2 * PI * r = 2 * 3.14159265 * 102 = 640.88
    const circumference = 640.88;
    const offset = circumference - (progress / 100) * circumference;
    const circleBar = document.getElementById('timerCircleBar');
    if (circleBar) {
        circleBar.style.strokeDashoffset = offset.toFixed(2);
    }

    // Geri sayım formatla (02:45 ve :12)
    const kSaat = Math.floor(kalanSaniye / 3600);
    const kDakika = Math.floor((kalanSaniye % 3600) / 60);
    const kSaniye = kalanSaniye % 60;
    const hmStr = `${String(kSaat).padStart(2, '0')}:${String(kDakika).padStart(2, '0')}`;
    const secStr = `:${String(kSaniye).padStart(2, '0')}`;

    const digitsHM = document.getElementById('digitsHM');
    const digitsSec = document.getElementById('digitsSec');
    if (digitsHM && digitsSec) {
        digitsHM.textContent = hmStr;
        digitsSec.textContent = secStr;
    } else {
        const countdownEl = document.getElementById('liveCountdownTimer');
        if (countdownEl) countdownEl.textContent = `${hmStr}${secStr}`;
    }

    const countdownLabelEl = document.getElementById('liveCountdownLabel');
    if (countdownLabelEl) countdownLabelEl.textContent = `${siradakiVakit.tr} Vaktine Kalan Süre`;
    const appNextVakitTag = document.getElementById('appNextVakitTag');
    if (appNextVakitTag) appNextVakitTag.textContent = siradakiVakit.tr.toUpperCase();

    // Şehir ismini kadran hapında güncelle
    const timerCityName = document.getElementById('appTimerCityName');
    const sehirSelectEl = document.getElementById('sehirSelect');
    if (timerCityName && sehirSelectEl) {
        timerCityName.textContent = sehirSelectEl.options[sehirSelectEl.selectedIndex]?.text || "İstanbul";
    }

    // Mockup içindeki küçük ekranı da güncelle
    const miniNextTime = document.getElementById('miniNextTime');
    const miniCountdown = document.getElementById('miniCountdownBadge');
    const miniNextLabel = document.getElementById('miniNextLabel');
    if (miniNextTime) miniNextTime.textContent = vakitler[siradakiVakit.key];
    if (miniCountdown) miniCountdown.textContent = `${kSaat} sa ${kDakika} dk kaldı`;
    if (miniNextLabel) miniNextLabel.textContent = `${siradakiVakit.tr} Vakti`;

    // Mockup satırlarını güncelle
    VAKIT_ISIMLERI.forEach(v => {
        const row = document.getElementById(`miniRow-${v.key}`);
        if (row) {
            if (v.key === oncekiVakit.key) {
                row.classList.add('active-prayer');
            } else {
                row.classList.remove('active-prayer');
            }
            const timeSpan = row.querySelector('.time');
            if (timeSpan) timeSpan.textContent = vakitler[v.key];
        }
    });
}

/* ==========================================================================
   5. İnteraktif Kur'an-ı Kerim, Tilavet, Hatim ve Canlı Radyo Motoru
   ========================================================================== */
let allSurahs = [];
let currentSurahNo = 2; // Bakara Sûresi (Varsayılan)
let currentAyahNo = 255; // Âyete'l-Kürsî (Varsayılan)
let currentSurahAyahs = [];
let surahCache = {};
let currentMealKey = 'diy'; // 'diy' = Diyanet, 'elm' = Elmalılı
let isAutoFlow = true;
let isRepeatEnabled = false;
let currentPlaybackSpeed = 1.0;
let karaokeRafId = null;
let currentJuzFilter = 0;
let surahSearchTerm = '';

// 30 Cüz Durum Haritası (Varsayılan 18 cüz tamamlanmış = %60)
let completedJuzMap = {
    1: true, 2: true, 3: true, 4: true, 5: true, 6: true,
    7: true, 8: true, 9: true, 10: true, 11: true, 12: true,
    13: true, 14: true, 15: true, 16: true, 17: true, 18: true
};

function initQuranShowcase() {
    initQuranNavTabs();
    initQuranTilavetPlayer();
    initHatimTracker();
    initQuranRadio();
}

/* --- A. Kur'an Ana Sekmeler (Player / Hatim / Radio) --- */
function initQuranNavTabs() {
    const tabBtns = document.querySelectorAll('.quran-nav-tab');
    const panels = document.querySelectorAll('.quran-tab-panel');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabKey = btn.getAttribute('data-tab');
            tabBtns.forEach(b => b.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));

            btn.classList.add('active');
            const targetPanel = document.getElementById(`quranPanel-${tabKey}`);
            if (targetPanel) {
                targetPanel.classList.add('active');
            }
        });
    });
}

/* --- B. Canlı Tilavet Çaları & Senkron Karaoke (114 Sûre & 6.236 Âyet) --- */
function initQuranTilavetPlayer() {
    const audioEl = document.getElementById('quranRecitationAudio');
    const playBtn = document.getElementById('mushafPlayBtn');
    const miniPlayBtn = document.getElementById('miniPlayBtn');
    const progressTrack = document.getElementById('mushafProgressTrack');
    const progressFill = document.getElementById('mushafProgressFill');
    const curTimeEl = document.getElementById('mushafCurTime');
    const durTimeEl = document.getElementById('mushafDurTime');
    const equalizer = document.getElementById('mushafEqualizer');
    const speedBtn = document.getElementById('mushafSpeedBtn');
    const repeatBtn = document.getElementById('mushafRepeatBtn');
    const autoFlowBtn = document.getElementById('autoNextAyahToggle');
    const mealSelect = document.getElementById('mealSelect');
    const prevAyahBtn = document.getElementById('prevAyahBtn');
    const nextAyahBtn = document.getElementById('nextAyahBtn');
    const ayahSelectDropdown = document.getElementById('ayahSelectDropdown');
    const surahPickerBtn = document.getElementById('mushafSurahPickerBtn');
    const currentSurahBtnTitle = document.getElementById('currentSurahBtnTitle');

    // Modal Öğeleri
    const surahModal = document.getElementById('surahModalBackdrop');
    const surahModalCloseBtn = document.getElementById('surahModalCloseBtn');
    const surahSearchInput = document.getElementById('surahSearchInput');
    const surahSearchClear = document.getElementById('surahSearchClear');
    const surahCuzChips = document.getElementById('surahCuzChips');
    const surahListGrid = document.getElementById('surahListGrid');

    // Metin Alanları
    const badgeEl = document.getElementById('mushafAyahBadge');
    const juzBadgeEl = document.getElementById('mushafJuzBadge');
    const arabicEl = document.getElementById('mushafArabicText');
    const latinEl = document.getElementById('mushafLatinText');
    const transEl = document.getElementById('mushafTranslationText');
    const tefekkurEl = document.getElementById('mushafTefekkurText');
    const titleEl = document.getElementById('mushafPlayingTitle');

    if (!audioEl || !playBtn) return;

    // 114 Sûre Fihristini Yükle
    fetch('/data/quran/surahs.json')
        .then(res => res.json())
        .then(data => {
            allSurahs = data;
            initSurahModalControls();
            loadSurah(currentSurahNo, currentAyahNo, false);
        })
        .catch(err => {
            console.error('Sûre kataloğu yüklenemedi:', err);
        });

    // Sûre Fihristi Modal Denetimleri
    function initSurahModalControls() {
        if (!surahModal) return;

        // Cüz Filtre Çiplerini Doldur
        if (surahCuzChips) {
            surahCuzChips.innerHTML = `<button class="cuz-filter-chip active" data-cuz="0">Tüm Sûreler</button>`;
            for (let c = 1; c <= 30; c++) {
                const btn = document.createElement('button');
                btn.className = 'cuz-filter-chip';
                btn.setAttribute('data-cuz', c);
                btn.textContent = `${c}. Cüz`;
                surahCuzChips.appendChild(btn);
            }

            surahCuzChips.querySelectorAll('.cuz-filter-chip').forEach(chip => {
                chip.addEventListener('click', () => {
                    surahCuzChips.querySelectorAll('.cuz-filter-chip').forEach(b => b.classList.remove('active'));
                    chip.classList.add('active');
                    currentJuzFilter = parseInt(chip.getAttribute('data-cuz'), 10) || 0;
                    renderSurahListGrid();
                });
            });
        }

        // Arama Çubuğu
        if (surahSearchInput) {
            surahSearchInput.addEventListener('input', (e) => {
                surahSearchTerm = e.target.value.trim().toLowerCase();
                if (surahSearchClear) {
                    surahSearchClear.style.display = surahSearchTerm ? 'block' : 'none';
                }
                renderSurahListGrid();
            });
        }

        if (surahSearchClear) {
            surahSearchClear.addEventListener('click', () => {
                if (surahSearchInput) surahSearchInput.value = '';
                surahSearchTerm = '';
                surahSearchClear.style.display = 'none';
                renderSurahListGrid();
            });
        }

        // Modal Açma / Kapatma
        if (surahPickerBtn) {
            surahPickerBtn.addEventListener('click', () => {
                openSurahModal();
            });
        }

        if (surahModalCloseBtn) {
            surahModalCloseBtn.addEventListener('click', closeSurahModal);
        }

        surahModal.addEventListener('click', (e) => {
            if (e.target === surahModal) closeSurahModal();
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && surahModal.classList.contains('open')) {
                closeSurahModal();
            }
        });
    }

    function openSurahModal() {
        if (!surahModal) return;
        renderSurahListGrid();
        surahModal.style.display = 'flex';
        // Küçük gecikmeyle CSS animasyonunu tetikle
        requestAnimationFrame(() => {
            surahModal.classList.add('open');
            if (surahSearchInput) surahSearchInput.focus();
        });
    }

    function closeSurahModal() {
        if (!surahModal) return;
        surahModal.classList.remove('open');
        setTimeout(() => {
            surahModal.style.display = 'none';
        }, 250);
    }

    function renderSurahListGrid() {
        if (!surahListGrid || !allSurahs.length) return;

        let filtered = allSurahs;
        if (currentJuzFilter > 0) {
            filtered = filtered.filter(s => s.cuz === currentJuzFilter);
        }
        if (surahSearchTerm) {
            const normTerm = normalizeSearchText(surahSearchTerm);
            filtered = filtered.filter(s => 
                normalizeSearchText(s.tr).includes(normTerm) ||
                (s.en && normalizeSearchText(s.en).includes(normTerm)) ||
                (s.ar && s.ar.includes(surahSearchTerm)) ||
                String(s.no).includes(surahSearchTerm)
            );
        }

        surahListGrid.innerHTML = filtered.map(s => `
            <div class="surah-grid-item ${s.no === currentSurahNo ? 'active' : ''}" data-no="${s.no}">
                <div class="surah-item-left">
                    <span class="surah-item-no">${s.no}</span>
                    <div class="surah-item-text">
                        <span class="surah-item-name">${s.tr} Sûresi</span>
                        <span class="surah-item-sub">${s.cuz}. Cüz • ${s.ayets} Âyet</span>
                    </div>
                </div>
                <div class="surah-item-ar">${s.ar}</div>
            </div>
        `).join('');

        surahListGrid.querySelectorAll('.surah-grid-item').forEach(item => {
            item.addEventListener('click', () => {
                const no = parseInt(item.getAttribute('data-no'), 10);
                if (no) {
                    loadSurah(no, 1, false);
                    closeSurahModal();
                }
            });
        });
    }

    // Sûre Yükleme Motoru (Cache destekli)
    function loadSurah(surahNo, targetAyahNo = 1, autoplay = false) {
        currentSurahNo = surahNo;
        const sInfo = allSurahs.find(s => s.no === surahNo) || { no: surahNo, tr: "Sûre", ayets: 7, cuz: 1, yer: "Medenî" };

        // Üst panel başlığını güncelle
        if (currentSurahBtnTitle) {
            currentSurahBtnTitle.textContent = `${sInfo.no}. ${sInfo.tr} Sûresi (${sInfo.ayets} Âyet)`;
        }

        // Âyet Dropdown Seçeneklerini Doldur
        if (ayahSelectDropdown) {
            ayahSelectDropdown.innerHTML = '';
            for (let i = 1; i <= sInfo.ayets; i++) {
                const opt = document.createElement('option');
                opt.value = i;
                opt.textContent = `${i}. Âyet`;
                ayahSelectDropdown.appendChild(opt);
            }
        }

        if (surahCache[surahNo]) {
            currentSurahAyahs = surahCache[surahNo];
            renderAyah(targetAyahNo, autoplay);
            return;
        }

        fetch(`/data/quran/surah_${surahNo}.json`)
            .then(res => res.json())
            .then(ayahs => {
                surahCache[surahNo] = ayahs;
                currentSurahAyahs = ayahs;
                renderAyah(targetAyahNo, autoplay);
            })
            .catch(err => {
                console.error(`Sûre ${surahNo} verisi alınamadı:`, err);
            });
    }

    // Âyet Render Etme ve Senkronizasyon
    function renderAyah(ayahNo, autoplay = false) {
        if (!currentSurahAyahs || !currentSurahAyahs.length) return;

        let ayah = currentSurahAyahs.find(a => a.a === ayahNo);
        if (!ayah) ayah = currentSurahAyahs[0];
        currentAyahNo = ayah.a;

        const sInfo = allSurahs.find(s => s.no === currentSurahNo) || { tr: "Bakara", yer: "Medenî", ayets: currentSurahAyahs.length };

        // Rozetler & Künye
        if (badgeEl) badgeEl.textContent = `${sInfo.tr.toUpperCase()} SÛRESİ • ${ayah.a}. ÂYET`;
        if (juzBadgeEl) juzBadgeEl.textContent = `${ayah.c}. CÜZ • ${sInfo.yer.toUpperCase()}`;
        if (titleEl) titleEl.textContent = `${sInfo.tr} Sûresi, ${ayah.a}. Âyet`;

        // Âyet Dropdown Seçimi
        if (ayahSelectDropdown) {
            ayahSelectDropdown.value = ayah.a;
        }

        // Önceki / Sonraki Buton Durumları
        if (prevAyahBtn) {
            prevAyahBtn.disabled = (currentSurahNo === 1 && ayah.a === 1);
        }
        if (nextAyahBtn) {
            nextAyahBtn.disabled = (currentSurahNo === 114 && ayah.a === sInfo.ayets);
        }

        // Arapça Hat (Kelime spans & Tıklanabilir Dinleme)
        if (arabicEl) {
            const words = ayah.words || [];
            if (words.length > 0) {
                arabicEl.innerHTML = words.map((item, idx) => 
                    `<span class="quran-word waiting" id="qWord-${idx}" data-start="${item.s}" data-end="${item.e}" title="${item.s.toFixed(2)}s">${item.w}</span>`
                ).join(' ');

                // Kelimeye tıklayınca tam o saniyeye atla
                arabicEl.querySelectorAll('.quran-word').forEach(span => {
                    span.addEventListener('click', () => {
                        const s = parseFloat(span.getAttribute('data-start'));
                        if (!isNaN(s) && audioEl) {
                            audioEl.currentTime = s;
                            if (audioEl.paused) togglePlay();
                            updateKaraoke();
                        }
                    });
                });
            } else {
                arabicEl.textContent = ayah.ar;
            }
        }

        // Latin Transkripsiyon (Tescilli Okunuş & Canlı Kelime Takibi)
        if (latinEl) {
            const words = ayah.words || [];
            const hasLatinWords = words.length > 0 && words.some(w => w.t);
            if (hasLatinWords) {
                latinEl.innerHTML = words.map((item, idx) => 
                    `<span class="quran-latin-word waiting" id="qLatinWord-${idx}" data-start="${item.s}" data-end="${item.e}" title="${item.s.toFixed(2)}s">${item.t || ''}</span>`
                ).join(' ');

                // Latin kelimeye tıklayınca tam o saniyeye atla
                latinEl.querySelectorAll('.quran-latin-word').forEach(span => {
                    span.addEventListener('click', () => {
                        const s = parseFloat(span.getAttribute('data-start'));
                        if (!isNaN(s) && audioEl) {
                            audioEl.currentTime = s;
                            if (audioEl.paused) togglePlay();
                            updateKaraoke();
                        }
                    });
                });
            } else if (ayah.ok) {
                latinEl.textContent = ayah.ok;
            } else if (currentSurahNo === 2 && ayah.a === 255) {
                latinEl.textContent = "Allâhu lâ ilâhe illâ huve'l-hayyu'l-kayyûm, lâ te'huzuhû sinetun velâ nevm, lehû mâ fî's-semâvâti vemâ fî'l-ard, men zellezî yeşfeu indehû illâ bi-iznih...";
            } else if (currentSurahNo === 1) {
                const fatihaLatin = [
                    "Bismillâhir-rahmânir-rahîm",
                    "Elhamdulillâhi rabbil-âlemîn",
                    "Er-rahmânir-rahîm",
                    "Mâliki yevmid-dîn",
                    "İyyâke na'budu ve iyyâke neste'în",
                    "İhdinas-sırâtal-mustakîm",
                    "Sırâtallezîne en'amte aleyhim gayril-magdûbi aleyhim veled-dâllîn"
                ];
                latinEl.textContent = fatihaLatin[ayah.a - 1] || "Şeyh Mişari Râşid el-Afâsî Stüdyo Tilaveti";
            } else {
                latinEl.textContent = "Şeyh Mişari Râşid el-Afâsî • Resmi Medine Kral Fehd Mushafı";
            }
        }

        // Türkçe Meal
        if (transEl) {
            const mealText = currentMealKey === 'elm' ? (ayah.elm || ayah.diy) : (ayah.diy || ayah.elm);
            transEl.textContent = `“ ${mealText} ”`;
        }

        // Nebevî Tefekkür Notu
        if (tefekkurEl) {
            if (currentSurahNo === 2 && ayah.a === 255) {
                tefekkurEl.textContent = "Âyete'l-Kürsî; tevhidin, ilahi kudretin ve sarsılmaz ilmin Kur'an'daki en azametli ifadesidir.";
            } else {
                tefekkurEl.textContent = `${sInfo.tr} Sûresi ${ayah.a}. âyet-i kerîmesi; ilahi hikmet, tefekkür ve manevi huzurun Kur'an'daki nurlu kapısıdır.`;
            }
        }

        // Audio Kaynağı
        const wasPlaying = !audioEl.paused;
        audioEl.src = ayah.audio;
        audioEl.playbackRate = currentPlaybackSpeed;
        if (autoplay || wasPlaying) {
            audioEl.play().catch(e => console.log('Autoplay error:', e));
        }

        updateKaraoke();
    }

    // Kelime Kelime Tescilli Senkron Karaoke (video.py Mimarisi & t_eval = curTime + 0.05s)
    function updateKaraoke() {
        if (!audioEl) return;
        const curTime = audioEl.currentTime || 0;
        const durTime = audioEl.duration || 0;

        if (durTime > 0) {
            const progress = (curTime / durTime);
            if (progressFill) progressFill.style.width = `${progress * 100}%`;
            if (curTimeEl) curTimeEl.textContent = formatAudioTime(curTime);
            if (durTimeEl) durTimeEl.textContent = formatAudioTime(durTime);
        }

        const ayah = currentSurahAyahs.find(a => a.a === currentAyahNo);
        if (ayah && ayah.words && ayah.words.length > 0) {
            const totalWords = ayah.words.length;

            // Oynatma başlamamışsa ve süre sıfırsa tüm kelimeler beklesin
            if (audioEl.paused && curTime === 0) {
                for (let i = 0; i < totalWords; i++) {
                    const wEl = document.getElementById(`qWord-${i}`);
                    if (wEl && wEl.className !== 'quran-word waiting') {
                        wEl.className = 'quran-word waiting';
                    }
                    const lEl = document.getElementById(`qLatinWord-${i}`);
                    if (lEl && lEl.className !== 'quran-latin-word waiting') {
                        lEl.className = 'quran-latin-word waiting';
                    }
                }
                return;
            }

            // 50 ms (0.05s) ince görsel avans uygulanır (video.py tescilli standardı & insan algı refleksi)
            const tEval = curTime + 0.05;
            const segments = ayah.segments && ayah.segments.length > 0 ? ayah.segments : null;

            let aktifIdx = -1;
            let lastCompletedIdx = -1;

            if (segments) {
                for (let j = 0; j < segments.length; j++) {
                    const seg = segments[j];
                    const wIdx = seg[0];
                    const sSec = seg[1];
                    const eSec = seg[2];
                    if (tEval >= sSec && tEval < eSec) {
                        aktifIdx = Math.min(wIdx, totalWords - 1);
                        break;
                    } else if (tEval < sSec) {
                        aktifIdx = lastCompletedIdx;
                        break;
                    } else {
                        lastCompletedIdx = Math.min(wIdx, totalWords - 1);
                    }
                }
                if (aktifIdx === -1) {
                    aktifIdx = lastCompletedIdx >= 0 ? lastCompletedIdx : (totalWords - 1);
                }
            } else {
                for (let i = 0; i < totalWords; i++) {
                    const w = ayah.words[i];
                    if (tEval >= w.s && tEval < w.e) {
                        aktifIdx = i;
                        break;
                    } else if (tEval >= w.e) {
                        lastCompletedIdx = i;
                    }
                }
                if (aktifIdx === -1) {
                    aktifIdx = lastCompletedIdx;
                }
            }

            for (let i = 0; i < totalWords; i++) {
                const wEl = document.getElementById(`qWord-${i}`);
                const lEl = document.getElementById(`qLatinWord-${i}`);

                if (i === aktifIdx) {
                    if (wEl && wEl.className !== 'quran-word active') wEl.className = 'quran-word active';
                    if (lEl && lEl.className !== 'quran-latin-word active') lEl.className = 'quran-latin-word active';
                } else if (i < aktifIdx) {
                    if (wEl && wEl.className !== 'quran-word done') wEl.className = 'quran-word done';
                    if (lEl && lEl.className !== 'quran-latin-word done') lEl.className = 'quran-latin-word done';
                } else {
                    if (wEl && wEl.className !== 'quran-word waiting') wEl.className = 'quran-word waiting';
                    if (lEl && lEl.className !== 'quran-latin-word waiting') lEl.className = 'quran-latin-word waiting';
                }
            }
        }

        if (!audioEl.paused && !audioEl.ended) {
            karaokeRafId = requestAnimationFrame(updateKaraoke);
        }
    }

    function togglePlay() {
        if (audioEl.paused) {
            // Canlı radyo çalıyorsa sustur
            const radioAudio = document.getElementById('quranLiveRadioAudio');
            if (radioAudio && !radioAudio.paused) {
                radioAudio.pause();
                const rPlayBtn = document.getElementById('radioMainPlayBtn');
                const rWave = document.getElementById('radioWaveform');
                if (rPlayBtn) rPlayBtn.innerHTML = `<svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor"><polygon points="6 4 20 12 6 20 6 4"></polygon></svg>`;
                if (rWave) rWave.classList.remove('playing');
            }
            audioEl.play().catch(e => console.log('Audio blocked:', e));
        } else {
            audioEl.pause();
        }
    }

    playBtn.addEventListener('click', togglePlay);
    if (miniPlayBtn) {
        miniPlayBtn.addEventListener('click', togglePlay);
    }

    audioEl.addEventListener('play', () => {
        playBtn.innerHTML = `
            <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="4" width="4" height="16" rx="2"></rect>
                <rect x="14" y="4" width="4" height="16" rx="2"></rect>
            </svg>
        `;
        if (equalizer) equalizer.classList.add('playing');
        if (miniPlayBtn) {
            miniPlayBtn.innerHTML = `
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                    <rect x="6" y="4" width="4" height="16" rx="1"></rect>
                    <rect x="14" y="4" width="4" height="16" rx="1"></rect>
                </svg>
            `;
        }
        cancelAnimationFrame(karaokeRafId);
        karaokeRafId = requestAnimationFrame(updateKaraoke);
    });

    audioEl.addEventListener('pause', () => {
        playBtn.innerHTML = `
            <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
                <polygon points="6 4 20 12 6 20 6 4"></polygon>
            </svg>
        `;
        if (equalizer) equalizer.classList.remove('playing');
        if (miniPlayBtn) {
            miniPlayBtn.innerHTML = `
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                    <polygon points="6 4 18 12 6 20 6 4"></polygon>
                </svg>
            `;
        }
        cancelAnimationFrame(karaokeRafId);
        updateKaraoke();
    });

    audioEl.addEventListener('timeupdate', updateKaraoke);
    audioEl.addEventListener('seeked', updateKaraoke);

    // Âyet Bittiğinde Otomatik Akış / Tekrar Mantığı
    audioEl.addEventListener('ended', () => {
        cancelAnimationFrame(karaokeRafId);

        if (isRepeatEnabled) {
            audioEl.currentTime = 0;
            audioEl.play().catch(e => console.log('Repeat blocked:', e));
            return;
        }

        if (isAutoFlow) {
            const sInfo = allSurahs.find(s => s.no === currentSurahNo);
            const totalAyah = sInfo ? sInfo.ayets : currentSurahAyahs.length;

            if (currentAyahNo < totalAyah) {
                // Sûre içindeki sıradaki âyete geç
                renderAyah(currentAyahNo + 1, true);
            } else if (currentSurahNo < 114) {
                // Sûre bitti, bir sonraki sûrenin 1. âyetine geç
                loadSurah(currentSurahNo + 1, 1, true);
            } else {
                if (progressFill) progressFill.style.width = '0%';
                if (curTimeEl) curTimeEl.textContent = "0:00";
                updateKaraoke();
            }
        } else {
            if (progressFill) progressFill.style.width = '0%';
            if (curTimeEl) curTimeEl.textContent = "0:00";
            updateKaraoke();
        }
    });

    // İlerleme Çubuğuna Tıklama (Seek)
    if (progressTrack) {
        progressTrack.addEventListener('click', (e) => {
            const rect = progressTrack.getBoundingClientRect();
            const clickPos = (e.clientX - rect.left) / rect.width;
            if (!isNaN(audioEl.duration)) {
                audioEl.currentTime = clickPos * audioEl.duration;
            }
        });
    }

    // Âyet Gezinme Butonları
    if (prevAyahBtn) {
        prevAyahBtn.addEventListener('click', () => {
            if (currentAyahNo > 1) {
                renderAyah(currentAyahNo - 1, true);
            } else if (currentSurahNo > 1) {
                const prevSurahInfo = allSurahs.find(s => s.no === currentSurahNo - 1);
                const lastAyah = prevSurahInfo ? prevSurahInfo.ayets : 1;
                loadSurah(currentSurahNo - 1, lastAyah, true);
            }
        });
    }

    if (nextAyahBtn) {
        nextAyahBtn.addEventListener('click', () => {
            const sInfo = allSurahs.find(s => s.no === currentSurahNo);
            const totalAyah = sInfo ? sInfo.ayets : currentSurahAyahs.length;

            if (currentAyahNo < totalAyah) {
                renderAyah(currentAyahNo + 1, true);
            } else if (currentSurahNo < 114) {
                loadSurah(currentSurahNo + 1, 1, true);
            }
        });
    }

    // Âyet Seçici Dropdown
    if (ayahSelectDropdown) {
        ayahSelectDropdown.addEventListener('change', (e) => {
            const aNo = parseInt(e.target.value, 10);
            if (aNo) renderAyah(aNo, true);
        });
    }

    // Meal Seçimi
    if (mealSelect) {
        mealSelect.addEventListener('change', (e) => {
            currentMealKey = e.target.value;
            const ayah = currentSurahAyahs.find(a => a.a === currentAyahNo);
            if (ayah && transEl) {
                const mealText = currentMealKey === 'elm' ? (ayah.elm || ayah.diy) : (ayah.diy || ayah.elm);
                transEl.textContent = `“ ${mealText} ”`;
            }
        });
    }

    // Otomatik Akış Modu Toggle
    if (autoFlowBtn) {
        autoFlowBtn.addEventListener('click', () => {
            isAutoFlow = !isAutoFlow;
            autoFlowBtn.classList.toggle('active', isAutoFlow);
        });
    }

    // Hız Butonu
    if (speedBtn) {
        speedBtn.addEventListener('click', () => {
            if (currentPlaybackSpeed === 1.0) {
                currentPlaybackSpeed = 1.25;
            } else if (currentPlaybackSpeed === 1.25) {
                currentPlaybackSpeed = 1.5;
            } else {
                currentPlaybackSpeed = 1.0;
            }
            speedBtn.textContent = `${currentPlaybackSpeed.toFixed(currentPlaybackSpeed % 1 === 0 ? 0 : 2)}x`;
            audioEl.playbackRate = currentPlaybackSpeed;
        });
    }

    // Tekrar Butonu
    if (repeatBtn) {
        repeatBtn.addEventListener('click', () => {
            isRepeatEnabled = !isRepeatEnabled;
            repeatBtn.classList.toggle('active', isRepeatEnabled);
        });
    }
}

/* --- C. 30 Cüz Çoklu Hatim Takibi --- */
function initHatimTracker() {
    const gridEl = document.getElementById('hatimJuzGrid');
    const percentEl = document.getElementById('hatimPercentText');
    const countEl = document.getElementById('hatimCountText');
    const barFill = document.getElementById('hatimProgressBarFill');

    if (!gridEl) return;

    function updateHatimStats() {
        const completedCount = Object.values(completedJuzMap).filter(Boolean).length;
        const percent = Math.round((completedCount / 30) * 100);

        if (percentEl) percentEl.textContent = `%${percent}`;
        if (countEl) countEl.textContent = `${completedCount} / 30 Cüz Okundu`;
        if (barFill) barFill.style.width = `${percent}%`;
    }

    gridEl.innerHTML = '';
    for (let i = 1; i <= 30; i++) {
        const isDone = !!completedJuzMap[i];
        const box = document.createElement('div');
        box.className = `juz-box ${isDone ? 'completed' : ''}`;
        box.id = `juzBox-${i}`;
        box.setAttribute('title', `${i}. Cüz (Tıkla ve durumunu değiştir)`);
        box.innerHTML = `
            <span class="juz-number">${i}</span>
            <span class="juz-status-dot"></span>
        `;

        box.addEventListener('click', () => {
            completedJuzMap[i] = !completedJuzMap[i];
            box.classList.toggle('completed', completedJuzMap[i]);
            updateHatimStats();

            if (navigator.vibrate) {
                navigator.vibrate(20);
            }
        });

        gridEl.appendChild(box);
    }

    updateHatimStats();
}

/* --- D. 7/24 Kesintisiz Kur'an Radyosu --- */
function initQuranRadio() {
    const radioAudio = document.getElementById('quranLiveRadioAudio');
    const rPlayBtn = document.getElementById('radioMainPlayBtn');
    const rWave = document.getElementById('radioWaveform');
    const statusTitle = document.getElementById('radioStatusTitle');
    const sleepBtns = document.querySelectorAll('.sleep-btn');
    let sleepTimeoutId = null;

    if (!radioAudio || !rPlayBtn) return;

    function toggleRadio() {
        if (radioAudio.paused) {
            // Tilavet çaları çalıyorsa durdur
            const qAudio = document.getElementById('quranRecitationAudio');
            if (qAudio && !qAudio.paused) {
                qAudio.pause();
            }

            if (statusTitle) statusTitle.textContent = "Bağlanıyor...";
            radioAudio.play().then(() => {
                if (statusTitle) statusTitle.textContent = "Canlı Yayın Çalıyor";
                rPlayBtn.innerHTML = `
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor">
                        <rect x="6" y="4" width="4" height="16" rx="2"></rect>
                        <rect x="14" y="4" width="4" height="16" rx="2"></rect>
                    </svg>
                `;
                if (rWave) rWave.classList.add('playing');
            }).catch(e => {
                console.log('Radio error:', e);
                if (statusTitle) statusTitle.textContent = "Bağlantı Hatası";
            });
        } else {
            radioAudio.pause();
            if (statusTitle) statusTitle.textContent = "Yayın Duraklatıldı";
            rPlayBtn.innerHTML = `
                <svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor">
                    <polygon points="6 4 20 12 6 20 6 4"></polygon>
                </svg>
            `;
            if (rWave) rWave.classList.remove('playing');
        }
    }

    rPlayBtn.addEventListener('click', toggleRadio);

    // Uyku Zamanlayıcısı
    sleepBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            sleepBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            if (sleepTimeoutId) clearTimeout(sleepTimeoutId);
            const mins = parseInt(btn.getAttribute('data-mins'), 10);
            if (mins > 0) {
                sleepTimeoutId = setTimeout(() => {
                    if (!radioAudio.paused) {
                        radioAudio.pause();
                        if (statusTitle) statusTitle.textContent = "Uyku Zamanlayıcı Durdurdu";
                        rPlayBtn.innerHTML = `
                            <svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor">
                                <polygon points="6 4 20 12 6 20 6 4"></polygon>
                            </svg>
                        `;
                        if (rWave) rWave.classList.remove('playing');
                    }
                }, mins * 60 * 1000);
            }
        });
    });
}

function formatAudioTime(sec) {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${String(s).padStart(2, '0')}`;
}

/* ==========================================================================
   6. Sahih Hadis Külliyatı — 1.900 Riyâzü's-Sâlihîn Hadis Kütüphanesi
   ========================================================================== */
let allHadiths = [];
let currentHadithIndex = 0;
let hadithSearchDebounce = null;
let currentHadithFilterTopic = "";
let hadithSearchResults = [];
let hadithCurrentPage = 1;
const HADITHS_PER_PAGE = 8;
let hadithArabicVisible = false;

function initHadithModule() {
    const searchInput = document.getElementById('hadithSearchInput');
    const searchClearBtn = document.getElementById('hadithSearchClearBtn');
    const randomBtn = document.getElementById('btnRandomHadith');
    const topicChips = document.querySelectorAll('.hadith-topic-chip');
    const statusBar = document.getElementById('hadithSearchStatusBar');
    const statusText = document.getElementById('hadithSearchStatusText');
    const statusClose = document.getElementById('hadithSearchStatusClose');
    const resultsGrid = document.getElementById('hadithResultsGrid');
    const pagination = document.getElementById('hadithResultsPagination');
    const arabicToggleBtn = document.getElementById('hadithArabicToggleBtn');

    // 1.900 Hadis Verisini Yükle
    fetch('/data/hadith/riyazus_salihin.json')
        .then(res => res.json())
        .then(data => {
            allHadiths = data;
            // İlk Hadisi Göster (Hadis #1 / Niyet Hadisi)
            displayHadith(allHadiths[0], false);
        })
        .catch(err => {
            console.error('Hadis külliyatı yüklenemedi:', err);
        });

    // Arapça Metin Aç/Kapa Butonu
    if (arabicToggleBtn) {
        arabicToggleBtn.addEventListener('click', () => {
            hadithArabicVisible = !hadithArabicVisible;
            updateHadithArabicVisibility();
        });
    }

    // Rastgele Hadis Getir Butonu
    if (randomBtn) {
        randomBtn.addEventListener('click', () => {
            if (!allHadiths.length) return;
            const randIdx = Math.floor(Math.random() * allHadiths.length);
            currentHadithIndex = randIdx;
            displayHadith(allHadiths[randIdx], true);
        });
    }

    // Arama Çubuğu (Debounce 200ms)
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const val = e.target.value.trim();
            if (searchClearBtn) searchClearBtn.style.display = val ? 'block' : 'none';

            clearTimeout(hadithSearchDebounce);
            hadithSearchDebounce = setTimeout(() => {
                executeHadithSearch(val);
            }, 200);
        });
    }

    if (searchClearBtn) {
        searchClearBtn.addEventListener('click', () => {
            if (searchInput) searchInput.value = '';
            searchClearBtn.style.display = 'none';
            closeHadithSearchResults();
        });
    }

    if (statusClose) {
        statusClose.addEventListener('click', () => {
            closeHadithSearchResults();
        });
    }

    // Konu Çipleri
    topicChips.forEach(chip => {
        chip.addEventListener('click', () => {
            topicChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            const topic = chip.getAttribute('data-topic') || '';
            currentHadithFilterTopic = topic;

            if (!topic) {
                if (searchInput) searchInput.value = '';
                if (searchClearBtn) searchClearBtn.style.display = 'none';
                closeHadithSearchResults();
            } else {
                if (searchInput) searchInput.value = topic;
                if (searchClearBtn) searchClearBtn.style.display = 'block';
                executeHadithSearch(topic);
            }
        });
    });

    function executeHadithSearch(query) {
        if (!query || query.length < 2) {
            closeHadithSearchResults();
            return;
        }

        const normQ = normalizeSearchText(query);
        hadithSearchResults = allHadiths.filter(h => 
            (h.metin && normalizeSearchText(h.metin).includes(normQ)) ||
            (h.tam && normalizeSearchText(h.tam).includes(normQ)) ||
            (h.ravi && normalizeSearchText(h.ravi).includes(normQ)) ||
            (h.kaynak && normalizeSearchText(h.kaynak).includes(normQ)) ||
            (h.ar && h.ar.includes(query)) ||
            (h.bab && normalizeSearchText(h.bab).includes(normQ)) ||
            String(h.no) === query.trim()
        );

        hadithCurrentPage = 1;
        renderHadithResults();
    }

    function renderHadithResults() {
        if (!statusBar || !resultsGrid || !pagination) return;

        statusBar.style.display = 'flex';
        statusText.textContent = `“${searchInput ? searchInput.value : ''}” ile ilgili ${hadithSearchResults.length} sahih hadis bulundu`;

        if (hadithSearchResults.length === 0) {
            resultsGrid.style.display = 'block';
            resultsGrid.innerHTML = `<div style="text-align:center; padding: 24px; color: var(--metin-ikincil);">Aradığınız kriterlere uygun hadis bulunamadı. Lütfen farklı bir kelime deneyin.</div>`;
            pagination.style.display = 'none';
            return;
        }

        resultsGrid.style.display = 'grid';
        const startIdx = (hadithCurrentPage - 1) * HADITHS_PER_PAGE;
        const pageItems = hadithSearchResults.slice(startIdx, startIdx + HADITHS_PER_PAGE);

        resultsGrid.innerHTML = pageItems.map(item => `
            <div class="hadith-result-card" data-no="${item.no}">
                <div class="hadith-result-top">
                    <span class="hadith-result-badge">HADİS #${item.no}</span>
                    <span class="hadith-result-source">${item.kaynak ? item.kaynak.split(';')[0].slice(0, 32) : 'Riyâzü\'s-Sâlihîn'}</span>
                </div>
                <div class="hadith-result-snippet">“ ${item.metin} ”</div>
            </div>
        `).join('');

        resultsGrid.querySelectorAll('.hadith-result-card').forEach(card => {
            card.addEventListener('click', () => {
                const no = parseInt(card.getAttribute('data-no'), 10);
                const targetHadith = allHadiths.find(h => h.no === no);
                if (targetHadith) {
                    displayHadith(targetHadith, true);
                    const stage = document.getElementById('hadithDisplayStage');
                    if (stage) stage.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            });
        });

        // Sayfalama
        const totalPages = Math.ceil(hadithSearchResults.length / HADITHS_PER_PAGE);
        if (totalPages > 1) {
            pagination.style.display = 'flex';
            let pageBtnsHtml = '';
            for (let p = 1; p <= totalPages; p++) {
                if (p === 1 || p === totalPages || (p >= hadithCurrentPage - 1 && p <= hadithCurrentPage + 1)) {
                    pageBtnsHtml += `<button class="hadith-page-btn ${p === hadithCurrentPage ? 'active' : ''}" data-page="${p}">${p}</button>`;
                } else if (p === hadithCurrentPage - 2 || p === hadithCurrentPage + 2) {
                    pageBtnsHtml += `<span style="color: var(--metin-soluk); padding: 0 4px;">...</span>`;
                }
            }
            pagination.innerHTML = pageBtnsHtml;

            pagination.querySelectorAll('.hadith-page-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    hadithCurrentPage = parseInt(btn.getAttribute('data-page'), 10);
                    renderHadithResults();
                });
            });
        } else {
            pagination.style.display = 'none';
        }
    }

    function closeHadithSearchResults() {
        if (statusBar) statusBar.style.display = 'none';
        if (resultsGrid) resultsGrid.style.display = 'none';
        if (pagination) pagination.style.display = 'none';
    }
}

// Arapça Metin Görünürlük Denetimi (Başlangıçta Kapalı / Butonla Aç/Kapa)
function updateHadithArabicVisibility() {
    const arabicText = document.getElementById('hadithArabicText');
    const arabicToggleBtn = document.getElementById('hadithArabicToggleBtn');
    const arabicToggleBtnText = document.getElementById('hadithArabicToggleBtnText');

    if (!arabicText) return;
    const hasText = (arabicText.textContent || '').trim().length > 0;

    if (!hasText) {
        arabicText.style.display = 'none';
        if (arabicToggleBtn) arabicToggleBtn.style.display = 'none';
        return;
    }

    if (arabicToggleBtn) arabicToggleBtn.style.display = 'inline-flex';

    if (hadithArabicVisible) {
        arabicText.style.display = 'block';
        if (arabicToggleBtn) {
            arabicToggleBtn.classList.add('active');
            arabicToggleBtn.setAttribute('aria-pressed', 'true');
        }
        if (arabicToggleBtnText) arabicToggleBtnText.textContent = 'Arapça Metni Gizle';
    } else {
        arabicText.style.display = 'none';
        if (arabicToggleBtn) {
            arabicToggleBtn.classList.remove('active');
            arabicToggleBtn.setAttribute('aria-pressed', 'false');
        }
        if (arabicToggleBtnText) arabicToggleBtnText.textContent = 'Arapça Metni Göster';
    }
}

// Aktif Sahih Hadisi Sahnede Göster (Erime Animasyonlu)
function displayHadith(item, animate = true) {
    const stage = document.getElementById('hadithDisplayStage');
    if (!stage || !item) return;

    const noBadge = document.getElementById('hadithNumberBadge');
    const sourceBadge = document.getElementById('hadithSourceBadge');
    const raviText = document.getElementById('hadithRaviText');
    const arabicText = document.getElementById('hadithArabicText');
    const turkishText = document.getElementById('hadithTurkishText');
    const sourceFullText = document.getElementById('hadithSourceFullText');
    const expBox = document.getElementById('hadithExplanationBox');
    const expText = document.getElementById('hadithExplanationText');

    const updateDom = () => {
        if (noBadge) noBadge.textContent = `RİYÂZÜ'S-SÂLİHÎN • HADİS #${item.no} / 1.900`;
        if (sourceBadge) {
            let shortSrc = "BUHÂRÎ & MÜSLİM";
            if (item.kaynak) {
                if (item.kaynak.includes('Buhârî') && item.kaynak.includes('Müslim')) shortSrc = "BUHÂRÎ & MÜSLİM";
                else if (item.kaynak.includes('Buhârî')) shortSrc = "SAHÎH-İ BUHÂRÎ";
                else if (item.kaynak.includes('Müslim')) shortSrc = "SAHÎH-İ MÜSLİM";
                else if (item.kaynak.includes('Tirmizî')) shortSrc = "SÜNEN-İ TİRMİZÎ";
                else if (item.kaynak.includes('Ebû Dâvûd')) shortSrc = "SÜNEN-İ EBÛ DÂVÛD";
                else shortSrc = "RİYÂZÜ'S-SÂLİHÎN";
            }
            sourceBadge.textContent = shortSrc;
        }

        if (raviText) {
            raviText.textContent = item.ravi ? `${item.ravi} rivayet etti:` : "Resûlullah sallallahu aleyhi ve sellem buyurdu:";
        }

        if (arabicText) {
            arabicText.textContent = item.ar || '';
            updateHadithArabicVisibility();
        }

        if (turkishText) {
            turkishText.textContent = `“ ${item.metin} ”`;
        }

        // Nebevî Açıklama & Tam Rivayet (Açıklama / Sebebi Vürûd / Sahabi Diyaloğu)
        if (expBox && expText) {
            const tam = (item.tam || '').trim();
            const metin = (item.metin || '').trim();
            if (tam && tam.length > metin.length + 15) {
                expText.textContent = tam;
                expBox.style.display = 'block';
            } else {
                expBox.style.display = 'none';
                expText.textContent = '';
            }
        }

        if (sourceFullText) {
            sourceFullText.textContent = item.kaynak || "İmam Nevevî, Riyâzü's-Sâlihîn";
        }
    };

    if (animate) {
        stage.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
        stage.style.opacity = '0';
        stage.style.transform = 'translateY(6px)';

        setTimeout(() => {
            updateDom();
            stage.style.opacity = '1';
            stage.style.transform = 'translateY(0)';
        }, 200);
    } else {
        updateDom();
    }
}

/* ==========================================================================
   7. QR Kod Modalı
   ========================================================================== */
function initQrModal() {
    const triggers = document.querySelectorAll('.qr-modal-trigger');
    const modal = document.getElementById('qrModalBackdrop');
    const closeBtn = document.getElementById('qrModalClose');

    if (!modal) return;

    triggers.forEach(trig => {
        trig.addEventListener('click', (e) => {
            e.preventDefault();
            modal.classList.add('active');
        });
    });

    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.classList.remove('active');
        });
    }

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            modal.classList.remove('active');
        }
    });
}

/* ==========================================================================
   7.5. Google Play Kapalı Beta Modalı
   ========================================================================== */
function initBetaModal() {
    const triggers = document.querySelectorAll('.beta-modal-trigger');
    const modal = document.getElementById('betaModalBackdrop');
    const closeBtn = document.getElementById('betaModalClose');
    const dismissBtn = document.getElementById('betaModalDismissBtn');

    if (!modal) return;

    triggers.forEach(trig => {
        trig.addEventListener('click', (e) => {
            e.preventDefault();
            modal.classList.add('active');
        });
    });

    const closeModal = () => modal.classList.remove('active');

    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (dismissBtn) dismissBtn.addEventListener('click', closeModal);

    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeModal();
        }
    });
}

/* ==========================================================================
   7.8. Akıllı Cihaz Tespiti & İndirme Butonu Uyarlayıcı
   ========================================================================== */
function initSmartDeviceDownload() {
    const btn = document.getElementById('headerDownloadBtn');
    const textEl = document.getElementById('headerBtnText');
    if (!btn || !textEl) return;

    const ua = (navigator.userAgent || navigator.vendor || window.opera || '').toLowerCase();
    const isIOS = /iphone|ipad|ipod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    const isMac = /macintosh|macintel/.test(ua) && !isIOS;
    const isAndroid = /android/.test(ua);

    const appStoreUrl = "https://apps.apple.com/us/app/ezan-plus-namaz-kuran/id6769426030";

    if (isIOS || isMac) {
        btn.classList.add('device-apple');
        textEl.textContent = "App Store'dan İndir";
        btn.href = appStoreUrl;
        btn.target = "_blank";
        btn.rel = "noopener";
    } else if (isAndroid) {
        btn.classList.add('device-android');
        textEl.textContent = "Google Play (Beta)";
        btn.href = "#";
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const betaModal = document.getElementById('betaModalBackdrop');
            if (betaModal) betaModal.classList.add('active');
        });
    } else {
        // Desktop Windows, Linux vb.
        btn.classList.add('device-desktop');
        textEl.textContent = "Uygulamayı İndir";
        btn.href = "#indir";
    }
}

/* ==========================================================================
   8. Three.js Manevi 3D Işık & Altın Parçacık Sahnesi
   ========================================================================== */
function initThreeJsBackground() {
    const canvas = document.getElementById('hero3dCanvas');
    if (!canvas || typeof THREE === 'undefined') return;

    const heroSection = document.querySelector('.hero-section');
    if (!heroSection) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, heroSection.clientWidth / heroSection.clientHeight, 0.1, 1000);
    camera.position.z = 24;

    const renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
    renderer.setSize(heroSection.clientWidth, heroSection.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // Altın ve Zümrüt Manevi Parçacık Sistemi
    const particleCount = 180;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    const goldColor = new THREE.Color('#D97706');
    const greenColor = new THREE.Color('#1B4332');
    const redColor = new THREE.Color('#9B1B1B');

    for (let i = 0; i < particleCount; i++) {
        positions[i * 3] = (Math.random() - 0.5) * 45;
        positions[i * 3 + 1] = (Math.random() - 0.5) * 25;
        positions[i * 3 + 2] = (Math.random() - 0.5) * 30;

        const mixRatio = Math.random();
        const c = mixRatio > 0.65 ? goldColor : (mixRatio > 0.35 ? greenColor : redColor);
        colors[i * 3] = c.r;
        colors[i * 3 + 1] = c.g;
        colors[i * 3 + 2] = c.b;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    // Yumuşak dairesel doku
    const pCanvas = document.createElement('canvas');
    pCanvas.width = 64;
    pCanvas.height = 64;
    const pCtx = pCanvas.getContext('2d');
    const gradient = pCtx.createRadialGradient(32, 32, 0, 32, 32, 32);
    gradient.addColorStop(0, 'rgba(255,255,255,1)');
    gradient.addColorStop(0.3, 'rgba(255,255,255,0.7)');
    gradient.addColorStop(1, 'rgba(255,255,255,0)');
    pCtx.fillStyle = gradient;
    pCtx.fillRect(0, 0, 64, 64);

    const pTexture = new THREE.CanvasTexture(pCanvas);
    const material = new THREE.PointsMaterial({
        size: 0.9,
        vertexColors: true,
        transparent: true,
        opacity: 0.42,
        map: pTexture,
        blending: THREE.NormalBlending,
        depthWrite: false
    });

    const particles = new THREE.Points(geometry, material);
    scene.add(particles);

    let mouseX = 0;
    let mouseY = 0;
    let targetX = 0;
    let targetY = 0;

    window.addEventListener('mousemove', (e) => {
        mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
        mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
    }, { passive: true });

    window.addEventListener('resize', () => {
        if (!heroSection) return;
        camera.aspect = heroSection.clientWidth / heroSection.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(heroSection.clientWidth, heroSection.clientHeight);
    });

    function animate() {
        requestAnimationFrame(animate);

        targetX += (mouseX * 2.2 - targetX) * 0.03;
        targetY += (-mouseY * 1.8 - targetY) * 0.03;

        particles.rotation.y += 0.0006;
        particles.rotation.x += 0.0003;

        camera.position.x = targetX;
        camera.position.y = targetY;
        camera.lookAt(scene.position);

        renderer.render(scene, camera);
    }
    animate();
}

/* ==========================================================================
   9. İnteraktif iPhone 16 Pro 3D Tilt Motoru
   ========================================================================== */
function init3dMockupTilt() {
    const mockupWrap = document.getElementById('iphone3dWrapper');
    if (mockupWrap) {
        mockupWrap.style.transform = 'none';
    }
}

/* ==========================================================================
   10. Kartlarda Yumuşak 3D Açı & Işık Efekti (3D Tilt Cards)
   ========================================================================== */
function init3dCardTilt() {
    const cards = document.querySelectorAll('.feature-card, .live-prayer-card, .audio-player-card, .wisdom-card');

    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width - 0.5;
            const y = (e.clientY - rect.top) / rect.height - 0.5;

            const rotX = y * -8;
            const rotY = x * 8;

            card.style.transform = `perspective(800px) rotateX(${rotX.toFixed(2)}deg) rotateY(${rotY.toFixed(2)}deg) translateY(-4px)`;
        }, { passive: true });

        card.addEventListener('mouseleave', () => {
            card.style.transform = `perspective(800px) rotateX(0deg) rotateY(0deg) translateY(0)`;
        });
    });
}

/* ==========================================================================
   11. 3D Uygulama İçi Keşif Galerisi (Coverflow Motoru)
   ========================================================================== */
function initGalleryCarousel() {
    const track = document.getElementById('galleryCardsTrack');
    const cards = document.querySelectorAll('.gallery-card');
    const prevBtn = document.getElementById('galleryPrev');
    const nextBtn = document.getElementById('galleryNext');
    const dotsContainer = document.getElementById('galleryDots');
    const scene = document.querySelector('.gallery-carousel-scene');

    if (!track || cards.length === 0) return;

    let activeIdx = 0;
    const total = cards.length;
    let autoInterval = null;

    // Sayfa Noktalarını (Dots) Oluştur
    if (dotsContainer) {
        dotsContainer.innerHTML = '';
        cards.forEach((_, i) => {
            const dot = document.createElement('button');
            dot.className = `gallery-dot ${i === 0 ? 'active' : ''}`;
            dot.setAttribute('aria-label', `Ekran ${i + 1}`);
            dot.addEventListener('click', () => {
                activeIdx = i;
                updateCoverflow();
                resetAutoPlay();
            });
            dotsContainer.appendChild(dot);
        });
    }

    function updateCoverflow() {
        const dots = document.querySelectorAll('.gallery-dot');
        dots.forEach((d, i) => d.classList.toggle('active', i === activeIdx));

        const isMobile = window.innerWidth <= 768;
        const xOffset1 = isMobile ? 160 : 260;
        const xOffset2 = isMobile ? 260 : 440;
        const zOffset1 = isMobile ? -100 : -160;
        const zOffset2 = isMobile ? -180 : -300;

        cards.forEach((card, i) => {
            let diff = i - activeIdx;
            if (diff > total / 2) diff -= total;
            if (diff < -total / 2) diff += total;

            if (diff === 0) {
                card.style.transform = 'translateX(0) translateZ(0) rotateY(0deg) scale(1)';
                card.style.opacity = '1';
                card.style.zIndex = '15';
                card.style.pointerEvents = 'auto';
                card.style.filter = 'none';
            } else if (diff === 1) {
                card.style.transform = `translateX(${xOffset1}px) translateZ(${zOffset1}px) rotateY(-24deg) scale(0.86)`;
                card.style.opacity = '0.85';
                card.style.zIndex = '10';
                card.style.pointerEvents = 'auto';
                card.style.filter = 'brightness(0.92)';
            } else if (diff === -1) {
                card.style.transform = `translateX(-${xOffset1}px) translateZ(${zOffset1}px) rotateY(24deg) scale(0.86)`;
                card.style.opacity = '0.85';
                card.style.zIndex = '10';
                card.style.pointerEvents = 'auto';
                card.style.filter = 'brightness(0.92)';
            } else if (diff === 2) {
                card.style.transform = `translateX(${xOffset2}px) translateZ(${zOffset2}px) rotateY(-36deg) scale(0.72)`;
                card.style.opacity = '0.45';
                card.style.zIndex = '6';
                card.style.pointerEvents = 'auto';
                card.style.filter = 'brightness(0.8)';
            } else if (diff === -2) {
                card.style.transform = `translateX(-${xOffset2}px) translateZ(${zOffset2}px) rotateY(36deg) scale(0.72)`;
                card.style.opacity = '0.45';
                card.style.zIndex = '6';
                card.style.pointerEvents = 'auto';
                card.style.filter = 'brightness(0.8)';
            } else {
                const side = diff > 0 ? 1 : -1;
                card.style.transform = `translateX(${side * 600}px) translateZ(-500px) rotateY(${side * -45}deg) scale(0.5)`;
                card.style.opacity = '0';
                card.style.zIndex = '1';
                card.style.pointerEvents = 'none';
            }
        });
    }

    // Karta Tıklayınca Merkeze Getir
    cards.forEach((card, i) => {
        card.addEventListener('click', () => {
            if (activeIdx !== i) {
                activeIdx = i;
                updateCoverflow();
                resetAutoPlay();
            }
        });
    });

    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            activeIdx = (activeIdx - 1 + total) % total;
            updateCoverflow();
            resetAutoPlay();
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            activeIdx = (activeIdx + 1) % total;
            updateCoverflow();
            resetAutoPlay();
        });
    }

    // Dokunma (Touch/Swipe) Desteği
    let startX = 0;
    let endX = 0;
    if (scene) {
        scene.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
        }, { passive: true });

        scene.addEventListener('touchend', (e) => {
            endX = e.changedTouches[0].clientX;
            const diffX = startX - endX;
            if (Math.abs(diffX) > 40) {
                if (diffX > 0) {
                    activeIdx = (activeIdx + 1) % total;
                } else {
                    activeIdx = (activeIdx - 1 + total) % total;
                }
                updateCoverflow();
                resetAutoPlay();
            }
        }, { passive: true });
    }

    // Otomatik Döndürme
    function startAutoPlay() {
        if (autoInterval) clearInterval(autoInterval);
        autoInterval = setInterval(() => {
            activeIdx = (activeIdx + 1) % total;
            updateCoverflow();
        }, 5000);
    }

    function resetAutoPlay() {
        clearInterval(autoInterval);
        startAutoPlay();
    }

    if (scene) {
        scene.addEventListener('mouseenter', () => clearInterval(autoInterval));
        scene.addEventListener('mouseleave', () => startAutoPlay());
    }

    updateCoverflow();
    startAutoPlay();
    window.addEventListener('resize', updateCoverflow, { passive: true });
}

/* ==========================================================================
   12. SSS (Sıkça Sorulan Sorular / Accordion)
   ========================================================================== */
function initFaqAccordion() {
    const items = document.querySelectorAll('.faq-item');

    items.forEach(item => {
        const btn = item.querySelector('.faq-question-btn');
        const panel = item.querySelector('.faq-answer-panel');

        if (!btn || !panel) return;

        btn.addEventListener('click', () => {
            const isActive = item.classList.contains('active');

            // Diğer tüm açık panelleri kapat
            items.forEach(other => {
                if (other !== item) {
                    other.classList.remove('active');
                    const otherPanel = other.querySelector('.faq-answer-panel');
                    if (otherPanel) otherPanel.style.maxHeight = '0px';
                }
            });

            if (isActive) {
                item.classList.remove('active');
                panel.style.maxHeight = '0px';
            } else {
                item.classList.add('active');
                panel.style.maxHeight = panel.scrollHeight + 'px';
            }
        });
    });
}

