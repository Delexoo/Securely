(function () {
  var header = document.getElementById("siteHeader");
  var toggle = document.getElementById("menuToggle");
  var nav = document.getElementById("mainNav");

  if (header) {
    window.addEventListener("scroll", function () {
      if (window.scrollY > 8) {
        header.classList.add("scrolled");
      } else {
        header.classList.remove("scrolled");
      }
    });
  }

  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("mobile-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.textContent = open ? "✕" : "☰";
    });

    nav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        nav.classList.remove("mobile-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.textContent = "☰";
      });
    });
  }

  /* Interactive threat demo (demo page only — home uses blurred preview + link to demo.html) */
  var demoRoot = document.getElementById("securelyThreatDemo");
  if (demoRoot && !demoRoot.classList.contains("threat-figure--home-preview")) {
    var scenarios = {
      email: {
        title: "Action required: Payroll deposit verification",
        bodyHtml:
          '<div class="threat-demo-email-headers">' +
          '<p class="threat-demo-line"><span class="threat-demo-k">From</span> Human Resources &lt;no-reply@acme-payroll-portal.net&gt;</p>' +
          '<p class="threat-demo-line"><span class="threat-demo-k">To</span> you@company.com</p>' +
          '<p class="threat-demo-line threat-demo-line-meta">Sent today, 4:12 PM</p>' +
          "</div>" +
          '<hr class="threat-demo-divider" aria-hidden="true" />' +
          '<div class="threat-demo-prose">' +
          "<p>Our payroll partner flagged an incomplete direct-deposit profile before this Friday’s run.</p>" +
          "<p>Please confirm your routing and account numbers using the secure portal below. If this is not completed by 5:00 PM ET, deposits may post as a paper check on the following cycle.</p>" +
          '<p class="threat-demo-cta-line"><a href="#" class="threat-demo-link">Review &amp; confirm payroll settings</a></p>' +
          '<p class="threat-demo-url-wrap"><a href="#" class="threat-demo-link threat-demo-url" title="Demo link (does not leave this page)">https://acme-payroll-portal.net/employee/update?ref=PR-2025-03-19&amp;tkn=7k2…</a></p>' +
          '<p class="threat-demo-footnote">Questions? Contact Payroll Services at ext. 4400. Do not reply to this message.</p>' +
          "</div>",
        meta: "Outlook · Inbox · Today, 4:12 PM",
        scanResult: "Malicious",
      },
      sms: {
        title: "New text message",
        bodyHtml:
          '<div class="threat-demo-sms">' +
          '<p class="threat-demo-sms-label">CHASE (auto)</p>' +
          "<p>Unusual activity on card ending in <strong>4821</strong>. A <strong>$529.42</strong> charge at <strong>TARGET T-2841</strong> was declined in Brooklyn, NY.</p>" +
          "<p>If this wasn’t you, secure your account immediately:</p>" +
          '<p class="threat-demo-url-wrap"><a href="#" class="threat-demo-link threat-demo-url" title="Demo link (does not leave this page)">https://chase-secure-alerts.net/verify?id=8K2m9x</a> <span class="threat-demo-muted">(tap to open)</span></p>' +
          '<p class="threat-demo-footnote">Did you make this purchase? Reply <strong>YES</strong> to confirm. Msg &amp; data rates may apply. <a href="#" class="threat-demo-link threat-demo-link-inline">STOP</a> to opt out.</p>' +
          "</div>",
        meta: "Messages · +1 (872) 555-0142 · Now",
        scanResult: "Malicious",
      },
      browser: {
        title: "Unusual sign-in activity",
        bodyHtml:
          '<div class="threat-demo-browser-chrome" role="presentation">' +
          '<span class="threat-demo-lock" aria-hidden="true"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M7 11V8a5 5 0 0 1 10 0v3" stroke="#3fb950" stroke-width="2" stroke-linecap="round"/><rect x="5" y="11" width="14" height="10" rx="2" stroke="#3fb950" stroke-width="2"/></svg></span>' +
          '<a href="#" class="threat-demo-link threat-demo-url threat-demo-addr" title="Demo link (does not leave this page)">https://account.microsoft.com/security</a>' +
          "</div>" +
          '<div class="threat-demo-prose threat-demo-signin">' +
          '<p class="threat-demo-brand">Microsoft account</p>' +
          '<h4 class="threat-demo-signin-title">Unusual sign-in activity</h4>' +
          "<p>We noticed a sign-in from a new device and location. If this was you, you can ignore this message. If not, another user may have accessed your account.</p>" +
          "<p>For your protection, change your password now so your email, files, and apps stay under your control.</p>" +
          '<p class="threat-demo-cta-line"><a href="#" class="threat-demo-link">Change your password</a></p>' +
          '<p class="threat-demo-trust"><span class="threat-demo-trust-dot"></span><span class="threat-demo-trust-copy">You are on account.microsoft.com · TLS 1.3 · Certificate issued to Microsoft Corporation</span></p>' +
          '<p class="threat-demo-footnote">This notice was generated automatically. Reference ID: SEC-ALERT-4281.</p>' +
          "</div>",
        meta: "Microsoft Edge · Active tab",
        scanResult: "Safe",
      },
      downloads: {
        title: "Downloads, 2 items",
        bodyHtml:
          '<div class="threat-demo-downloads">' +
          '<p class="threat-dl-toolbar">Today, 2:14 PM · Sorted by date</p>' +
          '<div class="threat-dl-card">' +
          '<p class="threat-dl-name"><a href="#" class="threat-demo-link threat-dl-file">RobloxPlayerInstaller.exe</a></p>' +
          "<p class=\"threat-dl-meta\">54.2 MB · Digital signature: ROBLOX Corporation · Completed 2:08 PM</p>" +
          "</div>" +
          '<div class="threat-dl-card threat-dl-card-warn">' +
          '<p class="threat-dl-name"><a href="#" class="threat-demo-link threat-dl-file">Autoclicker.exe</a></p>' +
          "<p class=\"threat-dl-meta\">1.2 MB · Publisher: Unknown · SmartScreen: Not commonly downloaded · Completed 2:14 PM</p>" +
          '<p class="threat-dl-source">Source: <a href="#" class="threat-demo-link threat-demo-url">https://cdn.free-game-tools.net/bundle_FreeRobuxHelper.zip</a></p>' +
          "</div>" +
          '<p class="threat-dl-path">Location: <a href="#" class="threat-demo-link">C:\\Users\\You\\Downloads</a></p>' +
          "</div>",
        meta: "File Explorer · Downloads · Today",
        scanResult: "Malicious",
      },
    };

    var widgetEl = document.getElementById("threatDemoWidget");
    var titleEl = document.getElementById("threatDemoTitle");
    var bodyEl = document.getElementById("threatDemoBody");
    var metaEl = document.getElementById("threatDemoMeta");
    var toastsEl = document.getElementById("threatDemoToasts");
    var quickScanBtn = document.getElementById("threatDemoQuickScan");
    var pickerBtns = demoRoot.querySelectorAll(".threat-demo-picker-btn");
    var currentKey = "email";
    var stageEl = document.getElementById("threatDemoStage");
    var floatingEl = document.getElementById("threatDemoFloating");
    var dragHandleEl = document.getElementById("threatDemoDragHandle");

    demoRoot.addEventListener("click", function (e) {
      if (e.target.closest("a.threat-demo-link")) {
        e.preventDefault();
      }
    });

    function clampNum(n, a, b) {
      return Math.min(Math.max(n, a), b);
    }

    function demoTopInsetPx() {
      var vw = window.innerWidth || document.documentElement.clientWidth || 0;
      if (vw <= 640) {
        return clampNum(vw * 0.025, 8, 20);
      }
      return clampNum(vw * 0.026, 10, 26);
    }

    function setFloatingPosition(left, top) {
      if (!stageEl || !floatingEl) return;
      var fw = floatingEl.offsetWidth;
      var fh = floatingEl.offsetHeight;
      var sw = stageEl.clientWidth;
      var sh = stageEl.clientHeight;
      var maxL = Math.max(0, sw - fw);
      var maxT = Math.max(0, sh - fh);
      floatingEl.style.left = clampNum(left, 0, maxL) + "px";
      floatingEl.style.top = clampNum(top, 0, maxT) + "px";
      floatingEl.style.right = "auto";
      floatingEl.style.marginLeft = "0";
      floatingEl.style.marginRight = "0";
      floatingEl.style.bottom = "auto";
      floatingEl.style.transform = "none";
    }

    function initFloatingPosition() {
      if (!stageEl || !floatingEl) return;
      window.requestAnimationFrame(function () {
        var fh = floatingEl.offsetHeight;
        if (!fh) return;
        floatingEl.style.left = "";
        floatingEl.style.right = "";
        floatingEl.style.marginLeft = "";
        floatingEl.style.marginRight = "";
        floatingEl.style.bottom = "auto";
        floatingEl.style.transform = "none";
        var sh = stageEl.clientHeight;
        var maxT = Math.max(0, sh - fh);
        floatingEl.style.top =
          clampNum(demoTopInsetPx(), 0, maxT) + "px";
      });
    }

    function reclampFloating() {
      if (!stageEl || !floatingEl) return;
      if (!floatingEl.style.left) {
        var fh = floatingEl.offsetHeight;
        var sh = stageEl.clientHeight;
        var maxT = Math.max(0, sh - fh);
        floatingEl.style.top =
          clampNum(demoTopInsetPx(), 0, maxT) + "px";
        return;
      }
      var left = parseFloat(floatingEl.style.left);
      var top = parseFloat(floatingEl.style.top);
      if (isNaN(left) || isNaN(top)) return;
      setFloatingPosition(left, top);
    }

    var dragPointerId = null;
    var dragOffsetX = 0;
    var dragOffsetY = 0;

    if (dragHandleEl && stageEl && floatingEl) {
      dragHandleEl.style.cursor = "grab";

      dragHandleEl.addEventListener("pointerdown", function (e) {
        if (e.button !== 0) return;
        e.preventDefault();
        var sr = stageEl.getBoundingClientRect();
        var fr = floatingEl.getBoundingClientRect();
        if (!floatingEl.style.left) {
          setFloatingPosition(fr.left - sr.left, fr.top - sr.top);
          fr = floatingEl.getBoundingClientRect();
        }
        dragPointerId = e.pointerId;
        dragOffsetX = e.clientX - fr.left;
        dragOffsetY = e.clientY - fr.top;
        dragHandleEl.setPointerCapture(e.pointerId);
        dragHandleEl.style.cursor = "grabbing";
      });

      dragHandleEl.addEventListener("pointermove", function (e) {
        if (dragPointerId == null || e.pointerId !== dragPointerId) return;
        var sr = stageEl.getBoundingClientRect();
        setFloatingPosition(
          e.clientX - sr.left - dragOffsetX,
          e.clientY - sr.top - dragOffsetY
        );
      });

      function endThreatDrag(e) {
        if (dragPointerId == null || e.pointerId !== dragPointerId) return;
        dragPointerId = null;
        dragHandleEl.style.cursor = "grab";
        try {
          dragHandleEl.releasePointerCapture(e.pointerId);
        } catch (ignore) {}
      }

      dragHandleEl.addEventListener("pointerup", endThreatDrag);
      dragHandleEl.addEventListener("pointercancel", endThreatDrag);

      dragHandleEl.addEventListener("keydown", function (e) {
        var step = e.shiftKey ? 24 : 8;
        var left = parseFloat(floatingEl.style.left);
        var top = parseFloat(floatingEl.style.top);
        if (isNaN(left)) {
          if (
            e.key === "ArrowLeft" ||
            e.key === "ArrowRight" ||
            e.key === "ArrowUp" ||
            e.key === "ArrowDown"
          ) {
            e.preventDefault();
            var sr = stageEl.getBoundingClientRect();
            var fr = floatingEl.getBoundingClientRect();
            var nl = fr.left - sr.left;
            var nt = isNaN(top) ? demoTopInsetPx() : top;
            if (e.key === "ArrowLeft") setFloatingPosition(nl - step, nt);
            else if (e.key === "ArrowRight") setFloatingPosition(nl + step, nt);
            else if (e.key === "ArrowUp") setFloatingPosition(nl, nt - step);
            else if (e.key === "ArrowDown") setFloatingPosition(nl, nt + step);
          }
          return;
        }
        if (isNaN(top)) return;
        if (e.key === "ArrowLeft") {
          e.preventDefault();
          setFloatingPosition(left - step, top);
        } else if (e.key === "ArrowRight") {
          e.preventDefault();
          setFloatingPosition(left + step, top);
        } else if (e.key === "ArrowUp") {
          e.preventDefault();
          setFloatingPosition(left, top - step);
        } else if (e.key === "ArrowDown") {
          e.preventDefault();
          setFloatingPosition(left, top + step);
        }
      });
    }

    var stageImg = stageEl && stageEl.querySelector(".threat-figure-bg");
    if (stageImg) {
      stageImg.addEventListener("load", function () {
        reclampFloating();
      });
    }

    window.addEventListener("resize", function () {
      reclampFloating();
    });

    function applyScenario(key) {
      var s = scenarios[key];
      if (!s) return;
      currentKey = key;
      titleEl.textContent = s.title;
      bodyEl.innerHTML = s.bodyHtml;
      metaEl.textContent = s.meta;
      if (widgetEl) {
        widgetEl.classList.toggle("is-download-files", key === "downloads");
      }
      toastsEl.innerHTML = "";
      pickerBtns.forEach(function (btn) {
        var on = btn.getAttribute("data-demo-scenario") === key;
        btn.classList.toggle("is-active", on);
        btn.setAttribute("aria-pressed", on ? "true" : "false");
      });
    }

    function pushToast(message) {
      var row = document.createElement("div");
      row.className = "threat-demo-toast";
      row.innerHTML =
        '<div class="threat-demo-toast-icon" aria-hidden="true"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div>' +
        '<div class="threat-demo-toast-body"><span class="threat-demo-toast-label">Securely</span><p class="threat-demo-toast-msg"></p></div>' +
        '<button type="button" class="threat-demo-toast-dismiss" aria-label="Dismiss notification">×</button>';
      row.querySelector(".threat-demo-toast-msg").textContent = message;
      var dismiss = row.querySelector(".threat-demo-toast-dismiss");
      dismiss.addEventListener("click", function () {
        row.remove();
      });
      toastsEl.appendChild(row);
      while (toastsEl.children.length > 4) {
        toastsEl.removeChild(toastsEl.firstChild);
      }
      window.setTimeout(function () {
        if (row.parentNode === toastsEl) row.remove();
      }, 8000);
    }

    pickerBtns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var key = btn.getAttribute("data-demo-scenario");
        applyScenario(key);
      });
    });

    if (quickScanBtn) {
      quickScanBtn.addEventListener("click", function () {
        var s = scenarios[currentKey];
        if (s) pushToast(s.scanResult);
      });
    }

    applyScenario("email");
    initFloatingPosition();
  }
})();

/* Scroll-triggered reveals (staggered groups + single elements) */
(function () {
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var opts = { threshold: 0.12, rootMargin: "0px 0px -28px 0px" };

  function showAll() {
    document.querySelectorAll(".sr-stagger, .sr").forEach(function (el) {
      el.classList.add("is-in");
    });
  }

  if (reduce) {
    showAll();
    return;
  }

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-in");
      io.unobserve(entry.target);
    });
  }, opts);

  document.querySelectorAll(".sr-stagger").forEach(function (el) {
    io.observe(el);
  });

  document.querySelectorAll(".sr").forEach(function (el) {
    if (el.closest(".sr-stagger")) return;
    io.observe(el);
  });
})();

/* Thin reading-progress bar (decorative; skipped when reduced motion is on) */
(function () {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  var bar = document.createElement("div");
  bar.className = "scroll-progress";
  bar.setAttribute("aria-hidden", "true");
  document.body.appendChild(bar);

  function update() {
    var root = document.documentElement;
    var scrollTop = root.scrollTop || document.body.scrollTop;
    var maxScroll = Math.max(1, root.scrollHeight - root.clientHeight);
    bar.style.transform = "scaleX(" + Math.min(1, scrollTop / maxScroll) + ")";
  }

  window.addEventListener("scroll", update, { passive: true });
  window.addEventListener("resize", update, { passive: true });
  update();
})();

/* Smooth eased scrolling (wheel / trackpad); native scroll if reduced motion or no Lenis */
(function initLenisSmoothScroll() {
  if (typeof Lenis === "undefined") return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  var rawNav = getComputedStyle(document.documentElement).getPropertyValue("--nav-h").trim();
  var navH = parseInt(rawNav, 10);
  if (isNaN(navH)) navH = 64;
  var navOffset = navH + 12;

  new Lenis({
    autoRaf: true,
    smoothWheel: true,
    lerp: 0.035,
    wheelMultiplier: 0.68,
    touchMultiplier: 1,
    syncTouch: false,
    anchors: {
      offset: navOffset,
    },
  });
})();
