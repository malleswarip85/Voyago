// Voyago — Frontend v6 — Single upfront form

// Safe fallback if airport_data.js fails to load
if (typeof getAirportsForDestination === 'undefined') {
    window.getAirportsForDestination = function(dest) { return []; };
}

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
    const INP = 'width:100%;padding:9px 12px;border:1.5px solid rgba(14,116,144,0.18);border-radius:8px;font-family:\'DM Sans\',sans-serif;font-size:13px;background:#f0fdfa;color:#1c1917;outline:none;transition:all 0.2s;box-sizing:border-box;';
    const LBL = 'font-size:10.5px;font-weight:700;color:#0c5c6b;display:block;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.06em;';
    const FCS = "this.style.borderColor='#06b6d4';this.style.background='white'";
    const BLR_DATE = "this.style.borderColor='rgba(14,116,144,0.18)';this.style.background='#f0fdfa'";

    return `
    <div style="background:linear-gradient(135deg,#0c5c6b,#0e7490);padding:14px 18px;">
        <div style="font-family:'Playfair Display',serif;font-size:17px;font-style:italic;color:white;font-weight:600;">Plan Your Trip ✈️</div>
        <div style="font-size:11px;color:rgba(255,255,255,0.7);margin-top:2px;">Fill in your details — agents will handle the rest!</div>
    </div>

    <div style="padding:16px 18px;" id="trip-form-body">

        <!-- Hidden airport code inputs (populated by selectAirport()) -->
        <input type="hidden" id="tf-origin-airport" value="">
        <input type="hidden" id="tf-destination-airport" value="">

        <!-- Row 1: Origin & Destination with Airport Picker -->
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">
            <div>
                <label style="${LBL}">🛫 From (City / Country)</label>
                <input type="text" id="tf-origin" placeholder="e.g. New Delhi, Chicago, London"
                    style="${INP}"
                    onfocus="${FCS}"
                    onblur="this.style.borderColor='rgba(14,116,144,0.18)';this.style.background='#f0fdfa';setTimeout(()=>showAirportPicker('origin'),250)"
                    oninput="onAirportTextChange('origin')">
                <span class="tf-error" id="err-origin" style="color:#cc3333;font-size:10.5px;display:block;margin-top:3px;font-weight:500;"></span>
                <div id="origin-selected-badge" style="display:none;"></div>
                <div id="origin-airport-wrap" style="display:none;margin-top:8px;"></div>
            </div>
            <div>
                <label style="${LBL}">📍 To (City / Country)</label>
                <input type="text" id="tf-destination" placeholder="e.g. Paris, Tokyo, Bali"
                    style="${INP}"
                    onfocus="${FCS}"
                    onblur="this.style.borderColor='rgba(14,116,144,0.18)';this.style.background='#f0fdfa';setTimeout(()=>showAirportPicker('destination'),250)"
                    oninput="onAirportTextChange('destination')">
                <span class="tf-error" id="err-destination" style="color:#cc3333;font-size:10.5px;display:block;margin-top:3px;font-weight:500;"></span>
                <div id="destination-selected-badge" style="display:none;"></div>
                <div id="destination-airport-wrap" style="display:none;margin-top:8px;"></div>
            </div>
        </div>

        <!-- Row 2: Dates -->
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">
            <div>
                <label style="${LBL}">📅 Check-in Date</label>
                <input type="date" id="tf-checkin"
                    style="${INP}"
                    onfocus="${FCS}" onblur="${BLR_DATE}">
                <span class="tf-error" id="err-checkin" style="color:#cc3333;font-size:10.5px;display:block;margin-top:3px;font-weight:500;"></span>
            </div>
            <div>
                <label style="${LBL}">📅 Check-out Date</label>
                <input type="date" id="tf-checkout"
                    style="${INP}"
                    onfocus="${FCS}" onblur="${BLR_DATE}">
                <span class="tf-error" id="err-checkout" style="color:#cc3333;font-size:10.5px;display:block;margin-top:3px;font-weight:500;"></span>
            </div>
        </div>

        <!-- Row 3: Budget, Travelers, Nonstop -->
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:16px;">
            <div>
                <label style="${LBL}">💰 Total Budget (USD)</label>
                <input type="number" id="tf-budget" placeholder="e.g. 3000" min="200"
                    style="${INP}"
                    onfocus="${FCS}" onblur="${BLR_DATE}">
                <span class="tf-error" id="err-budget" style="color:#cc3333;font-size:10.5px;display:block;margin-top:3px;font-weight:500;"></span>
            </div>
            <div>
                <label style="${LBL}">👥 No. of Travelers</label>
                <input type="number" id="tf-travelers" placeholder="e.g. 2" min="1" max="20"
                    style="${INP}"
                    onfocus="${FCS}" onblur="${BLR_DATE}">
                <span class="tf-error" id="err-travelers" style="color:#cc3333;font-size:10.5px;display:block;margin-top:3px;font-weight:500;"></span>
            </div>
            <div>
                <label style="${LBL}">✈️ Non-stop Flights?</label>
                <select id="tf-nonstop"
                    style="${INP}"
                    onfocus="${FCS}" onblur="${BLR_DATE}">
                    <option value="">Select...</option>
                    <option value="yes">Yes — Non-stop only</option>
                    <option value="no">No — Any flights</option>
                </select>
                <span class="tf-error" id="err-nonstop" style="color:#cc3333;font-size:10.5px;display:block;margin-top:3px;font-weight:500;"></span>
            </div>
        </div>

        <!-- Submit -->
        <button onclick="submitTripForm()"
            style="width:100%;padding:12px;background:linear-gradient(135deg,#0c5c6b,#0e7490);color:white;border:none;border-radius:9px;font-family:'DM Sans',sans-serif;font-size:14px;font-weight:700;cursor:pointer;transition:all 0.2s;box-shadow:0 4px 14px rgba(12,92,107,0.3);"
            onmouseover="this.style.transform='translateY(-1px)';this.style.boxShadow='0 6px 20px rgba(12,92,107,0.4)'"
            onmouseout="this.style.transform='';this.style.boxShadow='0 4px 14px rgba(12,92,107,0.3)'"
            id="tf-submit-btn">
            🔍 Search Flights, Hotels & Weather
        </button>

        <div style="text-align:center;font-size:10.5px;color:#a16207;margin-top:8px;">
            Powered by Google Flights · Google Hotels · OpenWeatherMap · Gemini AI
        </div>
    </div>
    `;
}

function onAirportTextChange(type) {
    // Clear existing selection when user types
    const hidden = document.getElementById(`tf-${type}-airport`);
    if (hidden && hidden.value) {
        hidden.value = '';
        const badge = document.getElementById(`${type}-selected-badge`);
        if (badge) badge.style.display = 'none';
    }
    clearTimeout(window[`_airportTimer_${type}`]);
    window[`_airportTimer_${type}`] = setTimeout(() => showAirportPicker(type), 400);
}

function showAirportPicker(type) {
    try {
        const input = document.getElementById(`tf-${type}`);
        const wrap = document.getElementById(`${type}-airport-wrap`);
        const hidden = document.getElementById(`tf-${type}-airport`);
        if (!input || !wrap) return;

        // If airport already selected, don't re-show picker
        if (hidden && hidden.value) { wrap.style.display = 'none'; return; }

        const val = input.value.trim();
        if (!val || val.length < 2) { wrap.style.display = 'none'; return; }

        const airports = (typeof getAirportsForDestination === 'function')
            ? getAirportsForDestination(val) : [];
        if (!airports || airports.length === 0) { wrap.style.display = 'none'; return; }

        const label = type === 'origin' ? '🛫 Select Departure Airport' : '🛬 Select Arrival Airport';
        const cards = airports.map(a => {
            const safeName = a.name.replace(/'/g, '&#39;');
            const safeCity = a.city.replace(/'/g, '&#39;');
            return `<button type="button"
                onclick="selectAirport('${type}','${a.code}','${safeCity}','${safeName}')"
                style="display:flex;flex-direction:column;align-items:flex-start;padding:8px 11px;border:1.5px solid rgba(14,116,144,0.22);border-radius:8px;background:#ecfeff;color:#0c5c6b;font-family:'DM Sans',sans-serif;cursor:pointer;transition:all 0.15s;text-align:left;min-width:0;"
                onmouseover="this.style.background='#0e7490';this.style.color='white';this.style.borderColor='#0e7490';this.style.transform='translateY(-1px)';this.style.boxShadow='0 3px 10px rgba(14,116,144,0.25)'"
                onmouseout="this.style.background='#ecfeff';this.style.color='#0c5c6b';this.style.borderColor='rgba(14,116,144,0.22)';this.style.transform='';this.style.boxShadow=''">
                <span style="font-size:13px;font-weight:800;letter-spacing:0.04em;">${a.code}</span>
                <span style="font-size:11px;font-weight:600;margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:160px;">${a.city}</span>
                <span style="font-size:9.5px;opacity:0.72;margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:160px;">${a.name}</span>
            </button>`;
        }).join('');

        wrap.innerHTML = `
            <div style="font-size:10px;font-weight:700;color:#0e7490;margin-bottom:7px;text-transform:uppercase;letter-spacing:0.07em;">${label}</div>
            <div style="display:flex;flex-wrap:wrap;gap:7px;">${cards}</div>
        `;

        wrap.style.display = 'block';
        wrap.style.opacity = '0';
        wrap.style.transform = 'translateY(-4px)';
        setTimeout(() => {
            wrap.style.transition = 'all 0.18s ease';
            wrap.style.opacity = '1';
            wrap.style.transform = 'translateY(0)';
        }, 10);
    } catch(e) {
        console.warn('Airport picker error:', e);
    }
}

function selectAirport(type, code, city, name) {
    // Store code in hidden input
    const hidden = document.getElementById(`tf-${type}-airport`);
    if (hidden) hidden.value = code;

    // Hide the picker
    const wrap = document.getElementById(`${type}-airport-wrap`);
    if (wrap) { wrap.style.display = 'none'; wrap.innerHTML = ''; }

    // Show selected badge
    const badge = document.getElementById(`${type}-selected-badge`);
    if (badge) {
        badge.innerHTML = `
            <div style="display:flex;align-items:center;gap:8px;padding:7px 10px;background:linear-gradient(135deg,rgba(14,116,144,0.08),rgba(6,182,212,0.06));border:1.5px solid rgba(14,116,144,0.3);border-radius:7px;margin-top:5px;">
                <span style="font-size:12.5px;font-weight:800;color:white;background:#0e7490;padding:2px 8px;border-radius:5px;letter-spacing:0.05em;">${code}</span>
                <div style="flex:1;min-width:0;">
                    <div style="font-size:11.5px;font-weight:600;color:#0c5c6b;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${city}</div>
                    <div style="font-size:10px;color:#a16207;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${name}</div>
                </div>
                <button type="button" onclick="clearAirportSelection('${type}')"
                    style="background:none;border:none;cursor:pointer;color:#888;font-size:15px;line-height:1;padding:2px 4px;border-radius:4px;flex-shrink:0;"
                    title="Change airport" onmouseover="this.style.color='#cc3333'" onmouseout="this.style.color='#888'">✕</button>
            </div>
        `;
        badge.style.display = 'block';
    }

    // Clear any error
    const err = document.getElementById(`err-${type}`);
    if (err) err.textContent = '';
}

function clearAirportSelection(type) {
    const hidden = document.getElementById(`tf-${type}-airport`);
    if (hidden) hidden.value = '';
    const badge = document.getElementById(`${type}-selected-badge`);
    if (badge) badge.style.display = 'none';
    // Re-trigger picker so user can choose again
    setTimeout(() => showAirportPicker(type), 100);
}


function clearTfErrors() {
    document.querySelectorAll('.tf-error').forEach(e => e.textContent = '');
    document.querySelectorAll('#trip-form-body input:not([type="hidden"]), #trip-form-body select').forEach(el => {
        el.style.borderColor = 'rgba(14,116,144,0.18)';
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

    // Require airport selection if airports are available for the typed city
    const originAirport = document.getElementById('tf-origin-airport')?.value || '';
    const destAirport = document.getElementById('tf-destination-airport')?.value || '';
    if (valid && origin && origin.length >= 2) {
        const availOrigin = (typeof getAirportsForDestination === 'function') ? getAirportsForDestination(origin) : [];
        if (availOrigin.length > 0 && !originAirport) {
            showTfError('tf-origin', 'err-origin', '⬆ Please select a departure airport above'); valid = false;
        }
    }
    if (valid && destination && destination.length >= 2) {
        const availDest = (typeof getAirportsForDestination === 'function') ? getAirportsForDestination(destination) : [];
        if (availDest.length > 0 && !destAirport) {
            showTfError('tf-destination', 'err-destination', '⬆ Please select an arrival airport above'); valid = false;
        }
    }

    if (!valid) return;

    // Disable form
    const btn = document.getElementById('tf-submit-btn');
    btn.disabled = true;
    btn.textContent = '⏳ Searching...';
    btn.style.opacity = '0.7';
    document.querySelectorAll('#trip-form-body input:not([type="hidden"]), #trip-form-body select').forEach(el => el.disabled = true);

    const originDisplay = originAirport ? `${origin} (${originAirport})` : origin;
    const destDisplay = destAirport ? `${destination} (${destAirport})` : destination;

    // Build structured message for orchestrator
    const nights = Math.round((new Date(checkout) - new Date(checkin)) / (1000*60*60*24));
    const summary = `TRIP_FORM:${JSON.stringify({
        origin, destination,
        origin_iata: originAirport || null,
        destination_iata: destAirport || null,
        checkin, checkout,
        budget: parseFloat(budget),
        travelers: tNum,
        nonstop_preferred: nonstop === 'yes',
        nights
    })}`;

    // Show summary to user
    const userSummary = `From: ${originDisplay} → ${destDisplay}\nDates: ${checkin} to ${checkout} (${nights} nights)\nBudget: $${parseFloat(budget).toLocaleString()} | Travelers: ${tNum} | Non-stop: ${nonstop === 'yes' ? 'Yes' : 'No'}`;
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
    document.querySelectorAll('#trip-form-body input:not([type="hidden"]), #trip-form-body select').forEach(el => el.disabled = false);
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
    pdfBar.style.cssText = 'padding:12px 18px;border-top:1px solid rgba(14,116,144,0.12);background:rgba(240,253,250,0.5);';
    pdfBar.innerHTML = `<a href="/api/download-pdf" target="_blank" style="display:inline-flex;align-items:center;gap:7px;padding:9px 18px;background:linear-gradient(135deg,#0c5c6b,#0e7490);color:white;border-radius:8px;text-decoration:none;font-size:12.5px;font-weight:600;box-shadow:0 3px 10px rgba(12,92,107,0.25);">📄 Download PDF Itinerary</a><span style="font-size:11px;color:#a16207;margin-left:10px;">Full day-by-day plan</span>`;
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
        <div style="background:linear-gradient(135deg,#0c5c6b,#0e7490);padding:18px 20px;color:white;">
            <div style="font-size:11px;opacity:0.7;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;">Your Trip Plan</div>
            <div style="font-size:20px;font-weight:700;font-family:'Playfair Display',serif;font-style:italic;">${dest}</div>
            <div style="font-size:12px;opacity:0.8;margin-top:4px;">${checkin} → ${checkout} &nbsp;·&nbsp; ${nights} nights &nbsp;·&nbsp; ${travelers} traveler(s) &nbsp;·&nbsp; $${Number(budget).toLocaleString()}</div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;border-bottom:1px solid rgba(14,116,144,0.12);">
            ${buildSummaryCard('✈️','Flight', sections.flight_summary,'#0e7490')}
            ${buildSummaryCard('🏨','Hotel', sections.hotel_summary,'#0c5c6b')}
            ${buildSummaryCard('🌤️','Weather', sections.weather_summary,'#d97706')}
        </div>`;

    if (sections.budget_summary) {
        html += `<div style="padding:14px 18px;border-bottom:1px solid rgba(14,116,144,0.08);background:rgba(240,253,250,0.4);">
            <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#0c5c6b;margin-bottom:8px;">💰 Budget Summary</div>
            <div style="font-size:12.5px;color:#1c1917;line-height:1.8;">${sections.budget_summary}</div></div>`;
    }

    const collapsibles = [
        { icon:'✈️', title:'Flight Options', color:'#0e7490', data: sections.flights },
        { icon:'🏨', title:'Hotel Options', color:'#0c5c6b', data: sections.hotels },
        { icon:'🌤️', title:'Day-by-Day Weather Forecast', color:'#d97706', data: sections.weather },
        { icon:'🗓️', title:'Day-by-Day Itinerary', color:'#0c5c6b', data: sections.itinerary },
        { icon:'💡', title:'Travel Tips & Packing List', color:'#0e7490', data: sections.tips },
    ];

    for (const sec of collapsibles) {
        if (!sec.data) continue;
        html += `<div class="report-section" style="border-bottom:1px solid rgba(14,116,144,0.08);">
            <button class="section-toggle" style="width:100%;display:flex;align-items:center;justify-content:space-between;padding:12px 18px;background:none;border:none;cursor:pointer;text-align:left;">
                <span style="display:flex;align-items:center;gap:8px;">
                    <span style="font-size:15px;">${sec.icon}</span>
                    <span style="font-size:12.5px;font-weight:700;color:${sec.color};">${sec.title}</span>
                </span>
                <span style="display:flex;align-items:center;gap:5px;font-size:11px;color:#0e7490;font-weight:600;">
                    <span class="toggle-label">Show details</span>
                    <span class="toggle-arrow" style="font-size:9px;">▼</span>
                </span>
            </button>
            <div class="section-body" style="display:none;padding:4px 18px 14px;font-size:12.5px;line-height:1.8;color:#1c1917;">
                ${markdownToHtml(sec.data)}
            </div>
        </div>`;
    }
    return html;
}

function buildSummaryCard(icon, label, summary, color) {
    return `<div style="padding:12px 14px;border-right:1px solid rgba(14,116,144,0.12);">
        <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:${color};margin-bottom:4px;">${icon} ${label}</div>
        <div style="font-size:11.5px;color:#1c1917;line-height:1.5;">${summary||'—'}</div>
    </div>`;
}

function parseSections(raw) {
    const sections = {
        flight_summary:'', hotel_summary:'', weather_summary:'',
        budget_summary:'', flights:'', hotels:'', weather:'', itinerary:'', tips:''
    };
    const text = raw.replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');

    // The orchestrator separates sections with \n---\n
    // Structure: intro | flight HTML | hotel HTML | weather text | itinerary text | footer
    const parts = text.split(/\n---+\n/);

    for (const part of parts) {
        const trimmed = part.trim();
        if (!trimmed) continue;

        // Flight HTML block — starts with <div data-summary= and contains flight timing markers
        if (!sections.flights && trimmed.startsWith('<div') && trimmed.includes('data-summary=') &&
            (trimmed.includes('dep_code') || trimmed.includes('Non-stop') || trimmed.includes(' stop') || /\d+h\s+\d+m/.test(trimmed))) {
            sections.flights = trimmed;
            continue;
        }
        // Hotel HTML block — starts with <div data-summary= (second such block = hotels)
        if (!sections.hotels && trimmed.startsWith('<div') && trimmed.includes('data-summary=') &&
            (trimmed.includes('/night') || trimmed.includes('room') || trimmed.includes('/10'))) {
            sections.hotels = trimmed;
            continue;
        }
        // Fallback: any remaining <div data-summary= block that wasn't captured yet
        if (!sections.flights && trimmed.startsWith('<div') && trimmed.includes('data-summary=')) {
            sections.flights = trimmed; continue;
        }
        if (!sections.hotels && trimmed.startsWith('<div') && trimmed.includes('data-summary=')) {
            sections.hotels = trimmed; continue;
        }
        // Weather section (text format from climate_agent)
        if (/###.*🌤️|###.*Weather/i.test(trimmed)) {
            sections.weather = trimmed; continue;
        }
        // Itinerary section
        if (/##.*📋.*Itinerary|##.*Day-by-Day.*Itinerary|##.*Complete.*Itinerary/i.test(trimmed)) {
            sections.itinerary = trimmed; continue;
        }
    }

    // Line-by-line pass for tips (may be inside itinerary block)
    if (sections.itinerary) {
        const iLines = sections.itinerary.split('\n');
        let tipBuffer = [], inTips = false;
        for (const line of iLines) {
            if (!inTips && /💡.*Local Tips|##.*Local Tips|##.*Travel Tips|##.*Packing/i.test(line)) {
                inTips = true; tipBuffer = [line]; continue;
            }
            if (inTips) tipBuffer.push(line);
        }
        if (tipBuffer.length > 2) sections.tips = tipBuffer.join('\n').trim();
    }

    // Extract summaries for top summary cards
    if (sections.flights) {
        const htmlSum = sections.flights.match(/data-summary="([^"]+)"/i);
        sections.flight_summary = htmlSum
            ? htmlSum[1]
            : sections.flights.split('\n').find(l=>l.trim().length>10)?.replace(/[#*✅🏆<>]/g,'').trim()||'';
    }
    if (sections.hotels) {
        const htmlSum = sections.hotels.match(/data-summary="([^"]+)"/i);
        sections.hotel_summary = htmlSum
            ? htmlSum[1]
            : sections.hotels.split('\n').find(l=>l.trim().length>10)?.replace(/[#*✅🏆<>]/g,'').trim()||'';
    }
    if (sections.weather) {
        const m = sections.weather.match(/\*\*Now:\*\*(.+?)(?:\n|$)/i) ||
                  sections.weather.match(/Now:(.+?)(?:\n|$)/i);
        sections.weather_summary = m
            ? m[1].replace(/\*\*/g,'').trim()
            : sections.weather.split('\n').find(l=>l.trim().length>10)?.replace(/[#*]/g,'').trim()||'';
    }
    // Budget summary lines from itinerary text
    const budgetLines = (sections.itinerary||'').split('\n')
        .filter(l => /flight|hotel|food|total|budget|remain|activit/i.test(l) && /\$/.test(l))
        .slice(0, 5);
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
        card.style.cssText = 'background:rgba(240,253,250,0.5);border:1px solid rgba(14,116,144,0.15);border-radius:10px;padding:14px 16px;margin-bottom:12px;';
        card.innerHTML = `
            <div style="font-weight:700;color:#0c5c6b;margin-bottom:12px;font-size:12.5px;display:flex;align-items:center;gap:6px;">
                <span style="background:#0e7490;color:white;width:22px;height:22px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:11px;">${i+1}</span>
                Traveler ${i+1}
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                <div>
                    <label style="font-size:10.5px;font-weight:600;color:#0c5c6b;display:block;margin-bottom:4px;">First Name <span style="color:#ff6b6b">*</span></label>
                    <input type="text" id="t${i}_first" placeholder="e.g. Maria" style="width:100%;padding:8px 10px;border:1.5px solid rgba(14,116,144,0.18);border-radius:7px;font-family:'DM Sans',sans-serif;font-size:12.5px;background:#f0fdfa;color:#1c1917;outline:none;" value="${t.first_name||''}">
                    <span class="field-error" id="err_t${i}_first"></span>
                </div>
                <div>
                    <label style="font-size:10.5px;font-weight:600;color:#0c5c6b;display:block;margin-bottom:4px;">Last Name <span style="color:#ff6b6b">*</span></label>
                    <input type="text" id="t${i}_last" placeholder="e.g. Smith" style="width:100%;padding:8px 10px;border:1.5px solid rgba(14,116,144,0.18);border-radius:7px;font-family:'DM Sans',sans-serif;font-size:12.5px;background:#f0fdfa;color:#1c1917;outline:none;" value="${t.last_name||''}">
                    <span class="field-error" id="err_t${i}_last"></span>
                </div>
                <div>
                    <label style="font-size:10.5px;font-weight:600;color:#0c5c6b;display:block;margin-bottom:4px;">Age <span style="color:#ff6b6b">*</span></label>
                    <input type="number" id="t${i}_age" placeholder="e.g. 28" min="1" max="120" style="width:100%;padding:8px 10px;border:1.5px solid rgba(14,116,144,0.18);border-radius:7px;font-family:'DM Sans',sans-serif;font-size:12.5px;background:#f0fdfa;color:#1c1917;outline:none;" value="${t.age||''}">
                    <span class="field-error" id="err_t${i}_age"></span>
                </div>
                <div>
                    <label style="font-size:10.5px;font-weight:600;color:#0c5c6b;display:block;margin-bottom:4px;">Gender <span style="color:#ff6b6b">*</span></label>
                    <select id="t${i}_gender" style="width:100%;padding:8px 10px;border:1.5px solid rgba(14,116,144,0.18);border-radius:7px;font-family:'DM Sans',sans-serif;font-size:12.5px;background:#f0fdfa;color:#1c1917;outline:none;">
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
    btn.style.cssText = 'width:100%;padding:11px;background:linear-gradient(135deg,#0c5c6b,#0e7490);color:white;border:none;border-radius:8px;font-family:\'DM Sans\',sans-serif;font-size:13px;font-weight:600;cursor:pointer;margin-top:4px;';
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
    // If content is already an HTML block, pass through without escaping
    if (/^\s*<(?:div|section|table|ul|ol|article)\b/i.test(text.trim())) return text;
    // Save HTML tags before escaping
    const htmlTags = [];
    text = text.replace(/<[a-z][^>]*>[\s\S]*?<\/[a-z]+>/gi, match => {
        htmlTags.push(match);
        return `__HTML_TAG_${htmlTags.length - 1}__`;
    });
    let s = text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    s = s
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
    htmlTags.forEach((tag, i) => {
        s = s.replace(`__HTML_TAG_${i}__`, tag);
    });
    return s;
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
        html+=`<div style="margin-top:7px;font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#a16207;padding-top:6px;border-top:1px solid rgba(14,116,144,0.15);">Passengers</div>`;
        done.forEach(t=>{html+=`<div style="padding:4px 0;border-bottom:1px solid rgba(240,253,250,0.8);"><div style="color:#0c5c6b;font-weight:700;font-size:11px;">👤 ${t.first_name} ${t.last_name}</div><div style="color:#a16207;font-size:10px;">Age ${t.age||'?'} · ${t.gender||'?'}</div></div>`;});
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

// ══════════════════════════════════════
// AUTH — Modal open/close/toggle
// ══════════════════════════════════════
let authMode = 'login'; // 'login' | 'register'

function openAuthModal() {
    authMode = 'login';
    _syncAuthModal();
    document.getElementById('authOverlay').style.display = 'flex';
    document.getElementById('authEmail').focus();
}

function closeAuthModal(event) {
    if (event && event.target !== document.getElementById('authOverlay')) return;
    document.getElementById('authOverlay').style.display = 'none';
    _clearAuthForm();
}

function toggleAuthMode() {
    authMode = authMode === 'login' ? 'register' : 'login';
    _syncAuthModal();
}

function _syncAuthModal() {
    const isLogin = authMode === 'login';
    document.getElementById('authModalTitle').textContent = isLogin ? 'Welcome back' : 'Create account';
    document.getElementById('authSub').textContent = isLogin ? 'Sign in to your Voyago account' : 'Join Voyago for free';
    document.getElementById('authSubmit').textContent = isLogin ? 'Sign In' : 'Register';
    document.getElementById('authToggleText').textContent = isLogin ? "Don't have an account?" : 'Already have an account?';
    document.getElementById('authToggleBtn').textContent = isLogin ? 'Register' : 'Sign In';
    document.getElementById('authPassword').autocomplete = isLogin ? 'current-password' : 'new-password';
    _clearAuthError();
}

function _clearAuthForm() {
    document.getElementById('authEmail').value = '';
    document.getElementById('authPassword').value = '';
    _clearAuthError();
}

function _clearAuthError() {
    const el = document.getElementById('authError');
    el.style.display = 'none';
    el.textContent = '';
}

function _showAuthError(msg) {
    const el = document.getElementById('authError');
    el.textContent = msg;
    el.style.display = 'block';
}

// Wire up form submit
document.getElementById('authForm').addEventListener('submit', () => {
    authMode === 'login' ? handleLogin() : handleRegister();
});

// ══════════════════════════════════════
// AUTH — Session check on page load
// ══════════════════════════════════════
async function checkAuthSession() {
    try {
        const res = await fetch('/auth/me', { credentials: 'same-origin' });
        if (res.ok) {
            const data = await res.json();
            _setLoggedIn(data.email);
        }
    } catch (_) { /* unauthenticated — ignore */ }
}

function _setLoggedIn(email) {
    document.getElementById('authHeaderBtn').style.display = 'none';
    document.getElementById('authUserEmail').textContent = email;
    document.getElementById('authUserInfo').style.display = 'flex';
}

function _setLoggedOut() {
    document.getElementById('authHeaderBtn').style.display = '';
    document.getElementById('authUserInfo').style.display = 'none';
    document.getElementById('authUserEmail').textContent = '';
}

// ══════════════════════════════════════
// AUTH — Login / Register / Logout
// ══════════════════════════════════════
async function handleLogin() {
    const email = document.getElementById('authEmail').value.trim();
    const password = document.getElementById('authPassword').value;
    const btn = document.getElementById('authSubmit');
    btn.disabled = true;
    _clearAuthError();
    try {
        const res = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ email, password }),
        });
        const data = await res.json();
        if (!res.ok) { _showAuthError(data.error || 'Login failed'); return; }
        _setLoggedIn(data.email);
        document.getElementById('authOverlay').style.display = 'none';
        _clearAuthForm();
    } catch (_) {
        _showAuthError('Network error. Please try again.');
    } finally {
        btn.disabled = false;
    }
}

async function handleRegister() {
    const email = document.getElementById('authEmail').value.trim();
    const password = document.getElementById('authPassword').value;
    const btn = document.getElementById('authSubmit');
    btn.disabled = true;
    _clearAuthError();
    try {
        const res = await fetch('/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ email, password }),
        });
        const data = await res.json();
        if (!res.ok) { _showAuthError(data.error || 'Registration failed'); return; }
        _setLoggedIn(data.email);
        document.getElementById('authOverlay').style.display = 'none';
        _clearAuthForm();
    } catch (_) {
        _showAuthError('Network error. Please try again.');
    } finally {
        btn.disabled = false;
    }
}

async function handleLogout() {
    try {
        await fetch('/auth/logout', { method: 'POST', credentials: 'same-origin' });
    } catch (_) { /* ignore network errors on logout */ }
    _setLoggedOut();
}

// Check session on load
window.addEventListener('load', () => { checkAuthSession(); });
