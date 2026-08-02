/* ═══════════════════════════════════════════════════════════════
   CottonGreen AI — Unified Frontend Application Logic
   ═══════════════════════════════════════════════════════════════ */

(function() {
  "use strict";

  // ── LANGUAGE STATE ────────────────────────────────────────────────
  let currentLang = localStorage.getItem("cgai_lang") || "en";

  // ── DOM ELEMENTS ─────────────────────────────────────────────────
  const $ = id => document.getElementById(id);

  const escapeHTML = str => {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  };

  const dropZone      = $("dropZone"),
        fileInput      = $("fileInput"),
        dropContent    = $("dropContent"),
        previewWrap    = $("previewWrap"),
        previewImg     = $("previewImg"),
        removeBtn      = $("removeBtn"),
        panelIdle      = $("panelIdle"),
        panelReady     = $("panelReady"),
        analyzeBtn     = $("analyzeBtn"),
        resultCard     = $("resultCard"),
        errorCard      = $("errorCard"),
        errorMsg       = $("errorMsg"),
        retryBtn       = $("retryBtn"),
        newBtn         = $("newBtn"),
        langSelect     = $("langSelect"),
        printBtn       = $("printBtn"),
        startCameraBtn = $("startCameraBtn"),
        cameraWrap     = $("cameraWrap"),
        cameraVideo    = $("cameraVideo"),
        captureBtn     = $("captureBtn"),
        closeCameraBtn = $("closeCameraBtn"),
        cameraCanvas   = $("cameraCanvas"),
        historyGrid    = $("historyGrid"),
        historyEmpty   = $("historyEmpty"),
        clearHistBtn   = $("clearHistoryBtn"),
        avatarBtn      = $("avatarBtn"),
        userDropdown   = $("userDropdown"),
        userDropdownWrap = $("userDropdownWrap"),
        oodWarning     = $("oodWarning"),
        normalResult   = $("normalResult"),
        oodDetectedLabel = $("oodDetectedLabel"),
        oodExplanation = $("oodExplanation");

  // Result Card fields
  const resultIcon     = $("resultIcon"),
        resultDisease  = $("resultDisease"),
        resultSeverity = $("resultSeverity"),
        confValue      = $("confValue"),
        confBarFill    = $("confBarFill"),
        resultDesc     = $("resultDesc"),
        resultTreatment   = $("resultTreatment"),
        resultPrevention  = $("resultPrevention"),
        top3List          = $("top3List");

  // ── STATE ─────────────────────────────────────────────────────────
  let selectedFile   = null;
  let probChart      = null;
  let lastResultData = null;  // Stores last prediction result for re-rendering on lang change
  let cameraStream   = null;
  let scanHistory    = [];    // Populated from the server

  // ── CSRF PROTECTION ───────────────────────────────────────────────
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute("content");

  // ── SEVERITY → CSS CLASS MAP ──────────────────────────────────────
  const SEV_CLASS = {
    "None":        "sev-none",
    "Low":         "sev-low",
    "Low–Medium":  "sev-low",
    "Medium":      "sev-medium",
    "High":        "sev-high",
    "Very High":   "sev-critical",
  };

  // ═══════════════════════════════════════════════════════════════════
  // I18N — LANGUAGE SYSTEM
  // ═══════════════════════════════════════════════════════════════════

  function t(key) {
    if (!window.TRANSLATIONS) return null;
    const lang = window.TRANSLATIONS[currentLang] || window.TRANSLATIONS["en"];
    return lang[key] !== undefined ? lang[key] : (window.TRANSLATIONS["en"][key] || null);
  }

  function tDisease(diseaseName, field) {
    if (!window.TRANSLATIONS) return "";
    const lang = window.TRANSLATIONS[currentLang] || window.TRANSLATIONS["en"];
    const diseases = lang.diseases || {};
    const info = diseases[diseaseName];
    if (info && info[field] !== undefined) return info[field];
    // Fallback to English
    const enInfo = window.TRANSLATIONS["en"].diseases[diseaseName];
    return enInfo ? (enInfo[field] || "") : "";
  }

  function applyLanguage(lang) {
    currentLang = lang;
    localStorage.setItem("cgai_lang", lang);
    document.body.setAttribute("data-lang", lang);
    document.documentElement.setAttribute("lang", lang === "te" ? "te" : lang === "hi" ? "hi" : "en");

    // Update language picker
    if (langSelect) langSelect.value = lang;

    // Translate all [data-i18n] elements
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const key = el.getAttribute("data-i18n");
      const translated = t(key);
      if (translated) el.textContent = translated;
    });

    // Translate all [data-i18n-title] attributes
    document.querySelectorAll("[data-i18n-title]").forEach(el => {
      const key = el.getAttribute("data-i18n-title");
      const translated = t(key);
      if (translated) el.setAttribute("title", translated);
    });

    // Translate disease cards [data-i18n-disease][data-i18n-field]
    document.querySelectorAll("[data-i18n-disease]").forEach(el => {
      const disease = el.getAttribute("data-i18n-disease");
      const field   = el.getAttribute("data-i18n-field");
      if (disease && field) {
        el.textContent = tDisease(disease, field);
      }
    });

    // Re-render result card if we have data
    if (lastResultData && resultCard && resultCard.style.display !== "none") {
      renderResult(lastResultData);
    }
    
    // Re-render history to translate names
    renderHistory();
    
    // Check model status (refreshes translation on header indicator)
    checkModelStatus();
  }

  if (langSelect) {
    langSelect.value = currentLang;
    langSelect.addEventListener("change", () => applyLanguage(langSelect.value));
  }

  // ── USER DROPDOWN ──────────────────────────────────────────────────
  if (avatarBtn && userDropdown) {
    avatarBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = userDropdown.style.display !== "none";
      userDropdown.style.display = isOpen ? "none" : "block";
      avatarBtn.setAttribute("aria-expanded", String(!isOpen));
    });

    // Close when clicking outside
    document.addEventListener("click", (e) => {
      if (userDropdownWrap && !userDropdownWrap.contains(e.target)) {
        userDropdown.style.display = "none";
        avatarBtn.setAttribute("aria-expanded", "false");
      }
    });

    // Close on Escape key
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        userDropdown.style.display = "none";
        avatarBtn.setAttribute("aria-expanded", "false");
      }
    });
  }

  // ── IMAGE COMPRESSION UTILITY ──────────────────────────────────────
  async function compressImage(file, maxDim = 1024, quality = 0.8) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
          const canvas = document.createElement("canvas");
          let width = img.width;
          let height = img.height;
          if (width > height && width > maxDim) {
            height *= maxDim / width;
            width = maxDim;
          } else if (height > maxDim) {
            width *= maxDim / height;
            height = maxDim;
          }
          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext("2d");
          ctx.drawImage(img, 0, 0, width, height);
          canvas.toBlob((blob) => {
            if (blob) {
              blob.name = file.name || "compressed.jpg";
              resolve(blob);
            } else {
              reject(new Error("Compression failed"));
            }
          }, "image/jpeg", quality);
        };
        img.onerror = () => reject(new Error("Image failed to load"));
        img.src = e.target.result;
      };
      reader.onerror = () => reject(new Error("File failed to read"));
      reader.readAsDataURL(file);
    });
  }

  // ── HANDLE FILE ───────────────────────────────────────────────────
  async function handleFile(file) {
    if (!file || !file.type.startsWith("image/")) {
      showError(t("err_invalid_image") || "Please select a valid image file (JPG, PNG, WebP).");
      return;
    }
    if (file.size > 16 * 1024 * 1024) {
      showError(t("err_file_too_large") || "File is too large. Maximum size is 16 MB.");
      return;
    }

    try {
      selectedFile = await compressImage(file);
    } catch (err) {
      selectedFile = file; // Fallback to raw file
    }

    const reader = new FileReader();
    reader.onload = e => {
      previewImg.src = e.target.result;
      previewWrap.style.display = "flex";
      if (dropContent) dropContent.style.display = "none";
      if (cameraWrap) cameraWrap.style.display  = "none";
      panelIdle.style.display   = "none";
      panelReady.style.display  = "block";
      resultCard.style.display  = "none";
      errorCard.style.display   = "none";
    };
    reader.readAsDataURL(selectedFile);
  }

  function resetUI() {
    selectedFile = null;
    lastResultData = null;
    if (fileInput) fileInput.value = "";
    previewWrap.style.display = "none";
    if (dropContent) dropContent.style.display = "block";
    panelIdle.style.display   = "block";
    panelReady.style.display  = "none";
    resultCard.style.display  = "none";
    errorCard.style.display   = "none";
    previewImg.src = "";
    setAnalyzeBtn(false);
    stopCamera();
    if (probChart) {
      probChart.destroy();
      probChart = null;
    }
  }

  if (dropZone) {
    dropZone.addEventListener("click", e => {
      if (e.target.closest("#startCameraBtn") || e.target.closest(".preview-remove") ||
          e.target.closest(".camera-controls")) return;
      fileInput.click();
    });
    dropZone.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") fileInput.click(); });
    dropZone.addEventListener("dragover", e => { e.preventDefault(); dropZone.classList.add("drag-over"); });
    dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
    dropZone.addEventListener("drop", e => {
      e.preventDefault();
      dropZone.classList.remove("drag-over");
      if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
    });
    fileInput.addEventListener("change", () => { if (fileInput.files.length) handleFile(fileInput.files[0]); });
  }
  if (removeBtn) removeBtn.addEventListener("click", e => { e.stopPropagation(); resetUI(); });

  // ── CAMERA LOGIC ──────────────────────────────────────────────────
  function stopCamera() {
    if (cameraStream) {
      cameraStream.getTracks().forEach(t => t.stop());
      cameraStream = null;
    }
    if (cameraWrap) cameraWrap.style.display = "none";
  }

  if (startCameraBtn) {
    startCameraBtn.addEventListener("click", async e => {
      e.stopPropagation();
      try {
        cameraStream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment", width: { ideal: 1280 } }
        });
        cameraVideo.srcObject = cameraStream;
        cameraWrap.style.display = "block";
        if (dropContent) dropContent.style.display = "none";
      } catch {
        showError(t("err_network") || "Camera access denied or not available.");
      }
    });
  }

  if (captureBtn) {
    captureBtn.addEventListener("click", e => {
      e.stopPropagation();
      if (!cameraStream) return;
      cameraCanvas.width  = cameraVideo.videoWidth;
      cameraCanvas.height = cameraVideo.videoHeight;
      cameraCanvas.getContext("2d").drawImage(cameraVideo, 0, 0);
      cameraCanvas.toBlob(blob => {
        if (blob) {
          handleFile(new File([blob], "camera_capture.jpg", { type: "image/jpeg" }));
          stopCamera();
        }
      }, "image/jpeg", 0.9);
    });
  }

  if (closeCameraBtn) {
    closeCameraBtn.addEventListener("click", e => {
      e.stopPropagation();
      stopCamera();
      if (dropContent) dropContent.style.display = "block";
    });
  }

  // ── ANALYZE ───────────────────────────────────────────────────────
  function setAnalyzeBtn(loading) {
    if (!analyzeBtn) return;
    const txtEl  = analyzeBtn.querySelector(".btn-text");
    const loadEl = analyzeBtn.querySelector(".btn-loader");
    analyzeBtn.disabled = loading;
    if (txtEl)  txtEl.style.display  = loading ? "none" : "inline";
    if (loadEl) loadEl.style.display = loading ? "inline-flex" : "none";
  }

  if (analyzeBtn) {
    analyzeBtn.addEventListener("click", async () => {
      if (!selectedFile) return;
      setAnalyzeBtn(true);
      errorCard.style.display  = "none";
      resultCard.style.display = "none";

      const form = new FormData();
      form.append("file", selectedFile);
      form.append("save", "true"); // Tell backend to save user scan history

      const headers = {};
      if (csrfToken) {
        headers["X-CSRFToken"] = csrfToken;
      }

      try {
        const res = await fetch("/api/v1/predict", {
          method: "POST",
          body: form,
          headers: headers
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || t("error_default") || "Server error");
        
        lastResultData = data;
        renderResult(data);
        await loadHistory(); // Reload server-backed history
      } catch (err) {
        showError(err.message || t("err_network") || "Network error. Please try again.");
      } finally {
        setAnalyzeBtn(false);
      }
    });
  }

  // ── RENDER OOD RESULT ─────────────────────────────────────────────
  function renderOodResult(data) {
    const label = data.ood_label || "Unknown Object";
    const conf = data.ood_confidence || 0;

    // Build detected label badge
    if (oodDetectedLabel) {
      oodDetectedLabel.innerHTML = `<span class="ood-badge">${escapeHTML(label)} (${conf.toFixed(1)}%)</span>`;
    }

    // Build detailed explanation
    const explanationText = (t("ood_explanation") || "Our AI system analyzed your image and identified it as \"{{label}}\" with {{conf}}% confidence. This application is specifically designed to diagnose diseases in cotton plant leaves only. The uploaded image does not appear to be a cotton leaf, so we cannot provide a reliable disease diagnosis. Please upload a clear photograph of a cotton leaf for accurate results.")
      .replace("{{label}}", label)
      .replace("{{conf}}", conf.toFixed(1));
    if (oodExplanation) oodExplanation.textContent = explanationText;

    // Show OOD, hide normal
    if (oodWarning) oodWarning.style.display = "block";
    if (normalResult) normalResult.style.display = "none";
    resultCard.style.display = "block";
    resultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  // ── RENDER RESULT ─────────────────────────────────────────────────
  function renderResult(data) {
    // Check for OOD (out-of-distribution) result
    if (data.is_ood) {
      renderOodResult(data);
      return;
    }

    // Show normal result, hide OOD
    if (oodWarning) oodWarning.style.display = "none";
    if (normalResult) normalResult.style.display = "block";

    const info = data.info || {};
    const diseaseName = data.disease; // Standard English disease name from model

    // Severity and localizations
    const translatedName = tDisease(diseaseName, "name") || diseaseName;
    const originalSev    = info.severity || "Unknown";
    const translatedSev  = tDisease(diseaseName, "severity") || originalSev;

    resultDisease.textContent  = translatedName;
    resultSeverity.textContent = translatedSev;
    resultSeverity.className   = "result-sev-badge " + (SEV_CLASS[originalSev] || "sev-medium");
    resultIcon.textContent     = diseaseName === "Healthy Leaf" ? "🌿" : "⚠️";

    // Confidence
    const conf = data.confidence;
    confValue.textContent = conf.toFixed(1) + "%";
    confBarFill.style.width = "0%";
    setTimeout(() => { confBarFill.style.width = conf + "%"; }, 50);

    // Multilingual description & remedies
    resultDesc.textContent       = tDisease(diseaseName, "description") || info.description || "—";
    resultTreatment.textContent  = tDisease(diseaseName, "treatment")   || info.treatment   || "—";
    resultPrevention.textContent = tDisease(diseaseName, "prevention")  || info.prevention  || "—";

    // Top 3 Prediction List with Rank Emojis
    const ranks = ["🥇", "🥈", "🥉"];
    top3List.innerHTML = "";
    if (data.top3) {
      data.top3.forEach((item, i) => {
        const [name, pct] = item;
        const translatedTopLabel = tDisease(name, "name") || name;
        top3List.innerHTML += `
          <div class="top3-row">
            <div class="top3-rank">${ranks[i] || i + 1}</div>
            <div class="top3-name">${escapeHTML(translatedTopLabel)}</div>
            <div class="top3-pct">${pct.toFixed(1)}%</div>
          </div>`;
      });
    }

    // Chart.js Class Probabilities
    if (data.all_probs) {
      const labels = Object.keys(data.all_probs).map(name => tDisease(name, "name") || name);
      const values = Object.values(data.all_probs);
      const maxVal = Math.max(...values);
      const colors = Object.keys(data.all_probs).map(name =>
        name === diseaseName ? "hsl(142,62%,45%)" : "hsl(142,12%,28%)"
      );

      if (probChart) probChart.destroy();
      probChart = new Chart($("probChart"), {
        type: "bar",
        data: {
          labels,
          datasets: [{
            data: values,
            backgroundColor: colors,
            borderRadius: 4,
            barThickness: 22
          }]
        },
        options: {
          indexAxis: "y",
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              max: 100,
              grid: { color: "rgba(255,255,255,.06)" },
              ticks: { color: "#8fa89a", callback: v => v + "%" }
            },
            y: {
              grid: { display: false },
              ticks: { color: "#e8f0ec", font: { size: 11 } }
            }
          },
          plugins: {
            legend: { display: false }
          }
        }
      });
    }

    resultCard.style.display = "block";
    resultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function showError(msg) {
    if (errorMsg) errorMsg.textContent = msg;
    if (errorCard) errorCard.style.display = "block";
    if (resultCard) resultCard.style.display = "none";
  }

  // ── Actions ───────────────────────────────────────────────────────
  if ($("newBtn")) $("newBtn").addEventListener("click", resetUI);
  if ($("retryBtn")) $("retryBtn").addEventListener("click", () => {
    errorCard.style.display = "none";
    if (selectedFile) analyzeBtn.click();
  });
  if (printBtn) printBtn.addEventListener("click", () => window.print());

  // ── SERVER SCANS HISTORY ──────────────────────────────────────────
  async function loadHistory() {
    try {
      const res = await fetch("/api/v1/history?page=1&per_page=12");
      if (res.ok) {
        const data = await res.json();
        scanHistory = data.scans || [];
      }
    } catch (_) { /* Fallback to offline empty */ }
    renderHistory();
  }

  function renderHistory() {
    if (!historyGrid) return;
    if (!scanHistory || scanHistory.length === 0) {
      historyGrid.innerHTML = "";
      if (historyEmpty) historyEmpty.style.display = "block";
      if (clearHistBtn) clearHistBtn.style.display = "none";
      return;
    }

    if (historyEmpty) historyEmpty.style.display = "none";
    if (clearHistBtn) clearHistBtn.style.display = "inline-flex";

    historyGrid.innerHTML = scanHistory.map(item => {
      const d = new Date(item.date);
      const isTe = currentLang === "te";
      const isHi = currentLang === "hi";
      const dateOpts = { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" };
      const dateStr = d.toLocaleDateString(isTe ? "te-IN" : isHi ? "hi-IN" : "en-US", dateOpts);

      const originalSev    = item.severity || "Unknown";
      const translatedName = tDisease(item.disease, "name") || item.disease;
      const translatedSev  = tDisease(item.disease, "severity") || originalSev;
      const severityClass  = SEV_CLASS[originalSev] || "sev-medium";
      const thumb = item.thumb || "";
      const thumbHtml = (thumb && thumb.startsWith("data:image/"))
        ? `<img class="history-thumb" src="${escapeHTML(thumb)}" alt="scan" style="width: 50px; height: 50px; object-fit: cover; border-radius: 6px; margin-right: 12px;" />`
        : `<div class="history-thumb-placeholder" style="width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,.05); border-radius: 6px; margin-right: 12px;">🍃</div>`;

      return `
        <div class="history-card" style="display: flex; align-items: center; padding: 12px; background: rgba(255,255,255,.02); border: 1px solid rgba(255,255,255,.06); border-radius: 8px;">
          ${thumbHtml}
          <div style="flex: 1;">
            <div style="display: flex; justify-content: space-between; font-weight: 500; font-family: 'Space Grotesk', sans-serif;">
              <span>${escapeHTML(translatedName)}</span>
              <span style="color: var(--accent);">${item.confidence.toFixed(1)}%</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 4px; font-size: 11px; color: #8fa89a;">
              <span class="hc-sev ${escapeHTML(severityClass)}" style="padding: 2px 6px; border-radius: 4px; font-size: 10px;">${escapeHTML(translatedSev)}</span>
              <span>${escapeHTML(dateStr)}</span>
            </div>
          </div>
        </div>`;
    }).join("");
  }

  if (clearHistBtn) {
    clearHistBtn.addEventListener("click", async () => {
      const confirmMsg = t("btn_clear_history") || "Clear all local scan history?";
      if (confirm(confirmMsg + "?")) {
        const headers = {};
        if (csrfToken) {
          headers["X-CSRFToken"] = csrfToken;
        }
        try {
          const res = await fetch("/api/v1/history", {
            method: "DELETE",
            headers: headers
          });
          if (res.ok) {
            scanHistory = [];
            renderHistory();
          }
        } catch (_) { /* Error handling */ }
      }
    });
  }

  // ── MODEL STATUS DOT ───────────────────────────────────────────────
  async function checkModelStatus() {
    try {
      const res  = await fetch("/health");
      const data = await res.json();
      const dot    = $("modelDot");
      const status = $("modelStatus");
      const isHealthy = data.model === "loaded" || data.model === "ready" || data.model === "lazy_loaded";
      if (!isHealthy) {
        if (dot)    { dot.style.background = "hsl(28,88%,58%)"; dot.classList.add("offline"); }
        if (status) { status.textContent = t("model_not_loaded") || "No Model"; }
      } else {
        if (dot)    { dot.style.background = ""; dot.classList.remove("offline"); }
        if (status) { status.textContent = t("model_ready") || "Model Ready"; }
      }
    } catch (_) { /* Server warming up */ }
  }

  // ── Smooth scroll for nav ────────────────────────────────────
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener("click", e => {
      const target = document.querySelector(a.getAttribute("href"));
      if (target) { e.preventDefault(); target.scrollIntoView({ behavior: "smooth" }); }
    });
  });

  // ── INITIALIZE ────────────────────────────────────────────────────
  applyLanguage(currentLang);
  loadHistory();
  setInterval(checkModelStatus, 10000);

})();
