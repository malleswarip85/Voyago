// Voyago — Frontend v6 — Single upfront form

const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const typingIndicator = document.getElementById('typingIndicator');
const agentWorking = document.getElementById('agentWorking');

const agentMessages = [
    { icon: '🎯', text: 'Orchestrator coordinating agents...' },
    { icon: '📋', text: 'Checking your requirements...' },
    { icon: '✈️', text: 'Flight Agent searching routes...' },
    { icon: '🏨', text: 'Hotel Agent finding best stays...' },
    { icon: '🌤️', text: 'Climate Agent fetching forecast...' },
    { icon: '🗺️', text: 'Planning Agent building itinerary...' },
];

let agentMsgInterval = null;
let isLoading = false;
let tripStage = 'greeting';
let tripFormShown = false;
let travelerFormPending = false;

// ══════════════════════════════════════
// INIT — Show trip planning form immediately
// ══════════════════════════════════════
window.addEventListener('load', () => {
    setTimeout(() => renderTripForm(), 600);
});

function renderTripForm() {
    if (tripFormShown) return;
    tripFormShown = true;

    const wrapper = document.createElement('div');
    wrapper.className = 'message assistant-message';
    wrapper.id = 'trip-form-wrapper';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '✈️';

    const content = document.createElement('div');
    content.className = 'message-content';
    content.style.maxWidth = '94%';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.style.padding = '0';
    bubble.style.overflow = 'hidden';

    bubble.innerHTML = buildTripForm();
    content.appendChild(bubble);
    wrapper.appendChild(avatar);
    wrapper.appendChild(content);

    if (typingIndicator && typingIndicator.parentNode === chatMessages) {
        chatMessages.insertBefore(wrapper, typingIndicator);
    } else {
        chatMessages.appendChild(wrapper);
    }
    scrollToBottom();

    // Set min date for date inputs
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('tf-checkin').min = today;
    document.getElementById('tf-checkout').min = today;

    // Auto-update checkout min when checkin changes
    document.getElementById('tf-checkin').addEventListener('change', function() {
        document.getElementById('tf-checkout').min = this.value;
        if (document.getElementById('tf-checkout').value < this.value) {
            document.getElementById('tf-checkout').value = '';
        }
    });
}

function buildTripForm() {
    return `
    <div style="background:linear-gradient(135deg,#1e3a8a,#1d4ed8);padding:14px 18px;">
        <div style="font-family:'Playfair Display',serif;font-size:17px;font-style:italic;color:white;font-weight:600;">Plan Your Trip ✈️</div>
        <div style="font-size:11px;color:rgba(255,255,255,0.7);margin-top:2px;">Fill in your details and we'll handle the rest!</div>
    </div>

    <div style="padding:16px 18px;" id="trip-form-body">

        <!-- Row 1: Origin & Destination -->
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">
            <div>
                <label style="font-size:10.5px;font-weight:700;color:#1e40af;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.06em;">🛫 From (Origin City)</label>
                <input type="text" id="tf-origin" placeholder="e.g. Atlanta, Chicago"
                    style="width:100%;padding:9px 12px;border:1.5px solid rgba(59,130,246,0.18);border-radius:8px;font-family:'DM Sans',sans-serif;font-size:13px;background:#eff6ff;color:#1e3058;outline:none;transition:all 0.2s;"
                    onfocus="this.style.borderColor='#00b894';this.style.background='white'"
                    onblur="this.style.borderColor='rgba(59,130,246,0.18)';this.style.background='#eff6ff'">
                <span class="tf-error" id="err-origin"></span>
            </div>
            <div>
                <label style="font-size:10.5px;font-weight:700;color:#1e40af;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.06em;">📍 To (Destination)</label>
                <input type="text" id="tf-destination" placeholder="e.g. Paris, Singapore"
                    style="width:100%;padding:9px 12px;border:1.5px solid rgba(59,130,246,0.18);border-radius:8px;font-family:'DM Sans',sans-serif;font-size:13px;background:#eff6ff;color:#1e3058;outline:none;transition:all 0.2s;"
                    onfocus="this.style.borderColor='#00b894';this.style.background='white'"
                    onblur="this.style.borderColor='rgba(59,130,246,0.18)';this.style.background='#eff6ff'">
                <span class="tf-error" id="err-destination"></span>
            </div>
        </div>

        <!-- Row 2: Dates -->
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">
            <div>
                <label style="font-size:10.5px;font-weight:700;color:#1e40af;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.06em;">📅 Check-in Date</label>
                <input type="date" id="tf-checkin"
                    style="width:100%;padding:9px 12px;border:1.5px solid rgba(59,130,246,0.18);border-radius:8px;font-family:'DM Sans',sans-serif;font-size:13px;background:#eff6ff;color:#1e3058;outline:none;transition:all 0.2s;"
                    onfocus="this.style.borderColor='#00b894';this.style.background='white'"
                    onblur="this.style.borderColor='rgba(59,130,246,0.18)';this.style.background='#eff6ff'">
                <span class="tf-error" id="err-checkin"></span>
            </div>
            <div>
                <label style="font-size:10.5px;font-weight:700;color:#1e40af;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.06em;">📅 Check-out Date</label>
                <input type="date" id="tf-checkout"
                    style="width:100%;padding:9px 12px;border:1.5px solid rgba(59,130,246,0.18);border-radius:8px;font-family:'DM Sans',sans-serif;font-size:13px;background:#eff6ff;color:#1e3058;outline:none;transition:all 0.2s;"
                    onfocus="this.style.borderColor='#00b894';this.style.background='white'"
                    onblur="this.style.borderColor='rgba(59,130,246,0.18)';this.style.background='#eff6ff'">
                <span class="tf-error" id="err-checkout"></span>
            </div>
        </div>

        <!-- Row 3: Budget, Travelers, Nonstop -->
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:16px;">
            <div>
                <label style="font-size:10.5px;font-weight:700;color:#1e40af;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.06em;">💰 Total Budget (USD)</label>
                <input type="number" id="tf-budget" placeholder="e.g. 3000" min="200"
                    style="width:100%;padding:9px 12px;border:1.5px solid rgba(59,130,246,0.18);border-radius:8px;font-family:'DM Sans',sans-serif;font-size:13px;background:#eff6ff;color:#1e3058;outline:none;transition:all 0.2s;"
                    onfocus="this.style.borderColor='#00b894';this.style.background='white'"
                    onblur="this.style.borderColor='rgba(59,130,246,0.18)';this.style.background='#eff6ff'">
                <span class="tf-error" id="err-budget"></span>
            </div>
            <div>
                <label style="font-size:10.5px;font-weight:700;color:#1e40af;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.06em;">👥 No. of Travelers</label>
                <input type="number" id="tf-travelers" placeholder="e.g. 2" min="1" max="20"
                    style="width:100%;padding:9px 12px;border:1.5px solid rgba(59,130,246,0.18);border-radius:8px;font-family:'DM Sans',sans-serif;font-size:13px;background:#eff6ff;color:#1e3058;outline:none;transition:all 0.2s;"
                    onfocus="this.style.borderColor='#00b894';this.style.background='white'"
                    onblur="this.style.borderColor='rgba(59,130,246,0.18)';this.style.background='#eff6ff'">
                <span class="tf-error" id="err-travelers"></span>
            </div>
            <div>
                <label style="font-size:10.5px;font-weight:700;color:#1e40af;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.06em;">✈️ Non-stop Flights?</label>
                <select id="tf-nonstop"
                    style="width:100%;padding:9px 12px;border:1.5px solid rgba(59,130,246,0.18);border-radius:8px;font-family:'DM Sans',sans-serif;font-size:13px;background:#eff6ff;color:#1e3058;outline:none;transition:all 0.2s;"
                    onfocus="this.style.borderColor='#00b894';this.style.background='white'"
                    onblur="this.style.borderColor='rgba(59,130,246,0.18)';this.style.background='#eff6ff'">
                    <option value="">Select...</option>
                    <option value="yes">Yes — Non-stop only</option>
                    <option value="no">No — Any flights</option>
                </select>
                <span class="tf-error" id="err-nonstop"></span>
            </div>
        </div>

        <!-- Submit -->
        <button onclick="submitTripForm()"
            style="width:100%;padding:12px;background:linear-gradient(135deg,#1e3a8a,#1d4ed8);color:white;border:none;border-radius:9px;font-family:'DM Sans',sans-serif;font-size:14px;font-weight:700;cursor:pointer;transition:all 0.2s;box-shadow:0 4px 14px rgba(0,184,148,0.3);"
            onmouseover="this.style.transform='translateY(-1px)';this.style.boxShadow='0 6px 20px rgba(0,184,148,0.4)'"
            onmouseout="this.style.transform='';this.style.boxShadow='0 4px 14px rgba(0,184,148,0.3)'"
            id="tf-submit-btn">
            🔍 Search Flights, Hotels & Weather
        </button>

        <div style="text-align:center;font-size:10.5px;color:#82a898;margin-top:8px;">
            Powered by Duffel · Booking.com · OpenWeatherMap · Gemini AI
        </div>
    </div>
    `;
}

function clearTfErrors() {
    document.querySelectorAll('.tf-error').forEach(e => e.textContent = '');
    document.querySelectorAll('#trip-form-body input, #trip-form-body select').forEach(el => {
        el.style.borderColor = 'rgba(59,130,246,0.18)';
    });
}

function showTfError(fieldId, errId, msg) {
    const field = document.getElementById(fieldId);
    const err = document.getElementById(errId);
    if (field) field.style.borderColor = '#ff6b6b';
    if (err) err.textContent = msg;
    err.style.cssText = 'color:#cc3333;font-size:10.5px;display:block;margin-top:3px;font-weight:500;';
}

function submitTripForm() {
    clearTfErrors();

    const origin      = document.getElementById('tf-origin')?.value.trim();
    const destination = document.getElementById('tf-destination')?.value.trim();
    const checkin     = document.getElementById('tf-checkin')?.value;
    const checkout    = document.getElementById('tf-checkout')?.value;
    const budget      = document.getElementById('tf-budget')?.value.trim();
    const travelers   = document.getElementById('tf-travelers')?.value.trim();
    const nonstop     = document.getElementById('tf-nonstop')?.value;

    let valid = true;
    const today = new Date().toISOString().split('T')[0];

    if (!origin || origin.length < 2) {
        showTfError('tf-origin', 'err-origin', 'Please enter your departure city'); valid = false;
    }
    if (!destination || destination.length < 2) {
        showTfError('tf-destination', 'err-destination', 'Please enter your destination'); valid = false;
    }
    if (!checkin || checkin < today) {
        showTfError('tf-checkin', 'err-checkin', 'Please select a future check-in date'); valid = false;
    }
    if (!checkout || checkout <= checkin) {
        showTfError('tf-checkout', 'err-checkout', 'Check-out must be after check-in'); valid = false;
    }
    if (!budget || parseFloat(budget) < 200) {
        showTfError('tf-budget', 'err-budget', 'Minimum budget is $200'); valid = false;
    }
    const tNum = parseInt(travelers);
    if (!travelers || isNaN(tNum) || tNum < 1 || tNum > 20) {
        showTfError('tf-travelers', 'err-travelers', 'Enter 1–20 travelers'); valid = false;
    }
    if (!nonstop) {
        showTfError('tf-nonstop', 'err-nonstop', 'Please select flight preference'); valid = false;
    }

    if (!valid) return;

    // Disable form
    const btn = document.getElementById('tf-submit-btn');
    btn.disabled = true;
    btn.textContent = '⏳ Searching...';
    btn.style.opacity = '0.7';
    document.querySelectorAll('#trip-form-body input, #trip-form-body select').forEach(el => el.disabled = true);

    // Build structured message for orchestrator
    const nights = Math.round((new Date(checkout) - new Date(checkin)) / (1000*60*60*24));
    const summary = `TRIP_FORM:${JSON.stringify({
        origin, destination, checkin, checkout,
        budget: parseFloat(budget),
        travelers: tNum,
        nonstop_preferred: nonstop === 'yes',
        nights
    })}`;

    // Show summary to user
    const userSummary = `From: ${origin} → ${destination}\nDates: ${checkin} to ${checkout} (${nights} nights)\nBudget: $${parseFloat(budget).toLocaleString()} | Travelers: ${tNum} | Non-stop: ${nonstop === 'yes' ? 'Yes' : 'No'}`;
    addMessage(userSummary, 'user');

    callAPI(summary);
}

// ══════════════════════════════════════
// SEND (for follow-up chat after form)
// ══════════════════════════════════════
async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text || isLoading) return;
    addMessage(text, 'user');
    messageInput.value = '';
    autoResize(messageInput);
    await callAPI(text);
}

function resetTripFormButton() {
    const btn = document.getElementById('tf-submit-btn');
    if (btn) {
        btn.disabled = false;
        btn.textContent = '🔍 Search Flights, Hotels & Weather';
        btn.style.opacity = '1';
    }
    document.querySelectorAll('#trip-form-body input, #trip-form-body select').forEach(el => el.disabled = false);
}

async function callAPI(text) {
    setLoading(true);
    try {
        const r = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });
        const data = await r.json();
        if (data.success) {
            tripStage = data.stage || 'collecting';

            if (data.message.includes('TRAVELER_FORM:')) {
                renderTravelerForm(data.message, data.collected);
            } else if (data.stage === 'done') {
                resetTripFormButton();
                renderTripReport(data.message, data.collected);
            } else {
                addMessage(data.message, 'assistant');
            }
            updateAgentPanel(data.stage, data.collected);
            updateTripInfo(data.collected);
        } else {
            addMessage(`❌ ${data.message || 'Something went wrong. Please try again!'}`, 'assistant');
            resetTripFormButton();
        }
    } catch (e) {
        console.error(e);
        addMessage('❌ Connection error. Please try again.', 'assistant');
    } finally {
        setLoading(false);
    }
}

// ══════════════════════════════════════
// TRIP REPORT
// ══════════════════════════════════════
function renderTripReport(rawMessage, collected) {
    const wrapper = document.createElement('div');
    wrapper.className = 'message assistant-message';
    wrapper.style.maxWidth = '100%';
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar'; avatar.textContent = '✈️';
    const content = document.createElement('div');
    content.className = 'message-content'; content.style.maxWidth = '92%';
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.style.cssText = 'padding:0;overflow:hidden;background:rgba(255,255,255,0.92);';
    bubble.innerHTML = buildTripReport(rawMessage, collected);

    const pdfBar = document.createElement('div');
    pdfBar.style.cssText = 'padding:12px 18px;border-top:1px solid rgba(219,234,254,0.5);background:rgba(219,234,254,0.4);';
    pdfBar.innerHTML = `<a href="/api/download-pdf" target="_blank" style="display:inline-flex;align-items:center;gap:7px;padding:9px 18px;background:linear-gradient(135deg,#1e3a8a,#1d4ed8);color:white;border-radius:8px;text-decoration:none;font-size:12.5px;font-weight:600;box-shadow:0 3px 10px rgba(30,58,138,0.25);">📄 Download PDF Itinerary</a><span style="font-size:11px;color:#82a898;margin-left:10px;">Full day-by-day plan</span>`;
    bubble.appendChild(pdfBar);

    content.appendChild(bubble); wrapper.appendChild(avatar); wrapper.appendChild(content);
    insertMessage(wrapper);

    bubble.querySelectorAll('.section-toggle').forEach(btn => {
        btn.addEventListener('click', () => {
            const body = btn.closest('.report-section').querySelector('.section-body');
            const isOpen = body.style.display !== 'none';
            body.style.display = isOpen ? 'none' : 'block';
            btn.querySelector('.toggle-arrow').textContent = isOpen ? '▼' : '▲';
            btn.querySelector('.toggle-label').textContent = isOpen ? 'Show details' : 'Hide details';
        });
    });
}

function buildTripReport(rawMessage, collected) {
    const sections = parseSections(rawMessage);
    const dest = collected?.destination || 'Your Destination';
    const checkin = collected?.checkin || '';
    const checkout = collected?.checkout || '';
    const nights = collected?.nights || '';
    const budget = collected?.budget || 0;
    const travelers = collected?.traveler_count || collected?.travelers || 1;

    let html = `
        <div style="background:linear-gradient(135deg,#1e3a8a,#1d4ed8);padding:18px 20px;color:white;">
            <div style="font-size:11px;opacity:0.7;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;">Your Trip Plan</div>
            <div style="font-size:20px;font-weight:700;font-family:'Playfair Display',serif;font-style:italic;">${dest}</div>
            <div style="font-size:12px;opacity:0.8;margin-top:4px;">${checkin} → ${checkout} &nbsp;·&nbsp; ${nights} nights &nbsp;·&nbsp; ${travelers} traveler(s) &nbsp;·&nbsp; $${Number(budget).toLocaleString()}</div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;border-bottom:1px solid rgba(219,234,254,0.5);">
            ${buildSummaryCard('✈️','Flight', sections.flight_summary,'#00b894')}
            ${buildSummaryCard('🏨','Hotel', sections.hotel_summary,'#00856a')}
            ${buildSummaryCard('🌤️','Weather', sections.weather_summary,'#ff6b6b')}
        </div>`;

    if (sections.budget_summary) {
        html += `<div style="padding:14px 18px;border-bottom:1px solid rgba(0,184,148,0.08);background:rgba(219,234,254,0.3);">
            <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#1e3a8a;margin-bottom:8px;">💰 Budget Summary</div>
            <div style="font-size:12.5px;color:#1e3058;line-height:1.8;">${sections.budget_summary}</div></div>`;
    }

    const collapsibles = [
        { icon:'✈️', title:'Flight Options', color:'#3b82f6', data: sections.flights },
        { icon:'🏨', title:'Hotel Options', color:'#1e3a8a', data: sections.hotels },
        { icon:'🌤️', title:'Day-by-Day Weather Forecast', color:'#f97316', data: sections.weather },
        { icon:'🗓️', title:'Day-by-Day Itinerary', color:'#1e3a8a', data: sections.itinerary },
        { icon:'💡', title:'Travel Tips & Packing List', color:'#60a5fa', data: sections.tips },
    ];

    for (const sec of collapsibles) {
        if (!sec.data) continue;
        html += `<div class="report-section" style="border-bottom:1px solid rgba(0,184,148,0.08);">
            <button class="section-toggle" style="width:100%;display:flex;align-items:center;justify-content:space-between;padding:12px 18px;background:none;border:none;cursor:pointer;text-align:left;">
                <span style="display:flex;align-items:center;gap:8px;">
                    <span style="font-size:15px;">${sec.icon}</span>
                    <span style="font-size:12.5px;font-weight:700;color:#1e3a8a;">${sec.title}</span>
                </span>
                <span style="display:flex;align-items:center;gap:5px;font-size:11px;color:#3b82f6;font-weight:600;">
                    <span class="toggle-label">Show details</span>
                    <span class="toggle-arrow" style="font-size:9px;">▼</span>
                </span>
            </button>
            <div class="section-body" style="display:none;padding:4px 18px 14px;font-size:12.5px;line-height:1.8;color:#1e3058;">
                ${markdownToHtml(sec.data)}
            </div>
        </div>`;
    }
    return html;
}

function buildSummaryCard(icon, label, summary, color) {
    return `<div style="padding:12px 14px;border-right:1px solid rgba(219,234,254,0.5);">
        <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:${color};margin-bottom:4px;">${icon} ${label}</div>
        <div style="font-size:11.5px;color:#1e3058;line-height:1.5;">${summary||'—'}</div>
    </div>`;
}

function parseSections(raw) {
    const sections = { flight_summary:'', hotel_summary:'', weather_summary:'', budget_summary:'', flights:'', hotels:'', weather:'', itinerary:'', tips:'' };
    const text = raw.replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
    const lines = text.split('\n');
    let current = null, buffer = [];
    const flush = () => { if (current && buffer.length) sections[current] = buffer.join('\n').trim(); buffer = []; };
    for (const line of lines) {
        const l = line.trim();
        if (/✈️.*Available Flights|### ✈️|Flight.*Options/i.test(l)) { flush(); current='flights'; continue; }
        if (/🏨.*Available Hotels|### 🏨|Hotel.*Options/i.test(l)) { flush(); current='hotels'; continue; }
        if (/🌤️.*Weather|### 🌤️|Weather.*Forecast/i.test(l)) { flush(); current='weather'; continue; }
        if (/Day-by-Day Itinerary|📋.*Itinerary|Complete.*Itinerary/i.test(l)) { flush(); current='itinerary'; continue; }
        if (/Budget Summary|💰.*Budget|Budget Breakdown/i.test(l)) { flush(); current='budget_raw'; continue; }
        if (/Travel Tips|Local Tips|Packing|💡|🎒/i.test(l) && current !== 'itinerary') { flush(); current='tips'; continue; }
        if (/^---+$/.test(l)) continue;
        if (current) buffer.push(line);
    }
    flush();
    if (sections.flights) {
        const m = sections.flights.match(/Recommended Flight.*?(?:\n|$)/);
        sections.flight_summary = m ? m[0].replace(/✅|\*\*/g,'').replace('Recommended Flight:','').trim() : sections.flights.split('\n').find(l=>l.trim().length>10)?.replace(/[#*✅🏆]/g,'').trim()||'';
    }
    if (sections.hotels) {
        const m = sections.hotels.match(/Recommended Hotel.*?(?:\n|$)/);
        sections.hotel_summary = m ? m[0].replace(/✅|\*\*/g,'').replace('Recommended Hotel:','').trim() : sections.hotels.split('\n').find(l=>l.trim().length>10)?.replace(/[#*✅🏆]/g,'').trim()||'';
    }
    if (sections.weather) {
        const m = sections.weather.match(/Now:.*?(?:\n|$)/);
        sections.weather_summary = m ? m[0].replace('Now:','').trim() : sections.weather.split('\n').find(l=>l.trim().length>10)?.replace(/[#*]/g,'').trim()||'';
    }
    const budgetSource = sections.budget_raw || sections.itinerary || '';
    const budgetLines = budgetSource.split('\n').filter(l => /flight|hotel|food|total|budget|remain|activit/i.test(l) && /\$/.test(l)).slice(0,5);
    sections.budget_summary = budgetLines.join('<br>').replace(/\*\*/g,'');
    return sections;
}

// ══════════════════════════════════════
// TRAVELER FORM (for multiple travelers)
// ══════════════════════════════════════
function renderTravelerForm(message, collected) {
    const formMatch = message.match(/TRAVELER_FORM:(\{.*\})/s);
    let formData = null;
    if (formMatch) { try { formData = JSON.parse(formMatch[1]); } catch(e){} }
    const textPart = message.split('TRAVELER_FORM:')[0].trim();
    const w=document.createElement('div'); w.className='message assistant-message';
    const av=document.createElement('div'); av.className='message-avatar'; av.textContent='✈️';
    const c=document.createElement('div'); c.className='message-content'; c.style.maxWidth='92%';
    const b=document.createElement('div'); b.className='message-bubble'; b.style.padding='16px 18px';
    const td=document.createElement('div'); td.innerHTML=markdownToHtml(textPart);
    b.appendChild(td);
    if (formData && formData.travelers_needed) b.appendChild(buildTravelerFormEl(formData.travelers_needed));
    c.appendChild(b); w.appendChild(av); w.appendChild(c);
    insertMessage(w);
}

function buildTravelerFormEl(travelers) {
    const container = document.createElement('div');
    container.className = 'traveler-form-container';
    container.style.marginTop = '14px';
    travelers.forEach((t, i) => {
        const card = document.createElement('div');
        card.style.cssText = 'background:rgba(219,234,254,0.4);border:1px solid rgba(59,130,246,0.15);border-radius:10px;padding:14px 16px;margin-bottom:12px;';
        card.innerHTML = `
            <div style="font-weight:700;color:#1e3a8a;margin-bottom:12px;font-size:12.5px;display:flex;align-items:center;gap:6px;">
                <span style="background:#1d4ed8;color:white;width:22px;height:22px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:11px;">${i+1}</span>
                Traveler ${i+1}
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                <div>
                    <label style="font-size:10.5px;font-weight:600;color:#1e40af;display:block;margin-bottom:4px;">First Name <span style="color:#ff6b6b">*</span></label>
                    <input type="text" id="t${i}_first" placeholder="e.g. Maria" style="width:100%;padding:8px 10px;border:1.5px solid rgba(59,130,246,0.18);border-radius:7px;font-family:'DM Sans',sans-serif;font-size:12.5px;background:#eff6ff;color:#1e3058;outline:none;" value="${t.first_name||''}">
                    <span class="field-error" id="err_t${i}_first"></span>
                </div>
                <div>
                    <label style="font-size:10.5px;font-weight:600;color:#1e40af;display:block;margin-bottom:4px;">Last Name <span style="color:#ff6b6b">*</span></label>
                    <input type="text" id="t${i}_last" placeholder="e.g. Smith" style="width:100%;padding:8px 10px;border:1.5px solid rgba(59,130,246,0.18);border-radius:7px;font-family:'DM Sans',sans-serif;font-size:12.5px;background:#eff6ff;color:#1e3058;outline:none;" value="${t.last_name||''}">
                    <span class="field-error" id="err_t${i}_last"></span>
                </div>
                <div>
                    <label style="font-size:10.5px;font-weight:600;color:#1e40af;display:block;margin-bottom:4px;">Age <span style="color:#ff6b6b">*</span></label>
                    <input type="number" id="t${i}_age" placeholder="e.g. 28" min="1" max="120" style="width:100%;padding:8px 10px;border:1.5px solid rgba(59,130,246,0.18);border-radius:7px;font-family:'DM Sans',sans-serif;font-size:12.5px;background:#eff6ff;color:#1e3058;outline:none;" value="${t.age||''}">
                    <span class="field-error" id="err_t${i}_age"></span>
                </div>
                <div>
                    <label style="font-size:10.5px;font-weight:600;color:#1e40af;display:block;margin-bottom:4px;">Gender <span style="color:#ff6b6b">*</span></label>
                    <select id="t${i}_gender" style="width:100%;padding:8px 10px;border:1.5px solid rgba(59,130,246,0.18);border-radius:7px;font-family:'DM Sans',sans-serif;font-size:12.5px;background:#eff6ff;color:#1e3058;outline:none;">
                        <option value="">Select...</option>
                        <option value="Male" ${t.gender==='Male'?'selected':''}>Male</option>
                        <option value="Female" ${t.gender==='Female'?'selected':''}>Female</option>
                        <option value="Other" ${t.gender==='Other'?'selected':''}>Other</option>
                    </select>
                    <span class="field-error" id="err_t${i}_gender"></span>
                </div>
            </div>`;
        container.appendChild(card);
    });
    const btn = document.createElement('button');
    btn.textContent = '✅ Submit Traveler Details';
    btn.style.cssText = 'width:100%;padding:11px;background:linear-gradient(135deg,#1e3a8a,#1d4ed8);color:white;border:none;border-radius:8px;font-family:\'DM Sans\',sans-serif;font-size:13px;font-weight:600;cursor:pointer;margin-top:4px;';
    btn.onclick = () => {
        const data = []; let valid = true;
        container.querySelectorAll('.field-error').forEach(e=>e.textContent='');
        travelers.forEach((t,i) => {
            const fn=document.getElementById(`t${i}_first`)?.value.trim();
            const ln=document.getElementById(`t${i}_last`)?.value.trim();
            const age=document.getElementById(`t${i}_age`)?.value.trim();
            const gender=document.getElementById(`t${i}_gender`)?.value;
            let rv=true;
            if(!fn||fn.length<2||/\d/.test(fn)){const e=document.getElementById(`err_t${i}_first`);if(e)e.textContent='Valid first name required';valid=rv=false;}
            if(!ln||ln.length<1||/\d/.test(ln)){const e=document.getElementById(`err_t${i}_last`);if(e)e.textContent='Valid last name required';valid=rv=false;}
            const an=parseInt(age);
            if(!age||isNaN(an)||an<1||an>120){const e=document.getElementById(`err_t${i}_age`);if(e)e.textContent='Age 1–120 required';valid=rv=false;}
            if(!gender){const e=document.getElementById(`err_t${i}_gender`);if(e)e.textContent='Please select gender';valid=rv=false;}
            if(rv) data.push({first_name:fn,last_name:ln,age:an,gender});
        });
        if(!valid) return;
        container.querySelectorAll('input,select,button').forEach(e=>e.disabled=true);
        btn.textContent='✅ Submitted!'; btn.style.background='linear-gradient(135deg,#10b981,#059669)';
        const summary = data.map((t,i)=>`Traveler ${i+1}: ${t.first_name} ${t.last_name}, Age ${t.age}, ${t.gender}`).join('\n');
        addMessage(summary,'user');
        callAPI(`traveler_form:${JSON.stringify({travelers:data})}`);
    };
    container.appendChild(btn);
    return container;
}

// ══════════════════════════════════════
// CORE UTILITIES
// ══════════════════════════════════════
function addMessage(text, role) {
    const w=document.createElement('div'); w.className=`message ${role}-message`;
    const av=document.createElement('div'); av.className='message-avatar'; av.textContent=role==='assistant'?'✈️':'👤';
    const c=document.createElement('div'); c.className='message-content';
    const b=document.createElement('div'); b.className='message-bubble'; b.innerHTML=markdownToHtml(text);
    c.appendChild(b); w.appendChild(av); w.appendChild(c);
    insertMessage(w);
}

function insertMessage(el) {
    if (typingIndicator&&typingIndicator.parentNode===chatMessages) chatMessages.insertBefore(el,typingIndicator);
    else chatMessages.appendChild(el);
    scrollToBottom();
}

function markdownToHtml(text) {
    if (!text) return '';
    let s = text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    return s
        .replace(/^### (.+)$/gm,'<h3>$1</h3>')
        .replace(/^## (.+)$/gm,'<h2>$1</h2>')
        .replace(/^# (.+)$/gm,'<h2>$1</h2>')
        .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
        .replace(/(^|\s)\*([^*\n]+)\*(\s|$)/g,'$1<em>$2</em>$3')
        .replace(/`(.+?)`/g,'<code>$1</code>')
        .replace(/^---$/gm,'<hr>')
        .replace(/^[•\-] (.+)$/gm,'<li>$1</li>')
        .replace(/^\d+\. (.+)$/gm,'<li>$1</li>')
        .replace(/\n\n/g,'<br><br>')
        .replace(/\n/g,'<br>');
}

function setLoading(state) {
    isLoading=state; sendBtn.disabled=state;
    if(state){typingIndicator.style.display='block';scrollToBottom();startAgentAnimation();}
    else{typingIndicator.style.display='none';stopAgentAnimation();}
}
function startAgentAnimation(){
    let idx=0; updateAgentWorking(agentMessages[0]);
    agentMsgInterval=setInterval(()=>{idx=(idx+1)%agentMessages.length;updateAgentWorking(agentMessages[idx]);highlightAgent(agentMessages[idx].icon);},2000);
}
function stopAgentAnimation(){if(agentMsgInterval){clearInterval(agentMsgInterval);agentMsgInterval=null;}}
function updateAgentWorking(msg){agentWorking.innerHTML=`<span class="working-icon">${msg.icon}</span><span class="working-text">${msg.text}</span>`;}
function updateAgentPanel(stage,collected){
    document.querySelectorAll('.agent-item').forEach(el=>{el.classList.remove('working','done','active');el.querySelector('.agent-status').textContent='Standby';});
    const map={'collecting':['agent-orchestrator','agent-requirements'],'planning':['agent-orchestrator','agent-requirements','agent-flights','agent-hotels','agent-climate','agent-planning'],'done':['agent-orchestrator','agent-requirements','agent-flights','agent-hotels','agent-climate','agent-planning']};
    (map[stage]||['agent-orchestrator']).forEach(id=>{const el=document.getElementById(id);if(el){if(stage==='done'){el.classList.add('done');el.querySelector('.agent-status').textContent='Complete ✓';}else{el.classList.add('active');el.querySelector('.agent-status').textContent='Active';}}});
}
function highlightAgent(icon){
    const m={'🎯':'agent-orchestrator','📋':'agent-requirements','✈️':'agent-flights','🏨':'agent-hotels','🌤️':'agent-climate','🗺️':'agent-planning'};
    const id=m[icon];if(!id)return;
    document.querySelectorAll('.agent-item').forEach(el=>el.classList.remove('working'));
    const el=document.getElementById(id);if(el){el.classList.add('working');el.querySelector('.agent-status').textContent='Working...';}
}

function updateTripInfo(collected) {
    if(!collected||Object.keys(collected).length===0) return;
    const panel=document.getElementById('trip-info'); const details=document.getElementById('trip-details');
    const fields=[
        {label:'Destination',key:'destination',icon:'📍'},
        {label:'From',key:'origin',icon:'🛫'},
        {label:'Check-in',key:'checkin',icon:'📅'},
        {label:'Check-out',key:'checkout',icon:'📅'},
        {label:'Nights',key:'nights',icon:'🌙'},
        {label:'Travelers',key:'traveler_count',icon:'👥'},
        {label:'Budget',key:'budget',icon:'💰',format:v=>`$${Number(v).toLocaleString()}`},
        {label:'Non-stop',key:'nonstop_preferred',icon:'✈️',format:v=>v===true?'Yes':v===false?'No':'—'},
    ];
    let html=fields.filter(f=>collected[f.key]!==undefined&&collected[f.key]!==null&&collected[f.key]!=='').map(f=>{
        const val=f.format?f.format(collected[f.key]):collected[f.key];
        return `<div class="trip-detail-item"><span class="trip-detail-label">${f.icon} ${f.label}</span><span class="trip-detail-value">${val}</span></div>`;
    }).join('');
    const travelers=collected.travelers||[];
    const done=travelers.filter(t=>t.first_name&&t.last_name);
    if(done.length>0){
        html+=`<div style="margin-top:7px;font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#82a898;padding-top:6px;border-top:1px solid rgba(59,130,246,0.15);">Passengers</div>`;
        done.forEach(t=>{html+=`<div style="padding:4px 0;border-bottom:1px solid rgba(219,234,254,0.5);"><div style="color:#1e3a8a;font-weight:700;font-size:11px;">👤 ${t.first_name} ${t.last_name}</div><div style="color:#82a898;font-size:10px;">Age ${t.age||'?'} · ${t.gender||'?'}</div></div>`;});
    }
    if(html){details.innerHTML=html;panel.style.display='block';}
}

function sendQuick(text){ messageInput.value=text; sendMessage(); }

async function resetChat(){
    try{await fetch('/api/reset',{method:'POST'});}catch(e){}
    chatMessages.querySelectorAll('.message').forEach((m,i)=>{if(i>0)m.remove();});
    document.querySelectorAll('.agent-item').forEach(el=>{el.classList.remove('working','done','active');el.querySelector('.agent-status').textContent='Standby';});
    document.getElementById('trip-info').style.display='none';
    messageInput.value=''; tripStage='greeting'; tripFormShown=false;
    setTimeout(()=>renderTripForm(), 300);
}
function handleKeyDown(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMessage();}}
function autoResize(el){el.style.height='auto';el.style.height=Math.min(el.scrollHeight,120)+'px';}
function scrollToBottom(){setTimeout(()=>{chatMessages.scrollTop=chatMessages.scrollHeight;},50);}
