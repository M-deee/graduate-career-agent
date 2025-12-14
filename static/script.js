// Helper to toggle password visibility
function setupPasswordToggle() {
    const toggleBtn = document.getElementById('toggle-password');
    const passwordInput = document.getElementById('password');

    if (toggleBtn && passwordInput) {
        toggleBtn.addEventListener('click', () => {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);

            // Toggle icons
            toggleBtn.querySelector('.eye-open').style.display = type === 'password' ? 'block' : 'none';
            toggleBtn.querySelector('.eye-closed').style.display = type === 'text' ? 'block' : 'none';
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;

    if (path.endsWith('login.html')) {
        initializeLogin();
    } else if (path.endsWith('register.html')) {
        initializeRegister();
    } else {
        // Main App
        checkAuth(); // Verify user is logged in
        setupLogout();

        // Only initialize if elements exist and haven't been initialized
        if (document.querySelector('.tab-button')) initializeTabs();

        // Setup scroll handler (global capture)
        setupScrollHandler();

        if (document.getElementById('chat-input')) initializeChat();
        if (document.getElementById('cv-form')) initializeCVForm();
        if (document.getElementById('analyze-jd-btn')) initializeAnalysis();
        if (document.getElementById('extract-skills-btn')) initializeProfile();

        const closeArtifactBtn = document.getElementById('close-artifact-btn');
        if (closeArtifactBtn) {
            closeArtifactBtn.addEventListener('click', closeArtifactPanel);
        }
    }
});

// --- Auth Functions ---

function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }
    // Optional: Verify token validity via API or simple expiry check
    // For now, assume if it exists, it's valid until a 401 happens
}

function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

function setupLogout() {
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.removeItem('access_token');
            window.location.href = 'login.html';
        });
    }
}

function initializeLogin() {
    setupPasswordToggle(); // Add toggle logic
    const form = document.getElementById('login-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const errorDiv = document.getElementById('login-error');

        try {
            const formData = new FormData();
            formData.append('username', email);
            formData.append('password', password);

            const response = await fetch('/api/token', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Login failed');
            }

            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            window.location.href = 'index.html'; // Redirect to main app
        } catch (error) {
            errorDiv.textContent = error.message;
            errorDiv.style.display = 'block';
        }
    });
}

function initializeRegister() {
    setupPasswordToggle(); // Add toggle logic
    const form = document.getElementById('register-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const fullname = document.getElementById('fullname').value;
        const errorDiv = document.getElementById('register-error');

        try {
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password, full_name: fullname })
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Registration failed');
            }

            // Auto login or redirect to login
            alert('Registration successful! Please login.');
            window.location.href = 'login.html';
        } catch (error) {
            errorDiv.textContent = error.message;
            errorDiv.style.display = 'block';
        }
    });
}

// --- Global State & Sync ---
let globalCVFile = null;
let globalJDText = '';
let syncTimeout = null; // Debounce for JD text

async function syncContextToBackend() {
    // We only sync if we have something to sync
    if (!globalCVFile && !globalJDText) return;

    const formData = new FormData();
    if (globalCVFile) formData.append('file', globalCVFile);
    if (globalJDText) formData.append('job_description', globalJDText);

    try {
        await fetch('/api/update_context', {
            method: 'POST',
            headers: { ...getAuthHeaders() },
            body: formData
        });
        console.log('Context synced to backend');
    } catch (e) {
        console.error('Failed to sync context:', e);
    }
}

function updateGlobalCV(file, sourceId) {
    if (!file) return;
    globalCVFile = file;

    // Sync to backend immediately for files
    syncContextToBackend();

    const fileInputs = {
        'cv-file': { displayId: null }, // Uses relative lookup
        'analysis-cv-file': { displayId: 'analysis-file-name' },
        'profile-cv-file': { displayId: 'profile-file-name' }
    };

    Object.keys(fileInputs).forEach(id => {
        if (id === sourceId) return;

        const input = document.getElementById(id);
        if (input) {
            // 1. Set the file on the input
            const dt = new DataTransfer();
            dt.items.add(file);
            input.files = dt.files;

            // 2. Update the visual text
            let nameDisplay = null;
            if (fileInputs[id].displayId) {
                nameDisplay = document.getElementById(fileInputs[id].displayId);
            } else {
                // Fallback for cv-file which doesn't have an ID on the span
                const container = input.closest('.file-drop-zone');
                if (container) nameDisplay = container.querySelector('.file-name');
            }

            if (nameDisplay) {
                nameDisplay.textContent = file.name;
                nameDisplay.style.color = 'var(--primary)'; // Visual feedback
            }
        }
    });
}

function updateGlobalJD(text, sourceId) {
    console.log(`updateGlobalJD called from ${sourceId}`);
    globalJDText = text;

    // Debounce backend sync for text typing
    if (syncTimeout) clearTimeout(syncTimeout);
    syncTimeout = setTimeout(syncContextToBackend, 1000); // 1 sec delay

    const inputIds = ['job-description', 'analysis-job-description'];
    inputIds.forEach(id => {
        if (id === sourceId) return;
        const input = document.getElementById(id);
        if (input) {
            console.log(`Syncing JD to input: ${id}`);
            input.value = text;
        } else {
            console.warn(`Target input ${id} not found`);
        }
    });
}

// --- App Functions ---

function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault(); // Prevent accidental form submits or jumps
            const targetTab = button.getAttribute('data-tab');

            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked button
            button.classList.add('active');

            // Find target content and activate it
            const targetContent = document.getElementById(`${targetTab}-tab`);
            if (targetContent) {
                targetContent.classList.add('active');

                // If switching tabs, we might need to reset scroll handler state or check scroll position
                // But global scroll handler covers this
            }
        });
    });
}

// Robust scroll handler using event capture and wheel detection
function setupScrollHandler() {
    const container = document.querySelector('.container');

    // SCROLL LISTENER: Handles layout changes based on actual scroll position
    window.addEventListener('scroll', (e) => {
        const target = e.target;
        if (target.classList?.contains('glass-card') || target.id === 'chat-messages') {
            // Collapse logic if actually scrolled down
            if (target.scrollTop > 20) {
                container.classList.add('compact-mode');
            }
        }
    }, true);

    // State for strict reveal
    let accumulatedScrollUp = 0;
    const REVEAL_THRESHOLD = 400; // Approx 3 "ticks" or swipes

    // WHEEL LISTENER: Handles intent to scroll (useful if content fits on screen or for lower latency)
    window.addEventListener('wheel', (e) => {
        // Only trigger if we are inside the main content areas
        const target = e.target.closest('.glass-card, #chat-messages');
        if (!target) return;

        // Scrolling DOWN (positive delta) -> Collapse
        if (e.deltaY > 0) {
            // Reset accumulator if we change direction
            accumulatedScrollUp = 0;

            // Collapse immediately if intent is down
            if (e.deltaY > 10) {
                container.classList.add('compact-mode');
            }
        }

        // Scrolling UP (negative delta) -> Expand ONLY if we match strict criteria
        else if (e.deltaY < 0) {
            const scrollParent = e.target.closest('.glass-card, #chat-messages') || document.querySelector('.content.glass-card');

            // Only count if we are effectively at the top
            if (scrollParent && scrollParent.scrollTop <= 0) {
                // Accumulate the absolute delta
                accumulatedScrollUp += Math.abs(e.deltaY);

                // Check if we hit the threshold
                if (accumulatedScrollUp > REVEAL_THRESHOLD) {
                    container.classList.remove('compact-mode');
                    accumulatedScrollUp = 0; // Reset after reveal
                }
            } else {
                // If not at top, reset
                accumulatedScrollUp = 0;
            }
        }
    }, { passive: true });
}

function initializeChat() {
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const resetBtn = document.getElementById('reset-btn');

    sendBtn.addEventListener('click', sendMessage);

    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    resetBtn.addEventListener('click', resetConversation);
}

async function sendMessage() {
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const messagesContainer = document.getElementById('chat-messages');

    const message = chatInput.value.trim();

    if (!message) return;

    addUserMessage(message);
    chatInput.value = '';

    chatInput.disabled = true;
    sendBtn.disabled = true;

    showTypingIndicator();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders() // Add Auth
            },
            body: JSON.stringify({ message }),
        });

        if (response.status === 401) {
            window.location.href = 'login.html';
            return;
        }

        const data = await response.json();

        removeTypingIndicator();

        if (data.response) {
            addBotMessage(data.response);
        } else if (data.error) {
            addBotMessage('Sorry, there was an error processing your message. Please try again.');
        }
    } catch (error) {
        console.error('Error:', error);
        removeTypingIndicator();
        addBotMessage('Sorry, I encountered an error. Please check your connection and try again.');
    } finally {
        chatInput.disabled = false;
        sendBtn.disabled = false;
        chatInput.focus();
    }
}

function addUserMessage(text) {
    const messagesContainer = document.getElementById('chat-messages');

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user-message';

    messageDiv.innerHTML = `
        <div class="message-avatar">👤</div>
        <div class="message-content">
            <p>${escapeHtml(text)}</p>
        </div>
    `;

    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

function addBotMessage(text) {
    const messagesContainer = document.getElementById('chat-messages');

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';

    messageDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <p>${escapeHtml(text)}</p>
        </div>
    `;

    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('chat-messages');

    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-message typing-indicator-message';
    typingDiv.id = 'typing-indicator';

    typingDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;

    messagesContainer.appendChild(typingDiv);
    scrollToBottom();
}

function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

function scrollToBottom() {
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

async function resetConversation() {
    if (!confirm('Are you sure you want to reset the conversation?')) {
        return;
    }

    try {
        await fetch('/api/reset', {
            method: 'POST',
            headers: { ...getAuthHeaders() }
        });

        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.innerHTML = `
            <div class="message bot-message">
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    <p>Hello! I'm Gradpilot. I can help you with:</p>
                    <ul>
                        <li>Career advice and guidance</li>
                        <li>Interview preparation</li>
                        <li>Job search strategies</li>
                        <li>CV and cover letter tips</li>
                    </ul>
                    <p>How can I assist you today?</p>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error resetting conversation:', error);
        alert('Failed to reset conversation. Please try again.');
    }
}

function initializeCVForm() {
    const cvForm = document.getElementById('cv-form');
    const fileInput = document.getElementById('cv-file');
    const jdInput = document.getElementById('job-description');

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        const fileName = file?.name || 'No file selected';

        // Use simpler, scoped selection
        const container = fileInput.closest('.file-drop-zone');
        const fileNameDisplay = container ? container.querySelector('.file-name') : null;

        if (fileNameDisplay) fileNameDisplay.textContent = fileName;
        if (file) updateGlobalCV(file, 'cv-file');
    });

    jdInput.addEventListener('input', (e) => {
        updateGlobalJD(e.target.value, 'job-description');
    });

    cvForm.addEventListener('submit', handleCVSubmit);
}

function initializeAnalysis() {
    const analyzeBtn = document.getElementById('analyze-jd-btn');
    const summarizeBtn = document.getElementById('summarize-jd-btn');
    const fileInput = document.getElementById('analysis-cv-file');
    const jdInput = document.getElementById('analysis-job-description');

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        const fileName = file?.name || 'No file selected';
        document.getElementById('analysis-file-name').textContent = fileName;
        if (file) updateGlobalCV(file, 'analysis-cv-file');
    });

    jdInput.addEventListener('input', (e) => {
        updateGlobalJD(e.target.value, 'analysis-job-description');
    });

    analyzeBtn.addEventListener('click', handleAnalyzeJD);
    summarizeBtn.addEventListener('click', handleSummarizeJD);
}

function initializeProfile() {
    const extractBtn = document.getElementById('extract-skills-btn');
    const atsBtn = document.getElementById('ats-score-btn');
    const fileInput = document.getElementById('profile-cv-file');

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        const fileName = file?.name || 'No file selected';
        document.getElementById('profile-file-name').textContent = fileName;
        if (file) updateGlobalCV(file, 'profile-cv-file');
    });

    extractBtn.addEventListener('click', handleExtractSkills);
    atsBtn.addEventListener('click', handleATSScore);
}

async function handleAnalyzeJD(e) {
    e.preventDefault();
    const file = document.getElementById('analysis-cv-file').files[0];
    const jobDesc = document.getElementById('analysis-job-description').value.trim();
    const resultDiv = document.getElementById('analysis-result');

    if (!file || !jobDesc) {
        alert('Please provide both CV and Job Description');
        return;
    }

    await processRequest('/api/analyze_jd', { file, job_description: jobDesc }, resultDiv);
}

async function handleSummarizeJD(e) {
    e.preventDefault();
    const jobDesc = document.getElementById('analysis-job-description').value.trim();
    const resultDiv = document.getElementById('analysis-result');

    if (!jobDesc) {
        alert('Please provide Job Description');
        return;
    }

    await processRequest('/api/summarize_jd', { job_description: jobDesc }, resultDiv, true);
}

async function handleExtractSkills(e) {
    e.preventDefault();
    const file = document.getElementById('profile-cv-file').files[0];
    const resultDiv = document.getElementById('profile-result');

    if (!file) {
        alert('Please upload your CV');
        return;
    }

    await processRequest('/api/extract_skills', { file }, resultDiv);
}

async function handleATSScore(e) {
    e.preventDefault();
    const file = document.getElementById('profile-cv-file').files[0];
    const resultDiv = document.getElementById('profile-result');

    if (!file) {
        alert('Please upload your CV');
        return;
    }

    await processRequest('/api/ats_score', { file }, resultDiv);
}

async function processRequest(url, data, resultDiv, isJson = false) {
    const loadingOverlay = document.getElementById('loading-overlay');
    loadingOverlay.classList.add('show');
    resultDiv.classList.remove('show');

    try {
        let options = {
            method: 'POST',
            headers: {
                ...getAuthHeaders() // Add Auth
            }
        };
        if (isJson) {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(data);
        } else {
            const formData = new FormData();
            for (const key in data) {
                formData.append(key, data[key]);
            }
            options.body = formData;
        }

        const response = await fetch(url, options);

        if (response.status === 401) {
            window.location.href = 'login.html';
            return;
        }

        const responseData = await response.json();

        if (responseData.response) {
            resultDiv.innerHTML = marked.parse(responseData.response);
            resultDiv.classList.add('show');
            resultDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else if (responseData.error) {
            alert('Error: ' + responseData.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to process request. Please try again.');
    } finally {
        loadingOverlay.classList.remove('show');
    }
}

async function handleCVSubmit(e) {
    e.preventDefault();

    const fileInput = document.getElementById('cv-file');
    const jobDescription = document.getElementById('job-description');
    const submitBtn = document.querySelector('.submit-button');
    const resultDiv = document.getElementById('cv-result');
    const loadingOverlay = document.getElementById('loading-overlay');

    const file = fileInput.files[0];
    const jobDesc = jobDescription.value.trim();

    if (!file) {
        alert('Please upload your CV (PDF file)');
        return;
    }

    if (!jobDesc) {
        alert('Please enter the job description');
        return;
    }

    if (file.type !== 'application/pdf') {
        alert('Please upload a PDF file');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('job_description', jobDesc);

    submitBtn.disabled = true;
    loadingOverlay.classList.add('show');
    resultDiv.classList.remove('show');

    try {
        const response = await fetch('/api/tailor_cv', {
            method: 'POST',
            headers: { ...getAuthHeaders() }, // Add Auth
            body: formData,
        });

        if (response.status === 401) {
            window.location.href = 'login.html';
            return;
        }

        const data = await response.json();

        if (data.response) {
            // Hide Input View elements
            const cvHeader = document.querySelector('#cv-tab .cv-header');
            const cvForm = document.getElementById('cv-form');
            if (cvHeader) cvHeader.style.display = 'none';
            if (cvForm) cvForm.style.display = 'none';

            const htmlContent = marked.parse(data.response);

            // Add "Back" button and "Artifact Card" to top of result
            const backBtnHtml = `
                <div class="result-actions" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
                    <button id="reset-cv-view" class="reset-button" style="background: var(--bg-secondary); color: var(--text-primary); border: 1px solid var(--border);">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/>
                        </svg>
                        Tailor Another CV
                    </button>
                </div>
            `;

            // Artifact Card for CV
            let artifactCardHtml = '';
            if (data.cv_content) {
                artifactCardHtml = `
                <div class="artifact-card" onclick="showCVContent()" style="cursor: pointer;">
                    <div class="artifact-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                            <polyline points="14 2 14 8 20 8"></polyline>
                            <line x1="16" y1="13" x2="8" y2="13"></line>
                            <line x1="16" y1="17" x2="8" y2="17"></line>
                            <polyline points="10 9 9 9 8 9"></polyline>
                        </svg>
                    </div>
                    <div class="artifact-info">
                        <div class="artifact-title">Tailored CV</div>
                        <div class="artifact-meta">Click to view & copy</div>
                    </div>
                    <div class="artifact-arrow">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                            <polyline points="15 3 21 3 21 9"></polyline>
                            <line x1="10" y1="14" x2="21" y2="3"></line>
                        </svg>
                    </div>
                </div>
                `;
            }

            resultDiv.innerHTML = backBtnHtml + artifactCardHtml + htmlContent;
            resultDiv.classList.add('show');
            resultDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });

            // Add event listener for back button
            document.getElementById('reset-cv-view').addEventListener('click', () => {
                if (cvHeader) cvHeader.style.display = 'block';
                if (cvForm) cvForm.style.display = 'block';
                resultDiv.classList.remove('show');
                resultDiv.innerHTML = ''; // Clear result
                closeArtifactPanel();
            });

            if (data.cv_content) {
                // Prepare UI for Code View
                window.currentCVContent = data.cv_content;
                showCVContent();
            }
        } else if (data.error) {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to process your CV. Please try again.');
    } finally {
        submitBtn.disabled = false;
        loadingOverlay.classList.remove('show');
    }
}

// Reusing Artifact Panel for LaTeX Code
function showCVContent() {
    const panel = document.getElementById('artifact-panel');
    const content = panel.querySelector('.artifact-content');
    const headerTitle = panel.querySelector('.artifact-header h3');

    // Update Header
    headerTitle.innerHTML = `
        <span style="font-size: 1.2em; margin-right: 8px;">📄</span> Tailored CV
    `;

    // Create Copy Button
    const copyBtn = document.createElement('button');
    copyBtn.className = 'submit-button';
    copyBtn.style.cssText = 'padding: 8px 16px; margin-left: auto; font-size: 0.85rem;';
    copyBtn.innerHTML = `
        <span class="btn-content" style="gap: 6px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
            Copy Text
        </span>
    `;

    copyBtn.onclick = () => {
        navigator.clipboard.writeText(window.currentCVContent).then(() => {
            const originalText = copyBtn.innerHTML;
            copyBtn.innerHTML = `<span class="btn-content">✅ Copied!</span>`;
            setTimeout(() => {
                copyBtn.innerHTML = originalText;
            }, 2000);
        });
    };

    // Clear existing header actions (except title and close)
    const existingCopy = panel.querySelector('.copy-action');
    if (existingCopy) existingCopy.remove();

    // Append Copy Button to Header (temporarily)
    const closeBtn = panel.querySelector('.close-btn');
    closeBtn.parentNode.insertBefore(copyBtn, closeBtn);
    copyBtn.classList.add('copy-action');

    // Render Markdown Content
    // We wrap it in a 'markdown-body' or similar for clean styling
    const htmlContent = marked.parse(window.currentCVContent);
    content.innerHTML = `
        <div class="cv-render-preview" style="padding: 24px; color: #333; line-height: 1.6;">
            ${htmlContent}
        </div>
    `;

    panel.classList.add('open');
    document.querySelector('.main-layout').classList.add('has-artifact');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
