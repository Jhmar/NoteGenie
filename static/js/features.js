// static/js/features.js

window.FeatureProcessor = {
    token: localStorage.getItem('access_token'),

    async processFile(tabId, file, action, endpoint) {
        const tab = window.RightPanel?.getTab(tabId);
        if (!tab) return;

        window.RightPanel.setTabLoading(tabId, `Running ${action}…`);

        try {
            const fd = new FormData();
            fd.append('file', file);
            if (action === 'tts') fd.append('language', 'en');
            if (action === 'stt') fd.append('language', 'en-US');

            const r = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${this.token}` },
                body: fd
            });
            const data = await r.json();

            if (!r.ok) throw new Error(data.detail || 'Processing failed');

            window.RightPanel.setTabOutput(tabId, action, data);

        } catch (e) {
            window.RightPanel.setTabError(tabId, e.message);
        }
    },

    async processText(tabId, text, action) {
        const labels = {
            'summary-extractive':    'Extractive Summary',
            'summary-abstractive':   'Abstractive Summary',
            'questions-comprehension': 'Comprehension Questions',
            'questions-mcq':         'Multiple Choice Questions',
            'questions-definition':  'Definition Questions',
            'questions-comparison':  'Comparison Questions',
            'questions-all':         'All Question Types',
            'tts':                   'Text to Speech',
        };
        window.RightPanel.setTabLoading(tabId, `Generating ${labels[action] || action}…`);

        try {
            const fd = new FormData();
            fd.append('text', text);

            let endpoint = '';

            // ── Summarization ──────────────────────────────────────────────
            if (action === 'summary-extractive') {
                fd.append('method', 'extractive');
                fd.append('num_sentences', '5');
                endpoint = '/api/summarization/summarize';
            } else if (action === 'summary-abstractive') {
                fd.append('method', 'abstractive');
                fd.append('max_length', '200');
                fd.append('min_length', '60');
                endpoint = '/api/summarization/summarize';

            // ── Questions ──────────────────────────────────────────────────
            } else if (action.startsWith('questions-')) {
                const qtype = action.replace('questions-', ''); // comprehension|mcq|definition|comparison|all
                fd.append('question_type', qtype);
                fd.append('num_questions', '6');
                endpoint = '/api/questions/generate-typed';

            // ── TTS ────────────────────────────────────────────────────────
            } else if (action === 'tts') {
                fd.append('language', 'en');          // ✅ add language field
                endpoint = '/api/tts/generate';       // ✅ fixed: was /api/tts/generate

            // ── Legacy fallback ────────────────────────────────────────────
            } else {
                fd.append('method', 'extractive');
                fd.append('num_sentences', '5');
                endpoint = '/api/summarization/summarize';
            }

            const r = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${this.token}` },
                body: fd
            });
            const data = await r.json();
            if (!r.ok) throw new Error(data.detail || 'Processing failed');

            // Map action to output renderer key
            const outputAction = action.startsWith('summary') ? 'summary'
                               : action.startsWith('questions') ? 'questions'
                               : action;
            window.RightPanel.setTabOutput(tabId, outputAction, data);

        } catch (e) {
            window.RightPanel.setTabError(tabId, e.message);
        }
    }
};


// ── Auto-extract then process ─────────────────────────────────────────────
// Used for Summarize / Questions clicked directly on a file
// without manually running OCR first.
window.FeatureProcessor.autoProcess = async function(tabId, file, action) {
    const actionLabel = action === 'auto-summary' ? 'Summarizing' : 'Generating Questions';
    window.RightPanel.setTabLoading(tabId, `Extracting text then ${actionLabel.toLowerCase()}…`);

    try {
        // Step 1 — extract text from the file
        const fd1 = new FormData();
        fd1.append('file', file);
        const r1 = await fetch('/api/ocr', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${this.token}` },
            body: fd1
        });
        const d1 = await r1.json();
        if (!r1.ok) throw new Error(d1.detail || d1.error || 'Text extraction failed');

        const text = d1.extracted_text || '';
        if (!text || text.trim().length < 50) {
            throw new Error('Not enough text could be extracted from this file.');
        }

        // Step 2 — run the actual processing on extracted text
        const targetAction = action === 'auto-summary'
            ? 'summary-extractive'
            : 'questions-all';

        await this.processText(tabId, text, targetAction);

    } catch (e) {
        window.RightPanel.setTabError(tabId, e.message);
    }
};

console.log('✅ features.js loaded');