(function () {
  "use strict";

  // ── Loading phrases ───────────────────────────────────────
  var LOADING_PHRASES = [
    "Fazendo o que o estagiário faria em 3 horas…",
    "Transformando Word em experiência de aprendizagem…",
    "Relendo o documento com mais atenção do que qualquer aluno jamais leu…",
    "Atualizando o Notion… brincadeira, isso é melhor que o Notion.",
    "Convertendo horas de planejamento em segundos…",
    "Fazendo a IA trabalhar enquanto você finalmente toma aquele café merecido…",
    "Trabalhando mais rápido do que você digita 'precisa de ajustes'…",
    "Fazendo em segundos o que levaria uma tarde inteira e dois cafés…",
  ];

  // ── DOM refs ──────────────────────────────────────────────
  const sidebarToggle = document.getElementById("sidebar-toggle");
  const sidebar = document.getElementById("sidebar");
  const sidebarOverlay = document.getElementById("sidebar-overlay");
  const navItems = document.querySelectorAll(".nav-item[data-view]");

  const form = document.getElementById("convert-form");
  const fileInput = document.getElementById("file-input");
  const dropZone = document.getElementById("drop-zone");
  const fileInfo = document.getElementById("file-info");
  const fileInfoName = document.getElementById("file-info-name");
  const fileInfoSize = document.getElementById("file-info-size");
  const clearFile = document.getElementById("clear-file");
  const profileSel = document.getElementById("profile-select");
  const profileDesc = document.getElementById("profile-desc");
  const mockCheck = document.getElementById("mock-checkbox");
  const toggleRow = document.getElementById("toggle-row");
  const submitBtn = document.getElementById("submit-btn");
  const spinner = document.getElementById("spinner");
  const errorBox = document.getElementById("error-box");
  const errorMsg = document.getElementById("error-message");
  const resultSec = document.getElementById("result-section");
  const dlLink = document.getElementById("download-link");
  const dlAllLink = document.getElementById("download-all-link");
  const copyHtmlBtn = document.getElementById("copy-html-btn");
  const topicoTabs = document.getElementById("topico-tabs");
  const previewHeader = document.getElementById("preview-header");
  const previewTitleText = document.getElementById("preview-title-text");
  const previewNavPos = document.getElementById("preview-nav-pos");
  const previewPrev = document.getElementById("preview-prev");
  const previewNext = document.getElementById("preview-next");
  const btnNew = document.getElementById("btn-new");
  const iframe = document.getElementById("preview-frame");

  const loadingPhrase = document.getElementById("loading-phrase");
  const profilesList = document.getElementById("profiles-list");
  const templatesList = document.getElementById("templates-list");
  const galleryGrid = document.getElementById("gallery-grid");
  const galleryLoading = document.getElementById("gallery-loading");
  const gallerySubtitle = document.getElementById("gallery-subtitle");
  const galleryProfileSelect = document.getElementById("gallery-profile-select");

  const infograficosGrid    = document.getElementById("infograficos-grid");
  const infograficosLoading = document.getElementById("infograficos-loading");
  const infograficosSubtitle = document.getElementById("infograficos-subtitle");
  const infograficosSearch  = document.getElementById("infograficos-search");
  const infograficosNoResults = document.getElementById("infograficos-no-results");
  const infograficosSearchTerm = document.getElementById("infograficos-search-term");

  // ── Sidebar toggle ────────────────────────────────────────
  const isMobile = () => window.innerWidth <= 768;

  sidebarToggle.addEventListener("click", function () {
    if (isMobile()) {
      document.body.classList.toggle("sidebar-open");
    } else {
      document.body.classList.toggle("sidebar-collapsed");
    }
  });

  sidebarOverlay.addEventListener("click", function () {
    document.body.classList.remove("sidebar-open");
  });

  // ── View navigation ───────────────────────────────────────
  var profilesLoaded = false;
  var templatesLoaded = false;
  var galleryLoaded = false;
  var galleryCurrentProfile = null;

  var infograficosLoaded = false;
  var infograficosCurrentMode = {};
  var INFOGRAFICOS_LIST = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28];

  navItems.forEach(function (btn) {
    btn.addEventListener("click", function () {
      var viewId = "view-" + btn.dataset.view;

      // Update nav active state
      navItems.forEach(function (b) {
        b.classList.remove("is-active");
        b.removeAttribute("aria-current");
      });
      btn.classList.add("is-active");
      btn.setAttribute("aria-current", "page");

      // Show/hide views
      document.querySelectorAll(".view").forEach(function (v) {
        v.hidden = v.id !== viewId;
      });

      // Lazy-load data views
      if (viewId === "view-profiles" && !profilesLoaded) loadProfiles();
      if (viewId === "view-templates" && !templatesLoaded) loadTemplates();
      if (viewId === "view-gallery" && !galleryLoaded) loadGallery();
      if (viewId === "view-infograficos" && !infograficosLoaded) loadInfograficos();

      // Close mobile sidebar
      if (isMobile()) document.body.classList.remove("sidebar-open");

      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  });

  // ── Profiles ──────────────────────────────────────────────
  async function loadProfiles() {
    try {
      const res = await fetch("/api/profiles");
      if (!res.ok) throw new Error("Falha ao carregar profiles.");
      const profiles = await res.json();

      // Populate select (converter view)
      profiles.forEach(function (p) {
        const opt = document.createElement("option");
        opt.value = p.name;
        opt.textContent = p.label || p.name;
        opt.dataset.descricao = p.descricao || "";
        profileSel.appendChild(opt);
      });
      updateProfileDesc();

      // Render profiles view
      if (!profiles.length) {
        profilesList.innerHTML =
          '<p style="color:var(--gray-500);font-size:.875rem;padding:1rem 0">Nenhum profile encontrado.</p>';
        profilesLoaded = true;
        return;
      }

      var html = "";
      profiles.forEach(function (p, i) {
        var comps = p.componentes || {};
        var compRows = Object.entries(comps)
          .map(function (entry) {
            return (
              "<tr><td>" +
              entry[0] +
              '</td><td><span class="comp-tag">' +
              (entry[1].model || "m1") +
              (entry[1].version || "v1") +
              "</span></td></tr>"
            );
          })
          .join("");

        html +=
          '<div class="profile-card fade-in" style="animation-delay: ' +
          i * 60 +
          'ms">' +
          '<div class="profile-card-header">' +
          '<div><div class="profile-name">' +
          escHtml(p.label || p.name) +
          "</div>" +
          (p.descricao
            ? '<div class="profile-desc-text">' +
              escHtml(p.descricao) +
              "</div>"
            : "") +
          "</div>" +
          '<span class="profile-badge">' +
          escHtml(p.name) +
          "</span>" +
          "</div>" +
          '<div class="profile-card-body">' +
          '<div class="profile-meta">' +
          (p.css ? "<div>CSS: <code>" + escHtml(p.css) + "</code></div>" : "") +
          (p.js ? "<div>JS: <code>" + escHtml(p.js) + "</code></div>" : "") +
          "</div>" +
          (compRows
            ? '<table class="comp-table"><thead><tr><th>Componente</th><th>Versão</th></tr></thead><tbody>' +
              compRows +
              "</tbody></table>"
            : "") +
          "</div>" +
          '<div class="profile-card-footer">' +
          '<button class="btn-demo-profile" data-profile="' + escHtml(p.name) + '">Ver demonstração</button>' +
          "</div>" +
          "</div>";
      });

      profilesList.innerHTML =
        '<div style="display:flex;flex-direction:column;gap:1rem">' +
        html +
        "</div>";

      profilesList.addEventListener("click", function (e) {
        var btn = e.target.closest(".btn-demo-profile");
        if (!btn) return;
        navigateToGallery(btn.dataset.profile);
      });

      profilesLoaded = true;
    } catch (err) {
      profilesList.innerHTML =
        '<p style="color:var(--danger);font-size:.875rem;padding:1rem 0">' +
        escHtml(err.message) +
        "</p>";
    }
  }

  function updateProfileDesc() {
    var sel = profileSel.selectedOptions[0];
    profileDesc.textContent = sel ? sel.dataset.descricao || "" : "";
  }
  profileSel.addEventListener("change", updateProfileDesc);

  // ── Templates ─────────────────────────────────────────────
  async function loadTemplates() {
    try {
      const res = await fetch("/api/templates");
      if (!res.ok) throw new Error("Falha ao carregar templates.");
      const data = await res.json();

      var entries = Object.entries(data);
      if (!entries.length) {
        templatesList.innerHTML =
          '<p style="color:var(--gray-500);font-size:.875rem">Nenhum template encontrado.</p>';
        templatesLoaded = true;
        return;
      }

      var html = '<div class="templates-grid">';
      entries.forEach(function (entry, i) {
        var tipo = entry[0];
        var versions = entry[1];
        html +=
          '<div class="template-group fade-in" style="animation-delay: ' +
          i * 60 +
          'ms">' +
          '<div class="template-group-header">' +
          escHtml(tipo) +
          "</div>" +
          '<div class="template-group-body">' +
          versions
            .map(function (v) {
              return '<div class="template-version">' + escHtml(v) + "</div>";
            })
            .join("") +
          "</div></div>";
      });
      html += "</div>";

      templatesList.innerHTML = html;
      templatesLoaded = true;
    } catch (err) {
      templatesList.innerHTML =
        '<p style="color:var(--danger);font-size:.875rem">' +
        escHtml(err.message) +
        "</p>";
    }
  }

  // ── Mock toggle ───────────────────────────────────────────
  mockCheck.addEventListener("change", function () {
    toggleRow.classList.toggle("inactive", !mockCheck.checked);
  });

  // ── Drag & drop ───────────────────────────────────────────
  dropZone.addEventListener("dragover", function (e) {
    e.preventDefault();
    dropZone.classList.add("drag-over");
  });
  dropZone.addEventListener("dragleave", function () {
    dropZone.classList.remove("drag-over");
  });
  dropZone.addEventListener("drop", function (e) {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    if (e.dataTransfer.files.length) setFile(e.dataTransfer.files[0]);
  });
  fileInput.addEventListener("change", function () {
    if (fileInput.files.length) setFile(fileInput.files[0]);
  });

  function formatBytes(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1048576).toFixed(1) + " MB";
  }
  function setFile(file) {
    fileInfoName.textContent = file.name;
    fileInfoSize.textContent = formatBytes(file.size);
    fileInfo.hidden = false;
    dropZone.style.display = "none";
    clearError();
  }
  clearFile.addEventListener("click", function () {
    fileInput.value = "";
    fileInfo.hidden = true;
    dropZone.style.display = "";
  });

  // ── UI helpers ────────────────────────────────────────────
  function showError(msg) {
    errorMsg.textContent = msg;
    errorBox.hidden = false;
  }
  function clearError() {
    errorBox.hidden = true;
    errorMsg.textContent = "";
  }

  var _phraseInterval = null;
  var _phraseIndex = 0;

  function startPhraseRotation() {
    var order = LOADING_PHRASES.slice().sort(function () { return Math.random() - 0.5; });
    _phraseIndex = 0;
    loadingPhrase.textContent = order[0];
    loadingPhrase.classList.remove("fade-out");

    _phraseInterval = setInterval(function () {
      loadingPhrase.classList.add("fade-out");
      setTimeout(function () {
        _phraseIndex = (_phraseIndex + 1) % order.length;
        if (_phraseIndex === 0) order.sort(function () { return Math.random() - 0.5; });
        loadingPhrase.textContent = order[_phraseIndex];
        loadingPhrase.classList.remove("fade-out");
      }, 370);
    }, 5600);
  }

  function stopPhraseRotation() {
    if (_phraseInterval) {
      clearInterval(_phraseInterval);
      _phraseInterval = null;
    }
    loadingPhrase.textContent = "";
  }

  function setLoading(loading) {
    spinner.hidden = !loading;
    submitBtn.disabled = loading;
    submitBtn.innerHTML = loading
      ? '<div class="spinner-ring" style="width:18px;height:18px;border-width:2px;flex-shrink:0"></div> Convertendo…'
      : '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:18px;height:18px"><path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z" /></svg> Converter documento';
    if (loading) startPhraseRotation(); else stopPhraseRotation();
  }

  // ── Blob management ───────────────────────────────────────
  var blobUrls = [];

  function revokeAllBlobs() {
    blobUrls.forEach(function (u) { URL.revokeObjectURL(u); });
    blobUrls = [];
  }

  function createBlobUrl(htmlString) {
    var blob = new Blob([htmlString], { type: "text/html; charset=utf-8" });
    var url = URL.createObjectURL(blob);
    blobUrls.push(url);
    return url;
  }

  // ── Tópico tabs ───────────────────────────────────────────
  var currentTopicos = [];
  var currentStem = "";

  var currentTopicoIndex = 0;

  function selectTopico(index) {
    var topico = currentTopicos[index];
    if (!topico) return;
    currentTopicoIndex = index;

    // Smooth loading transition on iframe
    iframe.classList.add("is-loading");
    iframe.src = topico._blobUrl;
    iframe.onload = function () { iframe.classList.remove("is-loading"); };

    // Update download-link (tópico atual)
    dlLink.href = topico._blobUrl;
    var safeName = (topico.titulo || "topico-" + (index + 1))
      .toLowerCase()
      .replace(/\s+/g, "-")
      .replace(/[^a-z0-9\-]/g, "");
    dlLink.download = currentStem + "-" + safeName + ".html";

    // Update active tab
    var tabs = topicoTabs.querySelectorAll(".topico-tab");
    tabs.forEach(function (t, i) {
      t.classList.toggle("is-active", i === index);
      t.setAttribute("aria-selected", i === index ? "true" : "false");
    });

    // Update preview header
    var titulo = topico.titulo || "Tópico " + (index + 1);
    previewTitleText.textContent = titulo;
    previewNavPos.textContent = (index + 1) + " / " + currentTopicos.length;
    previewPrev.disabled = index === 0;
    previewNext.disabled = index === currentTopicos.length - 1;
  }

  function renderTopicoTabs(topicos, stem) {
    currentTopicos = topicos;
    currentStem = stem;

    var multipleTopicos = topicos.length > 1;
    topicoTabs.hidden = !multipleTopicos;
    previewHeader.hidden = !multipleTopicos;
    dlAllLink.hidden = !multipleTopicos;

    if (!multipleTopicos) {
      topicoTabs.innerHTML = "";
      return;
    }

    var tabsHtml = topicos
      .map(function (t, i) {
        return (
          '<button class="topico-tab' + (i === 0 ? " is-active" : "") + '"' +
          ' data-index="' + i + '"' +
          ' role="tab"' +
          ' aria-selected="' + (i === 0 ? "true" : "false") + '">' +
          '<span class="topico-tab-num">' + (i + 1) + "</span>" +
          escHtml(t.titulo || "Tópico " + (i + 1)) +
          "</button>"
        );
      })
      .join("");

    // Append count badge at the end
    tabsHtml +=
      '<div class="topico-tabs-end">' +
      '<span class="topico-count-badge">' + topicos.length + " tópicos</span>" +
      "</div>";

    topicoTabs.innerHTML = tabsHtml;

    topicoTabs.querySelectorAll(".topico-tab").forEach(function (btn) {
      btn.addEventListener("click", function () {
        selectTopico(parseInt(btn.dataset.index, 10));
      });
    });
  }

  // ── Preview prev/next navigation ──────────────────────────
  previewPrev.addEventListener("click", function () {
    if (currentTopicoIndex > 0) selectTopico(currentTopicoIndex - 1);
  });
  previewNext.addEventListener("click", function () {
    if (currentTopicoIndex < currentTopicos.length - 1) selectTopico(currentTopicoIndex + 1);
  });

  // ── "Nova conversão" ──────────────────────────────────────
  btnNew.addEventListener("click", function () {
    resultSec.hidden = true;
    document.getElementById("form-section").hidden = false;
    fileInput.value = "";
    fileInfo.hidden = true;
    dropZone.style.display = "";
    revokeAllBlobs();
    topicoTabs.hidden = true;
    topicoTabs.innerHTML = "";
    previewHeader.hidden = true;
    dlAllLink.hidden = true;
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  // ── Submit ────────────────────────────────────────────────
  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    clearError();
    resultSec.hidden = true;
    revokeAllBlobs();

    const file = fileInput.files[0];
    if (!file) {
      showError("Selecione um arquivo .docx.");
      return;
    }

    const fd = new FormData();
    fd.append("file", file);
    fd.append("profile", profileSel.value);
    fd.append("mock", mockCheck.checked ? "true" : "false");

    setLoading(true);

    try {
      const res = await fetch("/api/convert", { method: "POST", body: fd });
      if (!res.ok) {
        let detail = "Erro " + res.status;
        try {
          const b = await res.json();
          detail = b.detail || detail;
        } catch (_) {}
        throw new Error(detail);
      }

      const data = await res.json();
      const stem = data.stem || file.name.replace(/\.docx$/i, "");

      // Cria blob URLs para cada tópico
      data.topicos.forEach(function (t) {
        t._blobUrl = createBlobUrl(t.html);
      });

      // Renderiza abas e seleciona o primeiro tópico
      renderTopicoTabs(data.topicos, stem);
      selectTopico(0);

      document.getElementById("form-section").hidden = true;
      resultSec.hidden = false;
      resultSec.scrollIntoView({ behavior: "smooth" });
      confetti({
        particleCount: 120,
        spread: 70,
        origin: { y: 0.6 },
        colors: ["#6366f1", "#818cf8", "#a5b4fc", "#ffffff"],
      });
    } catch (err) {
      showError(err.message);
    } finally {
      setLoading(false);
    }
  });

  // ── Escape HTML helper ────────────────────────────────────
  function escHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // ── ZIP download handler ──────────────────────────────────
  dlAllLink.addEventListener("click", function (e) {
    e.preventDefault();
    var zip = new JSZip();
    currentTopicos.forEach(function (t, i) {
      var slug = (t.titulo || "topico-" + (i + 1))
        .toLowerCase()
        .replace(/\s+/g, "-")
        .replace(/[^a-z0-9\-]/g, "");
      zip.file(currentStem + "-" + slug + ".html", t.html);
    });
    zip.generateAsync({ type: "blob" }).then(function (blob) {
      var url = URL.createObjectURL(blob);
      var a = document.createElement("a");
      a.href = url;
      a.download = currentStem + ".zip";
      a.click();
      URL.revokeObjectURL(url);
    });
  });

  // ── Gallery ───────────────────────────────────────────────
  async function loadGallery(profileName) {
    var target = profileName || galleryCurrentProfile || profileSel.value;
    galleryLoading.hidden = false;
    galleryGrid.innerHTML = "";

    try {
      // Populate profile selector on first load
      if (!galleryLoaded) {
        var profRes = await fetch("/api/profiles");
        if (profRes.ok) {
          var profiles = await profRes.json();
          galleryProfileSelect.innerHTML = profiles.map(function (p) {
            return '<option value="' + escHtml(p.name) + '"' +
              (p.name === target ? " selected" : "") + ">" +
              escHtml(p.label || p.name) + "</option>";
          }).join("");
        }
      }

      var res = await fetch("/api/gallery/" + encodeURIComponent(target));
      if (!res.ok) throw new Error("Falha ao carregar galeria.");
      var data = await res.json();

      galleryCurrentProfile = target;
      galleryLoaded = true;

      var count = data.components.length;
      gallerySubtitle.textContent = count + " componente" + (count !== 1 ? "s" : "") + " disponíve" + (count !== 1 ? "is" : "l");

      renderGalleryCards(data.components, data.assets);
    } catch (err) {
      galleryGrid.innerHTML =
        '<p style="color:var(--danger);font-size:.875rem;padding:1rem 0">' +
        escHtml(err.message) + "</p>";
    } finally {
      galleryLoading.hidden = true;
    }
  }

  function renderGalleryCards(components, assets) {
    var srcdocBase =
      '<!DOCTYPE html><html><head><meta charset="utf-8">' +
      '<meta name="viewport" content="width=device-width,initial-scale=1">' +
      (assets.css_bootstrap ? '<link rel="stylesheet" href="' + escHtml(assets.css_bootstrap) + '">' : "") +
      (assets.css ? '<link rel="stylesheet" href="' + escHtml(assets.css) + '">' : "") +
      "<style>body{margin:0;padding:12px;box-sizing:border-box;}*{box-sizing:border-box;}</style>" +
      "</head><body data-bs-theme='light'>";

    var srcdocScripts =
      (assets.j_query ? '<script src="' + escHtml(assets.j_query) + '"><\/script>' : "") +
      (assets.js_bootstrap ? '<script src="' + escHtml(assets.js_bootstrap) + '"><\/script>' : "") +
      (assets.js ? '<script src="' + escHtml(assets.js) + '"><\/script>' : "") +
      "</body></html>";

    var html = "";
    components.forEach(function (comp, i) {
      var encClass = assets.encapsulation_class ? ' class="' + escHtml(assets.encapsulation_class) + '"' : "";
      var srcdoc = srcdocBase +
        '<div' + encClass + '>' + comp.html + '</div>' +
        srcdocScripts;

      html +=
        '<div class="gallery-card" style="animation-delay:' + (i * 80) + 'ms">' +
        '<div class="gallery-card-header">' +
        '<span class="gallery-card-name">' + escHtml(comp.label) + "</span>" +
        '<span class="gallery-card-tipo">' + escHtml(comp.tipo) + "</span>" +
        "</div>" +
        '<div class="gallery-card-body">' +
        '<iframe srcdoc="' + srcdoc.replace(/"/g, "&quot;") + '" ' +
        'sandbox="allow-scripts allow-same-origin" ' +
        'scrolling="no" frameborder="0" ' +
        'onload="this.style.height=(this.contentDocument.body.scrollHeight+24)+\'px\'"></iframe>' +
        "</div></div>";
    });

    galleryGrid.innerHTML = html;

    // ResizeObserver for auto-height
    if (window.ResizeObserver) {
      galleryGrid.querySelectorAll("iframe").forEach(function (iframe) {
        var ro = new ResizeObserver(function () {
          try {
            var h = iframe.contentDocument && iframe.contentDocument.body
              ? iframe.contentDocument.body.scrollHeight
              : 0;
            if (h > 0) iframe.style.height = (h + 24) + "px";
          } catch (_) {}
        });
        iframe.addEventListener("load", function () {
          try {
            ro.observe(iframe.contentDocument.body);
          } catch (_) {}
        });
      });
    }
  }

  galleryProfileSelect && galleryProfileSelect.addEventListener("change", function () {
    galleryLoaded = false;
    loadGallery(galleryProfileSelect.value);
  });

  // ── Infográficos ──────────────────────────────────────────
  function loadInfograficos() {
    infograficosLoading.hidden = false;
    infograficosGrid.innerHTML = "";

    INFOGRAFICOS_LIST.forEach(function (n) {
      infograficosCurrentMode[n] = "desk";
      infograficosGrid.appendChild(createInfograficoCard(n));
    });

    var count = INFOGRAFICOS_LIST.length;
    infograficosSubtitle.textContent =
      count + " infográfico" + (count !== 1 ? "s" : "") + " disponíve" + (count !== 1 ? "is" : "l");

    INFOGRAFICOS_LIST.forEach(function (n, i) {
      setTimeout(function () { loadInfograficoIframe(n); }, i * 150);
    });

    infograficosLoaded = true;
    infograficosLoading.hidden = true;

    setupInfograficosSearch();
  }

  function createInfograficoCard(numero) {
    var col = document.createElement("div");
    col.className = "infog-col";
    col.dataset.infografico = numero;

    col.innerHTML =
      '<div class="infog-card">' +
        '<div class="infog-card-header">' +
          '<div class="infog-card-num">#' + numero + '</div>' +
          '<div class="infog-card-actions">' +
            '<button class="infog-copy-btn" ' +
              'onclick="infograficosCopy(\'infografico' + numero + '\',this)">Copiar ID</button>' +
          '</div>' +
        '</div>' +
        '<div class="infog-preview-container" id="info-preview-' + numero + '">' +
          '<div class="infog-spinner">' +
            '<div class="spinner-ring" style="width:20px;height:20px;border-width:2px"></div>' +
          '</div>' +
        '</div>' +
        '<div class="infog-card-footer">' +
          '<code class="infog-code">data-infografico="infografico' + numero + '"</code>' +
        '</div>' +
      '</div>';

    return col;
  }

  function loadInfograficoIframe(numero) {
    var mode = infograficosCurrentMode[numero] || "desk";
    var container = document.getElementById("info-preview-" + numero);
    if (!container) return;

    var iframe = document.createElement("iframe");
    iframe.src = "/web/infograficos/preview.html?id=infografico" + numero + "&mode=" + mode;
    iframe.title = "Infográfico " + numero + " — " + mode;
    iframe.loading = "lazy";
    iframe.setAttribute("scrolling", "no");
    iframe.setAttribute("frameborder", "0");

    container.innerHTML = "";
    container.appendChild(iframe);
  }

  function setupInfograficosSearch() {
    if (!infograficosSearch) return;
    infograficosSearch.addEventListener("input", function (e) {
      var q = e.target.value.toLowerCase().replace(/\s/g, "");
      var visible = 0;

      INFOGRAFICOS_LIST.forEach(function (n) {
        var col = infograficosGrid.querySelector('[data-infografico="' + n + '"]');
        if (!col) return;
        var matches = !q || ("infografico" + n).includes(q) || n.toString().includes(q);
        col.style.display = matches ? "" : "none";
        if (matches) visible++;
      });

      if (infograficosNoResults) {
        infograficosNoResults.hidden = visible > 0;
        if (infograficosSearchTerm) infograficosSearchTerm.textContent = q;
      }
    });
  }

  window.addEventListener("message", function (e) {
    var data = e.data || {};
    if (data.type === "infopack-loaded") {
      var match = (data.id || "").match(/\d+$/);
      if (!match) return;
      var numero = match[0];
      var container = document.getElementById("info-preview-" + numero);
      var iframe = container && container.querySelector("iframe");
      if (!iframe || !container) return;
      var containerWidth = container.offsetWidth || container.parentElement.offsetWidth || 400;
      if (!data.width || data.width <= 0) return;
      var scale = containerWidth / data.width;
      iframe.style.width  = data.width  + "px";
      iframe.style.height = data.height + "px";
      iframe.style.transform = "scale(" + scale + ")";
      container.style.height = Math.round(data.height * scale) + "px";
    }
    if (data.type === "infopack-error") {
      var match = (data.id || "").match(/\d+$/);
      if (!match) return;
      var col = infograficosGrid && infograficosGrid.querySelector('[data-infografico="' + match[0] + '"]');
      if (col) {
        var container = col.querySelector(".infog-preview-container");
        if (container) {
          container.innerHTML =
            '<p style="color:var(--gray-400);font-size:.75rem;padding:1rem;text-align:center">' +
            '⚠️ Não foi possível carregar este infográfico</p>';
        }
        infograficosGrid.appendChild(col);
      }
    }
  });

  window.infograficosToggleMode = function (numero, mode, btn) {
    infograficosCurrentMode[numero] = mode;
    var card = btn.closest(".infog-card");
    card.querySelectorAll(".infog-mode-btn").forEach(function (b) {
      b.classList.toggle("active", b.dataset.mode === mode);
    });
    loadInfograficoIframe(numero);
  };

  window.infograficosCopy = function (id, btn) {
    navigator.clipboard.writeText(id).then(function () {
      var orig = btn.textContent;
      btn.textContent = "✓ Copiado!";
      btn.classList.add("copied");
      setTimeout(function () {
        btn.textContent = orig;
        btn.classList.remove("copied");
      }, 2000);
    });
  };

  // ── navigateToGallery ─────────────────────────────────────
  function navigateToGallery(profileName) {
    navItems.forEach(function (b) {
      b.classList.remove("is-active");
      b.removeAttribute("aria-current");
    });
    var galleryBtn = document.querySelector('[data-view="gallery"]');
    if (galleryBtn) {
      galleryBtn.classList.add("is-active");
      galleryBtn.setAttribute("aria-current", "page");
    }
    document.querySelectorAll(".view").forEach(function (v) {
      v.hidden = v.id !== "view-gallery";
    });
    galleryLoaded = false;
    galleryCurrentProfile = profileName;
    loadGallery(profileName);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // ── Copiar HTML do tópico atual ───────────────────────────
  function copyCurrentTopicoHtml() {
    var topico = currentTopicos[currentTopicoIndex];
    if (!topico) return;
    var parser = new DOMParser();
    var doc = parser.parseFromString(topico.html, "text/html");
    var firstDiv = doc.body.firstElementChild;
    var htmlToCopy = firstDiv ? firstDiv.outerHTML : doc.body.innerHTML;
    navigator.clipboard.writeText(htmlToCopy).then(function () {
      var originalHTML = copyHtmlBtn.innerHTML;
      copyHtmlBtn.textContent = "Copiado!";
      copyHtmlBtn.disabled = true;
      setTimeout(function () {
        copyHtmlBtn.innerHTML = originalHTML;
        copyHtmlBtn.disabled = false;
      }, 2000);
    }).catch(function () {
      alert("Não foi possível copiar. Tente baixar o arquivo.");
    });
  }
  copyHtmlBtn.addEventListener("click", copyCurrentTopicoHtml);

  // ── Init ──────────────────────────────────────────────────
  loadProfiles();
})();
