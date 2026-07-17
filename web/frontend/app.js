/**
 * app.js — Lógica del Frontend (Conversión RAW a JPG)
 */

document.addEventListener('DOMContentLoaded', () => {
    // ── Referencias al DOM ──────────────────────────────────────────────────
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const fileSelectedView = document.getElementById('file-selected-view');
    const fileNameEl = document.getElementById('file-name');
    const fileSizeEl = document.getElementById('file-size');
    const btnChangeFile = document.getElementById('btn-change-file');
    
    const settingsGrid = document.getElementById('settings-grid');
    const qualitySlider = document.getElementById('quality-slider');
    const qualityValue = document.getElementById('quality-value');
    const resizeRadios = document.getElementsByName('resize');
    const customSizeRow = document.getElementById('custom-size-row');
    const customSizeInput = document.getElementById('custom-size-input');
    
    const btnConvert = document.getElementById('btn-convert');
    const footerBar = document.getElementById('convert-footer');
    
    const progressView = document.getElementById('progress-view');
    const progressBar = document.getElementById('progress-bar');
    const progressTitle = document.getElementById('progress-title');
    const progressSub = document.getElementById('progress-sub');
    
    const successView = document.getElementById('success-view');
    const btnDownload = document.getElementById('btn-download');
    const btnConvertAnother = document.getElementById('btn-convert-another');
    
    const errorView = document.getElementById('error-view');
    const errorMsgEl = document.getElementById('error-message');
    const btnRetry = document.getElementById('btn-retry');

    const wakeupNotice = document.getElementById('wakeup-notice');
    const serverDot = document.getElementById('server-dot');
    const serverStatusText = document.getElementById('server-status-text');

    // ── Estado ─────────────────────────────────────────────────────────────
    let currentFile = null;
    let objectUrl = null;
    let isServerAwake = false;

    // ── Configuración de API ────────────────────────────────────────────────
    // Si no está definida en config.js, usamos localhost para desarrollo local
    const API_URL = window.API_BASE_URL || 'http://localhost:10000';

    // ── Inicialización ──────────────────────────────────────────────────────
    initWakeUp();

    // ── Event Listeners: Drag & Drop ────────────────────────────────────────
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('drag-over'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('drag-over'), false);
    });

    dropZone.addEventListener('drop', handleDrop, false);
    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    btnChangeFile.addEventListener('click', () => {
        resetState();
        fileInput.click();
    });

    // ── Event Listeners: UI ─────────────────────────────────────────────────
    qualitySlider.addEventListener('input', (e) => {
        qualityValue.textContent = e.target.value;
    });

    Array.from(resizeRadios).forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (e.target.value === 'custom') {
                customSizeRow.classList.add('visible');
            } else {
                customSizeRow.classList.remove('visible');
            }
        });
    });

    btnConvert.addEventListener('click', startConversion);
    
    btnConvertAnother.addEventListener('click', resetState);
    btnRetry.addEventListener('click', () => {
        showView('main');
    });

    btnDownload.addEventListener('click', () => {
        if (objectUrl && currentFile) {
            const a = document.createElement('a');
            a.href = objectUrl;
            // Reemplazar extensión por .jpg
            const baseName = currentFile.name.substring(0, currentFile.name.lastIndexOf('.')) || currentFile.name;
            a.download = `${baseName}.jpg`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }
    });

    // ── Funciones Core ──────────────────────────────────────────────────────
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    }

    function handleFile(file) {
        // Validar extensión simple (el backend hace la validación real)
        const validExts = ['.nef', '.cr2', '.cr3', '.arw', '.dng', '.raf', '.rw2', '.orf', '.pef'];
        const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
        
        if (!validExts.includes(ext)) {
            showError(`El archivo ${file.name} no parece ser un archivo RAW soportado.`);
            return;
        }

        if (file.size > 80 * 1024 * 1024) {
            showError(`El archivo es demasiado grande (${formatBytes(file.size)}). El máximo permitido es 80 MB.`);
            return;
        }

        currentFile = file;
        fileNameEl.textContent = file.name;
        fileSizeEl.textContent = formatBytes(file.size);
        
        dropZone.classList.add('hidden');
        fileSelectedView.classList.remove('hidden');
        btnConvert.disabled = false;
        
        showView('main');
    }

    async function startConversion() {
        if (!currentFile) return;

        showView('progress');
        
        if (!isServerAwake) {
            wakeupNotice.style.display = 'block';
            progressTitle.textContent = "Despertando servidor...";
            progressSub.textContent = "Esto puede demorar hasta 40 segundos si el servidor estaba inactivo.";
            progressBar.classList.add('indeterminate');
        } else {
            wakeupNotice.style.display = 'none';
            progressTitle.textContent = "Convirtiendo...";
            progressSub.textContent = "Procesando RAW y aplicando ajustes";
            progressBar.classList.add('indeterminate');
        }

        // Preparar FormData
        const formData = new FormData();
        formData.append('file', currentFile);
        formData.append('quality', qualitySlider.value);
        
        // Determinar max_dimension
        let maxDim = 0;
        const selectedResize = document.querySelector('input[name="resize"]:checked').value;
        if (selectedResize === '1920') maxDim = 1920;
        else if (selectedResize === '3840') maxDim = 3840;
        else if (selectedResize === 'custom') {
            maxDim = parseInt(customSizeInput.value, 10);
            if (isNaN(maxDim) || maxDim <= 0) maxDim = 0;
        }
        formData.append('max_dimension', maxDim);

        try {
            const response = await fetch(`${API_URL}/convert`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                let errMsg = `Error del servidor (${response.status})`;
                try {
                    const errData = await response.json();
                    errMsg = errData.detail || errMsg;
                } catch (e) {}
                throw new Error(errMsg);
            }

            // Éxito: obtener el blob del JPEG
            const blob = await response.blob();
            
            // Limpiar URL anterior si existe
            if (objectUrl) URL.revokeObjectURL(objectUrl);
            
            objectUrl = URL.createObjectURL(blob);
            isServerAwake = true; // Si respondió, está despierto
            updateServerStatus(true);
            
            showView('success');

        } catch (error) {
            console.error("Error en conversión:", error);
            showError(error.message || "No se pudo conectar con el servidor. Revisá que esté corriendo.");
            updateServerStatus(false);
        } finally {
            progressBar.classList.remove('indeterminate');
        }
    }

    // ── Utilidades ──────────────────────────────────────────────────────────
    function showView(view) {
        settingsGrid.classList.add('hidden');
        footerBar.classList.add('hidden');
        progressView.style.display = 'none';
        successView.style.display = 'none';
        errorView.style.display = 'none';

        if (view === 'main') {
            settingsGrid.classList.remove('hidden');
            footerBar.classList.remove('hidden');
        } else if (view === 'progress') {
            progressView.style.display = 'flex';
        } else if (view === 'success') {
            successView.style.display = 'flex';
        } else if (view === 'error') {
            errorView.style.display = 'flex';
        }
    }

    function resetState() {
        currentFile = null;
        if (objectUrl) {
            URL.revokeObjectURL(objectUrl);
            objectUrl = null;
        }
        fileInput.value = '';
        dropZone.classList.remove('hidden');
        fileSelectedView.classList.add('hidden');
        btnConvert.disabled = true;
        showView('main');
    }

    function showError(msg) {
        errorMsgEl.textContent = msg;
        showView('error');
    }

    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    // Ping al servidor para despertarlo (Render free tier)
    async function initWakeUp() {
        updateServerStatus(false, "Conectando...");
        try {
            const res = await fetch(`${API_URL}/health`);
            if (res.ok) {
                isServerAwake = true;
                updateServerStatus(true);
            } else {
                updateServerStatus(false, "Servidor inactivo");
            }
        } catch (e) {
            updateServerStatus(false, "Servidor inactivo");
        }
    }

    function updateServerStatus(isAwake, textOverride = null) {
        if (isAwake) {
            serverDot.classList.remove('sleeping');
            serverStatusText.textContent = textOverride || "Backend conectado";
        } else {
            serverDot.classList.add('sleeping');
            serverStatusText.textContent = textOverride || "Servidor durmiendo (Render Free)";
        }
    }
});
