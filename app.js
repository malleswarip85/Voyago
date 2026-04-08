// TravelAI — Frontend Logic

const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const typingIndicator = document.getElementById('typingIndicator');
const agentWorking = document.getElementById('agentWorking');

// Agent working messages per stage
const agentMessages = [
    { icon: '🎯', text: 'Orchestrator is coordinating agents...' },
    { icon: '📋', text: 'Requirement Checker validating your details...' },
    { icon: '✈️', text: 'Flight Agent searching best routes...' },
    { icon: '🏨', text: 'Hotel Agent finding top stays...' },
    { icon: '🌤️', text: 'Climate Agent checking weather forecast...' },
    { icon: '🗺️', text: 'Planning Agent building your itinerary...' },
];

let agentMsgInterval = null;
let isLoading = false;

// ── Send message ──
async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text || isLoading) return;

    addMessage(text, 'user');
    messageInput.value = '';
    autoResize(messageInput);
    setLoading(true);

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });

        const data = await response.json();

        if (data.success) {
            addMessage(data.message, 'assistant');
            updateAgentPanel(data.stage, data.collected);
            updateTripInfo(data.collected);
        } else {
            addMessage("I'm having trouble connecting. Please try again! 😊", 'assistant');
        }
    } catch (err) {
        console.error(err);
        addMessage("Connection error. Please check your internet and try again.", 'assistant');
    } finally {
        setLoading(false);
    }
}

// ── Add message to chat ──
function addMessage(text, role) {
    const wrapper = document.createElement('div');
    wrapper.className = `message ${role}-message`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'assistant' ? '✈️' : '👤';

    const content = document.createElement('div');
    content.className = 'message-content';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerHTML = markdownToHtml(text);

    content.appendChild(bubble);
    wrapper.appendChild(avatar);
    wrapper.appendChild(content);

    // Insert before typing indicator or at end
    chatMessages.insertBefore(wrapper, typingIndicator);
    scrollToBottom();
}

// ── Basic markdown parser ──
function markdownToHtml(text) {
    return text
        // Headers
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^# (.+)$/gm, '<h2>$1</h2>')
        // Bold
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        // Code inline
        .replace(/`(.+?)`/g, '<code>$1</code>')
        // HR
        .replace(/^---$/gm, '<hr>')
        // Bullet lists
        .replace(/^  • (.+)$/gm, '<li style="margin-left:20px">$1</li>')
        .replace(/^• (.+)$/gm, '<li>$1</li>')
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/^\* (.+)$/gm, '<li>$1</li>')
        // Numbered lists
        .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
        // Newlines
        .replace(/\n\n/g, '<br><br>')
        .replace(/\n/g, '<br>');
}

// ── Loading state ──
function setLoading(state) {
    isLoading = state;
    sendBtn.disabled = state;

    if (state) {
        typingIndicator.style.display = 'block';
        scrollToBottom();
        startAgentAnimation();
    } else {
        typingIndicator.style.display = 'none';
        stopAgentAnimation();
    }
}

// ── Agent animation cycle ──
function startAgentAnimation() {
    let idx = 0;
    updateAgentWorking(agentMessages[0]);

    agentMsgInterval = setInterval(() => {
        idx = (idx + 1) % agentMessages.length;
        updateAgentWorking(agentMessages[idx]);
        highlightAgent(agentMessages[idx].icon);
    }, 2000);
}

function stopAgentAnimation() {
    if (agentMsgInterval) {
        clearInterval(agentMsgInterval);
        agentMsgInterval = null;
    }
}

function updateAgentWorking(msg) {
    agentWorking.innerHTML = `<span class="working-icon">${msg.icon}</span><span class="working-text">${msg.text}</span>`;
}

// ── Update sidebar agent panel ──
function updateAgentPanel(stage, collected) {
    // Reset all
    document.querySelectorAll('.agent-item').forEach(el => {
        el.classList.remove('working', 'done', 'active');
        el.querySelector('.agent-status').textContent = 'Standby';
    });

    const agentMap = {
        'collecting': ['agent-orchestrator', 'agent-requirements'],
        'planning': ['agent-orchestrator', 'agent-requirements', 'agent-flights', 'agent-hotels', 'agent-climate', 'agent-planning'],
        'done': ['agent-orchestrator', 'agent-requirements', 'agent-flights', 'agent-hotels', 'agent-climate', 'agent-planning'],
    };

    const activeAgents = agentMap[stage] || ['agent-orchestrator'];

    activeAgents.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            if (stage === 'done') {
                el.classList.add('done');
                el.querySelector('.agent-status').textContent = 'Complete ✓';
            } else {
                el.classList.add('active');
                el.querySelector('.agent-status').textContent = 'Active';
            }
        }
    });
}

function highlightAgent(icon) {
    const iconToId = {
        '🎯': 'agent-orchestrator',
        '📋': 'agent-requirements',
        '✈️': 'agent-flights',
        '🏨': 'agent-hotels',
        '🌤️': 'agent-climate',
        '🗺️': 'agent-planning',
    };
    const id = iconToId[icon];
    if (!id) return;

    document.querySelectorAll('.agent-item').forEach(el => el.classList.remove('working'));
    const el = document.getElementById(id);
    if (el) {
        el.classList.add('working');
        el.querySelector('.agent-status').textContent = 'Working...';
    }
}

// ── Trip info sidebar panel ──
function updateTripInfo(collected) {
    if (!collected || Object.keys(collected).length === 0) return;

    const panel = document.getElementById('trip-info');
    const details = document.getElementById('trip-details');

    const fields = [
        { label: 'Destination', key: 'destination', icon: '📍' },
        { label: 'Origin', key: 'origin', icon: '🛫' },
        { label: 'Check-in', key: 'checkin', icon: '📅' },
        { label: 'Check-out', key: 'checkout', icon: '📅' },
        { label: 'Nights', key: 'nights', icon: '🌙' },
        { label: 'Travelers', key: 'travelers', icon: '👤' },
        { label: 'Budget', key: 'budget', icon: '💰', format: v => `$${Number(v).toLocaleString()}` },
    ];

    const items = fields
        .filter(f => collected[f.key])
        .map(f => {
            const val = f.format ? f.format(collected[f.key]) : collected[f.key];
            return `<div class="trip-detail-item">
                <span class="trip-detail-label">${f.icon} ${f.label}</span>
                <span class="trip-detail-value">${val}</span>
            </div>`;
        }).join('');

    if (items) {
        details.innerHTML = items;
        panel.style.display = 'block';
    }
}

// ── Quick prompts ──
function sendQuick(text) {
    messageInput.value = text;
    sendMessage();
}

// ── Reset chat ──
async function resetChat() {
    try {
        await fetch('/api/reset', { method: 'POST' });
    } catch (e) {}

    // Clear messages except welcome
    const messages = chatMessages.querySelectorAll('.message');
    messages.forEach((m, i) => { if (i > 0) m.remove(); });

    // Reset sidebar
    document.querySelectorAll('.agent-item').forEach(el => {
        el.classList.remove('working', 'done', 'active');
        el.querySelector('.agent-status').textContent = 'Standby';
    });
    document.getElementById('trip-info').style.display = 'none';

    messageInput.value = '';
}

// ── Keyboard handler ──
function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

// ── Auto-resize textarea ──
function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

// ── Scroll to bottom ──
function scrollToBottom() {
    setTimeout(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 50);
}
