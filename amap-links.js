/* Official AMap URI App POI search; fall back to HTTPS on desktop. */
(function (root) {
  function linksFor(query, webUrl, device = {}) {
    const keyword = String(query || "").trim();
    const ua = device.userAgent || "";
    const ios = /iPhone|iPad|iPod/i.test(ua) || (device.platform === "MacIntel" && device.maxTouchPoints > 1);
    const android = /Android/i.test(ua);
    if (!keyword || (!ios && !android)) return { primaryUrl: webUrl, webUrl, isApp: false };
    const params = new URLSearchParams({ sourceApplication: "travelplan", [ios ? "name" : "keywords"]: keyword, dev: "0" });
    return { primaryUrl: `${ios ? "iosamap" : "androidamap"}://poi?${params.toString().replace(/\+/g, "%20")}`, webUrl, isApp: true };
  }
  root.TravelAmap = Object.freeze({ linksFor });
})(globalThis);
