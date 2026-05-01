// static/js/right-panel.js
// Self-contained right panel with multi-tab support

(function () {
    let tabs    = [];   // { id, type, title, icon, file, data, outputText, outputAction }
    let activeId = null;
    let tabCounter = 0;

    // ── DOM refs (set after DOMContentLoaded) ─────────────────────
    let panel, overlay, tabBar, tabContent, closeBtn;

    document.addEventListener('DOMContentLoaded', init);

    function init() {
        panel      = document.getElementById('rightPanel');
        overlay    = document.getElementById('rightPanelOverlay');
        tabBar     = document.getElementById('rpTabBar');
        tabContent = document.getElementById('rpTabContent');
        closeBtn   = document.getElementById('rpCloseBtn');

        if (!panel) return;

        // Create the collapsed edge strip
        const strip = document.createElement('div');
        strip.id = 'rpEdgeStrip';
        strip.className = 'rp-edge-strip';
        strip.innerHTML = '<div class="rp-edge-handle"><i class="fas fa-chevron-left"></i></div><div class="rp-edge-tabs" id="rpEdgeTabs"></div>';
        document.body.appendChild(strip);

        // Clicking the handle opens panel if tabs exist
        strip.querySelector('.rp-edge-handle').addEventListener('click', () => {
            if (tabs.length) openPanel();
        });

        closeBtn?.addEventListener('click', collapsePanel);
        overlay?.addEventListener('click', collapsePanel);
        document.addEventListener('keydown', e => { if (e.key === 'Escape') collapsePanel(); });
    }

    // ── Public API ────────────────────────────────────────────────

    function openFileTab(file, type) {
        const ext  = file.name.split('.').pop().toLowerCase();
        const icon = type === 'audio' ? 'fa-file-audio' :
                     ['jpg','jpeg','png','gif','bmp'].includes(ext) ? 'fa-file-image' :
                     ext === 'pdf' ? 'fa-file-pdf' : 'fa-file-alt';

        const id = ++tabCounter;
        tabs.push({ id, type: 'file', fileType: type, title: file.name, icon, file, outputText: null, outputAction: null });
        renderTabs();
        switchTab(id);
        openPanel();
        return id;
    }

    function openYoutubeTab(notes) {
        const id = ++tabCounter;
        tabs.push({ id, type: 'youtube', title: notes.title || 'YouTube Notes', icon: 'fa-youtube fab', notes, outputText: null });
        renderTabs();
        switchTab(id);
        openPanel();
        return id;
    }

    function openNoteTab(note) {
        // Re-use existing tab if same note is already open
        const existing = tabs.find(t => t.type === 'note' && t.noteId === note.id);
        if (existing) { switchTab(existing.id); openPanel(); return; }

        const id = ++tabCounter;
        tabs.push({ id, type: 'note', noteId: note.id, title: note.title, icon: 'fa-file-alt', note });
        renderTabs();
        switchTab(id);
        openPanel();
        return id;
    }

    function getTab(id) { return tabs.find(t => t.id === id); }

    function setTabLoading(id, msg) {
        if (activeId !== id) switchTab(id);
        tabContent.innerHTML = loadingHTML(msg);
    }

    function setTabOutput(id, action, data) {
        const tab = getTab(id);
        if (!tab) return;

        let text = '';
        let html = '';

        switch (action) {
            case 'ocr':
                text = data.extracted_text || '';
                html = textOutputHTML('Extracted Text', text, id);
                break;
            case 'stt':
                text = data.transcribed_text || '';
                html = textOutputHTML('Transcription', text, id);
                break;
            case 'summary':
                text = data.summary || '';
                html = textOutputHTML('Summary', text, id);
                break;
            case 'questions':
                text = buildQuestionsText(data.questions || []);
                html = questionsHTML(data.questions || [], id);
                break;
            case 'tts':
                html = ttsHTML(data.audio_url, id);
                break;
            case 'pdf':
                html = pdfHTML(data, id);
                break;
            default:
                text = JSON.stringify(data, null, 2);
                html = textOutputHTML(action, text, id);
        }

        tab.outputText   = text;
        tab.outputAction = action;

        if (activeId === id) tabContent.innerHTML = html;
    }

    function setTabError(id, msg) {
        if (activeId === id) tabContent.innerHTML = errorHTML(msg);
    }

    // ── Panel open/close ──────────────────────────────────────────

    function collapsePanel() {
        panel.classList.remove('open');
        overlay.classList.remove('active');
        document.body.classList.remove('rp-open');
        if (tabs.length) {
            const strip = document.getElementById('rpEdgeStrip');
            if (strip) { strip.classList.add('visible'); renderEdgeStrip(); }
        }
    }

    function openPanel() {
        panel.classList.add('open');
        overlay.classList.add('active');
        document.body.classList.add('rp-open');
        const strip = document.getElementById('rpEdgeStrip');
        if (strip) strip.classList.remove('visible');
    }

    function closePanel() { collapsePanel(); }

    // ── Tab rendering ─────────────────────────────────────────────

    function renderTabs() {
        if (!tabBar) return;
        tabBar.innerHTML = tabs.map(t => `
            <div class="rp-tab ${t.id === activeId ? 'active' : ''}" onclick="RightPanel.switchTab(${t.id})">
                <i class="fas ${t.icon}" style="font-size:0.75rem"></i>
                <span class="rp-tab-label">${truncate(t.title, 14)}</span>
                <span class="rp-tab-close" onclick="event.stopPropagation();RightPanel.closeTab(${t.id})">
                    <i class="fas fa-times"></i>
                </span>
            </div>`).join('');
    }

    function renderEdgeStrip() {
        const edgeTabs = document.getElementById('rpEdgeTabs');
        if (!edgeTabs) return;
        edgeTabs.innerHTML = tabs.map(t => `
            <div class="rp-edge-tab ${t.id === activeId ? 'active' : ''}"
                 title="${t.title}"
                 onclick="RightPanel.switchTab(${t.id});RightPanel.open()">
                <i class="fas ${t.icon}"></i>
                <span class="rp-edge-tab-label">${truncate(t.title, 12)}</span>
            </div>`).join('');
    }

    function switchTab(id) {
        activeId = id;
        renderTabs();
        renderContent(id);
    }

    function closeTab(id) {
        tabs = tabs.filter(t => t.id !== id);
        if (activeId === id) {
            activeId = tabs.length ? tabs[tabs.length - 1].id : null;
        }
        if (!tabs.length) {
            closePanel();
            const strip = document.getElementById('rpEdgeStrip');
            if (strip) strip.classList.remove('visible');
            return;
        }
        renderTabs();
        renderEdgeStrip();
        if (activeId) renderContent(activeId);
    }

    function renderContent(id) {
        if (!tabContent) return;
        const tab = getTab(id);
        if (!tab) { tabContent.innerHTML = ''; return; }

        if (tab.type === 'file')    tabContent.innerHTML = fileTabHTML(tab);
        if (tab.type === 'youtube') tabContent.innerHTML = youtubeTabHTML(tab);
        if (tab.type === 'note')    tabContent.innerHTML = noteTabHTML(tab);
    }

    // ── Tab content builders ──────────────────────────────────────

    function fileTabHTML(tab) {
        const features = window.getFeatures ? window.getFeatures(tab.file, tab.fileType) : [];
        const size = formatSize(tab.file.size);
        const ext  = tab.file.name.split('.').pop().toUpperCase();

        const featureBtns = features.map(f => {
            // auto-summary / auto-questions extract text first, then process
            const clickHandler = (f.action === 'auto-summary' || f.action === 'auto-questions')
                ? `FeatureProcessor.autoProcess(${tab.id}, RightPanel.getTab(${tab.id}).file, '${f.action}')`
                : `FeatureProcessor.processFile(${tab.id}, RightPanel.getTab(${tab.id}).file, '${f.action}', '${f.endpoint}')`;
            return `
            <button class="rp-feature-btn" onclick="${clickHandler}">
                <i class="fas ${f.icon}"></i>
                <span>${f.name}</span>
            </button>`;
        }).join('');

        return `
        <div class="rp-file-header">
            <div class="rp-file-icon ${tab.fileType}-icon">
                <i class="fas ${tab.icon}"></i>
            </div>
            <div class="rp-file-meta">
                <div class="rp-file-name">${tab.title}</div>
                <div class="rp-file-info">${ext} &bull; ${size}</div>
            </div>
        </div>
        <div class="rp-section-label">Choose a feature</div>
        <div class="rp-features-grid">${featureBtns}</div>
        <div id="rp-output-${tab.id}" class="rp-output-area"></div>`;
    }

    function youtubeTabHTML(tab) {
        const n = tab.notes;
        const dur = fmtDur(n.duration || 0);
        let html = `
        <div class="rp-yt-header">
            <span class="rp-yt-badge"><i class="fab fa-youtube"></i> YouTube</span>
            <span class="rp-meta">${n.author || ''}</span>
            <span class="rp-meta"><i class="fas fa-clock"></i> ${dur}</span>
        </div>
        <div class="rp-output-actions">
            <button class="rp-action-btn" onclick="RightPanel.copyTab(${tab.id})"><i class="fas fa-copy"></i> Copy</button>
            <button class="rp-action-btn" onclick="RightPanel.downloadTab(${tab.id})"><i class="fas fa-download"></i> Download</button>
            <button class="rp-action-btn primary" onclick="RightPanel.saveYouTubeTab(${tab.id})"><i class="fas fa-bookmark"></i> Save</button>
        </div>`;

        if (n.overview) html += section('📖 Overview', `<p class="rp-body-text">${n.overview}</p>`);

        if (n.key_points?.length) html += section('🔑 Key Points',
            n.key_points.map(p => `<div class="rp-point"><span class="rp-dot"></span>${p}</div>`).join(''));

        if (n.sections?.length) html += section('📚 Sections',
            n.sections.map(s => `<div class="rp-subsec"><div class="rp-subsec-title">${s.title}</div><div class="rp-subsec-body">${s.content}</div></div>`).join(''));

        if (n.questions?.length) html += section('❓ Questions',
            n.questions.map((q,i) => `<div class="rp-q"><span class="rp-qnum">Q${i+1}</span><span>${typeof q==='string'?q:q.question}</span></div>`).join(''));

        if (n.timestamps?.length) html += section('⏱️ Timestamps',
            n.timestamps.map(t => `<div class="rp-ts"><span class="rp-tsbadge">${t.time||'00:00'}</span><span class="rp-tstext">${t.text}</span></div>`).join(''));

        return html;
    }

    function noteTabHTML(tab) {
        const n   = tab.note;
        const raw = n.content || '';
        const safe = raw.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

        // Simple markdown-like rendering
        let rendered = safe
            .replace(/^### (.+)$/gm, '<div class="rp-h3">$1</div>')
            .replace(/^## (.+)$/gm,  '<div class="rp-h2">$1</div>')
            .replace(/^# (.+)$/gm,   '<div class="rp-h1">$1</div>')
            .replace(/^- (.+)$/gm,   '<div class="rp-li"><span class="rp-bullet">•</span><span>$1</span></div>')
            .replace(/^(\d+)\. (.+)$/gm, '<div class="rp-li"><span class="rp-num">$1.</span><span>$2</span></div>')
            .replace(/`([^`]+)`/g,   '<code class="rp-code">$1</code>')
            .replace(/^--- (Slide \d+) ---$/gm, '<div class="rp-slide-marker">$1</div>')
            .replace(/\n\n/g, '<div class="rp-spacer"></div>');

        const cj = JSON.stringify(raw);
        const tj = JSON.stringify(n.title || 'note');

        return [
            '<div class="rp-note-header">',
            '<div class="rp-note-title">' + (n.title || 'Untitled') + '</div>',
            '<div class="rp-note-meta">' + (n.file_type||'note').toUpperCase() + ' &bull; ' + timeAgo(n.last_opened) + '</div>',
            '</div>',
            '<div class="rp-output-actions">',
            '<button class="rp-action-btn" onclick="RightPanel.copyRaw(' + cj + ')"><i class="fas fa-copy"></i> Copy</button>',
            '<button class="rp-action-btn" onclick="RightPanel.downloadRaw(' + cj + ',' + tj + ')"><i class="fas fa-download"></i> Download</button>',
            '</div>',
            raw.length < 10
                ? '<div class="rp-error"><i class="fas fa-file-alt"></i><p>This note is empty.</p></div>'
                : '<div class="rp-note-rendered">' + rendered + '</div>'
        ].join('');
    }

    function textOutputHTML(label, text, tabId) {
        return `
        <div class="rp-output-actions">
            <button class="rp-action-btn" onclick="RightPanel.copyTab(${tabId})"><i class="fas fa-copy"></i> Copy</button>
            <button class="rp-action-btn" onclick="RightPanel.downloadTab(${tabId})"><i class="fas fa-download"></i> Download</button>
            <button class="rp-action-btn primary" onclick="RightPanel.saveTab(${tabId})"><i class="fas fa-bookmark"></i> Save</button>
        </div>

        <div class="rp-chain-label">Summarize</div>
        <div class="rp-chain-btns">
            <button class="rp-chain-btn" onclick="FeatureProcessor.processText(${tabId}, RightPanel.getTab(${tabId}).outputText, 'summary-extractive')">
                <i class="fas fa-scissors"></i> Extractive
            </button>
            <button class="rp-chain-btn" onclick="FeatureProcessor.processText(${tabId}, RightPanel.getTab(${tabId}).outputText, 'summary-abstractive')">
                <i class="fas fa-magic"></i> Abstractive
            </button>
        </div>

        <div class="rp-chain-label">Generate Questions</div>
        <div class="rp-chain-btns">
            <button class="rp-chain-btn" onclick="FeatureProcessor.processText(${tabId}, RightPanel.getTab(${tabId}).outputText, 'questions-comprehension')">
                <i class="fas fa-book-open"></i> Comprehension
            </button>
            <button class="rp-chain-btn" onclick="FeatureProcessor.processText(${tabId}, RightPanel.getTab(${tabId}).outputText, 'questions-mcq')">
                <i class="fas fa-check-circle"></i> MCQ
            </button>
            <button class="rp-chain-btn" onclick="FeatureProcessor.processText(${tabId}, RightPanel.getTab(${tabId}).outputText, 'questions-definition')">
                <i class="fas fa-book"></i> Definition
            </button>
            <button class="rp-chain-btn" onclick="FeatureProcessor.processText(${tabId}, RightPanel.getTab(${tabId}).outputText, 'questions-comparison')">
                <i class="fas fa-balance-scale"></i> Comparison
            </button>
            <button class="rp-chain-btn" onclick="FeatureProcessor.processText(${tabId}, RightPanel.getTab(${tabId}).outputText, 'questions-all')">
                <i class="fas fa-random"></i> All Types
            </button>
        </div>

        <div class="rp-chain-label">Other</div>
        <div class="rp-chain-btns">
            <button class="rp-chain-btn" onclick="FeatureProcessor.processText(${tabId}, RightPanel.getTab(${tabId}).outputText, 'tts')">
                <i class="fas fa-headphones"></i> Text to Speech
            </button>
        </div>

        <div class="rp-section-label">${label}</div>
        <div class="rp-text-output">${escHtml(text)}</div>`;
    }

    function questionsHTML(questions, tabId) {
        const items = questions.map((q, i) => {
            const qtext = typeof q === 'string' ? q : q.question || '';
            const ans   = typeof q === 'object' && q.answer ? `<div class="rp-q-answer">${q.answer}</div>` : '';
            const opts  = typeof q === 'object' && q.options?.length
                ? `<div class="rp-q-options">${q.options.map((o,j)=>`<div class="rp-q-opt ${j===q.correct_index?'correct':''}">${String.fromCharCode(65+j)}. ${o}</div>`).join('')}</div>` : '';
            return `<div class="rp-q-item"><span class="rp-qnum">Q${i+1}</span><div><div class="rp-q-text">${qtext}</div>${ans}${opts}</div></div>`;
        }).join('');
        return `
        <div class="rp-output-actions">
            <button class="rp-action-btn" onclick="RightPanel.copyTab(${tabId})"><i class="fas fa-copy"></i> Copy</button>
            <button class="rp-action-btn primary" onclick="RightPanel.saveTab(${tabId})"><i class="fas fa-bookmark"></i> Save</button>
        </div>
        <div class="rp-section-label">Generated Questions</div>
        <div class="rp-questions-list">${items}</div>`;
    }

    function ttsHTML(audioUrl, tabId) {
        return `
        <div class="rp-section-label">Audio Generated</div>
        <div class="rp-tts-box">
            <i class="fas fa-check-circle" style="color:#10b981;font-size:2rem;margin-bottom:0.75rem;"></i>
            <p style="color:#64748b;font-size:0.9rem;">Your audio is ready</p>
            ${audioUrl ? `<audio controls style="width:100%;margin-top:1rem"><source src="${audioUrl}" type="audio/mpeg"></audio>` : ''}
        </div>`;
    }

    function pdfHTML(data, tabId) {
        return `
        <div class="rp-section-label">PDF Created</div>
        <div class="rp-tts-box">
            <i class="fas fa-file-pdf" style="color:#ef4444;font-size:2rem;margin-bottom:0.75rem;"></i>
            ${data.pdf_url ? `<a href="${data.pdf_url}" class="rp-action-btn primary" download><i class="fas fa-download"></i> Download PDF</a>` : '<p style="color:#64748b;">PDF created successfully</p>'}
        </div>`;
    }

    function loadingHTML(msg) {
        return `<div class="rp-loading"><div class="rp-spinner"></div><p>${msg||'Processing…'}</p></div>`;
    }

    function errorHTML(msg) {
        return `<div class="rp-error"><i class="fas fa-exclamation-circle"></i><p>${msg}</p></div>`;
    }

    function section(title, body) {
        return `<div class="rp-section"><div class="rp-section-title">${title}</div><div class="rp-section-body">${body}</div></div>`;
    }

    // ── Tab actions ───────────────────────────────────────────────

    function copyTab(id) {
        const tab = getTab(id);
        if (!tab) return;
        const text = tab.outputText || tab.note?.content || '';
        navigator.clipboard.writeText(text).then(() =>
            Swal.fire({ icon:'success', title:'Copied!', timer:1500, showConfirmButton:false, background:'#1a1a24', color:'#e2e8f0' })
        );
    }

    function downloadTab(id) {
        const tab = getTab(id);
        if (!tab) return;
        const text  = tab.outputText || tab.note?.content || '';
        const fname = (tab.title || 'note').replace(/[^a-z0-9]/gi,'_').toLowerCase() + '.txt';
        downloadText(text, fname);
    }

    function downloadRaw(content, title) {
        downloadText(content, (title||'note').replace(/[^a-z0-9]/gi,'_').toLowerCase()+'.txt');
    }

    function copyRaw(text) {
        navigator.clipboard.writeText(text).then(() =>
            Swal.fire({ icon:'success', title:'Copied!', timer:1500, showConfirmButton:false, background:'#1a1a24', color:'#e2e8f0' })
        );
    }

    function downloadText(text, fname) {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(new Blob([text], { type:'text/plain' }));
        a.download = fname; document.body.appendChild(a); a.click();
        document.body.removeChild(a);
    }

    async function saveTab(id) {
        const tab = getTab(id);
        if (!tab || !tab.outputText) return;
        const { value: title } = await Swal.fire({
            title:'Save Note', input:'text', inputLabel:'Note title',
            inputValue: tab.title || 'My Note', showCancelButton:true,
            background:'#1a1a24', color:'#e2e8f0', confirmButtonColor:'#f59e0b'
        });
        if (!title) return;
        try {
            const fd = new FormData();
            fd.append('title', title); fd.append('content', tab.outputText); fd.append('file_type','text');
            const r = await fetch('/api/documents/save', {
                method:'POST', headers:{'Authorization':`Bearer ${localStorage.getItem('access_token')}`}, body:fd
            });
            if (r.ok) {
                Swal.fire({ icon:'success', title:'Saved!', timer:2000, showConfirmButton:false, background:'#1a1a24', color:'#e2e8f0' });
                if (window.loadNotes) window.loadNotes();
            }
        } catch(e) { Swal.fire({ icon:'error', title:'Error', text:e.message, background:'#1a1a24', color:'#e2e8f0', confirmButtonColor:'#f59e0b' }); }
    }

    async function saveYouTubeTab(id) {
        const tab = getTab(id);
        if (!tab?.notes) return;
        const title = prompt('Title for these notes:', tab.notes.title || 'YouTube Notes');
        if (!title) return;
        try {
            const fd = new FormData();
            fd.append('title', title); fd.append('notes_json', JSON.stringify(tab.notes));
            const r = await fetch('/api/v1/youtube/save', {
                method:'POST', headers:{'Authorization':`Bearer ${localStorage.getItem('access_token')}`}, body:fd
            });
            if (r.ok) {
                Swal.fire({ icon:'success', title:'Saved!', text:'Notes saved to your library', timer:2000, showConfirmButton:false, background:'#1a1a24', color:'#e2e8f0' });
                if (window.loadNotes) window.loadNotes();
            }
        } catch(e) { Swal.fire({ icon:'error', title:'Error', text:'Failed to save', background:'#1a1a24', color:'#e2e8f0', confirmButtonColor:'#f59e0b' }); }
    }

    // ── Utilities ─────────────────────────────────────────────────

    function truncate(s, n) { return s.length > n ? s.slice(0,n)+'…' : s; }
    function formatSize(b) {
        if (!b) return '0 B';
        const u=['B','KB','MB']; let s=b, i=0;
        while(s>=1024&&i<2){s/=1024;i++;} return `${s.toFixed(1)} ${u[i]}`;
    }
    function fmtDur(s) { return `${Math.floor(s/60)}:${Math.floor(s%60).toString().padStart(2,'0')}`; }
    function timeAgo(d) {
        if (!d) return 'never';
        const s=Math.floor((Date.now()-new Date(d))/1000);
        if(s<60) return 'just now'; if(s<3600) return Math.floor(s/60)+'m ago';
        if(s<86400) return Math.floor(s/3600)+'h ago'; return Math.floor(s/86400)+'d ago';
    }
    function escHtml(s) { return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
    function buildQuestionsText(qs) {
        return qs.map((q,i) => {
            const t = typeof q==='string'?q:q.question||'';
            const a = typeof q==='object'&&q.answer?`\nAnswer: ${q.answer}`:'';
            return `${i+1}. ${t}${a}`;
        }).join('\n\n');
    }

    // ── Expose ────────────────────────────────────────────────────
    window.RightPanel = {
        openFileTab, openYoutubeTab, openNoteTab,
        getTab, closeTab, switchTab,
        setTabLoading, setTabOutput, setTabError,
        copyTab, downloadTab, downloadRaw, copyRaw,
        saveTab, saveYouTubeTab,
        open: openPanel, close: collapsePanel, collapse: collapsePanel
    };

})();