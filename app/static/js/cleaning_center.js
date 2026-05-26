// ════════════════════════════════════════════════════════════════════════════
// CLEANING CENTER: PIPELINE & PREVIEW LOGIC
// ════════════════════════════════════════════════════════════════════════════

let currentPipeline = [];
let selectedTool = null;

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
    'drop_null_rows': { label: 'Drop Null Rows', fields: [] }, // Advanced: specify cols later
    'coerce_numeric': {
        label: 'Convert to Numeric',
        fields: [
            { name: 'column', label: 'Target Column (leave blank for all)', type: 'select', options: ['ALL', ...window.APP_DATA.columns] }
        ]
    },
    'lowercase': {
        label: 'Lowercase',
        fields: [{ name: 'column', label: 'Target Column', type: 'select', options: 'COLUMNS' }]
    },
    'uppercase': {
        label: 'Uppercase',
        fields: [{ name: 'column', label: 'Target Column', type: 'select', options: 'COLUMNS' }]
    }
};

document.addEventListener('DOMContentLoaded', () => {
    initToolbox();
    initTabs();
    initApplyButton();
    renderInitialBeforeTable();
});

// ────────────────────────────────────────────────────────────
// TOOLBOX INTERACTION
// ────────────────────────────────────────────────────────────

function initToolbox() {
    document.querySelectorAll('.tool-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const op = e.target.getAttribute('data-op');
            openToolConfig(op);
        });
    });

    document.getElementById('closeToolBtn').addEventListener('click', () => {
        document.getElementById('toolControlPanel').classList.add('hidden');
        selectedTool = null;
    });

    document.getElementById('addStepBtn').addEventListener('click', () => {
        if (!selectedTool) return;
        addStepToPipeline();
    });

    document.getElementById('clearPipelineBtn').addEventListener('click', () => {
        if (confirm("Clear all cleaning steps?")) {
            currentPipeline = [];
            renderPipelinePills();
            runPreview();
        }
    });
}

function openToolConfig(op) {
    const config = toolConfigs[op];
    if (!config) return;
    selectedTool = op;
    
    document.getElementById('toolTitle').textContent = config.label;
    const formHtml = generateFormHtml(config.fields);
    document.getElementById('toolForm').innerHTML = formHtml;
    
    // Add event listeners for dynamic fields (dependsOn)
    config.fields.forEach(f => {
        if (f.dependsOn) {
            const parentEl = document.getElementById(`field_${f.dependsOn.field}`);
            if (parentEl) {
                parentEl.addEventListener('change', () => {
                    const wrap = document.getElementById(`wrap_${f.name}`);
                    if (parentEl.value === f.dependsOn.value) wrap.classList.remove('hidden');
                    else wrap.classList.add('hidden');
                });
                // initial trigger
                parentEl.dispatchEvent(new Event('change'));
            }
        }
    });

    document.getElementById('toolControlPanel').classList.remove('hidden');
}

function generateFormHtml(fields) {
    if (fields.length === 0) return `<p class="text-sm text-stone-500 dark:text-stone-400">No configuration needed. Click add to pipeline.</p>`;
    
    return fields.map(f => {
        let inputHtml = '';
        const isHidden = f.dependsOn ? 'hidden' : '';
        
        if (f.type === 'select') {
            let options = [];
            if (f.options === 'COLUMNS') options = window.APP_DATA.columns;
            else options = f.options;
            
            const optsHtml = options.map(o => {
                const val = typeof o === 'string' && o === 'ALL' ? '' : o;
                const label = typeof o === 'string' ? o : o;
                return `<option value="${val}">${label}</option>`;
            }).join('');
            
            inputHtml = `<select id="field_${f.name}" class="w-full bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-700 rounded-lg px-3 py-2 text-sm text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-indigo-500 outline-none transition-all">${optsHtml}</select>`;
        } else {
            inputHtml = `<input type="${f.type}" id="field_${f.name}" class="w-full bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-700 rounded-lg px-3 py-2 text-sm text-stone-900 dark:text-stone-100 focus:ring-2 focus:ring-indigo-500 outline-none transition-all" placeholder="${f.label}">`;
        }
        
        return `
            <div id="wrap_${f.name}" class="${isHidden} flex flex-col gap-1.5">
                <label class="text-xs font-bold text-stone-700 dark:text-stone-300 uppercase tracking-wide">${f.label}</label>
                ${inputHtml}
            </div>
        `;
    }).join('');
}

function addStepToPipeline() {
    const config = toolConfigs[selectedTool];
    const params = {};
    
    let valid = true;
    config.fields.forEach(f => {
        const wrap = document.getElementById(`wrap_${f.name}`);
        if (!wrap.classList.contains('hidden')) {
            const val = document.getElementById(`field_${f.name}`).value;
            params[f.name] = val;
            if (!val && f.type !== 'select' && f.options !== 'ALL') valid = false; // crude validation
        }
    });

    currentPipeline.push({
        operation: selectedTool,
        params: params,
        label: config.label
    });

    document.getElementById('toolControlPanel').classList.add('hidden');
    selectedTool = null;
    
    renderPipelinePills();
    runPreview();
}

function renderPipelinePills() {
    const container = document.getElementById('pipelinePills');
    const msg = document.getElementById('emptyPipelineMsg');
    
    if (currentPipeline.length === 0) {
        container.innerHTML = '';
        msg.classList.remove('hidden');
        return;
    }
    
    msg.classList.add('hidden');
    container.innerHTML = currentPipeline.map((step, idx) => `
        <div class="flex items-center gap-1.5 bg-indigo-50 dark:bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 px-3 py-1.5 rounded-lg border border-indigo-200 dark:border-indigo-500/30 text-xs font-semibold animate-pop-in">
            <span class="w-4 h-4 rounded-full bg-indigo-500 text-white flex items-center justify-center text-[10px]">${idx + 1}</span>
            ${step.label}
            <button onclick="removeStep(${idx})" class="ml-1 text-indigo-400 hover:text-indigo-600 dark:hover:text-indigo-200">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
        </div>
    `).join('');
}

window.removeStep = function(idx) {
    currentPipeline.splice(idx, 1);
    renderPipelinePills();
    runPreview();
};

// ────────────────────────────────────────────────────────────
// PREVIEW ENGINE
// ────────────────────────────────────────────────────────────

function getCsrfToken() {
    return document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1] || '';
}

async function runPreview() {
    if (currentPipeline.length === 0) {
        renderInitialBeforeTable();
        return;
    }

    const loading = document.getElementById('previewLoading');
    loading.classList.remove('hidden');

    try {
        const response = await fetch(`/dataset/${window.APP_DATA.FILE_ID}/api/preview-cleaning/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
            body: JSON.stringify({ pipeline: currentPipeline })
        });

        const data = await response.json();
        if (data.status === 'success') {
            renderTable('tableAfter', data.after_columns, data.after);
            document.getElementById('previewStatsAfter').textContent = `Preview: ${data.after.length} rows, ${data.after_columns.length} cols`;
            document.getElementById('tabAfter').click(); // switch to after tab
        } else {
            console.error(data.error);
        }
    } catch (e) {
        console.error('Preview error', e);
    } finally {
        loading.classList.add('hidden');
    }
}

function renderInitialBeforeTable() {
    renderTable('tableBefore', window.APP_DATA.columns, window.APP_DATA.rawSnapshot);
    document.getElementById('previewStatsBefore').textContent = `Original: ${window.APP_DATA.rawSnapshot.length} rows`;
    
    // reset after
    document.getElementById('theadAfter').innerHTML = '';
    document.getElementById('tbodyAfter').innerHTML = `<tr><td class="p-10 text-center text-stone-500">Add steps to see preview</td></tr>`;
    document.getElementById('previewStatsAfter').textContent = `Preview: 0 rows`;
    document.getElementById('tabBefore').click();
}

function renderTable(tableId, cols, rows) {
    const tableDiv = document.getElementById(tableId);
    const thead = tableDiv.querySelector('thead');
    const tbody = tableDiv.querySelector('tbody');

    thead.innerHTML = `<tr>${cols.map(c => `<th class="px-4 py-3 text-xs font-bold text-stone-500 dark:text-stone-400 uppercase tracking-wider whitespace-nowrap">${c}</th>`).join('')}</tr>`;
    
    if (rows.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${cols.length}" class="p-10 text-center text-stone-500">No data</td></tr>`;
        return;
    }

    tbody.innerHTML = rows.map((r, i) => `
        <tr class="hover:bg-stone-50 dark:hover:bg-stone-800/50 transition-colors">
            ${cols.map(c => `<td class="px-4 py-2.5 whitespace-nowrap text-stone-900 dark:text-stone-200">${r[c] !== null && r[c] !== undefined ? r[c] : '<span class="text-stone-400">—</span>'}</td>`).join('')}
        </tr>
    `).join('');
}

function initTabs() {
    const tabBefore = document.getElementById('tabBefore');
    const tabAfter = document.getElementById('tabAfter');
    const tableBefore = document.getElementById('tableBefore');
    const tableAfter = document.getElementById('tableAfter');

    tabBefore.addEventListener('click', () => {
        tableBefore.classList.remove('hidden');
        tableAfter.classList.add('hidden');
        tabBefore.classList.add('text-stone-900', 'dark:text-stone-100', 'border-stone-800', 'dark:border-stone-200');
        tabBefore.classList.remove('text-stone-500', 'dark:text-stone-400', 'border-transparent');
        tabAfter.classList.remove('text-indigo-600', 'dark:text-indigo-400', 'border-indigo-500');
        tabAfter.classList.add('text-stone-500', 'dark:text-stone-400', 'border-transparent');
    });

    tabAfter.addEventListener('click', () => {
        tableAfter.classList.remove('hidden');
        tableBefore.classList.add('hidden');
        tabAfter.classList.add('text-indigo-600', 'dark:text-indigo-400', 'border-indigo-500');
        tabAfter.classList.remove('text-stone-500', 'dark:text-stone-400', 'border-transparent');
        tabBefore.classList.remove('text-stone-900', 'dark:text-stone-100', 'border-stone-800', 'dark:border-stone-200');
        tabBefore.classList.add('text-stone-500', 'dark:text-stone-400', 'border-transparent');
    });
}

// ────────────────────────────────────────────────────────────
// APPLY ENGINE
// ────────────────────────────────────────────────────────────

function initApplyButton() {
    const btn = document.getElementById('applyPipelineBtn');
    btn.addEventListener('click', async () => {
        if (currentPipeline.length === 0) {
            alert('Your pipeline is empty.');
            return;
        }

        btn.disabled = true;
        btn.innerHTML = `<svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg> Applying to Full Dataset...`;

        try {
            const response = await fetch(`/dataset/${window.APP_DATA.FILE_ID}/api/apply-cleaning/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
                body: JSON.stringify({ pipeline: currentPipeline })
            });

            const data = await response.json();
            if (data.status === 'success') {
                window.location.href = `/dataset/${window.APP_DATA.FILE_ID}/explorer/`; // Redirect to explorer to view results
            } else {
                alert('Error: ' + data.error);
                btn.disabled = false;
                btn.innerHTML = `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg> Apply to Dataset`;
            }
        } catch (e) {
            console.error(e);
            alert('Network error while applying pipeline.');
            btn.disabled = false;
            btn.innerHTML = `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg> Apply to Dataset`;
        }
    });
}
