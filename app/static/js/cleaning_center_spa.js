// ════════════════════════════════════════════════════════════════════════════
// DATA PRO UNIFIED SPA ARCHITECTURE
// Handles Routing, Cleaning, Explorer, and Analytics within a single page
// ════════════════════════════════════════════════════════════════════════════

// ────────────────────────────────────────────────────────────
// 1. STATE MANAGEMENT & ROUTING
// ────────────────────────────────────────────────────────────

const AppState = {
    pipeline: [],
    selectedTool: null,
    currentView: 'cleaning',
    
    // Explorer State
    explorerSearch: '',
    explorerPage: 1,
    explorerPageSize: 50,
    explorerStatsCol: '',
    
    // Analytics State
    chartInstance: null
};

document.addEventListener('DOMContentLoaded', () => {
    initSPA();
    initCleaningCenter();
    initExplorer();
    initAnalytics();
});

function initSPA() {
    const navBtns = document.querySelectorAll('.spa-nav-btn');
    navBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const target = e.currentTarget.getAttribute('data-target');
            if(!target) return;
            
            // Update Active State
            navBtns.forEach(b => {
                b.classList.remove('active', 'bg-stone-100', 'dark:bg-zinc-800', 'text-stone-900', 'dark:text-zinc-100');
                b.classList.add('text-stone-600', 'dark:text-zinc-400');
            });
            e.currentTarget.classList.add('active', 'bg-stone-100', 'dark:bg-zinc-800', 'text-stone-900', 'dark:text-zinc-100');
            e.currentTarget.classList.remove('text-stone-600', 'dark:text-zinc-400');
            
            // Switch View
            document.querySelectorAll('.spa-view').forEach(v => {
                v.classList.add('hidden');
                v.classList.remove('block');
            });
            document.getElementById(`view-${target}`).classList.remove('hidden');
            document.getElementById(`view-${target}`).classList.add('block');
            
            AppState.currentView = target;
            
            // Trigger View Specific Render
            if (target === 'explorer') renderExplorer();
            if (target === 'analytics') renderAnalytics();
        });
    });
}

// ────────────────────────────────────────────────────────────
// 2. CLEANING CENTER LOGIC
// ────────────────────────────────────────────────────────────

const toolConfigs = {
    'remove_duplicates': { label: 'Remove Duplicates', fields: [] },
    'trim_whitespace': { label: 'Trim Whitespace', fields: [] },
    'remove_empty_rows': { label: 'Remove Empty Rows', fields: [] },
    'remove_empty_columns': { label: 'Remove Empty Columns', fields: [] },
    'fill_nulls': { 
        label: 'Fill Missing Values', 
        fields: [
            { name: 'column', label: 'Target Column', type: 'select', options: 'COLUMNS' },
            { name: 'strategy', label: 'Fill Strategy', type: 'select', options: ['mean', 'median', 'mode', 'custom'] },
            { name: 'custom_value', label: 'Custom Value', type: 'text', dependsOn: { field: 'strategy', value: 'custom' } }
        ] 
    },
    'drop_null_rows': { label: 'Drop Null Rows', fields: [] },
    'coerce_numeric': {
        label: 'Convert to Numeric',
        fields: [{ name: 'column', label: 'Target Column', type: 'select', options: ['ALL', ...window.APP_DATA.columns] }]
    },
    'lowercase': { label: 'Lowercase', fields: [{ name: 'column', label: 'Target Column', type: 'select', options: 'COLUMNS' }] },
    'uppercase': { label: 'Uppercase', fields: [{ name: 'column', label: 'Target Column', type: 'select', options: 'COLUMNS' }] }
};

function initCleaningCenter() {
    document.querySelectorAll('.tool-btn').forEach(btn => {
        btn.addEventListener('click', (e) => openToolConfig(e.target.getAttribute('data-op')));
    });

    document.getElementById('closeToolBtn').addEventListener('click', () => {
        document.getElementById('toolControlPanel').classList.add('hidden');
    });

    document.getElementById('addStepBtn').addEventListener('click', addStepToPipeline);
    
    document.getElementById('clearPipelineBtn').addEventListener('click', () => {
        if (confirm("Clear all steps?")) {
            AppState.pipeline = [];
            renderPipelinePills();
            runPreview();
        }
    });

    document.getElementById('applyPipelineBtn').addEventListener('click', applyPipelineToDataset);

    // Setup Tabs for preview
    document.getElementById('tabBefore').addEventListener('click', (e) => {
        e.target.classList.add('text-stone-800', 'dark:text-zinc-200');
        e.target.classList.remove('text-stone-500', 'dark:text-zinc-400');
        document.getElementById('tabAfter').classList.add('text-orange-500');
        document.getElementById('tabAfter').classList.remove('text-stone-800', 'dark:text-zinc-200');
        renderPreviewTable(window.APP_DATA.columns, window.APP_DATA.rawSnapshot);
    });

    document.getElementById('tabAfter').addEventListener('click', (e) => {
        runPreview();
    });

    renderPreviewTable(window.APP_DATA.columns, window.APP_DATA.rawSnapshot);
}

function openToolConfig(op) {
    const config = toolConfigs[op];
    if (!config) return;
    AppState.selectedTool = op;
    
    document.getElementById('toolTitle').textContent = config.label;
    
    if (config.fields.length === 0) {
        document.getElementById('toolForm').innerHTML = `<p class="text-sm text-zinc-500">No configuration needed.</p>`;
    } else {
        document.getElementById('toolForm').innerHTML = config.fields.map(f => {
            const isHidden = f.dependsOn ? 'hidden' : '';
            let input = '';
            
            if (f.type === 'select') {
                let opts = f.options === 'COLUMNS' ? window.APP_DATA.columns : f.options;
                input = `<select id="field_${f.name}" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-orange-500">
                    ${opts.map(o => `<option value="${o==='ALL'?'':o}">${o}</option>`).join('')}
                </select>`;
            } else {
                input = `<input type="${f.type}" id="field_${f.name}" class="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-orange-500" placeholder="${f.label}">`;
            }
            return `<div id="wrap_${f.name}" class="${isHidden} flex flex-col gap-1"><label class="text-xs font-bold text-zinc-400 uppercase">${f.label}</label>${input}</div>`;
        }).join('');
        
        // Handle dependencies
        config.fields.forEach(f => {
            if (f.dependsOn) {
                const parent = document.getElementById(`field_${f.dependsOn.field}`);
                if (parent) {
                    parent.addEventListener('change', () => {
                        const wrap = document.getElementById(`wrap_${f.name}`);
                        if (parent.value === f.dependsOn.value) wrap.classList.remove('hidden');
                        else wrap.classList.add('hidden');
                    });
                }
            }
        });
    }

    document.getElementById('toolControlPanel').classList.remove('hidden');
}

function addStepToPipeline() {
    const config = toolConfigs[AppState.selectedTool];
    const params = {};
    config.fields.forEach(f => {
        const wrap = document.getElementById(`wrap_${f.name}`);
        if (!wrap.classList.contains('hidden')) {
            params[f.name] = document.getElementById(`field_${f.name}`).value;
        }
    });

    AppState.pipeline.push({ operation: AppState.selectedTool, params: params, label: config.label });
    document.getElementById('toolControlPanel').classList.add('hidden');
    AppState.selectedTool = null;
    
    renderPipelinePills();
    runPreview();
}

function renderPipelinePills() {
    const container = document.getElementById('pipelinePills');
    const msg = document.getElementById('emptyPipelineMsg');
    
    if (AppState.pipeline.length === 0) {
        container.innerHTML = '';
        msg.classList.remove('hidden');
        return;
    }
    msg.classList.add('hidden');
    container.innerHTML = AppState.pipeline.map((step, idx) => `
        <div class="flex items-center gap-1.5 bg-orange-500/10 text-orange-500 px-3 py-1.5 rounded-lg border border-orange-500/30 text-xs font-semibold">
            <span class="w-4 h-4 rounded-full bg-orange-500 text-white flex items-center justify-center text-[10px]">${idx + 1}</span>
            ${step.label}
            <button onclick="removeStep(${idx})" class="ml-1 text-orange-400 hover:text-orange-300">✕</button>
        </div>
    `).join('');
}

window.removeStep = function(idx) {
    AppState.pipeline.splice(idx, 1);
    renderPipelinePills();
    runPreview();
};

function getCsrfToken() {
    return document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1] || '';
}

async function runPreview() {
    if (AppState.pipeline.length === 0) {
        renderPreviewTable(window.APP_DATA.columns, window.APP_DATA.rawSnapshot);
        return;
    }

    try {
        const response = await fetch(`/dataset/${window.APP_DATA.FILE_ID}/api/preview-cleaning/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
            body: JSON.stringify({ pipeline: AppState.pipeline })
        });
        const data = await response.json();
        if (data.status === 'success') {
            renderPreviewTable(data.after_columns, data.after);
        }
    } catch (e) { console.error('Preview error', e); }
}

function renderPreviewTable(cols, rows) {
    const thead = document.getElementById('previewThead');
    const tbody = document.getElementById('previewTbody');
    
    thead.innerHTML = `<tr>${cols.map(c => `<th class="px-4 py-3 text-xs font-bold text-zinc-400 uppercase tracking-wider whitespace-nowrap">${c}</th>`).join('')}</tr>`;
    
    if (rows.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${cols.length}" class="p-10 text-center text-zinc-600">No data</td></tr>`;
        return;
    }

    tbody.innerHTML = rows.map(r => `
        <tr class="hover:bg-zinc-800/50">
            ${cols.map(c => `<td class="px-4 py-2.5 whitespace-nowrap text-zinc-200">${r[c] !== null && r[c] !== undefined ? r[c] : '<span class="text-zinc-600">—</span>'}</td>`).join('')}
        </tr>
    `).join('');
}

async function applyPipelineToDataset() {
    if (AppState.pipeline.length === 0) return alert('Pipeline is empty.');
    
    const btn = document.getElementById('applyPipelineBtn');
    btn.disabled = true;
    btn.textContent = 'Applying...';

    try {
        const response = await fetch(`/dataset/${window.APP_DATA.FILE_ID}/api/apply-cleaning/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
            body: JSON.stringify({ pipeline: AppState.pipeline })
        });
        const data = await response.json();
        if (data.status === 'success') {
            alert('Pipeline Applied Successfully!');
            // Full SPA refresh of local data
            window.location.reload(); // Ideally fetch new data, but reload ensures pure state
        } else {
            alert('Error: ' + data.error);
        }
    } catch (e) {
        console.error(e);
        alert('Network error.');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Apply to Dataset';
    }
}


// ────────────────────────────────────────────────────────────
// 3. DATA EXPLORER LOGIC
// ────────────────────────────────────────────────────────────

function initExplorer() {
    const search = document.getElementById('explorerSearch');
    search.addEventListener('input', (e) => {
        AppState.explorerSearch = e.target.value.toLowerCase();
        AppState.explorerPage = 1;
        renderExplorer();
    });
    
    document.getElementById('explorerPrev').addEventListener('click', () => {
        if(AppState.explorerPage > 1) { AppState.explorerPage--; renderExplorer(); }
    });
    document.getElementById('explorerNext').addEventListener('click', () => {
        AppState.explorerPage++; renderExplorer();
    });

    const statCol = document.getElementById('explorerStatsCol');
    statCol.innerHTML = `<option value="">-- Select Column --</option>` + window.APP_DATA.columns.map(c => `<option value="${c}">${c}</option>`).join('');
    statCol.addEventListener('change', (e) => {
        AppState.explorerStatsCol = e.target.value;
        renderExplorerStats();
    });
}

function getFilteredRows() {
    const term = AppState.explorerSearch;
    if (!term) return window.APP_DATA.allRows;
    return window.APP_DATA.allRows.filter(r => 
        window.APP_DATA.columns.some(c => String(r[c]).toLowerCase().includes(term))
    );
}

function renderExplorer() {
    const rows = getFilteredRows();
    const start = (AppState.explorerPage - 1) * AppState.explorerPageSize;
    const end = start + AppState.explorerPageSize;
    const pageRows = rows.slice(start, end);
    const cols = window.APP_DATA.columns;

    const thead = document.getElementById('explorerThead');
    const tbody = document.getElementById('explorerTbody');
    
    thead.innerHTML = `<tr>${cols.map(c => `<th class="px-4 py-3 text-xs font-bold text-zinc-400 uppercase tracking-wider whitespace-nowrap">${c}</th>`).join('')}</tr>`;
    
    if (pageRows.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${cols.length}" class="p-10 text-center text-zinc-600">No data found</td></tr>`;
    } else {
        tbody.innerHTML = pageRows.map(r => `
            <tr class="hover:bg-zinc-800/50">
                ${cols.map(c => `<td class="px-4 py-2 whitespace-nowrap text-zinc-200">${r[c] !== null && r[c] !== undefined ? r[c] : '<span class="text-zinc-600">—</span>'}</td>`).join('')}
            </tr>
        `).join('');
    }

    document.getElementById('explorerCount').textContent = `Showing ${Math.min(start + 1, rows.length)} - ${Math.min(end, rows.length)} of ${rows.length} rows`;
    document.getElementById('explorerPage').textContent = `Page ${AppState.explorerPage}`;
    document.getElementById('explorerPrev').disabled = AppState.explorerPage === 1;
    document.getElementById('explorerNext').disabled = end >= rows.length;

    renderExplorerStats();
}

function renderExplorerStats() {
    const col = AppState.explorerStatsCol;
    const grid = document.getElementById('explorerStatsGrid');
    
    if (!col) {
        grid.innerHTML = `<div class="text-xs text-zinc-500 col-span-4">Select a column to view contextual stats.</div>`;
        return;
    }

    const rows = getFilteredRows();
    let sum = 0, count = 0, numericCount = 0;
    let min = Infinity, max = -Infinity;

    rows.forEach(r => {
        const val = r[col];
        if (val !== null && val !== undefined && val !== '') {
            count++;
            const num = parseFloat(val);
            if (!isNaN(num)) {
                numericCount++;
                sum += num;
                if (num < min) min = num;
                if (num > max) max = num;
            }
        }
    });

    const isNumeric = numericCount > (count * 0.5); // weak check

    let html = `
        <div class="bg-zinc-950 border border-zinc-800 rounded-lg p-3"><div class="text-[10px] text-zinc-500 uppercase font-bold mb-1">Total Valid</div><div class="text-lg font-bold text-zinc-100">${count}</div></div>
        <div class="bg-zinc-950 border border-zinc-800 rounded-lg p-3"><div class="text-[10px] text-zinc-500 uppercase font-bold mb-1">Missing</div><div class="text-lg font-bold text-zinc-100">${rows.length - count}</div></div>
    `;

    if (isNumeric && numericCount > 0) {
        html += `
            <div class="bg-zinc-950 border border-zinc-800 rounded-lg p-3"><div class="text-[10px] text-zinc-500 uppercase font-bold mb-1">Sum</div><div class="text-lg font-bold text-zinc-100">${sum.toFixed(2)}</div></div>
            <div class="bg-zinc-950 border border-zinc-800 rounded-lg p-3"><div class="text-[10px] text-zinc-500 uppercase font-bold mb-1">Mean</div><div class="text-lg font-bold text-zinc-100">${(sum/numericCount).toFixed(2)}</div></div>
            <div class="bg-zinc-950 border border-zinc-800 rounded-lg p-3"><div class="text-[10px] text-zinc-500 uppercase font-bold mb-1">Min</div><div class="text-lg font-bold text-zinc-100">${min}</div></div>
            <div class="bg-zinc-950 border border-zinc-800 rounded-lg p-3"><div class="text-[10px] text-zinc-500 uppercase font-bold mb-1">Max</div><div class="text-lg font-bold text-zinc-100">${max}</div></div>
        `;
    }

    grid.innerHTML = html;
}


// ────────────────────────────────────────────────────────────
// 4. ANALYTICS STUDIO LOGIC (NATIVE DROPDOWNS)
// ────────────────────────────────────────────────────────────

function initAnalytics() {
    const colOptions = window.APP_DATA.columns.map(c => `<option value="${c}">${c}</option>`).join('');
    document.getElementById('analyticsX').innerHTML = colOptions;
    document.getElementById('analyticsY').innerHTML = colOptions;
    
    // Default Y to second column if exists
    if(window.APP_DATA.columns.length > 1) {
        document.getElementById('analyticsY').selectedIndex = 1;
    }

    const selects = ['analyticsType', 'analyticsX', 'analyticsY', 'analyticsAgg'];
    selects.forEach(id => {
        document.getElementById(id).addEventListener('change', renderAnalytics);
    });
}

function renderAnalytics() {
    if (AppState.currentView !== 'analytics') return;

    const type = document.getElementById('analyticsType').value;
    const xCol = document.getElementById('analyticsX').value;
    const yCol = document.getElementById('analyticsY').value;
    const agg = document.getElementById('analyticsAgg').value;
    
    if (!xCol || !yCol) return;

    // Process data
    let labels = [];
    let data = [];
    const rows = window.APP_DATA.allRows;

    if (agg === 'none') {
        labels = rows.map(r => r[xCol]).slice(0, 500); // cap to prevent lag
        data = rows.map(r => parseFloat(r[yCol])).slice(0, 500);
    } else {
        // Grouping
        const grouped = {};
        rows.forEach(r => {
            const key = String(r[xCol]);
            if (!grouped[key]) grouped[key] = [];
            const val = parseFloat(r[yCol]);
            if (!isNaN(val)) grouped[key].push(val);
        });

        labels = Object.keys(grouped).slice(0, 100);
        data = labels.map(k => {
            const arr = grouped[k];
            if (arr.length === 0) return 0;
            if (agg === 'sum') return arr.reduce((a,b)=>a+b,0);
            if (agg === 'count') return arr.length;
            if (agg === 'mean') return arr.reduce((a,b)=>a+b,0) / arr.length;
            return 0;
        });
    }

    // Render Chart.js
    const ctx = document.getElementById('analyticsCanvas').getContext('2d');
    
    if (AppState.chartInstance) {
        AppState.chartInstance.destroy();
    }

    AppState.chartInstance = new Chart(ctx, {
        type: type,
        data: {
            labels: labels,
            datasets: [{
                label: yCol,
                data: data,
                backgroundColor: 'rgba(249, 115, 22, 0.5)',
                borderColor: 'rgba(249, 115, 22, 1)',
                borderWidth: 1,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#a1a1aa' } }
            },
            scales: (type === 'pie' || type === 'doughnut') ? {} : {
                x: { ticks: { color: '#71717a' }, grid: { color: '#27272a' } },
                y: { ticks: { color: '#71717a' }, grid: { color: '#27272a' } }
            }
        }
    });
}
