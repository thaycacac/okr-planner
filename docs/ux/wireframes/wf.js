// Bilingual wireframe labels: every label is authored as "tiếng Việt¦English".
// ?lang=en (or the header toggle) switches the rendered language.
(function () {
  const SEP = "\u00a6";
  const original = new WeakMap();
  const ATTRS = ["placeholder", "title", "aria-label"];

  // Whole text node "vi¦en", or inline "{vi¦en}" when a node mixes several labels.
  const INLINE = /\{([^{}¦]*)¦([^{}]*)\}/g;
  function pick(text, lang) {
    if (text.indexOf(SEP) === -1) return text;
    if (/\{[^{}]*¦[^{}]*\}/.test(text)) {
      return text.replace(INLINE, function (_, vi, en) { return lang === "en" ? en : vi; });
    }
    const parts = text.split(SEP);
    return lang === "en" ? parts[1] : parts[0];
  }

  function apply(lang) {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) {
      if (!original.has(node)) {
        if (node.nodeValue.indexOf(SEP) === -1) continue;
        original.set(node, node.nodeValue);
      }
      node.nodeValue = pick(original.get(node), lang);
    }
    document.querySelectorAll("*").forEach(function (el) {
      ATTRS.forEach(function (a) {
        const key = "data-orig-" + a;
        if (!el.hasAttribute(key) && el.hasAttribute(a) && el.getAttribute(a).indexOf(SEP) !== -1) {
          el.setAttribute(key, el.getAttribute(a));
        }
        if (el.hasAttribute(key)) el.setAttribute(a, pick(el.getAttribute(key), lang));
      });
    });
    document.documentElement.lang = lang;
    document.querySelectorAll(".langseg").forEach(function (s) {
      s.children[0].classList.toggle("on", lang === "vi");
      s.children[1].classList.toggle("on", lang === "en");
    });
    document.querySelectorAll("[data-lang-btn]").forEach(function (b) {
      b.classList.toggle("on", b.getAttribute("data-lang-btn") === lang);
    });
  }

  window.setLang = function (lang) {
    const url = new URL(location.href);
    url.searchParams.set("lang", lang);
    history.replaceState(null, "", url);
    apply(lang);
  };

  const FEAS = {
    ok: '<span class="feas-pill ok"><span class="sym ok" style="width:16px;height:16px;font-size:10px">✓</span>Khả thi¦Feasible</span>',
    warn: '<span class="feas-pill warn"><span class="sym warn" style="width:16px;height:16px;font-size:10px">!</span>Sát – dùng buffer¦Tight – using buffer</span>',
    err: '<span class="feas-pill err"><span class="sym err" style="width:16px;height:16px;font-size:10px">×</span>Quá tải – thiếu 58h¦Overloaded – 58h short</span>',
    loading: '<span class="feas-pill" style="color:#64748b;border-color:#e2e8f0"><span class="spin"></span>Đang tính…¦Calculating…</span>',
    stale: '<span class="feas-pill" style="color:#78350f;background:#fffbeb;border-color:#fcd34d;border-style:dashed">⟳ Cần xếp lại¦Needs rescheduling</span>',
    none: ""
  };

  function topbar(el) {
    const feas = FEAS[el.getAttribute("data-topbar") || "none"];
    const q = el.getAttribute("data-quarter") || "Q4/2026";
    el.classList.add("topbar");
    el.innerHTML =
      '<span class="logo">OKR Planner</span>' +
      '<span class="select" style="height:32px;margin-left:12px;font-weight:700">' + q + "</span>" +
      '<span class="spacer"></span>' + feas +
      '<span class="seg langseg" style="margin-left:8px"><span class="on">VI</span><span>EN</span></span>' +
      '<span class="btn ghost sm">Đăng xuất¦Sign out</span>';
  }

  function sidebar(el) {
    const on = el.getAttribute("data-sidebar");
    const mvp = el.hasAttribute("data-mvp");
    const items = [
      ["okr", "Kế hoạch OKR¦OKR plan", false],
      ["tasks", "Công việc¦Tasks", false],
      ["calendar", "Lịch¦Calendar", false],
      ["workload", "Workload¦Workload", true],
      ["quarters", "Quản lý quý¦Quarters", true],
      ["settings", "Cài đặt¦Settings", false]
    ];
    el.classList.add("sidebar");
    el.innerHTML =
      items.filter(function (i) { return !(mvp && i[2]); }).map(function (i) {
        return '<div class="item' + (i[0] === on ? " on" : "") + '">' + i[1] + "</div>";
      }).join("") +
      '<div style="flex:1"></div><div class="item small muted' + (on === "policy" ? " on" : "") + '">Chính sách dữ liệu¦Data policy</div>';
  }

  function tabbar(el) {
    const on = el.getAttribute("data-tabbar");
    // Wave 2 folds Workload / Quarters / Settings / Data policy into a "More" tab.
    const last = el.hasAttribute("data-w2") ? ["more", "Thêm¦More"] : ["settings", "Cài đặt¦Settings"];
    const items = [["okr", "OKR"], ["tasks", "Công việc¦Tasks"], ["calendar", "Lịch¦Calendar"], last];
    el.classList.add("tabbar");
    el.innerHTML = items.map(function (i) {
      return '<div class="' + (i[0] === on ? "on" : "") + '">' + i[1] + "</div>";
    }).join("");
  }

  function browser(el) {
    el.classList.add("browserbar");
    el.innerHTML = "<i></i><i></i><i></i><span class=\"url\">okr-planner.local" + (el.getAttribute("data-browser") || "/") + "</span>";
  }

  function mstatus(el) {
    el.classList.add("statusbar");
    el.innerHTML = "<span>9:41</span><span>●●● ▮</span>";
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-topbar]").forEach(topbar);
    document.querySelectorAll("[data-sidebar]").forEach(sidebar);
    document.querySelectorAll("[data-tabbar]").forEach(tabbar);
    document.querySelectorAll("[data-browser]").forEach(browser);
    document.querySelectorAll("[data-mstatus]").forEach(mstatus);
    const lang = new URLSearchParams(location.search).get("lang") === "en" ? "en" : "vi";
    apply(lang);
  });
})();
