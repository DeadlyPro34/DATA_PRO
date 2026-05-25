// profiler.js
function initProfiler() {
    const statsColEl = document.getElementById('statsColumn');
    const statsGrid  = document.getElementById('statsGrid');
    if (!statsColEl || !statsGrid) return;
    
    const APP_DATA = window.APP_DATA || {};
    
    // We expect the backend to pass APP_DATA.stats, which is a dictionary of precomputed stats per column.
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
        return;
    }
    
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
        blue:   'bg-blue-500/10 border-blue-500/20 text-blue-400',
        orange: 'bg-orange-500/10 border-orange-500/20 text-orange-400',
        amber:  'bg-amber-500/10 border-amber-500/20 text-amber-400',
        emerald:'bg-emerald-500/10 border-emerald-500/20 text-emerald-400',
        sky:    'bg-sky-500/10 border-sky-500/20 text-sky-400',
        rose:   'bg-rose-500/10 border-rose-500/20 text-rose-400',
        violet: 'bg-violet-500/10 border-violet-500/20 text-violet-400',
        pink:   'bg-pink-500/10 border-pink-500/20 text-pink-400',
    };
    
    function renderStats(col) {
        if (!col || !stats[col]) return;
        const s = stats[col];
        
        statsGrid.innerHTML = STAT_DEFS.map(d => {
            const val = s[d.key];
            const fmtVal = window.fmtNum ? window.fmtNum(val) : val;
            return `
            <div class="bg-stone-900/60 border border-stone-800 rounded-2xl p-4 flex flex-col gap-1 hover:border-stone-700 transition-colors">
                <div class="flex items-center justify-between mb-1">
                    <span class="text-xs font-bold text-stone-500 uppercase tracking-wider">${d.label}</span>
                    <span class="w-6 h-6 rounded-lg border flex items-center justify-center text-xs font-bold ${CLR[d.clr]}">${d.sym}</span>
                </div>
                <span class="text-lg font-bold text-stone-100 leading-none truncate" title="${val}">${fmtVal}</span>
            </div>`;
        }).join('');
    }
    
    statsColEl.addEventListener('change', () => renderStats(statsColEl.value));
    renderStats(numericCols[0]);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initProfiler);
} else {
    initProfiler();
}
