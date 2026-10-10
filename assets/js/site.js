/* ==========================================================================
   Affinitty replica — interaction layer
   Re-implements the Framer runtime behaviours: Lenis smooth scroll,
   appear animations, hero cursor, letter reveals, testimonial slider,
   email-copy button, ribbons, pixel status grid and nav state.
   ========================================================================== */
(function () {
  "use strict";

  document.documentElement.classList.add("js");

  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var clamp = function (v, a, b) { return Math.max(a, Math.min(b, v)); };

  /* ------------------------------------------------------------------ Lenis */
  var lenis = null;
  if (window.Lenis && !reducedMotion) {
    lenis = new window.Lenis({
      duration: 1.15,
      easing: function (t) { return Math.min(1, 1.001 - Math.pow(2, -10 * t)); },
      smoothWheel: true
    });
    document.documentElement.classList.add("lenis", "lenis-smooth");
    function raf(time) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }
    requestAnimationFrame(raf);
  }

  var scrollToY = function (y) {
    if (lenis) lenis.scrollTo(y, { offset: 0 });
    else window.scrollTo({ top: y });
  };

  /* ------------------------------------------- viewport height css variable */
  function setVH() {
    document.documentElement.style.setProperty(
      "--framer-viewport-height", window.innerHeight + "px");
  }
  setVH();
  window.addEventListener("resize", setVH);

  /* ------------------------------------------------------- section tag text */
  document.querySelectorAll("[data-code-component-plugin-id] [aria-label]").forEach(function (el) {
    var label = el.getAttribute("aria-label");
    if (!label) return;
    var span = el.querySelector("span > span");
    if (span && !span.textContent.trim()) span.setAttribute("data-tag-text", label);
  });

  /* ------------------------------------------------------ appear animations */
  var appearEls = Array.prototype.slice.call(
    document.querySelectorAll("[data-framer-appear-id]"));

  if (appearEls.length && !reducedMotion) {
    appearEls.forEach(function (el) { el.classList.add("pre-appear"); });
    // hero items animate in on load, staggered; the rest on scroll
    var inHero = appearEls.filter(function (el) {
      return !!el.closest('[data-framer-name="Hero"]');
    });
    var rest = appearEls.filter(function (el) { return inHero.indexOf(el) < 0; });

    requestAnimationFrame(function () {
      setTimeout(function () {
        inHero.forEach(function (el, i) {
          setTimeout(function () { el.classList.remove("pre-appear"); }, i * 110);
        });
      }, 120);
    });

    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.remove("pre-appear");
            io.unobserve(entry.target);
          }
        });
      }, { threshold: 0.15, rootMargin: "0px 0px -8% 0px" });
      rest.forEach(function (el) { io.observe(el); });
    } else {
      rest.forEach(function (el) { el.classList.remove("pre-appear"); });
    }
  }

  /* ---------------------------------------------------- hero custom cursor */
  var hero = document.querySelector('[data-framer-name="Hero"]');
  var cursorHolder = hero && hero.querySelector('[data-framer-name="Cusor holder"]');
  var heroFrame = hero && hero.querySelector('[data-framer-name="Main frame"]');

  if (cursorHolder && heroFrame && window.matchMedia("(pointer: fine)").matches) {
    var cx = 60, cy = 60, tx = 60, ty = 60, lastX = 60, cursorOn = false;

    heroFrame.addEventListener("mouseenter", function () {
      cursorOn = true;
      document.body.classList.add("hero-cursor-active");
      cursorHolder.style.opacity = "1";
    });
    heroFrame.addEventListener("mouseleave", function () {
      cursorOn = false;
      document.body.classList.remove("hero-cursor-active");
      cursorHolder.style.opacity = "0";
    });
    heroFrame.addEventListener("mousemove", function (e) {
      var r = heroFrame.getBoundingClientRect();
      tx = e.clientX - r.left;
      ty = e.clientY - r.top;
      if (!cursorOn) return;
    });

    cursorHolder.style.opacity = "0";

    (function tick() {
      if (cursorOn) {
        cx += (tx - cx) * 0.16;
        cy += (ty - cy) * 0.16;
        var vx = clamp((tx - cx) * 0.35, -26, 26);
        var tilt = clamp((cx - lastX) * 1.4, -14, 14);
        lastX = cx;
        cursorHolder.style.left = "0px";
        cursorHolder.style.top = "0px";
        cursorHolder.style.transform =
          "translate3d(" + (cx - 13) + "px," + (cy - 8) + "px,0)";
        var arrow = cursorHolder.querySelector('[data-framer-name="Cursor"]');
        if (arrow) arrow.style.transform = "rotate(" + tilt + "deg)";
        var bubble = cursorHolder.querySelector('[data-framer-name="Comment"]');
        if (bubble) bubble.style.transform =
          "translateX(" + vx + "px) rotate(" + (tilt * 0.4) + "deg)";
      }
      requestAnimationFrame(tick);
    })();
  }

  /* --------------------------- about blockquote: per-letter colour reveal */
  var aboutQuote = document.querySelector(
    '[data-framer-name="About us container"] blockquote');

  if (aboutQuote && !reducedMotion) {
    // per-letter colour overlays (aria-hidden copies stacked over the faded text)
    var overlays = Array.prototype.slice.call(
      aboutQuote.querySelectorAll('span[aria-hidden="true"]'));

    overlays.forEach(function (s) { s.style.opacity = "0"; });

    var revealed = 0;
    function updateLetters() {
      var r = aboutQuote.getBoundingClientRect();
      var vh = window.innerHeight;
      var p = clamp((vh * 0.92 - r.top) / (vh * 0.62), 0, 1);
      var n = Math.round(p * overlays.length);
      if (n !== revealed) {
        for (var i = 0; i < overlays.length; i++) {
          overlays[i].style.opacity = i < n ? "1" : "0";
        }
        revealed = n;
      }
    }
    window.addEventListener("scroll", updateLetters, { passive: true });
    window.addEventListener("resize", updateLetters);
    updateLetters();
  }

  /* ----------------------------------------------- testimonial word lift */
  var quoteEl = document.querySelector('[data-framer-name="Testimonial 1"]');
  if (quoteEl) {
    // normalise Framer's per-letter pre-animation state; we animate per-word
    Array.prototype.forEach.call(
      quoteEl.querySelectorAll('span[style*="opacity:0.001"]'), function (s) {
        s.style.opacity = "1";
        s.style.transform = "none";
      });
  }
  if (quoteEl && !reducedMotion) {
    var words = Array.prototype.slice.call(
      quoteEl.querySelectorAll(".framer-text > span"));
    words.forEach(function (w, i) {
      w.style.transitionDelay = (i * 26) + "ms";
    });
    quoteEl.classList.add("quote-anim");
    var qio = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          quoteEl.classList.add("quote-in");
          qio.disconnect();
        }
      });
    }, { threshold: 0.3 });
    qio.observe(quoteEl);
  }

  /* ------------------------------------------------- testimonials slider */
  var sliderHost = document.querySelector(".framer-1sjsuhg-container");
  var slideEl = sliderHost && sliderHost.querySelector(".framer-6pttY");

  if (sliderHost && slideEl) {
    // hoist the controls (counter / arrows / progress) out of the slide so
    // cloned slides don't duplicate them
    var controlsEl = slideEl.querySelector('[data-framer-name="Progressive bar"]');
    if (controlsEl) {
      sliderHost.style.display = "flex";
      sliderHost.style.flexDirection = "column";
      sliderHost.style.gap = "40px";
      sliderHost.appendChild(controlsEl);
    }
    var SLIDES = [
      null, // slide 1 = markup already in the DOM
      {
        quote: "\u201cDavid brought order to a product that had grown faster than its design. Every screen he touched became clearer, calmer and easier to use \u2014 and our activation numbers proved it.\u201d",
        name: "Sofia Ramirez",
        role: "VP of Product, Loopline",
        avatar: null,
        initials: "SR",
        bg: "#f4ac28"
      },
      {
        quote: "\u201cA rare mix of speed and care. David prototypes in days what others scope in months, and the result always feels considered down to the last pixel.\u201d",
        name: "Jonas Weber",
        role: "Founder, Northbeam Labs",
        avatar: null,
        initials: "JW",
        bg: "#8427de"
      }
    ];

    var counter = sliderHost.querySelector('[data-framer-name="Number + icon"] .framer-bgvrbj .framer-text');
    var counterCur = counter && counter.querySelector("span");
    var fill = sliderHost.querySelector('[data-framer-name="Divider 1"] > div > div + div');
    var prevBtn = sliderHost.querySelector(".framer-1v6ocmr");
    var nextBtn = sliderHost.querySelector(".framer-1f0llxj");
    var DUR = 6500;
    var cur = 0, busy = false, timer = null;
    var visibleSlide = slideEl;
    slideEl.classList.add("t-slide");

    if (fill) {
      fill.classList.add("t-progress-fill");
      fill.style.setProperty("--t-dur", DUR + "ms");
    }

    function setCounter(n) {
      if (counterCur) counterCur.textContent = "0" + (n + 1);
    }

    function restartBar() {
      if (!fill) return;
      fill.classList.remove("t-run");
      fill.style.width = "0%";
      void fill.offsetWidth; // reflow
      fill.classList.add("t-run");
    }

    function buildSlide(idx) {
      var clone = slideEl.cloneNode(true);
      var d = SLIDES[idx];
      var q = clone.querySelector('[data-framer-name^="Testimonial"]');
      if (q) {
        // replace word-span soup with plain text (keeps same styling hooks)
        var p = q.querySelector(".framer-text");
        if (p) {
          p.innerHTML = "";
          d.quote.split(" ").forEach(function (w) {
            var s = document.createElement("span");
            s.textContent = w + "\u00a0";
            s.style.transitionDelay = "0ms";
            p.appendChild(s);
          });
          q.classList.add("quote-anim", "quote-in");
        }
      }
      var nameEl = clone.querySelector('[data-framer-name="Text"] .framer-18bem3u .framer-text');
      var roleEl = clone.querySelector('[data-framer-name="Text"] .framer-ornkb8 .framer-text');
      if (nameEl) nameEl.textContent = d.name;
      if (roleEl) roleEl.textContent = d.role;
      var avatarBox = clone.querySelector('[data-framer-name="Author 1"] > div');
      if (avatarBox && d.avatar === null) {
        avatarBox.innerHTML =
          '<div style="position:absolute;inset:0;border-radius:inherit;background:' +
          d.bg + ';display:flex;align-items:center;justify-content:center;' +
          'font-family:Inter,sans-serif;font-weight:600;font-size:14px;color:#fff">' +
          d.initials + "</div>";
      }
      clone.classList.add("t-slide");
      return clone;
    }

    function goTo(idx, dir) {
      if (busy || idx === cur) return;
      busy = true;
      var outgoing = visibleSlide;
      var incoming = buildSlide(idx);
      incoming.classList.add(dir > 0 ? "t-pre" : "t-out");
      sliderHost.insertBefore(incoming, controlsEl || null);
      requestAnimationFrame(function () {
        requestAnimationFrame(function () {
          outgoing.classList.add(dir > 0 ? "t-out" : "t-pre");
          incoming.classList.remove("t-pre", "t-out");
        });
      });
      setTimeout(function () {
        outgoing.remove();
        visibleSlide = incoming;
        cur = idx;
        setCounter(cur);
        busy = false;
      }, 480);
      restartBar();
      schedule();
    }

    function schedule() {
      clearTimeout(timer);
      timer = setTimeout(function () {
        goTo((cur + 1) % 3, 1);
      }, DUR);
    }

    if (prevBtn) prevBtn.addEventListener("click", function () {
      goTo((cur + 2) % 3, -1);
    });
    if (nextBtn) nextBtn.addEventListener("click", function () {
      goTo((cur + 1) % 3, 1);
    });

    sliderHost.addEventListener("mouseenter", function () {
      clearTimeout(timer);
      if (fill) { fill.style.transition = "none"; }
    });
    sliderHost.addEventListener("mouseleave", function () {
      restartBar();
      schedule();
    });

    restartBar();
    schedule();
  }

  /* --------------------------------------------------- email copy button */
  var copyBtn = document.querySelector(".framer-3dmM2");
  if (copyBtn) {
    var btn = copyBtn.querySelector("button");
    var stack = btn && btn.querySelector("span[style*='position: relative'], span[style*='position:relative']");
    if (stack) stack.setAttribute("data-copy-stack", "");
    var EMAIL = "uxridham@gmail.com";
    var resetTimer = null;

    if (btn) btn.addEventListener("click", function () {
      var done = function () {
        copyBtn.classList.add("is-copied");
        clearTimeout(resetTimer);
        resetTimer = setTimeout(function () {
          copyBtn.classList.remove("is-copied");
        }, 2200);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(EMAIL).then(done, function () {
          fallbackCopy(); done();
        });
      } else { fallbackCopy(); done(); }

      function fallbackCopy() {
        var ta = document.createElement("textarea");
        ta.value = EMAIL;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand("copy"); } catch (e) {}
        document.body.removeChild(ta);
      }
    });
  }

  /* ---------------------------------------------- footer "Let's talk" */
  var letsTalk = document.querySelector(".framer-ahm9ni");
  if (letsTalk && !letsTalk.closest("a")) {
    var a = document.createElement("a");
    a.href = "mailto:uxridham@gmail.com";
    a.className = "lets-talk-link";
    letsTalk.parentNode.insertBefore(a, letsTalk);
    a.appendChild(letsTalk);
  }

  /* ------------------------------------------------------------ ribbons */
  document.querySelectorAll('[data-framer-name="AnimatedRibbons"]').forEach(function (r) {
    r.setAttribute("data-ribbon", "");
  });

  /* ------------------------------------------------------- pixel grid */
  var grid = document.querySelector('[aria-label="Loading"] > div');
  if (grid) grid.setAttribute("data-pixel-grid", "");
  document.querySelectorAll("[data-pixel-grid]").forEach(function (g) {
    var dots = Array.prototype.slice.call(g.children);
    if (!dots.length) return;
    var GREEN = "rgb(3, 151, 84)";
    (function sparkle() {
      if (document.hidden) { setTimeout(sparkle, 900); return; }
      var i = Math.floor(Math.random() * dots.length);
      var d = dots[i];
      d.style.backgroundColor = GREEN;
      setTimeout(function () { d.style.backgroundColor = "transparent"; }, 650);
      setTimeout(sparkle, 160 + Math.random() * 320);
    })();
  });

  /* --------------------- generic scale-in appear (sticker images etc.) */
  var scaleIns = Array.prototype.filter.call(
    document.querySelectorAll("div[style]"), function (el) {
      var st = el.getAttribute("style") || "";
      return /transform:\s*scale\(0\)/.test(st) && /opacity:\s*0/.test(st);
    });
  if (scaleIns.length) {
    if (reducedMotion || !("IntersectionObserver" in window)) {
      scaleIns.forEach(function (el) {
        el.style.opacity = "1";
        el.style.transform = "scale(1)";
      });
    } else {
      scaleIns.forEach(function (el) {
        el.style.transition =
          "opacity 0.7s cubic-bezier(0.16,1,0.3,1), transform 0.7s cubic-bezier(0.17,0.67,0.3,1.2)";
      });
      var sio = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.style.opacity = "1";
            entry.target.style.transform = "scale(1)";
            sio.unobserve(entry.target);
          }
        });
      }, { threshold: 0.4 });
      scaleIns.forEach(function (el) { sio.observe(el); });
    }
  }

  /* ------------------------------------------- subpage section reveals */
  var pgSections = document.querySelectorAll(".pg-main .pg-hero, .pg-main .pg-section");
  if (pgSections.length) {
    if (reducedMotion || !("IntersectionObserver" in window)) {
      pgSections.forEach(function (s) { s.classList.add("pg-in"); });
    } else {
      var pio = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("pg-in");
            pio.unobserve(entry.target);
          }
        });
      }, { threshold: 0.06, rootMargin: "0px 0px -4% 0px" });
      pgSections.forEach(function (s) { pio.observe(s); });
    }
  }

  /* --------------------------------------------------- nav current page */
  var path = window.location.pathname.replace(/index\.html$/, "");
  document.querySelectorAll('nav a[data-framer-name]').forEach(function (a) {
    var href = a.getAttribute("href") || "";
    var isCurrent = false;
    if (href === "/") isCurrent = path === "/" || path === "";
    else if (href.indexOf("/projects") === 0) {
      isCurrent = path.indexOf("/projects") === 0;
    } else {
      isCurrent = path.indexOf(href) === 0 && href !== "/";
    }
    if (isCurrent) a.setAttribute("data-framer-page-link-current", "true");
  });

  /* ------------------------------------------------- page transitions */
  if (!reducedMotion) {
    document.addEventListener("click", function (e) {
      var a = e.target.closest ? e.target.closest("a[href]") : null;
      if (!a) return;
      var href = a.getAttribute("href") || "";
      if (a.target === "_blank" || e.metaKey || e.ctrlKey || e.shiftKey) return;
      if (/^(mailto:|tel:|https?:\/\/)/.test(href)) return;
      if (a.hasAttribute("download")) return;
      if (href.charAt(0) !== "/" && href.charAt(0) !== "." && href.indexOf("index.html") !== 0) return;
      e.preventDefault();
      document.body.classList.add("page-leaving");
      var dest = href;
      setTimeout(function () { window.location.href = dest; }, 300);
    });
  }
})();
