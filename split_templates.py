import re
import os

with open('app/templates/dataset.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Make JS defensive (simple replacements)
text = re.sub(r'const\s+(\w+)\s*=\s*document\.getElementById\(([\'\"].+?[\'\"])\);(\s+)\1\.addEventListener', r'const \1 = document.getElementById(\2);\3if (\1) \1.addEventListener', text)

text = re.sub(r'document\.getElementById\(([\'\"].+?[\'\"])\)\.addEventListener', r'var __el = document.getElementById(\1); if (__el) __el.addEventListener', text)

# Function to get section
def get_section(name):
    # Escape parentheses in the name parameter, but wait, I pass regex strings.
    # Actually name might have regex characters
    match = re.search(r'(<!-- ───── ' + name + r' ───── -->.*?)(?=<!-- ─────|$)', text, re.DOTALL)
    return match.group(1) if match else ''

header = get_section('Header')
pipeline = get_section('Pipeline Visualization')
health = get_section('Data Health Scan Panel')
banner = get_section(r'Smart File Analysis Banner \(messy Excel\)')
toggles = get_section('Cleaning Toggles')
actions = get_section(r'Cleaning Actions Panel \(Enhanced\)')
before = get_section('Before vs After Stats')
insights = get_section('AI Insights Panel')
stats = get_section('Smart Stats Panel')
chart = get_section('Enhanced Chart Builder')
table = get_section('Data Table with Tabs')
payload = get_section('Data Payload')
logic = get_section('App Logic')

# Add defensive checks in logic
logic = logic.replace('qualityScoreNum.textContent', 'if (qualityScoreNum) qualityScoreNum.textContent')
logic = logic.replace('qualityCircle.style', 'if (qualityCircle) qualityCircle.style')
logic = logic.replace('insightsCount.textContent', 'if (insightsCount) insightsCount.textContent')
logic = logic.replace('aiInsightsContainer.innerHTML', 'if (aiInsightsContainer) aiInsightsContainer.innerHTML')
logic = logic.replace('healthMetricsGrid.innerHTML', 'if (healthMetricsGrid) healthMetricsGrid.innerHTML')
logic = logic.replace('messyExcelBanner.classList', 'if (typeof messyExcelBanner !== "undefined" && messyExcelBanner) messyExcelBanner.classList')
logic = logic.replace('messyExcelIssues.innerHTML', 'if (typeof messyExcelIssues !== "undefined" && messyExcelIssues) messyExcelIssues.innerHTML')

def write_tpl(name, blocks, extra=''):
    content = '{% extends "base_app.html" %}\n{% block app_content %}\n'
    content += header
    for b in blocks: content += b
    content += extra
    content += payload
    content += logic
    content += '{% endblock %}\n'
    with open('app/templates/' + name, 'w', encoding='utf-8') as f:
        f.write(content)

write_tpl('cleaning_lab.html', [pipeline, health, banner, toggles, actions, before])
write_tpl('data_explorer.html', [stats, table])
write_tpl('analytics_studio.html', [chart])

# AI Insights has the panel, but we need to add the AI Chat interface
chat_html = '''
<!-- ───── AI Chat with Dataset ───── -->
<div class="glass-panel rounded-3xl p-6 mb-8 shadow-2xl relative overflow-hidden">
    <div class="absolute top-0 right-0 w-[400px] h-[400px] bg-sky-500/5 rounded-full blur-[100px] pointer-events-none"></div>
    <div class="flex items-center gap-3 mb-6 relative z-10">
        <div class="p-2 rounded-xl bg-sky-500/20 text-sky-400 border border-sky-500/20">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>
        </div>
        <h2 class="text-xl font-bold text-stone-100 tracking-tight">Chat with Dataset</h2>
    </div>
    
    <div class="bg-stone-900/50 rounded-2xl border border-stone-800 flex flex-col h-[500px] relative z-10">
        <div id="chatMessages" class="flex-1 p-5 overflow-y-auto custom-scrollbar flex flex-col gap-4">
            <div class="flex gap-3 max-w-[80%]">
                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-rose-500 flex items-center justify-center shrink-0 shadow-lg">
                    <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path></svg>
                </div>
                <div class="bg-stone-800 rounded-2xl rounded-tl-sm p-3.5 text-sm text-stone-200 shadow-sm">
                    Hi! I am your AI Data Assistant. Ask me anything about <b>{{ file.original_filename }}</b>.<br><br>
                    <span class="text-stone-400">Try asking:</span><br>
                    <button onclick="document.getElementById('chatInput').value=this.innerText;" class="text-orange-400 hover:text-orange-300 mt-1 block text-left">"Who has the highest marks?"</button>
                    <button onclick="document.getElementById('chatInput').value=this.innerText;" class="text-orange-400 hover:text-orange-300 mt-0.5 block text-left">"Show the average fees by class"</button>
                </div>
            </div>
        </div>
        <div class="p-3 border-t border-stone-800 bg-stone-900/80 rounded-b-2xl">
            <form id="chatForm" onsubmit="submitChat(event)" class="flex gap-2">
                <input type="text" id="chatInput" placeholder="Ask a question in plain English..." class="flex-1 bg-stone-950 border border-stone-800 rounded-xl px-4 py-3 text-sm text-stone-200 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-colors shadow-inner" autocomplete="off">
                <button type="submit" class="px-5 py-3 bg-sky-600 hover:bg-sky-500 text-white rounded-xl font-bold shadow-[0_0_15px_rgba(2,132,199,0.3)] transition-all">
                    Send
                </button>
            </form>
        </div>
    </div>
</div>
<script>
async function submitChat(e) {
    e.preventDefault();
    const input = document.getElementById('chatInput');
    const query = input.value.trim();
    if (!query) return;
    
    const messages = document.getElementById('chatMessages');
    
    // User message
    messages.innerHTML += `
        <div class="flex gap-3 max-w-[80%] self-end flex-row-reverse">
            <div class="w-8 h-8 rounded-full bg-stone-700 flex items-center justify-center shrink-0 shadow-sm">
                <svg class="w-4 h-4 text-stone-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
            </div>
            <div class="bg-sky-600 rounded-2xl rounded-tr-sm p-3.5 text-sm text-white shadow-md">
                ${query}
            </div>
        </div>
    `;
    input.value = '';
    messages.scrollTop = messages.scrollHeight;
    
    // Loading state
    const loadingId = 'loading-' + Date.now();
    messages.innerHTML += `
        <div id="${loadingId}" class="flex gap-3 max-w-[80%]">
            <div class="w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-rose-500 flex items-center justify-center shrink-0 shadow-lg">
                <svg class="w-4 h-4 text-white animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>
            </div>
            <div class="bg-stone-800 rounded-2xl rounded-tl-sm p-3.5 text-sm text-stone-400 italic shadow-sm">
                Thinking...
            </div>
        </div>
    `;
    messages.scrollTop = messages.scrollHeight;
    
    try {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
        const res = await fetch(`/dataset/${FILE_ID}/chat/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ query })
        });
        const data = await res.json();
        
        document.getElementById(loadingId).remove();
        
        messages.innerHTML += `
            <div class="flex gap-3 max-w-[80%]">
                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-rose-500 flex items-center justify-center shrink-0 shadow-lg">
                    <svg class="w-4 h-4 text-white" fill="none" stroke=\"currentColor\" viewBox=\"0 0 24 24\"><path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2.5\" d=\"M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z\"></path></svg>
                </div>
                <div class="bg-stone-800 border border-orange-500/30 rounded-2xl rounded-tl-sm p-3.5 text-sm text-stone-200 shadow-lg shadow-orange-500/5">
                    ${data.answer || data.error || 'I could not process that request.'}
                </div>
            </div>
        `;
        messages.scrollTop = messages.scrollHeight;
        
    } catch (e) {
        document.getElementById(loadingId).remove();
        messages.innerHTML += `<div class="text-red-400 text-sm p-2">Error communicating with AI.</div>`;
    }
}
</script>
'''

write_tpl('ai_insights_page.html', [insights], extra=chat_html)

exports_html = '''
<!-- ───── Exports & Reports ───── -->
<div class="glass-panel rounded-3xl p-6 mb-8 shadow-2xl relative overflow-hidden">
    <div class="absolute top-0 right-0 w-[400px] h-[400px] bg-emerald-500/5 rounded-full blur-[100px] pointer-events-none"></div>
    <div class="flex items-center gap-3 mb-6 relative z-10">
        <div class="p-2 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/20">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
        </div>
        <h2 class="text-xl font-bold text-stone-100 tracking-tight">Export Center</h2>
    </div>
    
    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5 relative z-10">
        
        <!-- Cleaned CSV -->
        <div class="bg-stone-900/60 border border-stone-800 rounded-2xl p-5 hover:border-emerald-500/30 transition-all group flex flex-col justify-between h-[160px]">
            <div>
                <h3 class="text-stone-200 font-bold mb-1 flex items-center gap-2">
                    <svg class="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                    Cleaned CSV
                </h3>
                <p class="text-xs text-stone-400">Download the fully cleaned and processed data as a CSV file.</p>
            </div>
            <button onclick="downloadJSONAsCSV(allRows, '{{ file.original_filename }}_cleaned.csv')" class="w-full py-2 bg-stone-800 hover:bg-emerald-600 hover:text-white text-stone-300 rounded-lg text-xs font-bold transition-colors">
                Download CSV
            </button>
        </div>
        
        <!-- Raw CSV -->
        <div class="bg-stone-900/60 border border-stone-800 rounded-2xl p-5 hover:border-stone-500/30 transition-all group flex flex-col justify-between h-[160px]">
            <div>
                <h3 class="text-stone-200 font-bold mb-1 flex items-center gap-2">
                    <svg class="w-4 h-4 text-stone-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3M3 17V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"></path></svg>
                    Raw Data (Original)
                </h3>
                <p class="text-xs text-stone-400">Download the original messy data snippet.</p>
            </div>
            <button onclick="downloadJSONAsCSV(rawSnapshot, '{{ file.original_filename }}_raw.csv')" class="w-full py-2 bg-stone-800 hover:bg-stone-600 hover:text-white text-stone-300 rounded-lg text-xs font-bold transition-colors">
                Download Raw Snapshot
            </button>
        </div>

        <!-- Cleaned JSON -->
        <div class="bg-stone-900/60 border border-stone-800 rounded-2xl p-5 hover:border-amber-500/30 transition-all group flex flex-col justify-between h-[160px]">
            <div>
                <h3 class="text-stone-200 font-bold mb-1 flex items-center gap-2">
                    <svg class="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
                    Cleaned JSON
                </h3>
                <p class="text-xs text-stone-400">Download the cleaned dataset as a structured JSON array.</p>
            </div>
            <button onclick="downloadAsJSON(allRows, '{{ file.original_filename }}_cleaned.json')" class="w-full py-2 bg-stone-800 hover:bg-amber-600 hover:text-white text-stone-300 rounded-lg text-xs font-bold transition-colors">
                Download JSON
            </button>
        </div>

    </div>
</div>

<script>
function downloadJSONAsCSV(data, filename) {
    if (!data || !data.length) { alert('No data available'); return; }
    const keys = Object.keys(data[0]);
    const csvStr = [
        keys.join(','),
        ...data.map(row => keys.map(k => {
            let cell = row[k] === null || row[k] === undefined ? '' : row[k];
            cell = cell.toString().replace(/"/g, '""');
            return `"${cell}"`;
        }).join(','))
    ].join('\\n');
    
    const blob = new Blob([csvStr], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function downloadAsJSON(data, filename) {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
</script>
'''

write_tpl('exports_reports.html', [], extra=exports_html)

print('Templates split successfully!')
