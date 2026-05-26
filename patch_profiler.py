import os
import re

filepath = 'app/templates/data_profiler.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the HTML for Quick Math Calculator with Column Data Extractor
old_ui_start = content.find('<div class="glass-panel rounded-3xl p-6 mb-8 relative overflow-hidden animate-pop-in" style="animation-delay: 50ms;">')
old_ui_end = content.find('<div class="glass-panel rounded-3xl p-6 mb-8 relative overflow-hidden animate-pop-in" style="animation-delay: 100ms;">')

new_ui = '''<div class="glass-panel rounded-3xl p-6 mb-8 relative overflow-hidden animate-pop-in" style="animation-delay: 50ms;">
    <div class="flex items-center gap-3 mb-6 relative z-10">
        <div class="p-2 rounded-xl bg-orange-500/20 text-orange-500 border border-orange-500/20">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path></svg>
        </div>
        <h2 class="text-xl font-bold text-stone-950 dark:text-stone-100 tracking-tight">Column Data Extractor</h2>
    </div>
    
    <div class="flex flex-col gap-6 relative z-10">
        <div>
            <label class="block text-xs font-bold text-stone-700 dark:text-stone-400 uppercase tracking-wider mb-2">Select Any Column to Extract Data</label>
            <select id="extractorColSelect" class="w-full max-w-md bg-stone-50 dark:bg-stone-900 border border-stone-300 dark:border-stone-800 rounded-xl px-4 py-3 text-sm text-stone-950 dark:text-stone-100 focus:outline-none focus:border-orange-500 transition-colors">
                <option value="">-- Select a column --</option>
            </select>
        </div>
        
        <!-- Stats Area -->
        <div id="extractorStats" class="hidden grid-cols-2 lg:grid-cols-5 gap-4">
            <!-- Filled dynamically -->
        </div>
        
        <!-- Data Table Area -->
        <div id="extractorTableContainer" class="hidden flex-col gap-3 mt-2">
            <div class="flex justify-between items-center">
                <h3 class="text-sm font-bold text-stone-950 dark:text-stone-200">Extracted Column Data (Showing top 1000 rows)</h3>
            </div>
            <div class="w-full bg-stone-50 dark:bg-stone-900/50 border border-stone-300 dark:border-stone-800 rounded-xl overflow-hidden">
                <div class="max-h-[350px] overflow-y-auto" id="extractorScrollWrapper">
                    <table class="w-full text-left text-sm text-stone-700 dark:text-stone-400">
                        <thead class="text-xs text-stone-950 dark:text-stone-300 bg-stone-100 dark:bg-stone-800/80 sticky top-0 uppercase z-10">
                            <tr>
                                <th class="px-4 py-3 border-b border-stone-300 dark:border-stone-700 font-bold w-16">Row</th>
                                <th class="px-4 py-3 border-b border-stone-300 dark:border-stone-700 font-bold" id="extractorTableHead">Value</th>
                            </tr>
                        </thead>
                        <tbody id="extractorTableBody" class="divide-y divide-stone-200 dark:divide-stone-800">
                            <!-- Rows populated by JS -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>

'''

content = content[:old_ui_start] + new_ui + content[old_ui_end:]

# First, clean up the previous mathSelect logic inside grid.innerHTML map loop
start_cleanup = content.find("const mathSelect = document.getElementById('quickMathColSelect');")
if start_cleanup != -1:
    end_cleanup = content.find('const badges = [];', start_cleanup)
    content = content[:start_cleanup] + content[end_cleanup:]


# Now replace from '// Quick Math Logic' down
qm_start = content.find('// Quick Math Logic')
if qm_start != -1:
    new_js = """    // Extractor Logic
    document.addEventListener('appDataLoaded', () => {
        const extractorSelect = document.getElementById('extractorColSelect');
        const statsContainer = document.getElementById('extractorStats');
        const tableContainer = document.getElementById('extractorTableContainer');
        const tableHead = document.getElementById('extractorTableHead');
        const tableBody = document.getElementById('extractorTableBody');
        
        // Populate all columns
        columns.forEach(col => {
            const opt = document.createElement('option');
            opt.value = col;
            opt.textContent = col;
            extractorSelect.appendChild(opt);
        });
        
        extractorSelect.addEventListener('change', () => {
            const col = extractorSelect.value;
            if (!col || !window.APP_DATA || !window.APP_DATA.allRows || window.APP_DATA.allRows.length === 0) {
                statsContainer.classList.add('hidden');
                statsContainer.classList.remove('grid');
                tableContainer.classList.add('hidden');
                tableContainer.classList.remove('flex');
                return;
            }
            
            statsContainer.classList.remove('hidden');
            statsContainer.classList.add('grid');
            tableContainer.classList.remove('hidden');
            tableContainer.classList.add('flex');
            
            const colStats = stats[col] || {};
            const isNumeric = colStats.mean !== undefined;
            const fmt = (num) => typeof num === 'number' ? num.toLocaleString(undefined, { maximumFractionDigits: 3 }) : num;
            
            if (isNumeric) {
                // Extract numeric values, ignoring nulls and NaNs
                let values = window.APP_DATA.allRows.map(row => Number(row[col])).filter(val => !isNaN(val));
                let sum = values.length > 0 ? values.reduce((a, b) => a + b, 0) : 0;
                let avg = values.length > 0 ? sum / values.length : 0;
                let min = values.length > 0 ? Math.min(...values) : 0;
                let max = values.length > 0 ? Math.max(...values) : 0;
                
                let median = 0;
                if (values.length > 0) {
                    values.sort((a, b) => a - b);
                    const mid = Math.floor(values.length / 2);
                    median = values.length % 2 !== 0 ? values[mid] : (values[mid - 1] + values[mid]) / 2;
                }
                
                statsContainer.innerHTML = `
                    <div class="bg-stone-50 dark:bg-stone-900/50 rounded-xl p-4 border border-stone-300 dark:border-stone-800"><div class="text-stone-700 dark:text-stone-500 text-xs font-bold mb-1">Sum</div><div class="text-stone-950 dark:text-stone-200 font-mono text-lg font-semibold">${fmt(sum)}</div></div>
                    <div class="bg-stone-50 dark:bg-stone-900/50 rounded-xl p-4 border border-stone-300 dark:border-stone-800"><div class="text-stone-700 dark:text-stone-500 text-xs font-bold mb-1">Average</div><div class="text-stone-950 dark:text-stone-200 font-mono text-lg font-semibold">${fmt(avg)}</div></div>
                    <div class="bg-stone-50 dark:bg-stone-900/50 rounded-xl p-4 border border-stone-300 dark:border-stone-800"><div class="text-stone-700 dark:text-stone-500 text-xs font-bold mb-1">Minimum</div><div class="text-stone-950 dark:text-stone-200 font-mono text-lg font-semibold">${fmt(min)}</div></div>
                    <div class="bg-stone-50 dark:bg-stone-900/50 rounded-xl p-4 border border-stone-300 dark:border-stone-800"><div class="text-stone-700 dark:text-stone-500 text-xs font-bold mb-1">Maximum</div><div class="text-stone-950 dark:text-stone-200 font-mono text-lg font-semibold">${fmt(max)}</div></div>
                    <div class="bg-stone-50 dark:bg-stone-900/50 rounded-xl p-4 border border-stone-300 dark:border-stone-800"><div class="text-stone-700 dark:text-stone-500 text-xs font-bold mb-1">Median</div><div class="text-stone-950 dark:text-stone-200 font-mono text-lg font-semibold">${fmt(median)}</div></div>
                `;
            } else {
                statsContainer.innerHTML = `
                    <div class="bg-stone-50 dark:bg-stone-900/50 rounded-xl p-4 border border-stone-300 dark:border-stone-800 col-span-2 lg:col-span-1"><div class="text-stone-700 dark:text-stone-500 text-xs font-bold mb-1">Unique Values</div><div class="text-stone-950 dark:text-stone-200 font-mono text-lg font-semibold">${fmt(colStats.unique || colStats.nunique || '--')}</div></div>
                    <div class="bg-stone-50 dark:bg-stone-900/50 rounded-xl p-4 border border-stone-300 dark:border-stone-800 col-span-2 lg:col-span-2"><div class="text-stone-700 dark:text-stone-500 text-xs font-bold mb-1">Most Frequent (Top Value)</div><div class="text-stone-950 dark:text-stone-200 font-mono text-lg font-semibold truncate" title="${colStats.top || ''}">${colStats.top || '--'}</div></div>
                    <div class="bg-stone-50 dark:bg-stone-900/50 rounded-xl p-4 border border-stone-300 dark:border-stone-800 col-span-2 lg:col-span-2"><div class="text-stone-700 dark:text-stone-500 text-xs font-bold mb-1">Frequency of Top</div><div class="text-stone-950 dark:text-stone-200 font-mono text-lg font-semibold">${fmt(colStats.freq || '--')}</div></div>
                `;
            }
            
            // Render Table
            tableHead.textContent = col.toUpperCase();
            
            // Virtualize or limit to 1000 rows
            const rowsToRender = window.APP_DATA.allRows.slice(0, 1000);
            
            tableBody.innerHTML = rowsToRender.map((row, idx) => {
                const val = row[col];
                const displayVal = val !== null && val !== undefined ? String(val).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;') : '<span class="text-stone-500 italic">null</span>';
                return `<tr class="hover:bg-stone-200/50 dark:hover:bg-stone-800/80 transition-colors">
                    <td class="px-4 py-2 border-b border-stone-200 dark:border-stone-800/50 font-mono text-xs text-stone-500">${idx + 1}</td>
                    <td class="px-4 py-2 border-b border-stone-200 dark:border-stone-800/50 font-mono text-sm text-stone-950 dark:text-stone-300 truncate max-w-xl">${displayVal}</td>
                </tr>`;
            }).join('');
        });
    });
</script>
{% endblock %}"""
    content = content[:qm_start] + new_js

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated data_profiler.html to Column Extractor.')
