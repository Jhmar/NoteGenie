// Check auth status on every page
document.addEventListener('DOMContentLoaded', function() {
    checkAuthStatus();
});

function checkAuthStatus() {
    const token = localStorage.getItem('access_token');
    const username = localStorage.getItem('username');
    
    const authLinks = document.getElementById('authLinks');
    const userMenu = document.getElementById('userMenu');
    const usernameDisplay = document.getElementById('usernameDisplay');
    
    if (token && userMenu && authLinks) {
        // User is logged in
        authLinks.style.display = 'none';
        userMenu.style.display = 'flex';
        if (usernameDisplay) {
            usernameDisplay.textContent = username || 'User';
        }
    } else {
        // User is not logged in
        if (authLinks) authLinks.style.display = 'flex';
        if (userMenu) userMenu.style.display = 'none';
    }
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('username');
    localStorage.removeItem('role');
    
    window.location.href = '/';
}


// Check if user is logged in
document.addEventListener('DOMContentLoaded', function() {
    checkAuthStatus();
});

function checkAuthStatus() {
    const token = localStorage.getItem('access_token');
    const username = localStorage.getItem('username');
    
    const authLinks = document.querySelectorAll('.auth-link');
    const userMenu = document.getElementById('userMenu');
    const usernameDisplay = document.getElementById('usernameDisplay');
    
    if (token && userMenu && usernameDisplay) {
        // User is logged in
        authLinks.forEach(link => link.style.display = 'none');
        userMenu.style.display = 'flex';
        usernameDisplay.textContent = username || 'User';
    }
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('username');
    localStorage.removeItem('role');
    
    window.location.href = '/';
}

// Wait for the page to load
document.addEventListener('DOMContentLoaded', function() {
    console.log('NoteGenie loaded successfully!');
    
    // Initialize tool selection
    initializeTools();
    
    // Setup file input listeners
    setupFileInputs();
    
    // Setup form submissions
    setupForms();
    
    // Initialize TTS
    setupTTS();
});

// ============ TOOL MANAGEMENT ============

function initializeTools() {
    // Add click handlers to all feature cards
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.addEventListener('click', function(e) {
            if (!e.target.classList.contains('close-tool')) {
                const toolId = this.getAttribute('onclick').match(/showTool\('(\w+)'\)/)[1];
                showTool(toolId);
                
                // Scroll to tools section
                document.getElementById('tools').scrollIntoView({ 
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Close tool buttons
    document.querySelectorAll('.close-tool').forEach(btn => {
        btn.addEventListener('click', hideAllTools);
    });
}

function showTool(toolId) {
    // Hide all tools first
    hideAllTools();
    
    // Remove active class from all feature cards
    document.querySelectorAll('.feature-card').forEach(card => {
        card.classList.remove('active');
    });
    
    // Add active class to clicked feature card
    const activeCard = document.querySelector(`[onclick*="${toolId}"]`);
    if (activeCard) {
        activeCard.classList.add('active');
    }
    
    // Show the selected tool
    const toolElement = document.getElementById(`${toolId}-tool`);
    if (toolElement) {
        toolElement.classList.remove('hidden');
    }
}

function hideAllTools() {
    // Hide all tools
    document.querySelectorAll('.tool-container').forEach(tool => {
        tool.classList.add('hidden');
    });
    
    // Remove active class from all feature cards
    document.querySelectorAll('.feature-card').forEach(card => {
        card.classList.remove('active');
    });
}

// ============ FILE INPUT HANDLING ============

function setupFileInputs() {
    // OCR file input
    const ocrFileInput = document.getElementById('ocrFile');
    const ocrFileName = document.getElementById('ocrFileName');
    
    if (ocrFileInput) {
        ocrFileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                ocrFileName.textContent = `Selected: ${this.files[0].name}`;
                ocrFileName.style.display = 'block';
            } else {
                ocrFileName.style.display = 'none';
            }
        });
    }
    
    // PDF files input
    const pdfFilesInput = document.getElementById('pdfFiles');
    const pdfFileNames = document.getElementById('pdfFileNames');
    
    if (pdfFilesInput) {
        pdfFilesInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                let fileList = 'Selected files:';
                for (let i = 0; i < this.files.length; i++) {
                    fileList += `\n${i + 1}. ${this.files[i].name}`;
                }
                pdfFileNames.textContent = fileList;
                pdfFileNames.style.display = 'block';
            } else {
                pdfFileNames.style.display = 'none';
            }
        });
    }
}

// ============ FORM SUBMISSIONS ============

function setupForms() {
    // OCR Form
    const ocrForm = document.getElementById('ocrForm');
    const ocrResult = document.getElementById('ocrResult');
    
    if (ocrForm) {
        ocrForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('ocrFile');
            const submitButton = this.querySelector('button[type="submit"]');
            
            if (!fileInput.files[0]) {
                showMessage(ocrResult, '📝 Please select an image or PDF file first!', 'error');
                return;
            }
            
            // Show loading state
            const originalText = submitButton.innerHTML;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            submitButton.disabled = true;
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            
            try {
                showMessage(ocrResult, 
                    '<div class="loading-message">' +
                    '<i class="fas fa-spinner fa-spin"></i><br>' +
                    '<strong>Processing OCR...</strong><br>' +
                    '<small>This may take a moment</small>' +
                    '</div>', 
                    'loading');
                
                const response = await fetch('/api/ocr', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (response.ok && (result.status === 'success' || result.status === 'placeholder')) {
                    const extractedText = result.extracted_text || 'No text could be extracted';
                    const escapedText = escapeHtml(extractedText);
                    
                    const resultHTML = `
                        <div class="ocr-result-container">
                            <div class="result-header success">
                                <i class="fas fa-check-circle"></i>
                                <h4>✅ OCR Processing Complete!</h4>
                            </div>
                            <div class="result-details">
                                <p><strong>File:</strong> ${escapeHtml(result.filename)}</p>
                                <p><strong>Characters Extracted:</strong> ${extractedText.length}</p>
                            </div>
                            <div class="extracted-text-section">
                                <h5>Extracted Text:</h5>
                                <div class="extracted-text-box" id="extractedTextContent">
                                    ${escapedText}
                                </div>
                                <div class="text-actions">
                                    <button class="action-btn copy-btn" onclick="copyExtractedText()">
                                        <i class="fas fa-copy"></i> Copy Text
                                    </button>
                                    <button class="action-btn download-btn" onclick="downloadExtractedText('${escapeHtml(result.filename)}', \`${escapeJs(extractedText)}\`)">
                                        <i class="fas fa-download"></i> Download as TXT
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    showMessage(ocrResult, resultHTML, 'success');
                    
                } else {
                    showMessage(ocrResult, 
                        `❌ <strong>OCR Failed</strong><br>
                         Error: ${escapeHtml(result.error || result.extracted_text || 'Unknown error')}`, 
                        'error');
                }
                
            } catch (error) {
                showMessage(ocrResult, 
                    `❌ <strong>Network Error</strong><br>
                     ${escapeHtml(error.message)}`, 
                    'error');
            } finally {
                // Restore button
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
            }
        });
    }
    
    // PDF Form
    const pdfForm = document.getElementById('pdfForm');
    const pdfResult = document.getElementById('pdfResult');
    
    if (pdfForm) {
        pdfForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('pdfFiles');
            const submitButton = this.querySelector('button[type="submit"]');
            
            if (!fileInput.files.length) {
                showMessage(pdfResult, '📝 Please select at least one image file!', 'error');
                return;
            }
            
            // Show loading state
            const originalText = submitButton.innerHTML;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Converting...';
            submitButton.disabled = true;
            
            const formData = new FormData();
            for (let i = 0; i < fileInput.files.length; i++) {
                formData.append('files', fileInput.files[i]);
            }
            
            try {
                showMessage(pdfResult, '⏳ Converting images to PDF...', 'loading');
                
                const response = await fetch('/api/image-to-pdf', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (response.ok && result.status === 'success') {
                    showMessage(pdfResult, 
                        `✅ <strong>PDF Created Successfully!</strong><br><br>
                         <strong>File:</strong> ${result.pdf_filename}<br>
                         <strong>Pages:</strong> ${result.page_count} image(s)<br>
                         <strong>Status:</strong> ${result.message}<br><br>
                         <div class="pdf-actions">
                             <a href="${result.download_url}" class="action-btn download-pdf-btn" target="_blank">
                                 <i class="fas fa-download"></i> Download PDF
                             </a>
                             <button class="action-btn copy-link-btn" onclick="copyPdfLink('${result.pdf_filename}')">
                                 <i class="fas fa-link"></i> Copy Link
                             </button>
                         </div>`, 
                        'success');
                } else {
                    showMessage(pdfResult, 
                        `❌ <strong>PDF Conversion Failed</strong><br>
                         Error: ${result.message || 'Unknown error'}`, 
                        'error');
                }
                
            } catch (error) {
                showMessage(pdfResult, 
                    `❌ <strong>Network Error</strong><br>
                     ${error.message}`, 
                    'error');
            } finally {
                // Restore button
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
            }
        });
    }
}

// ============ TEXT ACTIONS FUNCTIONS ============

function copyExtractedText() {
    const textBox = document.getElementById('extractedTextContent');
    if (textBox) {
        const textToCopy = textBox.textContent || textBox.innerText;
        
        // Use the modern Clipboard API
        navigator.clipboard.writeText(textToCopy).then(() => {
            // Show success notification
            showCopyNotification('Text copied to clipboard!', 'success');
            
            // Briefly change button text
            const copyBtn = document.querySelector('.copy-btn');
            if (copyBtn) {
                const originalHtml = copyBtn.innerHTML;
                copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                copyBtn.style.background = '#27ae60';
                
                // Reset after 2 seconds
                setTimeout(() => {
                    copyBtn.innerHTML = originalHtml;
                    copyBtn.style.background = '';
                }, 2000);
            }
        }).catch(err => {
            console.error('Failed to copy: ', err);
            
            // Fallback for older browsers
            try {
                const textArea = document.createElement('textarea');
                textArea.value = textToCopy;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                showCopyNotification('Text copied to clipboard!', 'success');
            } catch (fallbackErr) {
                showCopyNotification('Failed to copy. Please select and copy manually.', 'error');
            }
        });
    } else {
        showCopyNotification('No text to copy!', 'error');
    }
}

function downloadExtractedText(filename, text) {
    try {
        // Unescape the text if needed
        const unescapedText = text
            .replace(/\\\\/g, '\\')
            .replace(/\\`/g, '`')
            .replace(/\\\$/g, '$')
            .replace(/\\n/g, '\n')
            .replace(/\\r/g, '\r')
            .replace(/\\t/g, '\t')
            .replace(/\\"/g, '"')
            .replace(/\\'/g, "'");
        
        // Create filename
        const cleanName = filename.replace(/\.[^/.]+$/, "") + '_extracted.txt';
        
        // Create blob and download
        const blob = new Blob([unescapedText], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        
        a.href = url;
        a.download = cleanName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        // Show notification
        showCopyNotification(`Downloaded: ${cleanName}`, 'success');
        
    } catch (error) {
        console.error('Download error:', error);
        showCopyNotification('Error downloading file', 'error');
    }
}

function copyPdfLink(filename) {
    const pdfUrl = `${window.location.origin}/download-pdf/${filename}`;
    navigator.clipboard.writeText(pdfUrl).then(() => {
        showCopyNotification('PDF link copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy: ', err);
        showCopyNotification('Failed to copy link', 'error');
    });
}

function showCopyNotification(message, type) {
    // Remove existing notification
    const existingNote = document.getElementById('copyNotification');
    if (existingNote) {
        existingNote.remove();
    }
    
    // Create notification
    const notification = document.createElement('div');
    notification.id = 'copyNotification';
    notification.className = `copy-notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Show with animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }, 3000);
}

// ============ HELPER FUNCTIONS ============

function showMessage(element, message, type) {
    const placeholder = element.querySelector('.result-placeholder') || element;
    
    // Clear and set new content
    placeholder.innerHTML = message;
    
    // Remove all type classes
    placeholder.classList.remove('success', 'error', 'loading', 'info');
    
    // Add appropriate class
    if (type) {
        placeholder.classList.add(type);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function escapeJs(text) {
    return text
        .replace(/\\/g, '\\\\')
        .replace(/`/g, '\\`')
        .replace(/\$/g, '\\$')
        .replace(/\n/g, '\\n')
        .replace(/\r/g, '\r')
        .replace(/\t/g, '\\t')
        .replace(/"/g, '\\"')
        .replace(/'/g, "\\'");
}

// ============ TTS FUNCTIONALITY ============

function setupTTS() {
    const ttsText = document.getElementById('tts-text');
    const charCount = document.getElementById('charCount');
    const generateBtn = document.getElementById('tts-generate-btn');
    
    console.log('TTS Setup - Elements found:', {
        ttsText: !!ttsText,
        charCount: !!charCount,
        generateBtn: !!generateBtn
    });
    
    if (!ttsText || !generateBtn) {
        console.error('TTS elements not found!');
        return;
    }
    
    // Character counter
    ttsText.addEventListener('input', function() {
        const count = this.value.length;
        charCount.textContent = count;
        
        if (count > 5000) {
            charCount.style.color = '#e74c3c';
        } else if (count > 4000) {
            charCount.style.color = '#f39c12';
        } else {
            charCount.style.color = '#27ae60';
        }
    });
    
    // Generate button click handler
    generateBtn.addEventListener('click', async function() {
        console.log('Generate Audio button clicked!');
        
        const text = ttsText.value.trim();
        const language = document.getElementById('tts-language').value;
        const resultDiv = document.getElementById('tts-result');
        
        console.log('Input values:', { text, language, resultDiv: !!resultDiv });
        
        // Validation
        if (!text) {
            console.error('No text entered');
            showMessage(resultDiv, '❌ <strong>Please enter some text to convert to speech</strong>', 'error');
            return;
        }
        
        if (text.length > 5000) {
            console.error('Text too long:', text.length);
            showMessage(resultDiv, '❌ <strong>Text is too long!</strong><br>Maximum 5000 characters allowed.', 'error');
            return;
        }
        
        // Show loading state
        const originalText = generateBtn.innerHTML;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating Audio...';
        generateBtn.disabled = true;
        console.log('Button disabled, showing loading state');
        
        try {
            // Show loading message
            showMessage(resultDiv, 
                '<div class="loading-message">' +
                '<i class="fas fa-spinner fa-spin"></i><br>' +
                '<strong>Generating audio...</strong><br>' +
                '<small>This may take a moment</small>' +
                '</div>', 
                'loading');
            
            console.log('Calling TTS API...');
            
            // Call TTS API
            // New code:
           const params = new URLSearchParams();
            params.append('text', text);
            params.append('language', language);

            const response = await fetch('/api/tts/generate', {
            method: 'POST',
            headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: params
            });
            
            console.log('Response status:', response.status);
            console.log('Response headers:', response.headers);
            
            const result = await response.json();
            console.log('Response data:', result);
            
            if (response.ok && result.status === 'success') {
                console.log('TTS Success!');
                
                // Create audio player HTML
                const languageSelect = document.getElementById('tts-language');
                const languageName = languageSelect.options[languageSelect.selectedIndex].text;
                
                const audioHTML = `
                    <div class="tts-result-container">
                        <div class="result-header success">
                            <i class="fas fa-check-circle"></i>
                            <h4>✅ Audio Generated Successfully!</h4>
                        </div>
                        <div class="result-details">
                            <p><strong>Text Length:</strong> ${result.text_length} characters</p>
                            <p><strong>Language:</strong> ${languageName}</p>
                            <p><strong>File:</strong> ${result.audio_filename}</p>
                        </div>
                        <div class="audio-player-section">
                            <h5>Listen to Audio:</h5>
                            <audio controls class="audio-player" id="tts-audio-player">
                                <source src="${result.preview_url}" type="audio/mpeg">
                                Your browser does not support the audio element.
                            </audio>
                            <div class="audio-actions">
                                <a href="${result.download_url}" class="action-btn download-btn" target="_blank">
                                    <i class="fas fa-download"></i> Download MP3
                                </a>
                                <button class="action-btn play-btn" onclick="document.getElementById('tts-audio-player').play()">
                                    <i class="fas fa-play"></i> Play Audio
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                
                showMessage(resultDiv, audioHTML, 'success');
                console.log('Result displayed successfully');
                
            } else {
                console.error('TTS API Error:', result);
                showMessage(resultDiv, 
                    `❌ <strong>Failed to generate audio</strong><br>
                     Error: ${result.message || 'Unknown error'}<br>
                     Status: ${response.status}`, 
                    'error');
            }
            
        } catch (error) {
            console.error('TTS Fetch Error:', error);
            showMessage(resultDiv, 
                `❌ <strong>Network Error</strong><br>
                 ${error.message}`, 
                'error');
        } finally {
            // Restore button
            generateBtn.innerHTML = originalText;
            generateBtn.disabled = false;
            console.log('Button restored');
        }
    });
    
    console.log('TTS setup complete');
}
// ============ STT FUNCTIONALITY ============

function setupSTT() {
    const sttForm = document.getElementById('sttForm');
    const sttFileInput = document.getElementById('sttFile');
    const sttFileName = document.getElementById('sttFileName');
    const generateBtn = document.getElementById('stt-generate-btn');
    
    if (!sttForm || !sttFileInput || !generateBtn) return;
    
    // File input handler
    sttFileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            sttFileName.textContent = `Selected: ${this.files[0].name} (${(this.files[0].size / (1024*1024)).toFixed(2)} MB)`;
            sttFileName.style.display = 'block';
        } else {
            sttFileName.style.display = 'none';
        }
    });
    
    // Form submission
    sttForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const fileInput = document.getElementById('sttFile');
        const language = document.getElementById('stt-language').value;
        const resultDiv = document.getElementById('stt-result');
        
        if (!fileInput.files[0]) {
            showMessage(resultDiv, '📝 Please select an audio file first!', 'error');
            return;
        }
        
        // Show loading state
        const originalText = generateBtn.innerHTML;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Transcribing...';
        generateBtn.disabled = true;
        
        try {
            showMessage(resultDiv, 
                '<div class="loading-message">' +
                '<i class="fas fa-spinner fa-spin"></i><br>' +
                '<strong>Transcribing audio...</strong><br>' +
                '<small>This may take a moment</small>' +
                '</div>', 
                'loading');
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('language', language);
            
            const response = await fetch('/api/stt/transcribe', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok && result.status === 'success') {
                const transcribedText = result.transcribed_text || 'No text could be transcribed';
                const escapedText = escapeHtml(transcribedText);
                
                const resultHTML = `
                    <div class="stt-result-container">
                        <div class="result-header success">
                            <i class="fas fa-check-circle"></i>
                            <h4>✅ Transcription Complete!</h4>
                        </div>
                        <div class="result-details">
                            <p><strong>File:</strong> ${escapeHtml(result.filename)}</p>
                            <p><strong>Language:</strong> ${result.details.language || language}</p>
                            <p><strong>Words:</strong> ${result.details.words || 0}</p>
                            <p><strong>Characters:</strong> ${result.details.characters || 0}</p>
                        </div>
                        <div class="transcribed-text-section">
                            <h5>Transcribed Text:</h5>
                            <div class="transcribed-text-box" id="transcribedTextContent">
                                ${escapedText}
                            </div>
                            <div class="text-actions">
                                <button class="action-btn copy-btn" onclick="copyTranscribedText()">
                                    <i class="fas fa-copy"></i> Copy Text
                                </button>
                                <button class="action-btn download-btn" onclick="downloadTranscribedText('${escapeHtml(result.filename)}', \`${escapeJs(transcribedText)}\`)">
                                    <i class="fas fa-download"></i> Download as TXT
                                </button>
                                <button class="action-btn tts-btn" onclick="useTranscribedTextForTTS()">
                                    <i class="fas fa-volume-up"></i> Convert to Speech
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                
                showMessage(resultDiv, resultHTML, 'success');
                
            } else {
                showMessage(resultDiv, 
                    `❌ <strong>Transcription Failed</strong><br>
                     Error: ${escapeHtml(result.detail || result.message || 'Unknown error')}`, 
                    'error');
            }
            
        } catch (error) {
            showMessage(resultDiv, 
                `❌ <strong>Network Error</strong><br>
                 ${escapeHtml(error.message)}`, 
                'error');
        } finally {
            // Restore button
            generateBtn.innerHTML = originalText;
            generateBtn.disabled = false;
        }
    });
}

// Copy transcribed text
function copyTranscribedText() {
    const textBox = document.getElementById('transcribedTextContent');
    if (textBox) {
        const textToCopy = textBox.textContent || textBox.innerText;
        navigator.clipboard.writeText(textToCopy).then(() => {
            showCopyNotification('Text copied to clipboard!', 'success');
        }).catch(err => {
            showCopyNotification('Failed to copy. Please select and copy manually.', 'error');
        });
    }
}

// Download transcribed text
function downloadTranscribedText(filename, text) {
    try {
        const unescapedText = text
            .replace(/\\\\/g, '\\')
            .replace(/\\`/g, '`')
            .replace(/\\\$/g, '$')
            .replace(/\\n/g, '\n')
            .replace(/\\r/g, '\r')
            .replace(/\\t/g, '\t')
            .replace(/\\"/g, '"')
            .replace(/\\'/g, "'");
        
        const cleanName = filename.replace(/\.[^/.]+$/, "") + '_transcribed.txt';
        const blob = new Blob([unescapedText], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        
        a.href = url;
        a.download = cleanName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showCopyNotification(`Downloaded: ${cleanName}`, 'success');
        
    } catch (error) {
        showCopyNotification('Error downloading file', 'error');
    }
}

// Use transcribed text for TTS
function useTranscribedTextForTTS() {
    const transcribedTextElement = document.getElementById('transcribedTextContent');
    const ttsText = document.getElementById('tts-text');
    
    if (transcribedTextElement && ttsText) {
        const transcribedText = transcribedTextElement.textContent || transcribedTextElement.innerText;
        ttsText.value = transcribedText;
        ttsText.dispatchEvent(new Event('input'));
        
        // Switch to TTS tool
        showTool('tts');
        showCopyNotification('Text copied to TTS! Switch to TTS tab.', 'success');
    }
}

// Initialize STT when page loads
document.addEventListener('DOMContentLoaded', function() {
    setupSTT();
});

// ============ SUMMARIZATION FUNCTIONALITY ============

function setupSummarization() {
    const summaryForm = document.getElementById('summaryForm');
    const summaryText = document.getElementById('summary-text');
    const summaryMethod = document.getElementById('summary-method');
    const generateBtn = document.getElementById('summary-generate-btn');
    const charCount = document.getElementById('summaryCharCount');
    const sentenceCount = document.getElementById('summarySentenceCount');
    
    if (!summaryForm || !summaryText || !summaryMethod) return;
    
    // Character and sentence counter
    summaryText.addEventListener('input', function() {
        const text = this.value;
        const charCountValue = text.length;
        charCount.textContent = charCountValue;
        
        // Count sentences (simple approximation)
        const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
        const sentenceCountValue = sentences.length;
        
        if (sentenceCountValue > 0) {
            sentenceCount.textContent = ` | ${sentenceCountValue} sentences`;
            sentenceCount.style.display = 'inline';
        } else {
            sentenceCount.style.display = 'none';
        }
        
        // Update color based on length
        if (charCountValue < 100) {
            charCount.style.color = '#e74c3c';
        } else if (charCountValue < 300) {
            charCount.style.color = '#f39c12';
        } else {
            charCount.style.color = '#27ae60';
        }
    });
    
    // Method selection handler
    summaryMethod.addEventListener('change', function() {
        const method = this.value;
        document.getElementById('extractive-params').style.display = 
            method === 'extractive' ? 'block' : 'none';
        document.getElementById('abstractive-params').style.display = 
            method === 'abstractive' ? 'block' : 'none';
    });
    
    // Slider value displays
    const sliders = document.querySelectorAll('.param-slider');
    sliders.forEach(slider => {
        const displayId = slider.id + '-value';
        const displayElement = document.getElementById(displayId);
        
        if (displayElement) {
            // Initial value
            displayElement.textContent = slider.value;
            
            // Update on slide
            slider.addEventListener('input', function() {
                displayElement.textContent = this.value;
            });
        }
    });
    
    // Form submission
    summaryForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const text = summaryText.value.trim();
        const method = summaryMethod.value;
        const resultDiv = document.getElementById('summary-result');
        
        // Validation
        if (!text) {
            showMessage(resultDiv, '❌ <strong>Please enter some text to summarize</strong>', 'error');
            return;
        }
        
        if (text.length < 100) {
            showMessage(resultDiv, '❌ <strong>Text is too short!</strong><br>Minimum 100 characters required for summarization.', 'error');
            return;
        }
        
        // Show loading state
        const originalText = generateBtn.innerHTML;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating Summary...';
        generateBtn.disabled = true;
        
        try {
            showMessage(resultDiv, 
                '<div class="loading-message">' +
                '<i class="fas fa-spinner fa-spin"></i><br>' +
                '<strong>Generating summary...</strong><br>' +
                '<small>This may take a moment, especially for long texts</small>' +
                '</div>', 
                'loading');
            
            // Prepare parameters based on method
            let params = new URLSearchParams();
            params.append('text', text);
            params.append('method', method);
            
            if (method === 'extractive') {
                const numSentences = document.getElementById('num-sentences').value;
                params.append('num_sentences', numSentences);
            } else {
                const maxLength = document.getElementById('max-length').value;
                const minLength = document.getElementById('min-length').value;
                params.append('max_length', maxLength);
                params.append('min_length', minLength);
            }
            
            const response = await fetch('/api/summarization/summarize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: params
            });
            
            const result = await response.json();
            
            if (response.ok && result.status === 'success') {
                const summary = result.summary;
                const details = result.details;
                const escapedSummary = escapeHtml(summary);
                
                const resultHTML = `
                    <div class="summary-result-container">
                        <div class="result-header success">
                            <i class="fas fa-check-circle"></i>
                            <h4>✅ Summary Generated Successfully!</h4>
                        </div>
                        <div class="result-details">
                            <p><strong>Method:</strong> ${details.method === 'extractive' ? 'Extractive' : 'Abstractive'}</p>
                            <p><strong>Original:</strong> ${details.original_words} words, ${details.original_chars} characters</p>
                            <p><strong>Summary:</strong> ${details.summary_words} words, ${details.summary_chars} characters</p>
                            <p><strong>Reduction:</strong> ${details.word_reduction} words, ${details.char_reduction} characters</p>
                            ${details.sentences_original ? 
                                `<p><strong>Sentences:</strong> ${details.sentences_original} → ${details.sentences_summary} (${details.compression_ratio})</p>` : ''}
                        </div>
                        <div class="summary-section">
                            <h5>Generated Summary:</h5>
                            <div class="summary-box" id="summaryContent">
                                ${escapedSummary}
                            </div>
                            <div class="text-actions">
                                <button class="action-btn copy-btn" onclick="copySummaryText()">
                                    <i class="fas fa-copy"></i> Copy Summary
                                </button>
                                <button class="action-btn download-btn" onclick="downloadSummaryText('${escapeJs(summary)}')">
                                    <i class="fas fa-download"></i> Download as TXT
                                </button>
                                <button class="action-btn tts-btn" onclick="useSummaryForTTS()">
                                    <i class="fas fa-volume-up"></i> Convert to Speech
                                </button>
                            </div>
                        </div>
                        <div class="comparison-section">
                            <h5>Before & After Comparison:</h5>
                            <div class="comparison-grid">
                                <div class="comparison-col">
                                    <h6><i class="fas fa-file-alt"></i> Original Text</h6>
                                    <div class="comparison-box original">
                                        <div class="comparison-stats">
                                            <span class="stat-badge">${details.original_words} words</span>
                                            <span class="stat-badge">${details.original_chars} chars</span>
                                        </div>
                                        <div class="comparison-text">${escapeHtml(text.substring(0, 300))}${text.length > 300 ? '...' : ''}</div>
                                    </div>
                                </div>
                                <div class="comparison-col">
                                    <h6><i class="fas fa-file-contract"></i> Summary</h6>
                                    <div class="comparison-box summary">
                                        <div class="comparison-stats">
                                            <span class="stat-badge">${details.summary_words} words</span>
                                            <span class="stat-badge">${details.summary_chars} chars</span>
                                            <span class="stat-badge reduction">${details.word_reduction} reduced</span>
                                        </div>
                                        <div class="comparison-text">${escapedSummary}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                showMessage(resultDiv, resultHTML, 'success');
                
            } else {
                showMessage(resultDiv, 
                    `❌ <strong>Summarization Failed</strong><br>
                     Error: ${escapeHtml(result.detail || result.message || 'Unknown error')}`, 
                    'error');
            }
            
        } catch (error) {
            showMessage(resultDiv, 
                `❌ <strong>Network Error</strong><br>
                 ${escapeHtml(error.message)}`, 
                'error');
        } finally {
            // Restore button
            generateBtn.innerHTML = originalText;
            generateBtn.disabled = false;
        }
    });
}

// Helper functions for summarization
function useExtractedText() {
    const summaryText = document.getElementById('summary-text');
    const extractedTextElement = document.getElementById('extractedTextContent');
    
    if (extractedTextElement) {
        const extractedText = extractedTextElement.textContent || extractedTextElement.innerText;
        if (extractedText && extractedText !== 'Text will appear here after extraction...') {
            summaryText.value = extractedText;
            summaryText.dispatchEvent(new Event('input'));
            showCopyNotification('OCR text copied to summarization!', 'success');
        } else {
            showCopyNotification('No extracted text found. Please extract text using OCR first.', 'error');
        }
    } else {
        showCopyNotification('No extracted text found. Please extract text using OCR first.', 'error');
    }
}

function useTranscribedText() {
    const summaryText = document.getElementById('summary-text');
    const transcribedTextElement = document.getElementById('transcribedTextContent');
    
    if (transcribedTextElement) {
        const transcribedText = transcribedTextElement.textContent || transcribedTextElement.innerText;
        if (transcribedText) {
            summaryText.value = transcribedText;
            summaryText.dispatchEvent(new Event('input'));
            showCopyNotification('Transcribed text copied to summarization!', 'success');
        } else {
            showCopyNotification('No transcribed text found. Please transcribe audio using STT first.', 'error');
        }
    } else {
        showCopyNotification('No transcribed text found. Please transcribe audio using STT first.', 'error');
    }
}

function clearSummaryText() {
    const summaryText = document.getElementById('summary-text');
    summaryText.value = '';
    summaryText.dispatchEvent(new Event('input'));
    showCopyNotification('Text cleared', 'info');
}

function copySummaryText() {
    const textBox = document.getElementById('summaryContent');
    if (textBox) {
        const textToCopy = textBox.textContent || textBox.innerText;
        navigator.clipboard.writeText(textToCopy).then(() => {
            showCopyNotification('Summary copied to clipboard!', 'success');
        }).catch(err => {
            showCopyNotification('Failed to copy. Please select and copy manually.', 'error');
        });
    }
}

function downloadSummaryText(text) {
    try {
        const unescapedText = text
            .replace(/\\\\/g, '\\')
            .replace(/\\`/g, '`')
            .replace(/\\\$/g, '$')
            .replace(/\\n/g, '\n')
            .replace(/\\r/g, '\r')
            .replace(/\\t/g, '\t')
            .replace(/\\"/g, '"')
            .replace(/\\'/g, "'");
        
        const filename = `summary_${new Date().getTime()}.txt`;
        const blob = new Blob([unescapedText], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showCopyNotification(`Downloaded: ${filename}`, 'success');
        
    } catch (error) {
        showCopyNotification('Error downloading file', 'error');
    }
}

function useSummaryForTTS() {
    const summaryText = document.getElementById('summary-text');
    const summaryContent = document.getElementById('summaryContent');
    const ttsText = document.getElementById('tts-text');
    
    if (summaryContent && ttsText) {
        const summary = summaryContent.textContent || summaryContent.innerText;
        ttsText.value = summary;
        ttsText.dispatchEvent(new Event('input'));
        
        // Switch to TTS tool
        showTool('tts');
        showCopyNotification('Summary copied to TTS! Switch to TTS tab.', 'success');
    }
}

// Initialize summarization when page loads
document.addEventListener('DOMContentLoaded', function() {
    setupSummarization();
});

// ============ QUESTION GENERATOR FUNCTIONALITY ============

function setupQuestionGenerator() {
    const questionsForm = document.getElementById('questionsForm');
    const questionsText = document.getElementById('questions-text');
    const generateBtn = document.getElementById('questions-generate-btn');
    const charCount = document.getElementById('questionsCharCount');
    const numQuestionsSlider = document.getElementById('num-questions');
    const numQuestionsValue = document.getElementById('num-questions-value');
    
    if (!questionsForm || !questionsText) return;
    
    // Character counter
    questionsText.addEventListener('input', function() {
        const count = this.value.length;
        charCount.textContent = count;
        
        if (count < 50) {
            charCount.style.color = '#e74c3c';
        } else if (count < 200) {
            charCount.style.color = '#f39c12';
        } else {
            charCount.style.color = '#27ae60';
        }
    });
    
    // Slider value display
    if (numQuestionsSlider && numQuestionsValue) {
        numQuestionsValue.textContent = numQuestionsSlider.value;
        numQuestionsSlider.addEventListener('input', function() {
            numQuestionsValue.textContent = this.value;
        });
    }
    
    // Form submission
    questionsForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const text = questionsText.value.trim();
        const resultDiv = document.getElementById('questions-result');
        
        // Validation
        if (!text) {
            showMessage(resultDiv, '❌ <strong>Please enter some study material</strong>', 'error');
            return;
        }
        
        if (text.length < 50) {
            showMessage(resultDiv, '❌ <strong>Text is too short!</strong><br>Minimum 50 characters required.', 'error');
            return;
        }
        
        // Get selected question types
        const checkboxes = document.querySelectorAll('input[name="question-type"]:checked');
        if (checkboxes.length === 0) {
            showMessage(resultDiv, '❌ <strong>Please select at least one question type</strong>', 'error');
            return;
        }
        
        const questionTypes = Array.from(checkboxes).map(cb => cb.value).join(',');
        const numQuestions = document.getElementById('num-questions').value;
        
        // Show loading state
        const originalText = generateBtn.innerHTML;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating Questions...';
        generateBtn.disabled = true;
        
        try {
            showMessage(resultDiv, 
                '<div class="loading-message">' +
                '<i class="fas fa-spinner fa-spin"></i><br>' +
                '<strong>Generating questions...</strong><br>' +
                '<small>Analyzing text and creating exam questions</small>' +
                '</div>', 
                'loading');
            
            // Prepare request
            const params = new URLSearchParams();
            params.append('text', text);
            params.append('question_types', questionTypes);
            params.append('num_questions', numQuestions);
            
            const response = await fetch('/api/questions/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: params
            });
            
            const result = await response.json();
            
            if (response.ok && result.status === 'success') {
                // Format questions for display
                let questionsHTML = `
                    <div class="questions-result-container">
                        <div class="result-header success">
                            <i class="fas fa-check-circle"></i>
                            <h4>✅ ${result.total_generated} Questions Generated!</h4>
                        </div>
                        <div class="result-details">
                            <p><strong>Text Analysis:</strong> ${result.stats.sentences} sentences, ${result.stats.words} words</p>
                            <p><strong>Found:</strong> ${result.stats.key_terms_found} key terms, ${result.stats.concepts_found} concepts</p>
                            <p><strong>Question Types:</strong> ${questionTypes.split(',').join(', ')}</p>
                        </div>
                        <div class="questions-section">
                            <h5>Practice Questions:</h5>
                            <div class="questions-list" id="questionsList">
                `;
                
                result.questions.forEach((q, index) => {
                    const qNumber = index + 1;
                    let qHTML = `
                        <div class="question-item" data-type="${q.type}">
                            <div class="question-header">
                                <span class="question-number">${qNumber}.</span>
                                <span class="question-type">${q.type.toUpperCase()}</span>
                                <span class="question-text">${escapeHtml(q.question)}</span>
                            </div>
                    `;
                    
                    if (q.type === 'mcq') {
                        qHTML += '<div class="mcq-options">';
                        q.options.forEach((option, optIndex) => {
                            const letter = String.fromCharCode(65 + optIndex);
                            const isCorrect = optIndex === q.correct_index;
                            const optionClass = isCorrect ? 'correct-option' : '';
                            qHTML += `
                                <div class="mcq-option ${optionClass}" data-index="${optIndex}">
                                    <span class="option-letter">${letter}.</span>
                                    <span class="option-text">${escapeHtml(option)}</span>
                                    ${isCorrect ? '<span class="correct-badge"><i class="fas fa-check"></i> Correct</span>' : ''}
                                </div>
                            `;
                        });
                        qHTML += '</div>';
                        
                        if (q.explanation) {
                            qHTML += `<div class="question-explanation"><strong>Explanation:</strong> ${escapeHtml(q.explanation)}</div>`;
                        }
                    } else {
                        qHTML += `<div class="question-answer"><strong>Answer:</strong> ${escapeHtml(q.answer)}</div>`;
                    }
                    
                    qHTML += '</div>';
                    questionsHTML += qHTML;
                });
                
                questionsHTML += `
                            </div>
                            <div class="questions-actions">
                                <button class="action-btn download-btn" onclick="downloadQuestionsAsText()">
                                    <i class="fas fa-download"></i> Download as TXT
                                </button>
                                <button class="action-btn quiz-btn" onclick="startQuizMode()">
                                    <i class="fas fa-play-circle"></i> Start Quiz Mode
                                </button>
                                <button class="action-btn copy-btn" onclick="copyQuestions()">
                                    <i class="fas fa-copy"></i> Copy Questions
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                
                // Store questions for later use
                window.generatedQuestions = result.questions;
                
                showMessage(resultDiv, questionsHTML, 'success');
                
            } else {
                showMessage(resultDiv, 
                    `❌ <strong>Question Generation Failed</strong><br>
                     Error: ${escapeHtml(result.detail || result.message || 'Unknown error')}`, 
                    'error');
            }
            
        } catch (error) {
            showMessage(resultDiv, 
                `❌ <strong>Network Error</strong><br>
                 ${escapeHtml(error.message)}`, 
                'error');
        } finally {
            // Restore button
            generateBtn.innerHTML = originalText;
            generateBtn.disabled = false;
        }
    });
}

// Helper functions for question generator
function useExtractedTextForQuestions() {
    const questionsText = document.getElementById('questions-text');
    const extractedTextElement = document.getElementById('extractedTextContent');
    
    if (extractedTextElement) {
        const extractedText = extractedTextElement.textContent || extractedTextElement.innerText;
        if (extractedText && extractedText !== 'Text will appear here after extraction...') {
            questionsText.value = extractedText;
            questionsText.dispatchEvent(new Event('input'));
            showCopyNotification('OCR text copied to question generator!', 'success');
        }
    }
}

function useTranscribedTextForQuestions() {
    const questionsText = document.getElementById('questions-text');
    const transcribedTextElement = document.getElementById('transcribedTextContent');
    
    if (transcribedTextElement) {
        const transcribedText = transcribedTextElement.textContent || transcribedTextElement.innerText;
        if (transcribedText) {
            questionsText.value = transcribedText;
            questionsText.dispatchEvent(new Event('input'));
            showCopyNotification('Transcribed text copied to question generator!', 'success');
        }
    }
}

function useSummaryTextForQuestions() {
    const questionsText = document.getElementById('questions-text');
    const summaryContent = document.getElementById('summaryContent');
    
    if (summaryContent) {
        const summary = summaryContent.textContent || summaryContent.innerText;
        if (summary) {
            questionsText.value = summary;
            questionsText.dispatchEvent(new Event('input'));
            showCopyNotification('Summary copied to question generator!', 'success');
        }
    }
}

function clearQuestionsText() {
    const questionsText = document.getElementById('questions-text');
    questionsText.value = '';
    questionsText.dispatchEvent(new Event('input'));
    showCopyNotification('Text cleared', 'info');
}

function downloadQuestionsAsText() {
    if (!window.generatedQuestions) {
        showCopyNotification('No questions to download', 'error');
        return;
    }
    
    try {
        let textContent = "=== GENERATED PRACTICE QUESTIONS ===\n\n";
        
        window.generatedQuestions.forEach((q, index) => {
            textContent += `${index + 1}. [${q.type.toUpperCase()}] ${q.question}\n`;
            
            if (q.type === 'mcq') {
                q.options.forEach((option, optIndex) => {
                    const letter = String.fromCharCode(65 + optIndex);
                    textContent += `   ${letter}. ${option}\n`;
                });
                textContent += `   Answer: ${q.options[q.correct_index]} (Option ${String.fromCharCode(65 + q.correct_index)})\n`;
            } else {
                textContent += `   Answer: ${q.answer}\n`;
            }
            
            textContent += "\n";
        });
        
        const filename = `practice_questions_${new Date().getTime()}.txt`;
        const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showCopyNotification(`Downloaded: ${filename}`, 'success');
        
    } catch (error) {
        showCopyNotification('Error downloading questions', 'error');
    }
}

function copyQuestions() {
    if (!window.generatedQuestions) {
        showCopyNotification('No questions to copy', 'error');
        return;
    }
    
    try {
        let textContent = "";
        
        window.generatedQuestions.forEach((q, index) => {
            textContent += `${index + 1}. ${q.question}\n`;
            if (q.type === 'mcq') {
                q.options.forEach((option, optIndex) => {
                    const letter = String.fromCharCode(65 + optIndex);
                    textContent += `   ${letter}. ${option}\n`;
                });
            }
            textContent += "\n";
        });
        
        navigator.clipboard.writeText(textContent).then(() => {
            showCopyNotification('Questions copied to clipboard!', 'success');
        });
        
    } catch (error) {
        showCopyNotification('Error copying questions', 'error');
    }
}

function startQuizMode() {
    showCopyNotification('Quiz mode coming soon!', 'info');
}

// Initialize question generator when page loads
document.addEventListener('DOMContentLoaded', function() {
    setupQuestionGenerator();
});
// Add to script.js
function checkDashboardAuth() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login';
        return false;
    }
    return true;
}

// If you're on dashboard page, check auth
if (window.location.pathname === '/dashboard') {
    if (!checkDashboardAuth()) {
        // Redirecting...
    }
}