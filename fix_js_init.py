import re

with open('app/templates/cleaning_lab.html', 'r', encoding='utf-8') as f:
    content = f.read()

new_script = """<script>
// ════════════════════════════════════════════════════════════════════════════
// GLOBALS & STATE
// ════════════════════════════════════════════════════════════════════════════
const appState = {
    currentOptions: {
        removeDuplicates: false,
        normalizeHeaders: false,
        trimWhitespace: false,
        removeEmptyRows: false,
        removeEmptyColumns: false,
        coerceNumeric: false
    }
};

// ════════════════════════════════════════════════════════════════════════════
// HEALTH SCORE GAUGE ANIMATION & METRICS
// ════════════════════════════════════════════════════════════════════════════
function initHealthScan() {
    const qualityScoreNum = document.getElementById('qualityScoreNum');
    const qualityCircle = document.getElementById('qualityCircle');
    const qualityScore = (window.APP_DATA && window.APP_DATA.qualityScore) ? window.APP_DATA.qualityScore : 100;
    
    if (qualityScoreNum && qualityCircle) {
        let start = 0;
        const duration = 1500;
        const startTime = performance.now();
        function animateNum(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            const currentScore = Math.floor(easeOutQuart * qualityScore);
            qualityScoreNum.textContent = currentScore;
            if (progress < 1) requestAnimationFrame(animateNum);
        }
        requestAnimationFrame(animateNum);

        const circumference = 326.73;
        const dashoffset = circumference - (qualityScore / 100) * circumference;
        qualityCircle.style.transition = 'stroke-dashoffset 1.5s cubic-bezier(0.165, 0.84, 0.44, 1)';
        setTimeout(() => {
            qualityCircle.style.strokeDashoffset = dashoffset;
        }, 50);

        qualityScoreNum.className = 'text-3xl font-bold';
        qualityCircle.className.baseVal = '';
        if (qualityScore >= 80) {
            qualityScoreNum.classList.add('text-emerald-400');
            qualityCircle.classList.add('stroke-emerald-500');
        } else if (qualityScore >= 50) {
            qualityScoreNum.classList.add('text-amber-400');
            qualityCircle.classList.add('stroke-amber-500');
        } else {
            qualityScoreNum.classList.add('text-red-400');
            qualityCircle.classList.add('stroke-red-500');
        }
    }

    const grid = document.getElementById('healthMetricsGrid');
    const healthReport = window.APP_DATA ? window.APP_DATA.healthReport : null;
    if (grid && healthReport) {
        const metrics = [
            { label: 'Missing Values', val: healthReport.missing_values || 0, icon: '⚠️', color: 'text-amber-400' },
            { label: 'Duplicates', val: healthReport.duplicate_rows || 0, icon: '📋', color: 'text-blue-400' },
            { label: 'Empty Rows', val: healthReport.empty_rows || 0, icon: '🗑️', color: 'text-stone-400' },
            { label: 'Empty Columns', val: healthReport.empty_columns || 0, icon: '🗑️', color: 'text-stone-400' },
            { label: 'Type Issues', val: (healthReport.inconsistent_types || []).length, icon: '🔄', color: 'text-violet-400' },
            { label: 'Blank Headers', val: healthReport.blank_headers || 0, icon: '🏷️', color: 'text-rose-400' }
        ];
        
        grid.innerHTML = metrics.map(m => `
            <div class="bg-stone-900/40 rounded-xl p-3 border border-stone-800 flex items-center gap-3 hover:bg-stone-800/40 transition-colors">
                <div class="w-8 h-8 rounded-lg bg-stone-800 flex items-center justify-center text-sm">${m.icon}</div>
                <div>
                    <div class="text-lg font-bold ${m.val > 0 ? m.color : 'text-stone-300'}">${m.val}</div>
                    <div class="text-[10px] font-bold text-stone-500 uppercase tracking-wider">${m.label}</div>
                </div>
            </div>
        `).join('');
    }
}

function initBeforeAfter() {
    const pnl = document.getElementById('beforeAfterPanel');
    const bStats = document.getElementById('beforeStats');
    const aStats = document.getElementById('afterStats');
    const beforeAfter = window.APP_DATA ? window.APP_DATA.beforeAfter : null;
    if (!pnl || !bStats || !aStats || !beforeAfter || !beforeAfter.before) return;
    
    pnl.classList.remove('hidden');
    
    const render = (data) => `
        <div class="flex justify-between items-center text-sm border-b border-stone-800/50 pb-2">
            <span class="text-stone-400">Rows</span>
            <span class="font-bold text-stone-200">${data.rows}</span>
        </div>
        <div class="flex justify-between items-center text-sm border-b border-stone-800/50 pb-2">
            <span class="text-stone-400">Columns</span>
            <span class="font-bold text-stone-200">${data.columns}</span>
        </div>
        <div class="flex justify-between items-center text-sm border-b border-stone-800/50 pb-2">
            <span class="text-stone-400">Missing Values</span>
            <span class="font-bold ${data.missing_values > 0 ? 'text-amber-400' : 'text-stone-200'}">${data.missing_values}</span>
        </div>
        <div class="flex justify-between items-center text-sm border-b border-stone-800/50 pb-2">
            <span class="text-stone-400">Empty Rows</span>
            <span class="font-bold ${data.empty_rows > 0 ? 'text-red-400' : 'text-stone-200'}">${data.empty_rows}</span>
        </div>
        <div class="flex justify-between items-center text-sm">
            <span class="text-stone-400">Duplicates</span>
            <span class="font-bold ${data.duplicates > 0 ? 'text-red-400' : 'text-stone-200'}">${data.duplicates}</span>
        </div>
    `;
    
    bStats.innerHTML = render(beforeAfter.before);
    aStats.innerHTML = render(beforeAfter.after);
}

function initMessyExcel() {
    const banner = document.getElementById('messyExcelBanner');
    const issuesList = document.getElementById('messyExcelIssues');
    const healthReport = window.APP_DATA ? window.APP_DATA.healthReport : null;
    if (!banner || !issuesList || !healthReport || !healthReport.file_analysis) return;
    const analysis = healthReport.file_analysis;
    if (analysis.is_messy_excel) {
        banner.classList.remove('hidden');
        issuesList.innerHTML = analysis.issues_detected.map(i => `
            <li class="text-sm font-medium text-stone-300 flex items-center gap-2">
                <div class="w-1.5 h-1.5 rounded-full bg-amber-500"></div> ${i}
            </li>
        `).join('');
    }
}

function initToggles() {
    document.querySelectorAll('.toggle-switch').forEach(el => {
        const key = el.getAttribute('data-key');
        if (appState.currentOptions[key] !== false) {
            el.classList.add('active');
            el.innerHTML = '<div class="toggle-knob active"></div>';
            appState.currentOptions[key] = true;
        } else {
            el.innerHTML = '<div class="toggle-knob"></div>';
            appState.currentOptions[key] = false;
        }
        
        el.addEventListener('click', () => {
            const isActive = el.classList.contains('active');
            if (isActive) {
                el.classList.remove('active');
                el.querySelector('.toggle-knob').classList.remove('active');
                appState.currentOptions[key] = false;
            } else {
                el.classList.add('active');
                el.querySelector('.toggle-knob').classList.add('active');
                appState.currentOptions[key] = true;
            }
        });
    });
}

function updatePipelineVisuals() {
    const steps = document.querySelectorAll('.pipeline-step .step-dot');
    steps.forEach((s, i) => {
        if (i === 0) return;
        s.className = 'step-dot active animate-pulse';
        s.innerHTML = '<svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>';
    });
}

function getCsrfToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1] || '';
}

async function recleanDataset() {
    const btn = document.getElementById('recleanBtn');
    if (!btn) return;
    btn.disabled = true;
    btn.innerHTML = '<svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg> Processing...';
    
    updatePipelineVisuals();
    
    try {
        const fileId = window.APP_DATA && window.APP_DATA.FILE_ID ? window.APP_DATA.FILE_ID : '';
        const response = await fetch(`/dataset/${fileId}/reclean/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(appState.currentOptions)
        });
        
        if (!response.ok) {
            let errorMsg = `HTTP ${response.status}`;
            try {
                const errData = await response.json();
                if (errData.error) errorMsg = errData.error;
            } catch (e) {}
            throw new Error(errorMsg);
        }
        
        const data = await response.json();
        console.log('Reclean success:', data);
        
        setTimeout(() => {
            window.location.reload();
        }, 500);
        
    } catch (e) {
        console.error('Reclean API Error:', e);
        alert('Cleaning failed: ' + e.message);
        
        btn.disabled = false;
        btn.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg> Re-Clean Dataset';
        
        const steps = document.querySelectorAll('.pipeline-step .step-dot');
        steps.forEach((s, i) => {
            if (i === 0) return;
            s.className = 'step-dot bg-stone-800 text-stone-500';
            const svg = s.querySelector('svg');
            if (svg) svg.classList.remove('animate-spin');
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize options from APP_DATA
    if (window.APP_DATA && window.APP_DATA.cleaningOptions) {
        Object.assign(appState.currentOptions, window.APP_DATA.cleaningOptions);
    }

    // 2. Initialize Page Components
    initHealthScan();
    initBeforeAfter();
    initMessyExcel();
    initToggles();
});
</script>"""

# Using regex to find the second <script> block and replace it
# The first <script> block has window.APP_DATA definitions
# The second one has src="..."
# The third one is what we want to replace
pattern = re.compile(r'<script>\s*// ════════════════════════════════════════════════════════════════════════════\s*// HEALTH SCORE GAUGE ANIMATION & METRICS[\s\S]*?</script>', re.MULTILINE)
new_content = pattern.sub(new_script, content)

with open('app/templates/cleaning_lab.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Updated cleaning_lab.html')
