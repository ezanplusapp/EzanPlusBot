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
    initThreeJsBackground();
    init3dMockupTilt();
    init3dCardTilt();
    initMockupTabs();
    initInteractiveDhikr();
    initLivePrayerTimes();
    initAudioPlayer();
    initWisdomRotator();
    initQrModal();
});

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
   2. İnteraktif iPhone Mockup Sekmeleri
   ========================================================================== */
function initMockupTabs() {
    const tabButtons = document.querySelectorAll('.mockup-tab-btn');
    const screens = document.querySelectorAll('.mockup-screen-content');

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

    // Geri sayım formatla (02:45:12)
    const kSaat = Math.floor(kalanSaniye / 3600);
    const kDakika = Math.floor((kalanSaniye % 3600) / 60);
    const kSaniye = kalanSaniye % 60;
    const formatliSure = `${String(kSaat).padStart(2, '0')}:${String(kDakika).padStart(2, '0')}:${String(kSaniye).padStart(2, '0')}`;

    const countdownEl = document.getElementById('liveCountdownTimer');
    const countdownLabelEl = document.getElementById('liveCountdownLabel');
    if (countdownEl) countdownEl.textContent = formatliSure;
    if (countdownLabelEl) countdownLabelEl.textContent = `${siradakiVakit.tr} Vaktine Kalan Süre`;

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
   5. İnteraktif Tilavet & Audio Player
   ========================================================================== */
function initAudioPlayer() {
    const playBtn = document.getElementById('btnPlayRecitation');
    const audioEl = document.getElementById('recitationAudio');
    const progressBar = document.getElementById('audioProgressBar');
    const progressFill = document.getElementById('audioProgressFill');
    const curTimeEl = document.getElementById('audioCurTime');
    const durTimeEl = document.getElementById('audioDurTime');
    const eqBars = document.getElementById('equalizerBars');

    if (!playBtn || !audioEl) return;

    function togglePlay() {
        if (audioEl.paused) {
            audioEl.play().catch(e => console.log('Audio autoplay blocked:', e));
        } else {
            audioEl.pause();
        }
    }

    playBtn.addEventListener('click', togglePlay);

    // Mockup içindeki küçük oynat butonu da aynı sesi çalsın
    const miniPlayBtn = document.getElementById('miniPlayBtn');
    if (miniPlayBtn) {
        miniPlayBtn.addEventListener('click', togglePlay);
    }

    audioEl.addEventListener('play', () => {
        playBtn.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="4" width="4" height="16" rx="2"></rect>
                <rect x="14" y="4" width="4" height="16" rx="2"></rect>
            </svg>
        `;
        if (eqBars) eqBars.classList.add('playing');
        if (miniPlayBtn) {
            miniPlayBtn.innerHTML = `
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                    <rect x="6" y="4" width="4" height="16" rx="1"></rect>
                    <rect x="14" y="4" width="4" height="16" rx="1"></rect>
                </svg>
            `;
        }
    });

    audioEl.addEventListener('pause', () => {
        playBtn.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <polygon points="5 3 19 12 5 21 5 3"></polygon>
            </svg>
        `;
        if (eqBars) eqBars.classList.remove('playing');
        if (miniPlayBtn) {
            miniPlayBtn.innerHTML = `
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                    <polygon points="6 4 18 12 6 20 6 4"></polygon>
                </svg>
            `;
        }
    });

    audioEl.addEventListener('timeupdate', () => {
        if (!isNaN(audioEl.duration) && audioEl.duration > 0) {
            const percent = (audioEl.currentTime / audioEl.duration) * 100;
            if (progressFill) progressFill.style.width = `${percent}%`;

            if (curTimeEl) curTimeEl.textContent = formatAudioTime(audioEl.currentTime);
            if (durTimeEl) durTimeEl.textContent = formatAudioTime(audioEl.duration);
        }
    });

    audioEl.addEventListener('ended', () => {
        if (progressFill) progressFill.style.width = '0%';
        if (curTimeEl) curTimeEl.textContent = "0:00";
    });

    if (progressBar) {
        progressBar.addEventListener('click', (e) => {
            const rect = progressBar.getBoundingClientRect();
            const clickPos = (e.clientX - rect.left) / rect.width;
            if (!isNaN(audioEl.duration)) {
                audioEl.currentTime = clickPos * audioEl.duration;
            }
        });
    }
}

function formatAudioTime(sec) {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${String(s).padStart(2, '0')}`;
}

/* ==========================================================================
   6. Günün Hikmeti & Tescilli Külliyat Rotatoru
   ========================================================================== */
const TESCİLLİ_KÜLLİYAT = [
    {
        kategori: "hadis",
        ar: "مَنْ لَا يَرْحَمِ النَّاسَ لَا يَرْحَمْهُ اللَّهُ",
        tr: "“ İnsanlara merhamet etmeyene, Allah da merhamet etmez. ”",
        kaynak: "RİYÂZÜ'S-SÂLİHÎN • BUHÂRÎ & MÜSLİM",
        tefekkur: "İslam ahlakı; insanlara şefkatle muamele etmeyi ve merhameti hayatın merkezine koymayı öğütler."
    },
    {
        kategori: "ayet",
        ar: "فَإِنَّ مَعَ الْعُسْرِ يُسْرًا • إِنَّ مَعَ الْعُسْرِ يُسْرًا",
        tr: "“ Elbette zorlukla beraber bir kolaylık vardır. Gerçekten zorlukla beraber bir kolaylık vardır. ”",
        kaynak: "İNŞİRÂH SÛRESİ • 5-6. ÂYET",
        tefekkur: "Hayatın en çetin imtihanlarında dahi ilahi rahmet kapıdadır; sabır, ferahlığın anahtarıdır."
    },
    {
        kategori: "dua",
        ar: "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ",
        tr: "“ Ey Rabbimiz! Bize dünyada da iyilik ver, ahirette de iyilik ver. Ve bizi cehennem azabından koru. ”",
        kaynak: "BAKARA SÛRESİ • 201. ÂYET",
        tefekkur: "Dünya ile ahiret dengesini mükemmel bir ahenkle birleştiren en kapsamlı nebevî münacattır."
    },
    {
        kategori: "hadis",
        ar: "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ",
        tr: "“ Ameller ancak niyetlere göredir. Herkes için niyet ettiği ne ise o vardır. ”",
        kaynak: "RİYÂZÜ'S-SÂLİHÎN • BUHÂRÎ, BED'Ü'L-VAHY 1",
        tefekkur: "Amellerin manevi ağırlığını ve değerini belirleyen tek ölçü; kalbin samimiyeti ve ihlasıdır."
    },
    {
        kategori: "ayet",
        ar: "أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ",
        tr: "“ Bilesiniz ki kalpler ancak Allah'ı anmakla huzur ve sükûna kavuşur. ”",
        kaynak: "RA'D SÛRESİ • 28. ÂYET",
        tefekkur: "Ruhun aradığı gerçek dinginlik ne dünyalık meşgalelerde ne de maddiyattadır; yalnız Hakk'ın zikrindendir."
    }
];

let aktifKategori = "hepsi";
let hikmetIndex = 0;

function initWisdomRotator() {
    const tabBtns = document.querySelectorAll('.wisdom-tab-btn');
    const refreshBtn = document.getElementById('btnRefreshWisdom');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            aktifKategori = btn.getAttribute('data-kat');
            hikmetGoster(true);
        });
    });

    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            hikmetIndex = (hikmetIndex + 1) % TESCİLLİ_KÜLLİYAT.length;
            hikmetGoster(false);
        });
    }

    hikmetGoster(false);
}

function hikmetGoster(kategoriDegisti) {
    const contentBox = document.getElementById('wisdomContentBox');
    if (!contentBox) return;

    let uygunHavuz = TESCİLLİ_KÜLLİYAT;
    if (aktifKategori !== "hepsi") {
        uygunHavuz = TESCİLLİ_KÜLLİYAT.filter(item => item.kategori === aktifKategori);
    }
    if (uygunHavuz.length === 0) uygunHavuz = TESCİLLİ_KÜLLİYAT;

    const item = uygunHavuz[hikmetIndex % uygunHavuz.length];

    // Pürüzsüz erime (Fade) animasyonu
    contentBox.style.opacity = '0';
    setTimeout(() => {
        const arEl = document.getElementById('wisdomArabic');
        const quoteEl = document.getElementById('wisdomQuote');
        const sourceEl = document.getElementById('wisdomSource');
        const tefekkurEl = document.getElementById('wisdomTefekkur');

        if (arEl) arEl.textContent = item.ar;
        if (quoteEl) quoteEl.textContent = item.tr;
        if (sourceEl) sourceEl.textContent = item.kaynak;
        if (tefekkurEl) tefekkurEl.textContent = `“ ${item.tefekkur} ”`;

        contentBox.style.opacity = '1';
    }, 250);
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
    const container = document.querySelector('.hero-section');
    const glare = document.querySelector('.mockup-glare');
    if (!mockupWrap || !container) return;

    let currentX = 0;
    let currentY = 0;
    let targetX = 0;
    let targetY = 0;
    let isHovered = false;

    container.addEventListener('mousemove', (e) => {
        isHovered = true;
        const rect = container.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width;
        const y = (e.clientY - rect.top) / rect.height;

        targetX = (y - 0.5) * -22; // rotateX
        targetY = (x - 0.5) * 26;  // rotateY

        if (glare) {
            const angle = Math.atan2(y - 0.5, x - 0.5) * (180 / Math.PI) + 90;
            glare.style.background = `linear-gradient(${angle}deg, rgba(255, 255, 255, 0.35) 0%, rgba(255, 255, 255, 0.04) 40%, transparent 70%)`;
        }
    }, { passive: true });

    container.addEventListener('mouseleave', () => {
        isHovered = false;
        targetX = 0;
        targetY = 0;
    });

    function updateTilt() {
        requestAnimationFrame(updateTilt);
        currentX += (targetX - currentX) * 0.08;
        currentY += (targetY - currentY) * 0.08;

        mockupWrap.style.transform = `rotateX(${currentX.toFixed(2)}deg) rotateY(${currentY.toFixed(2)}deg)`;
    }
    updateTilt();
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

