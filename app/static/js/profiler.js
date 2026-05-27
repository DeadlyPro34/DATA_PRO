// profiler.js
function initProfiler() {
    const statsColEl = document.getElementById('statsColumn');
    const statsGrid  = document.getElementById('statsGrid');
    const contextLabel = document.getElementById('statsContextLabel');
    if (!statsColEl || !statsGrid) return;
    
    const APP_DATA = window.APP_DATA || {};
    
    // We expect the backend to pass APP_DATA.stats, which is a dictionary of precomputed stats per column.
    // We will use this only to find out WHICH columns are numeric.
    const stats = APP_DATA.stats || {};
    
    // Filter numeric columns
    const numericCols = APP_DATA.columns?.filter(col => {
        return stats[col] && stats[col].mean !== undefined && stats[col].mean !== null;
    }) || [];
    
    // Populate dropdown
    numericCols.forEach(col => statsColEl.add(new Option(col, col)));
    
    if (!numericCols.length) {
        statsColEl.add(new Option('No numeric columns', ''));
        statsColEl.disabled = true;
        statsGrid.innerHTML = '<p class="text-stone-500 text-sm col-span-full text-center py-4">Upload a file with numeric columns to see statistics.</p>';
        if(contextLabel) contextLabel.textContent = 'No context available';
        return;
    }
    
    let currentContextRows = APP_DATA.allRows || [];
    let selectedRowData = null;

    document.addEventListener('rowsFiltered', (e) => {
        currentContextRows = e.detail || APP_DATA.allRows || [];
        renderStats(statsColEl.value);
    });

    document.addEventListener('rowSelected', (e) => {
        selectedRowData = e.detail;
        renderStats(statsColEl.value);
    });

    const STAT_DEFS = [
        { key:'count',    label:'Count',    sym:'#',  clr:'blue'   },
        { key:'sum',      label:'Sum',      sym:'Σ',  clr:'orange' },
        { key:'mean',     label:'Mean',     sym:'μ',  clr:'amber'  },
        { key:'median',   label:'Median',   sym:'M',  clr:'emerald'},
        { key:'min',      label:'Min',      sym:'↓',  clr:'sky'    },
        { key:'max',      label:'Max',      sym:'↑',  clr:'rose'   },
        { key:'std',      label:'Std Dev',  sym:'σ',  clr:'violet' },
        { key:'variance', label:'Variance', sym:'σ²', clr:'pink'   },
    ];
    
    const CLR = {
        blue:   'bg-blue-500/10 border-blue-500/20 text-blue-600 dark:text-blue-400',
        orange: 'bg-orange-500/10 border-orange-500/20 text-orange-600 dark:text-orange-400',
        amber:  'bg-amber-500/10 border-amber-500/20 text-amber-600 dark:text-amber-400',
        emerald:'bg-emerald-500/10 border-emerald-500/20 text-emerald-600 dark:text-emerald-400',
        sky:    'bg-sky-500/10 border-sky-500/20 text-sky-600 dark:text-sky-400',
        rose:   'bg-rose-500/10 border-rose-500/20 text-rose-600 dark:text-rose-400',
        violet: 'bg-violet-500/10 border-violet-500/20 text-violet-600 dark:text-violet-400',
        pink:   'bg-pink-500/10 border-pink-500/20 text-pink-600 dark:text-pink-400',
    };
    
    function renderStats(col) {
        if (!col) return;
        
        // Determine the array of numeric values to compute on
        let targetRows = selectedRowData ? [selectedRowData] : currentContextRows;
        // Coerce values to numbers first — JSON rows may contain numeric strings (e.g. "42.5")
        let rowVals = targetRows
            .map(row => { const v = row[col]; return (v === null || v === undefined || v === '') ? NaN : parseFloat(v); })
            .filter(v => !isNaN(v) && isFinite(v));
        
        // Update Label
        if (contextLabel) {
            if (selectedRowData) {
                contextLabel.innerHTML = `Calculating for <b class="text-stone-900 dark:text-stone-200">Selected Row</b>`;
            } else if (targetRows.length === (APP_DATA.allRows || []).length) {
                contextLabel.innerHTML = `Calculating for <b class="text-stone-900 dark:text-stone-200">Full Dataset</b> (${targetRows.length.toLocaleString()} rows)`;
            } else {
                contextLabel.innerHTML = `Calculating for <b class="text-stone-900 dark:text-stone-200">Filtered Data</b> (${targetRows.length.toLocaleString()} rows)`;
            }
        }

        // Compute statistics dynamically
        let count = rowVals.length;
        let sum = rowVals.reduce((a, b) => a + b, 0);
        let mean = count > 0 ? sum / count : 0;
        let min = count > 0 ? Math.min(...rowVals) : 0;
        let max = count > 0 ? Math.max(...rowVals) : 0;
        
        let median = 0;
        if (count > 0) {
            const sorted = [...rowVals].sort((a, b) => a - b);
            const mid = Math.floor(sorted.length / 2);
            median = sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
        }

        let variance = 0;
        let std = 0;
        if (count > 1) {
            const meanVal = sum / count;
            const sqDiffs = rowVals.map(v => (v - meanVal) ** 2);
            variance = sqDiffs.reduce((a, b) => a + b, 0) / (count - 1); // Sample variance
            std = Math.sqrt(variance);
        }

        const computedStats = {
            count: count,
            sum: count > 0 ? sum : '—',
            mean: count > 0 ? mean : '—',
            median: count > 0 ? median : '—',
            min: count > 0 ? min : '—',
            max: count > 0 ? max : '—',
            std: count > 1 ? std : '—',
            variance: count > 1 ? variance : '—'
        };

        statsGrid.innerHTML = STAT_DEFS.map(d => {
            let val = computedStats[d.key];
            const fmtVal = val === '—' ? val : (window.fmtNum ? window.fmtNum(val) : val);
            return `
            <div class="bg-white dark:bg-stone-900/60 border border-stone-200 dark:border-stone-800 rounded-2xl p-4 flex flex-col gap-1 hover:border-stone-300 dark:hover:border-stone-700 transition-colors shadow-sm dark:shadow-none animate-fade-in" style="animation-duration: 200ms">
                <div class="flex items-center justify-between mb-1">
                    <span class="text-xs font-bold text-stone-500 uppercase tracking-wider">${d.label}</span>
                    <span class="w-6 h-6 rounded-lg border flex items-center justify-center text-xs font-bold ${CLR[d.clr]}">${d.sym}</span>
                </div>
                <span class="text-lg font-bold text-stone-950 dark:text-stone-100 leading-none truncate" title="${val !== null && val !== undefined ? val : ''}">${fmtVal}</span>
            </div>`;
        }).join('');
    }
    
    statsColEl.addEventListener('change', () => renderStats(statsColEl.value));
    renderStats(numericCols[0]);
}

document.addEventListener('appDataLoaded', initProfiler);
