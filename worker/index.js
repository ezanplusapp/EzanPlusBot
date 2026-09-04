/**
 * ezan-plus-tetikleyici — Cloudflare Worker Zamanlayıcı
 * Her gün 19:45 TSİ'de (16:45 UTC) GitHub Actions'ı sıfır gecikmeyle tetikler.
 */

export default {
  async scheduled(event, env, ctx) {
    if (!env.GITHUB_PAT || !env.GITHUB_REPO) {
      console.error("GITHUB_PAT veya GITHUB_REPO eksik!");
      return;
    }

    const url = `https://api.github.com/repos/${env.GITHUB_REPO}/dispatches`;
    console.log(`[Zamanlayıcı] GitHub Actions tetikleniyor: ${env.GITHUB_REPO}`);

    const res = await fetch(url, {
      method: "POST",
      headers: {
        Accept: "application/vnd.github+json",
        Authorization: `Bearer ${env.GITHUB_PAT}`,
        "User-Agent": "EzanPlus-CloudflareWorker",
      },
      body: JSON.stringify({
        event_type: "gunluk_reels",
        client_payload: {
          tetikleyen: "cloudflare_cron",
          saat: "19:45 TSİ",
        },
      }),
    });

    console.log(`[Zamanlayıcı] Yanıt: ${res.status}`);
  },

  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Manuel test veya acil durum tetiklemesi: /tetikle
    if (url.pathname === "/tetikle") {
      if (!env.GITHUB_PAT || !env.GITHUB_REPO) {
        return new Response("Hata: GITHUB_PAT veya GITHUB_REPO ayarlanmamış.", { status: 500 });
      }

      const ghUrl = `https://api.github.com/repos/${env.GITHUB_REPO}/dispatches`;
      const res = await fetch(ghUrl, {
        method: "POST",
        headers: {
          Accept: "application/vnd.github+json",
          Authorization: `Bearer ${env.GITHUB_PAT}`,
          "User-Agent": "EzanPlus-CloudflareWorker",
        },
        body: JSON.stringify({
          event_type: "gunluk_reels",
          client_payload: {
            tetikleyen: "manuel_web",
          },
        }),
      });

      return new Response(`Reels üretimi tetiklendi! GitHub Yanıt Kodu: ${res.status}`);
    }

    return new Response(
      "🕌 Ezan Plus Reels Zamanlayıcı Servisi Aktif.\n" +
      "Her gün 19:45 TSİ'de GitHub Actions'ı sıfır gecikmeyle çalıştırır.\n" +
      "Manuel tetiklemek için /tetikle adresine istek atabilirsiniz."
    );
  },
};
