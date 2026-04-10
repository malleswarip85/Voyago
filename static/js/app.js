// Voyago — Frontend v5 — Clean collapsible report

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
let lastAsked = '';
let tripStage = 'greeting';

// ══════════════════════════════════════
// VALIDATION
// ══════════════════════════════════════
const VALIDATORS = {
    origin_city: { validate: v => v.trim().length >= 2 && !/^\d+$/.test(v.trim()), error: '⚠️ Please enter a valid city name (e.g. "Chicago", "New York").' },
    destination_city: { validate: v => v.trim().length >= 2 && !/^\d+$/.test(v.trim()), error: '⚠️ Please enter a valid destination city (e.g. "Singapore", "Paris").' },
    checkin_date: { validate: v => { const d = parseDate(v); return d && d >= new Date(new Date().setHours(0,0,0,0)); }, error: '⚠️ Please enter a valid future date (e.g. 2025-08-01).' },
    checkout_date: { validate: v => parseDate(v) !== null, error: '⚠️ Please enter a valid date or number of nights.' },
    budget: { validate: v => { const n = parseFloat(v.replace(/[$,]/g,'')); return !isNaN(n) && n >= 200; }, error: '⚠️ Please enter a valid budget (minimum $200).' },
    nonstop_preference: { validate: v => ['yes','no','y','n','yeah','nope','sure','nonstop','non-stop','direct','any'].some(w => v.toLowerCase().includes(w)), error: '⚠️ Please reply "Yes" for non-stop or "No" for any flights.' },
    traveler_count: { validate: v => { const n = parseInt(v)||parseWordNumber(v); return n>=1&&n<=20; }, error: '⚠️ Please enter a number between 1 and 20.' },
};

function parseDate(str) {
    str = str.trim();
    if (/^\d{4}-\d{2}-\d{2}$/.test(str)) { const d = new Date(str); return isNaN(d)?null:d; }
    if (/^\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4}$/.test(str)) { const p=str.split(/[\/\-]/); const d=new Date(`${p[2]}-${p[1].padStart(2,'0')}-${p[0].padStart(2,'0')}`); return isNaN(d)?null:d; }
    if (/^\d+\s*(nights?|days?)$/i.test(str)) return new Date();
    const d = new Date(str); return isNaN(d)?null:d;
}
function parseWordNumber(s){const w={one:1,two:2,three:3,four:4,five:5,six:6,seven:7,eight:8,nine:9,ten:10};return w[s.trim().toLowerCase()]||0;}
function getValidatorKey(la){
    const l=(la||'').toLowerCase();
    if(l.includes('origin')||l==='origin_city') return 'origin_city';
    if(l.includes('destination')||l==='destination_city') return 'destination_city';
    if(l.includes('check-in')||l==='checkin_date') return 'checkin_date';
    if(l.includes('check-out')||l==='checkout_date') return 'checkout_date';
    if(l.includes('budget')) return 'budget';
    if(l.includes('nonstop')||l.includes('non-stop')) return 'nonstop_preference';
    if(l.includes('traveler')||l.includes('how many')) return 'traveler_count';
    return null;
}
function validateInput(text, key){
    if(!key||!VALIDATORS[key]) return null;
    return VALIDATORS[key].validate(text) ? null : VALIDATORS[key].error;
}

// ══════════════════════════════════════
// SEND
// ══════════════════════════════════════
async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text || isLoading) return;
    if (tripStage === 'collecting' && lastAsked) {
        const err = validateInput(text, getValidatorKey(lastAsked));
        if (err) { addMessage(text,'user'); messageInput.value=''; autoResize(messageInput); showValidationError(err); return; }
    }
    addMessage(text,'user');
    messageInput.value='';
    autoResize(messageInput);
    await callAPI(text);
}

function showValidationError(msg) {
    const w=document.createElement('div'); w.className='message assistant-message';
    const av=document.createElement('div'); av.className='message-avatar'; av.textContent='✈️';
    const c=document.createElement('div'); c.className='message-content';
    const b=document.createElement('div'); b.className='message-bubble';
    b.innerHTML=`<div class="validation-error"><span class="err-icon">⛔</span><span>${msg}<br><small style="opacity:0.75;margin-top:3px;display:block;">Please try again.</small></span></div>`;
    c.appendChild(b); w.appendChild(av); w.appendChild(c);
    insertMessage(w);
    messageInput.style.borderColor='#ef4444';
    messageInput.style.boxShadow='0 0 0 3px rgba(239,68,68,0.12)';
    setTimeout(()=>{messageInput.style.borderColor='';messageInput.style.boxShadow='';},2500);
    messageInput.focus();
}

async function callAPI(text) {
    setLoading(true);
    try {
        const r = await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text})});
        const data = await r.json();
        if (data.success) {
            tripStage = data.stage||'collecting';
            extractLastAsked(data.message, data.missing);
            if (data.message.includes('TRAVELER_FORM:')) {
                renderTravelerForm(data.message, data.collected);
            } else if (data.stage === 'done') {
                renderTripReport(data.message, data.collected);
            } else {
                addMessage(data.message,'assistant');
            }
            updateAgentPanel(data.stage, data.collected);
            updateTripInfo(data.collected);
        } else {
            addMessage(`❌ ${data.message||'Something went wrong. Please try again!'}`, 'assistant');
        }
    } catch(e) {
        console.error(e);
        addMessage('❌ Connection error. Please try again.', 'assistant');
    } finally {
        setLoading(false);
    }
}

function extractLastAsked(message, missing) {
    if (missing&&missing.length>0){lastAsked=missing[0];return;}
    const m=message.toLowerCase();
    if(m.includes('departing from')||m.includes('origin')) lastAsked='origin_city';
    else if(m.includes('travel to')||m.includes('destination')) lastAsked='destination_city';
    else if(m.includes('check-in')||m.includes('departure date')) lastAsked='checkin_date';
    else if(m.includes('check-out')||m.includes('return date')||m.includes('nights')) lastAsked='checkout_date';
    else if(m.includes('budget')) lastAsked='budget';
    else if(m.includes('non-stop')||m.includes('nonstop')) lastAsked='nonstop_preference';
    else if(m.includes('how many')&&m.includes('traveler')) lastAsked='traveler_count';
    else lastAsked='';
}

// ══════════════════════════════════════
// CLEAN TRIP REPORT RENDERER
// ══════════════════════════════════════
function renderTripReport(rawMessage, collected) {
    const wrapper = document.createElement('div');
    wrapper.className = 'message assistant-message';
    wrapper.style.maxWidth = '100%';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '✈️';

    const content = document.createElement('div');
    content.className = 'message-content';
    content.style.maxWidth = '88%';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.style.padding = '0';
    bubble.style.overflow = 'hidden';
    bubble.style.background = 'rgba(255,255,255,0.92)';

    bubble.innerHTML = buildTripReport(rawMessage, collected);

    // Add PDF button
    const pdfBar = document.createElement('div');
    pdfBar.style.cssText = 'padding:12px 18px;border-top:1px solid rgba(26,58,110,0.08);background:rgba(26,58,110,0.03);';
    pdfBar.innerHTML = `
        <a href="/api/download-pdf" target="_blank" style="
            display:inline-flex;align-items:center;gap:7px;
            padding:9px 18px;
            background:linear-gradient(135deg,#005c4a,#00b894);
            color:white;border-radius:8px;text-decoration:none;
            font-size:12.5px;font-weight:600;
            box-shadow:0 3px 10px rgba(14,165,233,0.25);
            transition:all 0.2s;
        " onmouseover="this.style.transform='translateY(-1px)'" onmouseout="this.style.transform=''">
            📄 Download Full PDF Itinerary
        </a>
        <span style="font-size:11px;color:#8399b5;margin-left:10px;">Complete day-by-day plan with all details</span>
    `;

    bubble.appendChild(pdfBar);
    content.appendChild(bubble);
    wrapper.appendChild(avatar);
    wrapper.appendChild(content);
    insertMessage(wrapper);

    // Bind toggle events
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
    // Parse sections from raw message
    const sections = parseSections(rawMessage);
    const dest = collected?.destination || 'Your Destination';
    const checkin = collected?.checkin || '';
    const checkout = collected?.checkout || '';
    const nights = collected?.nights || '';
    const budget = collected?.budget || 0;
    const travelers = collected?.traveler_count || collected?.travelers || 1;

    let html = `
        <!-- Trip Header -->
        <div style="
            background:linear-gradient(135deg,#005c4a,#00856a);
            padding:18px 20px;color:white;
        ">
            <div style="font-size:11px;opacity:0.7;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;">Your Trip Plan</div>
            <div style="font-size:20px;font-weight:700;font-family:'Crimson Pro',serif;font-style:italic;">${dest}</div>
            <div style="font-size:12px;opacity:0.8;margin-top:4px;">
                ${checkin} → ${checkout} &nbsp;·&nbsp; ${nights} nights &nbsp;·&nbsp; ${travelers} traveler(s) &nbsp;·&nbsp; Budget: $${Number(budget).toLocaleString()}
            </div>
        </div>

        <!-- Summary Cards Row -->
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;border-bottom:1px solid rgba(26,58,110,0.1);">
            ${buildSummaryCard('✈️', 'Flight', sections.flight_summary, '#0ea5e9')}
            ${buildSummaryCard('🏨', 'Hotel', sections.hotel_summary, '#10b981')}
            ${buildSummaryCard('🌤️', 'Weather', sections.weather_summary, '#f59e0b')}
        </div>
    `;

    // Budget summary (always visible, compact)
    if (sections.budget_summary) {
        html += `
        <div style="padding:14px 18px;border-bottom:1px solid rgba(26,58,110,0.08);background:rgba(26,58,110,0.02);">
            <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#1a3a6e;margin-bottom:8px;">💰 Budget Summary</div>
            <div style="font-size:12.5px;color:#1a1a2e;line-height:1.8;">${sections.budget_summary}</div>
        </div>`;
    }

    // Collapsible sections
    const collapsibles = [
        { key: 'flights', icon: '✈️', title: 'Flight Options', color: '#00b894', data: sections.flights },
        { key: 'hotels', icon: '🏨', title: 'Hotel Options', color: '#00856a', data: sections.hotels },
        { key: 'weather', icon: '🌤️', title: 'Day-by-Day Weather Forecast', color: '#ff6b6b', data: sections.weather },
        { key: 'itinerary', icon: '🗓️', title: 'Day-by-Day Itinerary', color: '#005c4a', data: sections.itinerary },
        { key: 'tips', icon: '💡', title: 'Travel Tips & Packing List', color: '#82a898', data: sections.tips },
    ];

    for (const sec of collapsibles) {
        if (!sec.data) continue;
        html += buildCollapsibleSection(sec.icon, sec.title, sec.color, sec.data);
    }

    return html;
}

function buildSummaryCard(icon, label, summary, color) {
    return `
        <div style="padding:12px 14px;border-right:1px solid rgba(26,58,110,0.08);">
            <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:${color};margin-bottom:4px;">${icon} ${label}</div>
            <div style="font-size:11.5px;color:#1a1a2e;line-height:1.5;">${summary||'—'}</div>
        </div>`;
}

function buildCollapsibleSection(icon, title, color, content) {
    const safeContent = markdownToHtml(content);
    return `
        <div class="report-section" style="border-bottom:1px solid rgba(26,58,110,0.08);">
            <button class="section-toggle" style="
                width:100%;display:flex;align-items:center;justify-content:space-between;
                padding:12px 18px;background:none;border:none;cursor:pointer;
                text-align:left;transition:background 0.15s;
            " onmouseover="this.style.background='rgba(26,58,110,0.04)'"
               onmouseout="this.style.background='none'">
                <span style="display:flex;align-items:center;gap:8px;">
                    <span style="font-size:15px;">${icon}</span>
                    <span style="font-size:12.5px;font-weight:700;color:#1a3a6e;">${title}</span>
                </span>
                <span style="display:flex;align-items:center;gap:5px;font-size:11px;color:#00b894;font-weight:600;">
                    <span class="toggle-label">Show details</span>
                    <span class="toggle-arrow" style="font-size:9px;">▼</span>
                </span>
            </button>
            <div class="section-body" style="display:none;padding:4px 18px 14px;font-size:12.5px;line-height:1.8;color:#1a1a2e;">
                ${safeContent}
            </div>
        </div>`;
}

function parseSections(raw) {
    // Extract key parts from the raw message
    const sections = {
        flight_summary: '', hotel_summary: '', weather_summary: '',
        budget_summary: '', flights: '', hotels: '', weather: '',
        itinerary: '', tips: ''
    };

    // Clean the raw text
    const text = raw.replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
    const lines = text.split('\n');

    let current = null;
    let buffer = [];

    const flush = () => { if (current && buffer.length) { sections[current] = buffer.join('\n').trim(); } buffer = []; };

    for (const line of lines) {
        const l = line.trim();

        // Detect section headers
        if (/✈️.*Available Flights|### ✈️|Flight.*Options/i.test(l)) { flush(); current='flights'; continue; }
        if (/🏨.*Available Hotels|### 🏨|Hotel.*Options/i.test(l)) { flush(); current='hotels'; continue; }
        if (/🌤️.*Weather|### 🌤️|Weather.*Forecast/i.test(l)) { flush(); current='weather'; continue; }
        if (/Day-by-Day Itinerary|📋.*Itinerary|Complete.*Itinerary/i.test(l)) { flush(); current='itinerary'; continue; }
        if (/Budget Summary|💰.*Budget|Budget Breakdown/i.test(l)) { flush(); current='budget_raw'; continue; }
        if (/Travel Tips|Local Tips|Packing|💡|🎒/i.test(l) && current !== 'itinerary') { flush(); current='tips'; continue; }
        if (/^---+$/.test(l)) { continue; } // skip dividers

        if (current) buffer.push(line);
    }
    flush();

    // Build compact summaries for the top cards
    if (sections.flights) {
        const bestMatch = sections.flights.match(/Recommended Flight.*?(?:\n|$)/);
        sections.flight_summary = bestMatch
            ? bestMatch[0].replace(/✅|\*\*/g,'').replace('Recommended Flight:','').trim()
            : extractFirstLine(sections.flights);
    }
    if (sections.hotels) {
        const bestMatch = sections.hotels.match(/Recommended Hotel.*?(?:\n|$)/);
        sections.hotel_summary = bestMatch
            ? bestMatch[0].replace(/✅|\*\*/g,'').replace('Recommended Hotel:','').trim()
            : extractFirstLine(sections.hotels);
    }
    if (sections.weather) {
        const nowMatch = sections.weather.match(/Now:.*?(?:\n|$)/);
        sections.weather_summary = nowMatch
            ? nowMatch[0].replace('Now:','').trim()
            : extractFirstLine(sections.weather);
    }

    // Budget summary — extract from itinerary or budget_raw
    const budgetSource = sections.budget_raw || sections.itinerary || '';
    const budgetLines = budgetSource.split('\n').filter(l =>
        /flight|hotel|food|total|budget|remain|activit/i.test(l) && /\$/.test(l)
    ).slice(0, 5);
    sections.budget_summary = budgetLines.join('<br>').replace(/\*\*/g,'');

    return sections;
}

function extractFirstLine(text) {
    return text.split('\n').find(l => l.trim().length > 10)?.replace(/[#*✅🏆]/g,'').trim() || '';
}

// ══════════════════════════════════════
// TRAVELER FORM
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
    if (formData&&formData.travelers_needed) b.appendChild(buildTravelerForm(formData.travelers_needed));
    c.appendChild(b); w.appendChild(av); w.appendChild(c);
    insertMessage(w);
}

function buildTravelerForm(travelers) {
    const container = document.createElement('div');
    container.className = 'traveler-form-container';
    container.style.marginTop = '14px';

    travelers.forEach((t, i) => {
        const card = document.createElement('div');
        card.style.cssText = 'background:rgba(26,58,110,0.04);border:1px solid rgba(26,58,110,0.12);border-radius:10px;padding:14px 16px;margin-bottom:12px;';
        card.innerHTML = `
            <div style="font-weight:700;color:var(--primary);margin-bottom:12px;font-size:12.5px;display:flex;align-items:center;gap:6px;">
                <span style="background:var(--primary);color:white;width:22px;height:22px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:11px;">${i+1}</span>
                Traveler ${i+1}
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                <div>
                    <label style="font-size:10.5px;font-weight:600;color:var(--text-secondary);display:block;margin-bottom:4px;">First Name <span style="color:#ef4444">*</span></label>
                    <input type="text" id="t${i}_first" placeholder="e.g. Maria" style="width:100%;padding:8px 10px;border:1.5px solid rgba(26,58,110,0.15);border-radius:7px;font-family:var(--font);font-size:12.5px;background:rgba(255,255,255,0.8);color:var(--text-primary);outline:none;" value="${t.first_name||''}">
                    <span class="field-error" id="err_t${i}_first"></span>
                </div>
                <div>
                    <label style="font-size:10.5px;font-weight:600;color:var(--text-secondary);display:block;margin-bottom:4px;">Last Name <span style="color:#ef4444">*</span></label>
                    <input type="text" id="t${i}_last" placeholder="e.g. Smith" style="width:100%;padding:8px 10px;border:1.5px solid rgba(26,58,110,0.15);border-radius:7px;font-family:var(--font);font-size:12.5px;background:rgba(255,255,255,0.8);color:var(--text-primary);outline:none;" value="${t.last_name||''}">
                    <span class="field-error" id="err_t${i}_last"></span>
                </div>
                <div>
                    <label style="font-size:10.5px;font-weight:600;color:var(--text-secondary);display:block;margin-bottom:4px;">Age <span style="color:#ef4444">*</span></label>
                    <input type="number" id="t${i}_age" placeholder="e.g. 28" min="1" max="120" style="width:100%;padding:8px 10px;border:1.5px solid rgba(26,58,110,0.15);border-radius:7px;font-family:var(--font);font-size:12.5px;background:rgba(255,255,255,0.8);color:var(--text-primary);outline:none;" value="${t.age||''}">
                    <span class="field-error" id="err_t${i}_age"></span>
                </div>
                <div>
                    <label style="font-size:10.5px;font-weight:600;color:var(--text-secondary);display:block;margin-bottom:4px;">Gender <span style="color:#ef4444">*</span></label>
                    <select id="t${i}_gender" style="width:100%;padding:8px 10px;border:1.5px solid rgba(26,58,110,0.15);border-radius:7px;font-family:var(--font);font-size:12.5px;background:rgba(255,255,255,0.8);color:var(--text-primary);outline:none;">
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
    btn.style.cssText = 'width:100%;padding:11px;background:linear-gradient(135deg,var(--primary),var(--primary-mid));color:white;border:none;border-radius:8px;font-family:var(--font);font-size:13px;font-weight:600;cursor:pointer;margin-top:4px;transition:all 0.2s;box-shadow:0 3px 12px rgba(26,58,110,0.25);';
    btn.onmouseover=()=>btn.style.background='linear-gradient(135deg,var(--primary-mid),var(--accent))';
    btn.onmouseout=()=>btn.style.background='linear-gradient(135deg,var(--primary),var(--primary-mid))';

    btn.onclick = () => {
        const data = []; let valid = true;
        container.querySelectorAll('.field-error').forEach(e=>e.textContent='');
        container.querySelectorAll('input,select').forEach(e=>{e.classList.remove('input-error');e.style.borderColor='rgba(26,58,110,0.15)';});
        travelers.forEach((t,i)=>{
            const fn=document.getElementById(`t${i}_first`)?.value.trim();
            const ln=document.getElementById(`t${i}_last`)?.value.trim();
            const age=document.getElementById(`t${i}_age`)?.value.trim();
            const gender=document.getElementById(`t${i}_gender`)?.value;
            let rv=true;
            if(!fn||fn.length<2||/\d/.test(fn)){showFieldError(`t${i}_first`,`err_t${i}_first`,'Valid first name required');valid=rv=false;}
            if(!ln||ln.length<1||/\d/.test(ln)){showFieldError(`t${i}_last`,`err_t${i}_last`,'Valid last name required');valid=rv=false;}
            const an=parseInt(age);
            if(!age||isNaN(an)||an<1||an>120){showFieldError(`t${i}_age`,`err_t${i}_age`,'Age 1–120 required');valid=rv=false;}
            if(!gender){showFieldError(`t${i}_gender`,`err_t${i}_gender`,'Please select gender');valid=rv=false;}
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

function showFieldError(inputId,errId,msg){
    const inp=document.getElementById(inputId); const err=document.getElementById(errId);
    if(inp){inp.classList.add('input-error');inp.style.borderColor='#ef4444';}
    if(err) err.textContent=msg;
}

// ══════════════════════════════════════
// ADD MESSAGE
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

// ══════════════════════════════════════
// MARKDOWN
// ══════════════════════════════════════
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

// ══════════════════════════════════════
// LOADING & AGENTS
// ══════════════════════════════════════
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

// ══════════════════════════════════════
// TRIP INFO PANEL
// ══════════════════════════════════════
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
        html+=`<div style="margin-top:7px;font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:var(--text-muted);padding-top:6px;border-top:1px solid var(--border);">Passengers</div>`;
        done.forEach(t=>{html+=`<div style="padding:4px 0;border-bottom:1px solid var(--border);"><div style="color:var(--primary);font-weight:700;font-size:11px;">👤 ${t.first_name} ${t.last_name}</div><div style="color:var(--text-muted);font-size:10px;">Age ${t.age||'?'} · ${t.gender||'?'}</div></div>`;});
    }
    if(html){details.innerHTML=html;panel.style.display='block';}
}

function sendQuick(text){messageInput.value=text;sendMessage();}

async function resetChat(){
    try{await fetch('/api/reset',{method:'POST'});}catch(e){}
    chatMessages.querySelectorAll('.message').forEach((m,i)=>{if(i>0)m.remove();});
    document.querySelectorAll('.agent-item').forEach(el=>{el.classList.remove('working','done','active');el.querySelector('.agent-status').textContent='Standby';});
    document.getElementById('trip-info').style.display='none';
    messageInput.value='';lastAsked='';tripStage='greeting';
}
function handleKeyDown(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMessage();}}
function autoResize(el){el.style.height='auto';el.style.height=Math.min(el.scrollHeight,120)+'px';}
function scrollToBottom(){setTimeout(()=>{chatMessages.scrollTop=chatMessages.scrollHeight;},50);}
