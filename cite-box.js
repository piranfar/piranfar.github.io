/* cite-box.js: "Cite this post" button and panel. Data come from <script id="cite-data"> (cite-box.lua). */
(function () {
  "use strict";

  var MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
    "October", "November", "December"];
  var MON3 = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var MLA_MON = ["Jan.", "Feb.", "Mar.", "Apr.", "May", "June", "July", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."];

  var ICON = {
    quote: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7.2 6C4.9 7.3 3.5 9.6 3.5 12.6V18h6.2v-6.2H6.6c0-1.9.9-3.3 2.6-4.3L7.2 6zm9.6 0c-2.3 1.3-3.7 3.6-3.7 6.6V18h6.2v-6.2h-3.1c0-1.9.9-3.3 2.6-4.3L16.8 6z"/></svg>',
    copy: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="8.5" y="8.5" width="11" height="11" rx="2.2" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M15.5 8.5V6.7A2.2 2.2 0 0 0 13.3 4.5H6.7A2.2 2.2 0 0 0 4.5 6.7v6.6a2.2 2.2 0 0 0 2.2 2.2h1.8" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>',
    check: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.2 4.2L19 7" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    down: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v11m0 0l-4.5-4.5M12 15l4.5-4.5M5 19.5h14" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    close: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.5 6.5l11 11m0-11l-11 11" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    chev: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 10l5 5 5-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
  };

  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  function pad(n) { return (n < 10 ? "0" : "") + n; }
  // .ris and .bib: straight quotes, so older EndNote and BibTeX read them without encoding errors
  function plainQuotes(s) {
    return String(s).replace(/[\u2018\u2019]/g, "'").replace(/[\u201c\u201d]/g, '"');
  }
  function ymd(s) {
    var p = (s || "").split("-").map(Number);
    return { y: p[0], m: p[1], d: p[2] };
  }
  function today() {
    var t = new Date();
    return { y: t.getFullYear(), m: t.getMonth() + 1, d: t.getDate() };
  }
  function initials(given) {
    return given.split(/[\s-]+/).filter(Boolean).map(function (w) { return w.charAt(0).toUpperCase(); }).join("");
  }
  // "Why Plasmid Classifiers Fail on Short-Read Contigs" -> "Why plasmid classifiers fail on short-read contigs".
  // Words with inner capitals or digits (PlasmidCall, AMR, P1.14) are kept.
  function sentenceCase(t) {
    var keepNext = true;
    return t.split(/(\s+)/).map(function (w) {
      if (/^\s+$/.test(w) || w === "") return w;
      var out = keepNext ? w : w.split("-").map(function (p) {
        return /^[A-Z][a-z]+[:;,.?!]?$/.test(p) ? p.toLowerCase() : p;
      }).join("-");
      keepNext = /[:?!]$/.test(w);
      return out;
    }).join("");
  }
  function joinAuthors(list, sep, last) {
    if (list.length <= 1) return list.join("");
    return list.slice(0, -1).join(sep) + last + list[list.length - 1];
  }

  function build(D) {
    var p = ymd(D.date), now = today();
    var A = D.authors || [];
    var key = ((A[0] && A[0].family) || "anon").toLowerCase().replace(/[^a-z]/g, "") + p.y +
      ((D.title.match(/[A-Za-z]+/) || ["post"])[0]).toLowerCase();
    var titleSC = D.titleSentence || sentenceCase(D.title);
    var urlBare = D.url.replace(/^https?:\/\//, "").replace(/\/$/, "");
    var accessed = now.y + " " + MON3[now.m - 1] + " " + now.d;
    var accessedISO = now.y + "-" + pad(now.m) + "-" + pad(now.d);

    var van = joinAuthors(A.map(function (a) { return a.family + " " + initials(a.given); }), ", ", ", ") + ". " +
      D.title + " [Internet]. " + (D.place ? D.place + ": " : "") + D.site + "; " +
      p.y + " " + MON3[p.m - 1] + " " + p.d + " [cited " + accessed + "]. Available from: " + D.url;

    var apaNames = A.map(function (a) {
      return a.family + ", " + initials(a.given).split("").join(". ") + ".";
    });
    var apaAuth = joinAuthors(apaNames, ", ", A.length > 2 ? ", & " : " & ");
    var apaHead = apaAuth + " (" + p.y + ", " + MONTHS[p.m - 1] + " " + p.d + "). " + titleSC + ". ";
    var apa = { text: apaHead + D.site + ". " + D.url,
      html: esc(apaHead) + "<i>" + esc(D.site) + "</i>. " + esc(D.url) };

    var mlaAuth = A.length === 0 ? "" : A.length === 1 ? A[0].family + ", " + A[0].given :
      A.length === 2 ? A[0].family + ", " + A[0].given + ", and " + A[1].given + " " + A[1].family :
      A[0].family + ", " + A[0].given + ", et al";
    var mlaTail = ", " + p.d + " " + MLA_MON[p.m - 1] + " " + p.y + ", " + urlBare + ".";
    var mla = { text: mlaAuth + ". \u201c" + D.title + ".\u201d " + D.site + mlaTail,
      html: esc(mlaAuth) + ". \u201c" + esc(D.title) + ".\u201d <i>" + esc(D.site) + "</i>" + esc(mlaTail) };

    var bib = "@misc{" + key + ",\n" +
      "  author       = {" + A.map(function (a) { return a.family + ", " + a.given; }).join(" and ") + "},\n" +
      "  title        = {{" + D.title + "}},\n" +
      "  howpublished = {" + D.site + " (blog)},\n" +
      "  year         = {" + p.y + "},\n" +
      "  month        = {" + MONTHS[p.m - 1].slice(0, 3).toLowerCase() + "},\n" +
      "  day          = {" + p.d + "},\n" +
      "  url          = {" + D.url + "},\n" +
      "  urldate      = {" + accessedISO + "},\n" +
      "  note         = {Accessed " + accessedISO + "}\n}";

    var ris = ["TY  - BLOG", "TI  - " + D.title];
    A.forEach(function (a) { ris.push("AU  - " + a.family + ", " + a.given); });
    ris.push("PY  - " + p.y, "DA  - " + p.y + "/" + pad(p.m) + "/" + pad(p.d), "T2  - " + D.site,
      "PB  - " + D.site);
    if (D.place) ris.push("CY  - " + D.place);
    if (D.abstract) ris.push("AB  - " + D.abstract);
    (D.keywords || []).forEach(function (k) { ris.push("KW  - " + k); });
    ris.push("UR  - " + D.url, "Y2  - " + now.y + "/" + pad(now.m) + "/" + pad(now.d), "LA  - en", "ER  - ", "");

    return {
      key: key,
      styles: [
        { id: "vancouver", label: "Vancouver", kind: "text", text: van, html: esc(van) },
        { id: "apa", label: "APA", kind: "text", text: apa.text, html: apa.html },
        { id: "mla", label: "MLA", kind: "text", text: mla.text, html: mla.html },
        { id: "bibtex", label: "BibTeX", kind: "code", text: plainQuotes(bib) },
        { id: "ris", label: "RIS", kind: "code", text: plainQuotes(ris.join("\r\n")) }
      ]
    };
  }

  function copy(text, html) {
    if (navigator.clipboard && window.ClipboardItem && html) {
      return navigator.clipboard.write([new ClipboardItem({
        "text/plain": new Blob([text], { type: "text/plain" }),
        "text/html": new Blob([html], { type: "text/html" })
      })]).catch(function () { return navigator.clipboard.writeText(text); });
    }
    if (navigator.clipboard) return navigator.clipboard.writeText(text);
    return new Promise(function (ok) {
      var t = document.createElement("textarea");
      t.value = text; t.style.position = "fixed"; t.style.opacity = "0";
      document.body.appendChild(t); t.select();
      try { document.execCommand("copy"); } catch (e) { /* ignore */ }
      document.body.removeChild(t); ok();
    });
  }

  function download(name, text, type) {
    var a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([text], { type: type }));
    a.download = name;
    document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  }

  var uid = 0;
  function panel(D, C, opts) {
    var id = "cite" + (++uid);
    var el = document.createElement("div");
    el.className = "cite-card" + (opts.inline ? " cite-card--inline" : "");
    var tabs = C.styles.map(function (s, i) {
      return '<button type="button" role="tab" class="cite-tab" id="' + id + "-t-" + s.id + '" aria-controls="' +
        id + '-p" aria-selected="' + (i === 0) + '" tabindex="' + (i === 0 ? 0 : -1) + '" data-i="' + i + '">' +
        s.label + "</button>";
    }).join("");
    el.innerHTML =
      (opts.inline ? "" :
        '<div class="cite-card__head"><div><div class="cite-card__eyebrow">Cite this post</div>' +
        '<div class="cite-card__title">' + esc(D.title) + "</div></div>" +
        '<button type="button" class="cite-close" aria-label="Close">' + ICON.close + "</button></div>") +
      '<div class="cite-tabs" role="tablist" aria-label="Citation format">' + tabs + "</div>" +
      '<div class="cite-out" role="tabpanel" id="' + id + '-p">' +
      '<div class="cite-out__body"></div>' +
      '<button type="button" class="cite-copy">' + ICON.copy + "<span>Copy</span></button></div>" +
      '<div class="cite-actions">' +
      '<button type="button" class="cite-dl cite-dl--primary" data-f="ris">' + ICON.down +
      '<span><b>Download .ris</b><small>EndNote, Zotero, Mendeley</small></span></button>' +
      '<button type="button" class="cite-dl" data-f="bib">' + ICON.down +
      '<span><b>Download .bib</b><small>BibTeX, LaTeX</small></span></button></div>' +
      '<p class="cite-note">Accessed date is set to today. Zotero and Mendeley browser buttons also read this page directly.</p>';

    var body = el.querySelector(".cite-out__body");
    var copyBtn = el.querySelector(".cite-copy");
    var tabEls = Array.prototype.slice.call(el.querySelectorAll(".cite-tab"));
    var cur = 0;

    function show(i, focus) {
      cur = i;
      var s = C.styles[i];
      tabEls.forEach(function (t, j) {
        t.setAttribute("aria-selected", String(j === i));
        t.tabIndex = j === i ? 0 : -1;
      });
      el.querySelector(".cite-out").setAttribute("aria-labelledby", tabEls[i].id);
      body.className = "cite-out__body" + (s.kind === "code" ? " is-code" : "");
      body.innerHTML = s.kind === "code" ? "<pre>" + esc(s.text) + "</pre>" : "<p>" + s.html + "</p>";
      if (focus) tabEls[i].focus();
    }
    tabEls.forEach(function (t, i) {
      t.addEventListener("click", function () { show(i); });
      t.addEventListener("keydown", function (e) {
        if (e.key === "ArrowRight") { e.preventDefault(); show((i + 1) % tabEls.length, true); }
        if (e.key === "ArrowLeft") { e.preventDefault(); show((i - 1 + tabEls.length) % tabEls.length, true); }
      });
    });
    copyBtn.addEventListener("click", function () {
      var s = C.styles[cur];
      copy(s.text, s.kind === "text" ? s.html : null).then(function () {
        copyBtn.classList.add("is-done");
        copyBtn.innerHTML = ICON.check + "<span>Copied</span>";
        setTimeout(function () {
          copyBtn.classList.remove("is-done");
          copyBtn.innerHTML = ICON.copy + "<span>Copy</span>";
        }, 1800);
      });
    });
    el.querySelectorAll(".cite-dl").forEach(function (b) {
      b.addEventListener("click", function () {
        var ris = C.styles[4].text, bib = C.styles[3].text;
        if (b.dataset.f === "ris") download(C.key + ".ris", ris, "application/x-research-info-systems");
        else download(C.key + ".bib", bib + "\n", "application/x-bibtex");
      });
    });
    show(0);
    return el;
  }

  function init() {
    var node = document.getElementById("cite-data");
    if (!node) return;
    var D;
    try { D = JSON.parse(node.textContent); } catch (e) { return; }
    var C = build(D);

    // bottom: inline panel
    var inline = document.querySelector(".cite-inline-mount");
    if (inline) { inline.innerHTML = ""; inline.appendChild(panel(D, C, { inline: true })); }

    // top: button under the author line, opening a popover
    var header = document.getElementById("title-block-header");
    var bar = document.createElement("div");
    bar.className = "cite-bar";
    bar.innerHTML = '<button type="button" class="cite-trigger" aria-haspopup="dialog" aria-expanded="false">' +
      ICON.quote + "<span>Cite this post</span>" + ICON.chev + "</button>";
    var pop = document.createElement("div");
    pop.className = "cite-pop";
    pop.setAttribute("role", "dialog");
    pop.setAttribute("aria-label", "Cite this post");
    pop.appendChild(panel(D, C, { inline: false }));
    bar.appendChild(pop);
    var meta = header && header.querySelector(".quarto-title-meta");
    if (meta) meta.insertAdjacentElement("afterend", bar);
    else if (header) header.appendChild(bar);
    else {
      var mount = document.querySelector(".cite-top-mount");
      if (mount) { mount.hidden = false; mount.appendChild(bar); }
    }

    var trig = bar.querySelector(".cite-trigger");
    function open(v) {
      bar.classList.toggle("is-open", v);
      trig.setAttribute("aria-expanded", String(v));
      if (v) { var t = pop.querySelector(".cite-tab[aria-selected=true]"); if (t) t.focus({ preventScroll: true }); }
    }
    trig.addEventListener("click", function () { open(!bar.classList.contains("is-open")); });
    pop.querySelector(".cite-close").addEventListener("click", function () { open(false); trig.focus(); });
    document.addEventListener("click", function (e) {
      if (bar.classList.contains("is-open") && !bar.contains(e.target)) open(false);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && bar.classList.contains("is-open")) { open(false); trig.focus(); }
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
