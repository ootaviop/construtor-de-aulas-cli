(function () {
  "use strict";

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
  const btnNew = document.getElementById("btn-new");
  const iframe = document.getElementById("preview-frame");

  const profilesList = document.getElementById("profiles-list");
  const templatesList = document.getElementById("templates-list");

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
          "</div></div>";
      });

      profilesList.innerHTML =
        '<div style="display:flex;flex-direction:column;gap:1rem">' +
        html +
        "</div>";
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

  function setLoading(loading) {
    spinner.hidden = !loading;
    submitBtn.disabled = loading;
    submitBtn.innerHTML = loading
      ? '<div class="spinner-ring" style="width:18px;height:18px;border-width:2px;flex-shrink:0"></div> Convertendo…'
      : '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:18px;height:18px"><path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z" /></svg> Converter documento';
  }

  // ── Blob cleanup ──────────────────────────────────────────
  var previousBlobUrl = null;
  function cleanupPreviousBlob() {
    if (previousBlobUrl) {
      URL.revokeObjectURL(previousBlobUrl);
      previousBlobUrl = null;
    }
  }

  // ── "Nova conversão" ──────────────────────────────────────
  btnNew.addEventListener("click", function () {
    resultSec.hidden = true;
    document.getElementById("form-section").hidden = false;
    fileInput.value = "";
    fileInfo.hidden = true;
    dropZone.style.display = "";
    cleanupPreviousBlob();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  // ── Submit ────────────────────────────────────────────────
  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    clearError();
    resultSec.hidden = true;
    cleanupPreviousBlob();

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
    document.getElementById("form-section").hidden = true;

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

      const blob = await res.blob();
      const blobUrl = URL.createObjectURL(blob);
      previousBlobUrl = blobUrl;

      const stem = file.name.replace(/\.docx$/i, "");
      dlLink.href = blobUrl;
      dlLink.download = stem + ".html";
      iframe.src = blobUrl;

      resultSec.hidden = false;
      resultSec.scrollIntoView({ behavior: "smooth" });
    } catch (err) {
      document.getElementById("form-section").hidden = false;
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

  // ── Init ──────────────────────────────────────────────────
  loadProfiles();
})();
