document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    initializeChat();
    initializeCVForm();
    initializeAnalysis();
    initializeProfile();
});

function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');

            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            button.classList.add('active');
            document.getElementById(`${targetTab}-tab`).classList.add('active');
        });
    });
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
            },
            body: JSON.stringify({ message }),
        });

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
        });

        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.innerHTML = `
            <div class="message bot-message">
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    <p>Hello! I'm your Graduate Career Agent. I can help you with:</p>
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

    fileInput.addEventListener('change', (e) => {
        const fileName = e.target.files[0]?.name || 'No file selected';
        const fileNameDisplay = document.querySelector('.file-name');
        fileNameDisplay.textContent = fileName;
    });

    cvForm.addEventListener('submit', handleCVSubmit);
}

function initializeAnalysis() {
    const analyzeBtn = document.getElementById('analyze-jd-btn');
    const summarizeBtn = document.getElementById('summarize-jd-btn');
    const fileInput = document.getElementById('analysis-cv-file');

    fileInput.addEventListener('change', (e) => {
        const fileName = e.target.files[0]?.name || 'No file selected';
        document.getElementById('analysis-file-name').textContent = fileName;
    });

    analyzeBtn.addEventListener('click', handleAnalyzeJD);
    summarizeBtn.addEventListener('click', handleSummarizeJD);
}

function initializeProfile() {
    const extractBtn = document.getElementById('extract-skills-btn');
    const atsBtn = document.getElementById('ats-score-btn');
    const fileInput = document.getElementById('profile-cv-file');

    fileInput.addEventListener('change', (e) => {
        const fileName = e.target.files[0]?.name || 'No file selected';
        document.getElementById('profile-file-name').textContent = fileName;
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
        let options = { method: 'POST' };
        if (isJson) {
            options.headers = { 'Content-Type': 'application/json' };
            options.body = JSON.stringify(data);
        } else {
            const formData = new FormData();
            for (const key in data) {
                formData.append(key, data[key]);
            }
            options.body = formData;
        }

        const response = await fetch(url, options);
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
            body: formData,
        });

        const data = await response.json();

        if (data.response) {
            const htmlContent = marked.parse(data.response);
            resultDiv.innerHTML = htmlContent;
            resultDiv.classList.add('show');

            resultDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
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

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
