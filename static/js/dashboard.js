// static/js/dashboard.js

let currentFolderId = 'all';
let folders = [];
let currentNoteId = null;

const sampleNotes = [
    { id: '1', title: 'Machine Learning Notes', type: 'pdf', file_type: 'pdf', size: 2457600, content: 'Sample ML notes content...', last_opened: new Date(Date.now() - 2*3600000).toISOString(), icon: 'fa-file-pdf', folder_id: null },
    { id: '2', title: 'Physics Lecture',         type: 'audio', file_type: 'audio', size: 15938355, content: 'Transcribed physics lecture...', last_opened: new Date(Date.now() - 24*3600000).toISOString(), icon: 'fa-file-audio', folder_id: null },
    { id: '3', title: 'Deep Learning Summary',   type: 'text',  file_type: 'text',  size: 12288,    content: 'Summary of deep learning...', last_opened: new Date(Date.now() - 72*3600000).toISOString(), icon: 'fa-file-alt',   folder_id: null }
];

document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    loadAndDisplayFolders();
    loadNotes();
    setupEventListeners();
});

function checkAuth() {
    if (!localStorage.getItem('access_token')) window.location.href = '/login';
}

// ── Folders ───────────────────────────────────────────────────────

async function loadAndDisplayFolders() {
    try {
        const r = await fetch('/api/documents/folders/list', {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
        });
        folders = r.ok ? (await r.json()).folders || [] : sampleFolders();
    } catch { folders = sampleFolders(); }
    displayFolders();
    updateFolderSelect();
}

function sampleFolders() {
    return [
        { id: '1', name: 'Machine Learning', color: '#f59e0b', count: 2 },
        { id: '2', name: 'Physics', color: '#3b82f6', count: 1 }
    ];
}

function displayFolders() {
    const grid = document.getElementById('foldersGrid');
    if (!grid) return;
    const list = folders.filter(f => f.id !== 'all');
    if (!list.length) {
        grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1">No folders yet. Create one!</div>';
        return;
    }
    grid.innerHTML = list.map(f => `
        <div class="folder-card ${currentFolderId === f.id ? 'active' : ''}" onclick="selectFolder('${f.id}')">
            <div class="folder-icon"><i class="fas fa-folder" style="color:${f.color||'#f59e0b'}"></i></div>
            <div class="folder-info"><h4>${f.name}</h4><p>${f.count||0} items</p></div>
            <div class="folder-menu-btn" onclick="event.stopPropagation();showFolderMenu('${f.id}','${f.name}')">
                <i class="fas fa-ellipsis-h"></i>
            </div>
        </div>`).join('');
}

function selectFolder(folderId) {
    currentFolderId = folderId;
    document.querySelectorAll('.folder-card').forEach(c => c.classList.remove('active'));
    event.currentTarget.classList.add('active');
    loadNotes();
}

function showFolderMenu(folderId, folderName) {
    Swal.fire({
        title: folderName, icon: 'question',
        showCancelButton: true, showDenyButton: true,
        confirmButtonText: '<i class="fas fa-pen"></i> Rename',
        denyButtonText: '<i class="fas fa-trash"></i> Delete',
        cancelButtonText: 'Cancel',
        background: 'var(--modal-bg)', color: 'var(--text-primary)',
        confirmButtonColor: '#f59e0b', denyButtonColor: '#ef4444'
    }).then(r => {
        if (r.isConfirmed) renameFolder(folderId, folderName);
        else if (r.isDenied) deleteFolder(folderId, folderName);
    });
}

async function renameFolder(folderId, oldName) {
    const { value: newName } = await Swal.fire({
        title: 'Rename folder', input: 'text', inputValue: oldName,
        showCancelButton: true, background: 'var(--modal-bg)', color: 'var(--text-primary)', confirmButtonColor: '#f59e0b'
    });
    if (!newName || newName === oldName) return;
    try {
        const fd = new FormData(); fd.append('folder_id', folderId); fd.append('new_name', newName);
        const r = await fetch('/api/documents/folders/rename', {
            method: 'POST', headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }, body: fd
        });
        if (r.ok) { toast('Renamed!'); loadAndDisplayFolders(); }
    } catch { toast('Failed to rename', true); }
}

async function deleteFolder(folderId, folderName) {
    const conf = await Swal.fire({
        title: `Delete "${folderName}"?`, text: 'Notes inside will not be deleted.',
        icon: 'warning', showCancelButton: true,
        confirmButtonText: 'Delete', confirmButtonColor: '#ef4444',
        background: 'var(--modal-bg)', color: 'var(--text-primary)'
    });
    if (!conf.isConfirmed) return;
    try {
        const r = await fetch(`/api/documents/folders/${folderId}`, {
            method: 'DELETE', headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
        });
        if (r.ok) { toast('Folder deleted!'); currentFolderId = 'all'; loadAndDisplayFolders(); loadNotes(); }
    } catch { toast('Failed to delete', true); }
}

function updateFolderSelect() {
    const sel = document.getElementById('folderSelect');
    if (sel) sel.innerHTML = '<option value="">No folder</option>' +
        folders.filter(f => f.id !== 'all').map(f => `<option value="${f.id}">${f.name}</option>`).join('');
}

async function createFolder() {
    const name = document.getElementById('folderName').value.trim();
    if (!name) { toast('Folder name required', true); return; }
    try {
        const fd = new FormData(); fd.append('name', name);
        const r = await fetch('/api/documents/folders/create', {
            method: 'POST', headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }, body: fd
        });
        if (r.ok) {
            toast('Folder created!');
            document.getElementById('folderModal').classList.remove('active');
            document.getElementById('folderName').value = '';
            loadAndDisplayFolders();
        } else { toast('Failed to create folder', true); }
    } catch { toast('Failed to create folder', true); }
}

// ── Notes ─────────────────────────────────────────────────────────

async function loadNotes() {
    try {
        let url = '/api/documents/list';
        if (currentFolderId && currentFolderId !== 'all') url += `?folder_id=${currentFolderId}`;
        const r = await fetch(url, { headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` } });
        if (r.ok) { renderNotes((await r.json()).documents || []); return; }
    } catch {}
    renderNotes(currentFolderId === 'all' ? sampleNotes : sampleNotes.filter(n => n.folder_id === currentFolderId));
}

function renderNotes(notes) {
    const list = document.getElementById('notesList');
    if (!list) return;
    if (!notes.length) { list.innerHTML = '<div class="empty-state">📭 No notes here yet</div>'; return; }

    const iconMap = { pdf:'fa-file-pdf', audio:'fa-file-audio', youtube:'fa-youtube fab', text:'fa-file-alt', image:'fa-file-image' };

    // Store notes lookup map
    window._notesMap = {};
    notes.forEach(n => { window._notesMap[n.id] = n; });

    list.innerHTML = notes.map(n => `
        <div class="note-item" onclick="openNote('${n.id}')">
            <div class="note-icon"><i class="fas ${iconMap[n.file_type||n.type]||'fa-file-alt'}"></i></div>
            <div class="note-info">
                <h4>${n.title}</h4>
                <p>${(n.file_type||n.type||'note').toUpperCase()} &bull; ${formatFileSize(n.size)}</p>
            </div>
            <div class="note-meta">${timeAgo(n.last_opened)}</div>
            <div class="note-actions-wrap">
                <i class="fas fa-ellipsis-h note-menu-btn" onclick="event.stopPropagation();toggleNoteMenu(event,this)"></i>
                <div class="note-dropdown">
                    <div class="dropdown-item" onclick="event.stopPropagation();showMoveModal('${n.id}','${n.title}')"><i class="fas fa-folder"></i> Move</div>
                    <div class="dropdown-item" onclick="event.stopPropagation();renameNotePrompt('${n.id}','${n.title}')"><i class="fas fa-pen"></i> Rename</div>
                    <div class="dropdown-item danger" onclick="event.stopPropagation();deleteNote('${n.id}','${n.title}')"><i class="fas fa-trash"></i> Delete</div>
                </div>
            </div>
        </div>`).join('');
}

async function openNote(noteId) {
    try {
        const meta = window._notesMap && window._notesMap[noteId]
            ? window._notesMap[noteId]
            : { id: noteId };
        if (!window.RightPanel) return;

        // Show loading in panel immediately
        window.RightPanel.open();

        // Fetch full content from API
        const r = await fetch(`/api/documents/${meta.id}`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
        });

        if (!r.ok) {
            const err = await r.json();
            Swal.fire({ icon: 'error', title: 'Could not open note',
                text: err.detail || 'Failed to load note content',
                background: 'var(--modal-bg)', color: 'var(--text-primary)', confirmButtonColor: '#f59e0b' });
            return;
        }

        const note = await r.json();
        window.RightPanel.openNoteTab(note);

    } catch (e) {
        console.error('openNote error', e);
        Swal.fire({ icon: 'error', title: 'Error', text: e.message,
            background: 'var(--modal-bg)', color: 'var(--text-primary)', confirmButtonColor: '#f59e0b' });
    }
}

function toggleNoteMenu(e, el) {
    e.stopPropagation();
    document.querySelectorAll('.note-dropdown').forEach(d => d.classList.remove('show'));
    el.nextElementSibling.classList.toggle('show');
}
document.addEventListener('click', () => document.querySelectorAll('.note-dropdown').forEach(d => d.classList.remove('show')));

function showMoveModal(id, title) {
    currentNoteId = id;
    document.getElementById('moveModal').classList.add('active');
}

async function renameNotePrompt(id, oldTitle) {
    const { value: newTitle } = await Swal.fire({
        title: 'Rename note', input: 'text', inputValue: oldTitle,
        showCancelButton: true, background: 'var(--modal-bg)', color: 'var(--text-primary)', confirmButtonColor: '#f59e0b'
    });
    if (!newTitle || newTitle === oldTitle) return;
    try {
        const fd = new FormData(); fd.append('doc_id', id); fd.append('new_title', newTitle);
        const r = await fetch('/api/documents/rename', {
            method: 'POST', headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }, body: fd
        });
        if (r.ok) { toast('Renamed!'); loadNotes(); }
    } catch { toast('Failed to rename', true); }
}

async function deleteNote(id, title) {
    const conf = await Swal.fire({
        title: `Delete "${title}"?`, icon: 'warning',
        showCancelButton: true, confirmButtonText: 'Delete', confirmButtonColor: '#ef4444',
        background: 'var(--modal-bg)', color: 'var(--text-primary)'
    });
    if (!conf.isConfirmed) return;
    try {
        const r = await fetch(`/api/documents/${id}`, {
            method: 'DELETE', headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
        });
        if (r.ok) { toast('Deleted!'); loadNotes(); }
    } catch { toast('Failed to delete', true); }
}

async function moveNote() {
    const folderId = document.getElementById('folderSelect').value;
    if (!currentNoteId) return;
    try {
        const fd = new FormData(); fd.append('doc_id', currentNoteId); fd.append('folder_id', folderId || '');
        const r = await fetch('/api/documents/move', {
            method: 'POST', headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }, body: fd
        });
        if (r.ok) {
            toast('Moved!');
            document.getElementById('moveModal').classList.remove('active');
            loadNotes(); loadAndDisplayFolders();
        }
    } catch { toast('Failed to move', true); }
}

// ── Event listeners ───────────────────────────────────────────────

function setupEventListeners() {
    document.getElementById('audioCard')?.addEventListener('click', () => document.getElementById('audioFileInput').click());
    document.getElementById('documentCard')?.addEventListener('click', () => document.getElementById('docFileInput').click());
    document.getElementById('youtubeCard')?.addEventListener('click', () => document.getElementById('youtubeModal').classList.add('active'));
    document.getElementById('newFolderBtn')?.addEventListener('click', () => document.getElementById('folderModal').classList.add('active'));
    document.getElementById('createFolderBtn')?.addEventListener('click', createFolder);
    document.getElementById('moveBtn')?.addEventListener('click', moveNote);
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', function () {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
        });
    });
    document.getElementById('searchInput')?.addEventListener('input', function () {
        const q = this.value.toLowerCase();
        document.querySelectorAll('.note-item').forEach(item => {
            const title = item.querySelector('h4')?.textContent.toLowerCase() || '';
            item.style.display = title.includes(q) ? '' : 'none';
        });
    });
}

// ── Helpers ───────────────────────────────────────────────────────

function formatFileSize(b) {
    if (!b) return '0 B'; const u=['B','KB','MB']; let s=b,i=0;
    while(s>=1024&&i<2){s/=1024;i++;} return `${s.toFixed(1)} ${u[i]}`;
}
function timeAgo(d) {
    if(!d) return 'never'; const s=Math.floor((Date.now()-new Date(d))/1000);
    if(s<60) return 'just now'; if(s<3600) return Math.floor(s/60)+'m ago';
    if(s<86400) return Math.floor(s/3600)+'h ago'; return Math.floor(s/86400)+'d ago';
}
function toast(msg, isError) {
    Swal.fire({ icon: isError?'error':'success', title: msg, timer: 1800,
        showConfirmButton: false, background: 'var(--modal-bg)', color: 'var(--text-primary)' });
}

// Globals
window.loadNotes         = loadNotes;
window.selectFolder      = selectFolder;
window.showFolderMenu    = showFolderMenu;
window.openNote          = openNote;
window.toggleNoteMenu    = toggleNoteMenu;
window.showMoveModal     = showMoveModal;
window.renameNotePrompt  = renameNotePrompt;
window.deleteNote        = deleteNote;