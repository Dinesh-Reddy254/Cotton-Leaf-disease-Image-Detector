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
        videoPreview   = $("videoPreview"),
        captureBtn     = $("captureBtn"),
        cancelCameraBtn= $("cancelCameraBtn"),
        cameraModal    = $("cameraModal"),
        avatarBtn      = $("avatarBtn"),
        userDropdown   = $("userDropdown");

  let selectedFile = null;
  let lastResultData = null; // Store for re-translation
  let videoStream = null;

  // Confidence UI settings
  const SEVERITY_COLORS = {
    "None":        "#10b981", // green-500
    "Low":         "#10b981", // green-500
    "Low–Medium":  "#10b981", // green-500
    "Medium":      "#f59e0b", // amber-500
    "High":        "#ef4444", // red-500
    "Very High":   "#dc2626", // red-600
  };

  const SEVERITY_CLASSES = {
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

    document.addEventListener("click", (e) => {
      if (!avatarBtn.contains(e.target) && !userDropdown.contains(e.target)) {
        userDropdown.style.display = "none";
        avatarBtn.setAttribute("aria-expanded", "false");
      }
    });
  }

  // ═══════════════════════════════════════════════════════════════════
  // FILE UPLOAD & CAMERA SYSTEM
  // ═══════════════════════════════════════════════════════════════════

  if (dropZone) {
    ["dragenter", "dragover", "dragleave", "drop"].forEach(ev => {
      dropZone.addEventListener(ev, preventDefaults, false);
    });
    
    ["dragenter", "dragover"].forEach(ev => {
      dropZone.addEventListener(ev, () => dropZone.classList.add("dragover"), false);
    });
    
    ["dragleave", "drop"].forEach(ev => {
      dropZone.addEventListener(ev, () => dropZone.classList.remove("dragover"), false);
    });
    
    dropZone.addEventListener("drop", handleDrop, false);
    
    if (fileInput) {
      fileInput.addEventListener("change", function() {
        if (this.files && this.files.length > 0) {
          handleFile(this.files[0]);
        }
      });
    }
  }

  if (removeBtn) {
    removeBtn.addEventListener("click", resetUpload);
  }

  if (newBtn) {
    newBtn.addEventListener("click", resetUpload);
  }

  if (retryBtn) {
    retryBtn.addEventListener("click", () => {
      errorCard.style.display = "none";
      if (selectedFile) doAnalysis();
    });
  }

  if (analyzeBtn) {
    analyzeBtn.addEventListener("click", doAnalysis);
  }

  if (printBtn) {
    printBtn.addEventListener("click", () => {
      window.print();
    });
  }
  
  // CAMERA LOGIC
  if (startCameraBtn) {
    startCameraBtn.addEventListener("click", openCamera);
  }
  
  if (cancelCameraBtn) {
    cancelCameraBtn.addEventListener("click", closeCamera);
  }
  
  if (captureBtn) {
    captureBtn.addEventListener("click", captureImage);
  }

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) handleFile(files[0]);
  }

  function handleFile(file) {
    if (!file.type.match("image.*")) {
      alert("Please upload a valid image file (JPG, PNG, WebP).");
      return;
    }
    if (file.size > 16 * 1024 * 1024) {
      alert("File is too large. Maximum size is 16MB.");
      return;
    }
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = e => {
      previewImg.src = e.target.result;
      dropContent.style.display = "none";
      previewWrap.style.display = "block";
      panelIdle.style.display = "none";
      panelReady.style.display = "block";
      resultCard.style.display = "none";
      errorCard.style.display = "none";
    };
    reader.readAsDataURL(file);
  }

  function resetUpload() {
    selectedFile = null;
    if (fileInput) fileInput.value = "";
    previewImg.src = "";
    dropContent.style.display = "flex";
    previewWrap.style.display = "none";
    panelIdle.style.display = "block";
    panelReady.style.display = "none";
    resultCard.style.display = "none";
    errorCard.style.display = "none";
    lastResultData = null;
  }

  // Camera Functions
  async function openCamera() {
    try {
      videoStream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: "environment" } 
      });
      videoPreview.srcObject = videoStream;
      cameraModal.style.display = "flex";
      videoPreview.play();
    } catch (err) {
      alert("Could not access camera. Please ensure permissions are granted.");
      console.error("Camera error:", err);
    }
  }
  
  function closeCamera() {
    if (videoStream) {
      videoStream.getTracks().forEach(track => track.stop());
      videoStream = null;
    }
    cameraModal.style.display = "none";
  }
  
  function captureImage() {
    if (!videoStream) return;
    
    const canvas = document.createElement("canvas");
    canvas.width = videoPreview.videoWidth;
    canvas.height = videoPreview.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(videoPreview, 0, 0, canvas.width, canvas.height);
    
    canvas.toBlob(blob => {
      const file = new File([blob], "camera_capture.jpg", { type: "image/jpeg" });
      handleFile(file);
      closeCamera();
    }, "image/jpeg", 0.9);
  }

  // ═══════════════════════════════════════════════════════════════════
  // INFERENCE ENGINE
  // ═══════════════════════════════════════════════════════════════════

  async function doAnalysis() {
    if (!selectedFile) return;

    // Set UI to loading state
    analyzeBtn.disabled = true;
    const origText = analyzeBtn.innerHTML;
    analyzeBtn.innerHTML = `
      <svg class="spinner" viewBox="0 0 50 50">
        <circle class="path" cx="25" cy="25" r="20" fill="none" stroke-width="5"></circle>
      </svg>
      ${t("btn_analyzing") || "Analyzing..."}
    `;
    
    panelReady.style.opacity = "0.7";
    resultCard.style.display = "none";
    errorCard.style.display  = "none";

    const formData = new FormData();
    formData.append("file", selectedFile);
    
    // Add CSRF token if meta tag exists
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    const headers = {};
    if (csrfMeta) {
      headers['X-CSRFToken'] = csrfMeta.getAttribute('content');
    }

    try {
      const res = await fetch("/api/v1/predict", {
        method: "POST",
        headers: headers,
        body: formData,
      });
      
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || t("error_upload") || "Analysis failed.");
      }
      
      lastResultData = data;
      renderResult(data);
      
      // Auto-refresh history
      setTimeout(loadHistory, 500);
      
    } catch (err) {
      console.error("Diagnosis error:", err);
      errorMsg.textContent = err.message || t("error_network") || "A network error occurred.";
      errorCard.style.display = "flex";
      
      // If it's a cold start timeout (Render takes 50s to wake up), give a specific message
      if (err.message.includes("fetch")) {
        errorMsg.textContent = "Server is waking up. This takes ~50 seconds on the free tier. Please try again in a moment.";
      }
    } finally {
      // Restore UI
      analyzeBtn.disabled = false;
      analyzeBtn.innerHTML = origText;
      panelReady.style.opacity = "1";
    }
  }

  // ═══════════════════════════════════════════════════════════════════
  // RESULT RENDERING
  // ═══════════════════════════════════════════════════════════════════

  function renderResult(data) {
    // 1. Core Fields
    const conf    = data.confidence;
    const disease = data.disease;
    
    // Get translations for the detected disease
    const tName      = tDisease(disease, "name") || disease;
    const tDesc      = tDisease(disease, "desc") || data.info?.description || "";
    const tCause     = tDisease(disease, "cause") || data.info?.cause || "";
    const tTreatment = tDisease(disease, "treatment") || data.info?.treatment || "";

    $("resDiseaseName").textContent = tName;
    $("resConfidence").textContent  = `${conf.toFixed(1)}%`;
    $("resDesc").textContent        = tDesc;
    $("resCause").textContent       = tCause;
    $("resTreatment").textContent   = tTreatment;

    // Is it OOD?
    const isOOD = data.is_ood === true;
    
    // Configure visual severity
    const sevLabel = isOOD ? "Error" : (data.info?.severity || "Medium");
    const sevClass = isOOD ? "sev-critical" : (SEVERITY_CLASSES[sevLabel] || "sev-medium");
    const sevColor = isOOD ? "#dc2626" : (SEVERITY_COLORS[sevLabel] || "#f59e0b");
    const resSeverity = $("resSeverity");
    
    resSeverity.className = `res-severity ${sevClass}`;
    resSeverity.textContent = isOOD ? "N/A" : sevLabel.toUpperCase();
    
    // Warning icon logic
    const iconWarn = $("iconWarn");
    const iconCheck = $("iconCheck");
    if (disease === "Healthy") {
      iconCheck.style.display = "block";
      iconWarn.style.display = "none";
    } else {
      iconCheck.style.display = "none";
      iconWarn.style.display = "block";
      iconWarn.style.color = sevColor;
    }

    // Confidence Bar
    const confBar = $("confBarFill");
    confBar.style.width = "0%";
    confBar.style.backgroundColor = sevColor;
    
    setTimeout(() => {
      confBar.style.width = `${conf}%`;
    }, 50);

    // Render "Other Possibilities"
    const top3 = data.top3 || [];
    const ul = $("otherList");
    ul.innerHTML = "";
    
    if (isOOD) {
      // Don't show top3 for OOD
      ul.parentElement.style.display = "none";
    } else if (top3.length > 1) {
      ul.parentElement.style.display = "block";
      // Skip the first one since it's the primary prediction
      for (let i = 1; i < top3.length; i++) {
        const [dName, dConf] = top3[i];
        if (dConf < 1.0) continue; // Ignore < 1%
        
        const localizedDName = tDisease(dName, "name") || dName;
        const li = document.createElement("li");
        li.innerHTML = `
          <span class="other-name">${escapeHTML(localizedDName)}</span>
          <span class="other-conf">${dConf.toFixed(1)}%</span>
        `;
        ul.appendChild(li);
      }
      if (ul.children.length === 0) {
        ul.parentElement.style.display = "none";
      }
    } else {
      ul.parentElement.style.display = "none";
    }

    // Reveal Result Card
    panelIdle.style.display = "none";
    panelReady.style.display = "none";
    resultCard.style.display = "block";
    resultCard.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // ═══════════════════════════════════════════════════════════════════
  // DIAGNOSIS HISTORY
  // ═══════════════════════════════════════════════════════════════════

  let _histDataCache = []; // Cache to allow re-rendering on language switch

  async function loadHistory() {
    const histGrid = $("histGrid");
    const emptyState = $("histEmpty");
    if (!histGrid) return;

    try {
      const res = await fetch("/api/v1/history?page=1&per_page=12");
      if (res.ok) {
        const data = await res.json();
        _histDataCache = data.items || [];
        renderHistory();
      }
    } catch (e) {
      console.error("Failed to load history:", e);
    }
  }

  function renderHistory() {
    const histGrid = $("histGrid");
    const emptyState = $("histEmpty");
    if (!histGrid) return;

    histGrid.innerHTML = "";
    
    if (_histDataCache.length === 0) {
      emptyState.style.display = "flex";
      return;
    }
    
    emptyState.style.display = "none";

    _histDataCache.forEach(item => {
      const isOOD = item.disease === "Not a Cotton Leaf";
      const localizedName = isOOD ? (tDisease("Not a Cotton Leaf", "name") || "Not a Cotton Leaf") : (tDisease(item.disease, "name") || item.disease);
      
      const sevLabel = item.severity || "Medium";
      const sevClass = isOOD ? "sev-critical" : (SEVERITY_CLASSES[sevLabel] || "sev-medium");
      
      const date = new Date(item.created_at).toLocaleDateString(undefined, { 
        month: 'short', day: 'numeric' 
      });

      const card = document.createElement("div");
      card.className = "hist-card";
      card.innerHTML = `
        <div class="hist-img" style="background-image: url('${escapeHTML(item.image_url)}')">
          <div class="hist-badge ${sevClass}">${(item.confidence || 0).toFixed(0)}%</div>
        </div>
        <div class="hist-info">
          <h4 class="hist-title">${escapeHTML(localizedName)}</h4>
          <span class="hist-date">${escapeHTML(date)}</span>
        </div>
      `;
      histGrid.appendChild(card);
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
