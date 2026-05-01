// static/js/upload.js

document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('audioFileInput')?.addEventListener('change', e => {
        if (e.target.files[0]) handleFileUpload(e.target.files[0], 'audio');
    });
    document.getElementById('docFileInput')?.addEventListener('change', e => {
        if (e.target.files[0]) handleFileUpload(e.target.files[0], 'document');
    });
});

function handleFileUpload(file, type) {
    if (window.RightPanel) window.RightPanel.openFileTab(file, type);
}

function getFeatures(file, type) {
    const ext = file.name.split('.').pop().toLowerCase();

    if (type === 'audio') return [
        { icon: 'fa-microphone', name: 'Transcribe', action: 'stt', endpoint: '/api/stt/transcribe' }
    ];

    if (['jpg','jpeg','png','gif','bmp','tiff'].includes(ext)) return [
        { icon: 'fa-eye',        name: 'Extract Text', action: 'ocr', endpoint: '/api/ocr' },
        { icon: 'fa-file-pdf',   name: 'Convert to PDF', action: 'pdf', endpoint: '/api/image-to-pdf' }
    ];

    if (ext === 'pdf') return [
        { icon: 'fa-eye',          name: 'Extract Text',   action: 'ocr',      endpoint: '/api/ocr' },
        { icon: 'fa-compress-alt', name: 'Summarize',      action: 'auto-summary',   endpoint: '/api/ocr' },
        { icon: 'fa-brain',        name: 'Questions',      action: 'auto-questions', endpoint: '/api/ocr' },
        { icon: 'fa-headphones',   name: 'Text to Speech', action: 'tts',       endpoint: '/api/tts/generate' }
    ];

    if (ext === 'pptx') return [
        { icon: 'fa-file-powerpoint', name: 'Extract Text',   action: 'ocr',            endpoint: '/api/ocr' },
        { icon: 'fa-compress-alt',    name: 'Summarize',      action: 'auto-summary',   endpoint: '/api/ocr' },
        { icon: 'fa-brain',           name: 'Questions',      action: 'auto-questions', endpoint: '/api/ocr' },
    ];

    if (['docx','txt'].includes(ext)) return [
        { icon: 'fa-eye',          name: 'Extract Text',   action: 'ocr',            endpoint: '/api/ocr' },
        { icon: 'fa-compress-alt', name: 'Summarize',      action: 'auto-summary',   endpoint: '/api/ocr' },
        { icon: 'fa-brain',        name: 'Questions',      action: 'auto-questions', endpoint: '/api/ocr' },
        { icon: 'fa-headphones',   name: 'Text to Speech', action: 'tts',            endpoint: '/api/tts/generate' }
    ];

    return [];
}

window.handleFileUpload = handleFileUpload;
window.getFeatures = getFeatures;