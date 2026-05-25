// explorer.js
document.addEventListener('DOMContentLoaded', function() {
    if (!document.getElementById('singleTableView')) return;
    const APP_DATA = window.APP_DATA || {};
    
    // ════════════════════════════════════════════════════════════════════════════
    // 1. STATE & ELEMENTS
    // ════════════════════════════════════════════════════════════════════════════
    let currentTab = 'raw';
    let filteredRows = [];
    let currentPage  = 1;
    const rowsPerPage = 50;
    let sortCol = null, sortAsc = true;
    
    const tableHeader  = document.getElementById('tableHeader');
    const tableBody    = document.getElementById('tableBody');
    const searchInput  = document.getElementById('searchInput');
    const prevPageBtn  = document.getElementById('prevPage');
    const nextPageBtn  = document.getElementById('nextPage');
    const pageInfoEl   = document.getElementById('pageInfo');
    const showingCount = document.getElementById('showingCount');
    const singleTableView = document.getElementById('singleTableView');
    const sideBySideView  = document.getElementById('sideBySideView');
    
    if (!APP_DATA.rawSnapshot || APP_DATA.rawSnapshot.length === 0) {
        currentTab = 'cleaned';
    }
    
    // ════════════════════════════════════════════════════════════════════════════
    // 2. TAB SWITCHING
    // ════════════════════════════════════════════════════════════════════════════
    function switchDataTab(tab) {
        currentTab = tab;
        
        document.querySelectorAll('.data-tab').forEach(el => {
            el.classList.remove('active', 'text-orange-400');
            el.classList.add('text-stone-400');
            if (el.dataset.tab === tab) {
                el.classList.add('active', 'text-orange-400');
                el.classList.remove('text-stone-400');
            }
        });
        
        if (tab === 'sidebyside') {
            singleTableView.classList.add('hidden');
            sideBySideView.classList.remove('hidden');
            renderSideBySide();
        } else {
            singleTableView.classList.remove('hidden');
            sideBySideView.classList.add('hidden');
            
            filteredRows = tab === 'raw' ? [...(APP_DATA.rawSnapshot || [])] : [...(APP_DATA.allRows || [])];
            if (searchInput && searchInput.value) {
                doSearch(searchInput.value);
            } else {
                renderTable();
            }
        }
    }
    
    document.querySelectorAll('.data-tab').forEach(btn => {
        btn.addEventListener('click', (e) => {
            switchDataTab(e.currentTarget.dataset.tab);
        });
    });

    // ════════════════════════════════════════════════════════════════════════════
    // 3. TABLE RENDERING
    // ════════════════════════════════════════════════════════════════════════════
    function renderTable() {
        const isRaw = currentTab === 'raw';
        const cols = isRaw ? (APP_DATA.rawColumns || []) : (APP_DATA.columns || []);
        const annots = APP_DATA.cellAnnotations ? (APP_DATA.cellAnnotations[isRaw ? 'raw' : 'cleaned'] || {}) : {};
        
        // Render Header
        tableHeader.innerHTML = cols.map(col => `
            <th scope="col" class="px-6 py-4 text-left text-xs font-bold text-stone-400 uppercase tracking-widest cursor-pointer hover:bg-stone-800 transition-colors group whitespace-nowrap" data-col="${col.replace(/'/g,"\\'").replace(/"/g,"&quot;")}">
                <div class="flex items-center gap-2">
                    ${col}
                    <span class="text-orange-500 transition-opacity ${sortCol===col?'opacity-100':'opacity-0 group-hover:opacity-50'}">
                        ${sortCol===col?(sortAsc?'↑':'↓'):'↕'}
                    </span>
                </div>
            </th>`).join('');
            
        // Attach Sort Listeners
        tableHeader.querySelectorAll('th').forEach(th => {
            th.addEventListener('click', () => sortTable(th.dataset.col));
        });
    
        const totalPages = Math.ceil(filteredRows.length / rowsPerPage) || 1;
        if (currentPage > totalPages) currentPage = totalPages;
        const start   = (currentPage - 1) * rowsPerPage;
        const pageData = filteredRows.slice(start, start + rowsPerPage);
    
        // Render Body
        if (pageData.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="${cols.length}" class="px-6 py-12 text-center text-stone-500">No data found</td></tr>`;
        } else {
            tableBody.innerHTML = pageData.map((row, idx) => {
                const globalIdx = start + idx;
                const isDuplicate = isRaw && APP_DATA.cellAnnotations?.duplicate_row_indices?.includes(globalIdx);
                let rowClass = `hover:bg-stone-800/30 transition-colors duration-150 ${idx%2===0?'':'bg-stone-900/30'}`;
                if (isDuplicate) rowClass += ' bg-amber-500/10 hover:bg-amber-500/20';
        
                return `<tr class="${rowClass}">
                    ${cols.map((col, colIdx) => {
                        const v = row[col];
                        const display = (v !== null && v !== undefined) ? String(v) : '<span class="text-stone-600">—</span>';
                        const issue = annots[`${globalIdx},${colIdx}`];
                        
                        let cellClass = 'px-6 py-3 whitespace-nowrap text-stone-300';
                        if (issue === 'missing') cellClass += ' bg-red-500/20 text-red-300 font-medium border border-red-500/30';
                        if (issue === 'fixed') cellClass += ' bg-blue-500/20 text-blue-300 font-medium border border-blue-500/30';
                        if (issue === 'outlier') cellClass += ' bg-purple-500/20 text-purple-300 font-medium border border-purple-500/30';
        
                        return `<td class="${cellClass}">${display}</td>`;
                    }).join('')}
                </tr>`;
            }).join('');
        }
    
        if (pageInfoEl) pageInfoEl.textContent   = `Page ${currentPage} of ${totalPages}`;
        if (showingCount) showingCount.textContent = `Showing ${pageData.length} of ${filteredRows.length} rows`;
        if (prevPageBtn) prevPageBtn.disabled = currentPage === 1;
        if (nextPageBtn) nextPageBtn.disabled = currentPage === totalPages;
    }
    
    function sortTable(col) {
        if (currentTab === 'sidebyside') return;
        if (sortCol === col) sortAsc = !sortAsc; else { sortCol = col; sortAsc = true; }
        filteredRows.sort((a, b) => {
            let vA = a[col] ?? '', vB = b[col] ?? '';
            if (typeof vA === 'number' && typeof vB === 'number') return sortAsc ? vA-vB : vB-vA;
            return sortAsc ? String(vA).localeCompare(String(vB)) : String(vB).localeCompare(String(vA));
        });
        renderTable();
    }
    
    function doSearch(term) {
        const isRaw = currentTab === 'raw';
        const data = isRaw ? (APP_DATA.rawSnapshot || []) : (APP_DATA.allRows || []);
        const cols = isRaw ? (APP_DATA.rawColumns || []) : (APP_DATA.columns || []);
        term = term.toLowerCase();
        filteredRows = data.filter(row => cols.some(col => String(row[col]??'').toLowerCase().includes(term)));
        currentPage = 1; 
        renderTable();
    }
    
    if (searchInput) {
        searchInput.addEventListener('input', e => {
            if (currentTab === 'sidebyside') return;
            doSearch(e.target.value);
        });
    }

    if (prevPageBtn) prevPageBtn.addEventListener('click', () => { if (currentPage > 1) { currentPage--; renderTable(); } });
    if (nextPageBtn) nextPageBtn.addEventListener('click', () => { const tp = Math.ceil(filteredRows.length/rowsPerPage); if (currentPage < tp) { currentPage++; renderTable(); } });
    
    // ════════════════════════════════════════════════════════════════════════════
    // 4. SIDE BY SIDE VIEW
    // ════════════════════════════════════════════════════════════════════════════
    function renderSideBySide() {
        const rawHead = document.getElementById('rawSbsHeader');
        const rawBody = document.getElementById('rawSbsBody');
        
        if (rawHead && APP_DATA.rawColumns) {
            rawHead.innerHTML = APP_DATA.rawColumns.map(col => `<th class="px-3 py-2 text-left text-xs font-bold text-stone-400 uppercase tracking-widest whitespace-nowrap">${col}</th>`).join('');
        }
        
        if (rawBody && APP_DATA.rawSnapshot) {
            rawBody.innerHTML = APP_DATA.rawSnapshot.slice(0, 100).map((row, idx) => {
                const isDuplicate = APP_DATA.cellAnnotations?.duplicate_row_indices?.includes(idx);
                let rowClass = `hover:bg-stone-800/30 ${idx%2===0?'':'bg-stone-900/30'}`;
                if (isDuplicate) rowClass += ' bg-amber-500/10';
                return `<tr class="${rowClass}">
                    ${APP_DATA.rawColumns.map((col, colIdx) => {
                        const issue = (APP_DATA.cellAnnotations?.['raw'] || {})[`${idx},${colIdx}`];
                        let cellClass = 'px-3 py-1.5 whitespace-nowrap text-stone-300 text-xs';
                        if (issue === 'missing') cellClass += ' bg-red-500/20 text-red-300 border border-red-500/30';
                        const v = row[col];
                        return `<td class="${cellClass}">${v !== null && v !== undefined ? v : '—'}</td>`;
                    }).join('')}
                </tr>`;
            }).join('');
        }
    
        const clnHead = document.getElementById('cleanedSbsHeader');
        const clnBody = document.getElementById('cleanedSbsBody');
        
        if (clnHead && APP_DATA.columns) {
            clnHead.innerHTML = APP_DATA.columns.map(col => `<th class="px-3 py-2 text-left text-xs font-bold text-stone-400 uppercase tracking-widest whitespace-nowrap">${col}</th>`).join('');
        }
        
        if (clnBody && APP_DATA.allRows) {
            clnBody.innerHTML = APP_DATA.allRows.slice(0, 100).map((row, idx) => {
                return `<tr class="hover:bg-stone-800/30 ${idx%2===0?'':'bg-stone-900/30'}">
                    ${APP_DATA.columns.map((col, colIdx) => {
                        const issue = (APP_DATA.cellAnnotations?.['cleaned'] || {})[`${idx},${colIdx}`];
                        let cellClass = 'px-3 py-1.5 whitespace-nowrap text-stone-300 text-xs';
                        if (issue === 'fixed') cellClass += ' bg-blue-500/20 text-blue-300 border border-blue-500/30';
                        if (issue === 'outlier') cellClass += ' bg-purple-500/20 text-purple-300 border border-purple-500/30';
                        const v = row[col];
                        return `<td class="${cellClass}">${v !== null && v !== undefined ? v : '—'}</td>`;
                    }).join('')}
                </tr>`;
            }).join('');
        }
        
        if (showingCount) showingCount.textContent = `Showing top 100 rows (Side-by-Side)`;
        if (prevPageBtn) prevPageBtn.disabled = true;
        if (nextPageBtn) nextPageBtn.disabled = true;
    }
    
    // INITIALIZATION
    switchDataTab(APP_DATA.rawSnapshot && APP_DATA.rawSnapshot.length > 0 ? 'raw' : 'cleaned');
});
