// analytics.js
document.addEventListener("DOMContentLoaded", function () {
    console.log("Analytics Studio initialized");
    
    populateDropdown("xAxis");
    populateDropdown("yAxis");
    populateDropdown("filterColumn");

    const renderChartBtn = document.getElementById("renderChartBtn");
    if (renderChartBtn) {
        renderChartBtn.addEventListener("click", renderChart);
    }
});

function populateDropdown(selectId) {
    const select = document.getElementById(selectId);
    if (!select) return;

    if (typeof columns === 'undefined' || !columns || columns.length === 0) return;

    columns.forEach(column => {
        const option = document.createElement("option");
        option.value = column;
        option.textContent = column;
        select.appendChild(option);
function initAnalytics() {
    const APP_DATA = window.APP_DATA || {};
    const columns = APP_DATA.columns || [];
    const uniqueColumns = APP_DATA.uniqueColumns || [];
    const allRows = APP_DATA.allRows || [];
    const FILE_ID = APP_DATA.FILE_ID || '';
    const CHART_DATA_URL = APP_DATA.CHART_DATA_URL || `/dataset/${FILE_ID}/chart-data/`;

    // ── 1. COLUMN DETECTION ────────────────────────────────────────────────
    const numericCols = columns.filter(col =>
        allRows.some(r => r[col] !== null && r[col] !== undefined && typeof r[col] === 'number' && !isNaN(r[col]))
    );
    const dateCols = columns.filter(col => {
        const samples = allRows.slice(0, 30).map(r => r[col]).filter(v => v !== null && v !== undefined && v !== '');
        if (!samples.length) return false;
        const parseable = samples.filter(v => {
            const d = Date.parse(String(v));
            return !isNaN(d) && d > Date.parse('1900-01-01');
        });
        return parseable.length > samples.length * 0.6;
    });

let currentChart = null;

async function renderChart() {
    const chartType = document.getElementById("chartType").value;
    const xAxis = document.getElementById("xAxis").value;
    const yAxis = document.getElementById("yAxis").value;

    if (!chartType) {
        alert("Please select a Chart Type");
        return;
    }
    if (!xAxis) {
        alert("Please select an X-Axis");
        return;
    }
    if (!yAxis && chartType !== "pie") {
        alert("Please select a Y-Axis");
        return;
    }

    const renderChartBtn = document.getElementById("renderChartBtn");
    if (window.showLoadingState) window.showLoadingState(renderChartBtn);

    try {
        const chartDataUrl = window.APP_DATA?.CHART_DATA_URL || '';
        
        const payload = {
            chart_type: chartType,
            x_axis: xAxis,
            y_axes: yAxis ? [yAxis] : [],
            agg_mode: "sum",
            time_group: "",
            filters: [],
            top_n: 50
        };

        const csrf = window.getCsrfToken ? window.getCsrfToken() : '';
        const response = await fetch(chartDataUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf
            },
            body: JSON.stringify(payload)
    // ── 2. CHART REGISTRY ──────────────────────────────────────────────────
    const CHART_REGISTRY = [
        { id:'bar',           label:'Bar',           cat:'Basic',        engine:'chartjs',    needsX:true,  needsY:true,  icon:'📊' },
        { id:'column',        label:'Column',        cat:'Basic',        engine:'chartjs',    needsX:true,  needsY:true,  icon:'📊' },
        { id:'line',          label:'Line',          cat:'Basic',        engine:'chartjs',    needsX:true,  needsY:true,  icon:'📈' },
        { id:'area',          label:'Area',          cat:'Basic',        engine:'chartjs',    needsX:true,  needsY:true,  icon:'🏔️' },
        { id:'stepLine',      label:'Step Line',     cat:'Basic',        engine:'chartjs',    needsX:true,  needsY:true,  icon:'↗️' },
        { id:'scatter',       label:'Scatter',       cat:'Basic',        engine:'chartjs',    needsX:true,  needsY:true,  icon:'⚪' },
        { id:'bubble',        label:'Bubble',        cat:'Basic',        engine:'chartjs',    needsX:true,  needsY:true,  needsSize:true, icon:'🫧' },
        { id:'histogram',     label:'Histogram',     cat:'Distribution', engine:'plotly',     needsX:true,  needsY:false, needsBins:true, icon:'📉' },
        { id:'boxPlot',       label:'Box Plot',      cat:'Distribution', engine:'plotly',     needsX:false, needsY:true,  needsGroup:true, icon:'📦' },
        { id:'violin',        label:'Violin',        cat:'Distribution', engine:'plotly',     needsX:false, needsY:true,  needsGroup:true, icon:'🎻' },
        { id:'densityPlot',   label:'Density',       cat:'Distribution', engine:'plotly',     needsX:true,  needsY:false, icon:'〰️' },
        { id:'dotPlot',       label:'Dot Plot',      cat:'Distribution', engine:'chartjs',    needsX:true,  needsY:true,  icon:'⚫' },
        { id:'pie',           label:'Pie',           cat:'Part-to-Whole',engine:'chartjs',    needsX:true,  needsY:true,  icon:'🥧' },
        { id:'doughnut',      label:'Doughnut',      cat:'Part-to-Whole',engine:'chartjs',    needsX:true,  needsY:true,  icon:'🍩' },
        { id:'polarArea',     label:'Polar Area',    cat:'Part-to-Whole',engine:'chartjs',    needsX:true,  needsY:true,  icon:'🎯' },
        { id:'treemap',       label:'Treemap',       cat:'Part-to-Whole',engine:'plotly',     needsX:true,  needsY:true,  icon:'🗺️' },
        { id:'sunburst',      label:'Sunburst',      cat:'Part-to-Whole',engine:'plotly',     needsX:true,  needsY:true,  icon:'☀️' },
        { id:'funnel',        label:'Funnel',        cat:'Part-to-Whole',engine:'plotly',     needsX:true,  needsY:true,  icon:'🔻' },
        { id:'pyramid',       label:'Pyramid',       cat:'Part-to-Whole',engine:'plotly',     needsX:true,  needsY:true,  icon:'🔺' },
        { id:'wordCloud',     label:'Word Cloud',    cat:'Part-to-Whole',engine:'d3',         needsX:true,  needsY:false, icon:'💬' },
        { id:'packedBubble',  label:'Packed Bubble', cat:'Part-to-Whole',engine:'plotly',     needsX:true,  needsY:true,  icon:'🫧' },
        { id:'radar',         label:'Radar',         cat:'Comparison',   engine:'chartjs',    needsX:true,  needsY:true,  icon:'🕸️' },
        { id:'lollipop',      label:'Lollipop',      cat:'Comparison',   engine:'chartjs',    needsX:true,  needsY:true,  icon:'🍭' },
        { id:'errorBar',      label:'Error Bar',     cat:'Comparison',   engine:'plotly',     needsX:true,  needsY:true,  icon:'⊥' },
        { id:'rangeArea',     label:'Range Area',    cat:'Comparison',   engine:'plotly',     needsX:true,  needsY:true,  needsSize:true, icon:'↕️' },
        { id:'parallelCoords',label:'Parallel Coords',cat:'Comparison',  engine:'plotly',     needsX:false, needsY:true,  icon:'〣' },
        { id:'heatmap',       label:'Heatmap',       cat:'Correlation',  engine:'plotly',     needsX:false, needsY:false, icon:'🌡️' },
        { id:'hexbin',        label:'Hexbin',        cat:'Correlation',  engine:'plotly',     needsX:true,  needsY:true,  icon:'⬡' },
        { id:'stackedBar',    label:'Stacked Bar',   cat:'Stacked',      engine:'chartjs',    needsX:true,  needsY:true,  icon:'📊' },
        { id:'stackedArea',   label:'Stacked Area',  cat:'Stacked',      engine:'chartjs',    needsX:true,  needsY:true,  icon:'🏔️' },
        { id:'streamGraph',   label:'Stream Graph',  cat:'Stacked',      engine:'d3',         needsX:true,  needsY:true,  icon:'🌊' },
        { id:'marimekko',     label:'Marimekko',     cat:'Stacked',      engine:'plotly',     needsX:true,  needsY:true,  needsSize:true, icon:'🧩' },
        { id:'candlestick',   label:'Candlestick',   cat:'Financial',    engine:'plotly',     needsX:true,  needsY:true,  icon:'🕯️' },
        { id:'waterfall',     label:'Waterfall',     cat:'Financial',    engine:'plotly',     needsX:true,  needsY:true,  icon:'💧' },
        { id:'pareto',        label:'Pareto',        cat:'Financial',    engine:'plotly',     needsX:true,  needsY:true,  icon:'📐' },
        { id:'controlChart',  label:'Control Chart', cat:'Financial',    engine:'plotly',     needsX:true,  needsY:true,  icon:'🎛️' },
        { id:'gauge',         label:'Gauge',         cat:'Financial',    engine:'plotly',     needsX:false, needsY:true,  icon:'⏱️' },
        { id:'sankey',        label:'Sankey',        cat:'Flow',         engine:'plotly',     needsX:true,  needsY:true,  needsSize:true, icon:'🌀' },
        { id:'chord',         label:'Chord',         cat:'Flow',         engine:'d3',         needsX:true,  needsY:true,  icon:'⭕' },
        { id:'combo',         label:'Combo',         cat:'Combo',        engine:'chartjs',    needsX:true,  needsY:true,  icon:'🔀' },
        { id:'calendarHeatmap',label:'Calendar Heatmap',cat:'Special',   engine:'d3',         needsX:true,  needsY:true,  icon:'📅' },
        { id:'timeline',      label:'Timeline',      cat:'Special',      engine:'plotly',     needsX:true,  needsY:true,  needsSize:true, icon:'⏱️' },
        { id:'mosaic',        label:'Mosaic',        cat:'Special',      engine:'plotly',     needsX:true,  needsY:true,  icon:'🧩' },
        { id:'geoMap',        label:'Geo Map',       cat:'Unavailable',  engine:'unavailable', unavailableMsg:'Geographic Map requires latitude/longitude columns in your data.', icon:'🗺️' },
        { id:'choropleth',    label:'Choropleth',    cat:'Unavailable',  engine:'unavailable', unavailableMsg:'Choropleth Map requires ISO country/region codes and GeoJSON boundary files.', icon:'🌍' },
        { id:'networkGraph',  label:'Network Graph', cat:'Unavailable',  engine:'unavailable', unavailableMsg:'Network Graph requires source/target edge columns in your data.', icon:'🕸️' },
        { id:'gantt',         label:'Gantt',         cat:'Unavailable',  engine:'unavailable', unavailableMsg:'Gantt Chart requires start date, end date, and task name columns.', icon:'📅' },
    ];

    const ChartRegistry = {
        _map: Object.fromEntries(CHART_REGISTRY.map(c => [c.id, c])),
        get(id) { return this._map[id]; },
        all() { return CHART_REGISTRY; },
        byCategory() {
            const cats = {};
            CHART_REGISTRY.forEach(c => {
                if (c.cat === 'Unavailable') return;
                if (!cats[c.cat]) cats[c.cat] = [];
                cats[c.cat].push(c);
            });
            return cats;
        }
    };

    // ── 3. COLOUR PALETTE & THEME ──────────────────────────────────────────
    const PALETTE = [
        { b:'#f97316', bg:'rgba(249,115,22,0.65)'  },
        { b:'#3b82f6', bg:'rgba(59,130,246,0.65)'  },
        { b:'#10b981', bg:'rgba(16,185,129,0.65)'  },
        { b:'#f43f5e', bg:'rgba(244,63,94,0.65)'   },
        { b:'#8b5cf6', bg:'rgba(139,92,246,0.65)'  },
        { b:'#eab308', bg:'rgba(234,179,8,0.65)'   },
        { b:'#06b6d4', bg:'rgba(6,182,212,0.65)'   },
        { b:'#ec4899', bg:'rgba(236,72,153,0.65)'  },
        { b:'#14b8a6', bg:'rgba(20,184,166,0.65)'  },
        { b:'#a855f7', bg:'rgba(168,85,247,0.65)'  },
        { b:'#f59e0b', bg:'rgba(245,158,11,0.65)'  },
        { b:'#ef4444', bg:'rgba(239,68,68,0.65)'   },
    ];

    const PLOTLY_LAYOUT_BASE = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { family: 'Inter, sans-serif', color: '#a8a29e', size: 11 },
        margin: { t: 30, r: 20, b: 50, l: 60 },
        xaxis: { gridcolor: 'rgba(255,255,255,0.05)', zerolinecolor: 'rgba(255,255,255,0.1)', tickfont: { color: '#78716c' }, titlefont: { color: '#78716c' } },
        yaxis: { gridcolor: 'rgba(255,255,255,0.05)', zerolinecolor: 'rgba(255,255,255,0.1)', tickfont: { color: '#78716c' }, titlefont: { color: '#78716c' } },
        legend: { font: { color: '#a8a29e' }, bgcolor: 'rgba(0,0,0,0)' },
        colorway: PALETTE.map(p => p.b),
    };
    const PLOTLY_CONFIG = { responsive: true, displayModeBar: false };

    // ── 4. LAZY LIBRARY LOADERS ───────────────────────────────────────────
    let _plotlyLoaded = false, _plotlyPromise = null;
    function loadPlotly() {
        if (_plotlyLoaded) return Promise.resolve();
        if (_plotlyPromise) return _plotlyPromise;
        _plotlyPromise = new Promise((resolve, reject) => {
            const s = document.createElement('script');
            s.src = 'https://cdn.plot.ly/plotly-2.35.2.min.js';
            s.onload = () => { _plotlyLoaded = true; resolve(); };
            s.onerror = reject;
            document.head.appendChild(s);
        });
        return _plotlyPromise;
    }

    let _d3Loaded = false, _d3Promise = null;
    function loadD3() {
        if (_d3Loaded) return Promise.resolve();
        if (_d3Promise) return _d3Promise;
        _d3Promise = new Promise((resolve, reject) => {
            const s = document.createElement('script');
            s.src = 'https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js';
            s.onload = () => { _d3Loaded = true; resolve(); };
            s.onerror = reject;
            document.head.appendChild(s);
        });
        return _d3Promise;
    }

    // ── 5. DOM ELEMENTS ────────────────────────────────────────────────────
    const $chartCanvas       = document.getElementById('myChart');
    const $advMount          = document.getElementById('advancedChartMount');
    const $emptyState        = document.getElementById('chartEmptyState');
    const $loadingState      = document.getElementById('chartLoadingState');
    const $unavailableState  = document.getElementById('chartUnavailableState');
    const $unavailableMsg    = document.getElementById('chartUnavailableMsg');
    const $emptyMsg          = document.getElementById('chartEmptyMsg');
    const $zoomControls      = document.getElementById('zoomControls');
    const $chartContainer    = document.getElementById('chartContainer');

    const xAxisSel      = document.getElementById('xAxis');
    const yAxisPanel    = document.getElementById('yAxisPanel');
    const yAxisBtn      = document.getElementById('yAxisBtn');
    const yAxisBtnText  = document.getElementById('yAxisBtnText');
    const yAxisWrapper  = document.getElementById('yAxisDropdownWrapper');
    const timeGroupSel  = document.getElementById('timeGroup');
    const filterColSel  = document.getElementById('filterColumn');
    const filterValSel  = document.getElementById('filterValue');
    const topNSel       = document.getElementById('topN');
    const aggModeSel    = document.getElementById('aggMode');
    const renderBtn     = document.getElementById('renderChartBtn');
    const sizeAxisSel   = document.getElementById('sizeAxis');
    const groupAxisSel  = document.getElementById('groupAxis');
    const binsInput     = document.getElementById('binsInput');
    const extraAxisRow  = document.getElementById('extraAxisRow');
    const sizeAxisWrap  = document.getElementById('sizeAxisWrap');
    const binsWrap      = document.getElementById('binsWrap');
    const groupAxisWrap = document.getElementById('groupAxisWrap');
    const sizeAxisLabel = document.getElementById('sizeAxisLabel');
    const $badge        = document.getElementById('chartTypeBadge');

    // ── 6. UI STATE HELPERS ────────────────────────────────────────────────
    function showChartState(state, msg = '') {
        if ($chartCanvas) $chartCanvas.classList.toggle('hidden', state !== 'chart');
        if ($advMount) $advMount.classList.toggle('hidden', state !== 'advanced');
        if ($emptyState) $emptyState.classList.toggle('hidden', state !== 'empty');
        if ($loadingState) $loadingState.classList.toggle('hidden', state !== 'loading');
        if ($unavailableState) $unavailableState.classList.toggle('hidden', state !== 'unavailable');
        if (state === 'unavailable' && $unavailableMsg) $unavailableMsg.textContent = msg;
        if (state === 'empty' && $emptyMsg) $emptyMsg.textContent = msg || 'Select columns and click Render Chart.';
        if ($zoomControls) $zoomControls.classList.toggle('hidden', state !== 'chart');
    }

    function setRenderBtnLoading(loading) {
        if (!renderBtn) return;
        renderBtn.disabled = loading;
        renderBtn.innerHTML = loading
            ? `<svg class="animate-spin w-4 h-4 inline-block mr-2" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg> Loading…`
            : `<svg class="w-4 h-4 inline-block mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg> Render Chart`;
    }

    // ── 7. DATE HELPERS ────────────────────────────────────────────────────
    function dateKey(val, grp) {
        const d = new Date(val);
        if (isNaN(d)) return null;
        if (grp === 'year')    return String(d.getFullYear());
        if (grp === 'quarter') return `${d.getFullYear()} Q${Math.ceil((d.getMonth()+1)/3)}`;
        if (grp === 'month') {
            const M = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
            return `${M[d.getMonth()]} ${d.getFullYear()}`;
        }
        if (grp === 'week') {
            const t = new Date(d); t.setHours(0,0,0,0);
            t.setDate(t.getDate() + 4 - (t.getDay()||7));
            const ys = new Date(t.getFullYear(),0,1);
            const wk = Math.ceil((((t-ys)/86400000)+1)/7);
            return `${t.getFullYear()}-W${String(wk).padStart(2,'0')}`;
        }
        return null;
    }

    function sortDateLabels(labels, grp) {
        if (grp === 'year') return [...labels].sort();
        if (grp === 'quarter') return [...labels].sort((a,b) => {
            const [ayStr, aqStr] = a.split(' Q'); const [byStr, bqStr] = b.split(' Q');
            return (parseInt(ayStr)*4+parseInt(aqStr)) - (parseInt(byStr)*4+parseInt(bqStr));
        });
        if (grp === 'month') {
            const M = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
            return [...labels].sort((a,b) => {
                const [am,ay] = a.split(' '), [bm,by] = b.split(' ');
                return (parseInt(ay)*12 + M.indexOf(am)) - (parseInt(by)*12 + M.indexOf(bm));
            });
        }
        return [...labels].sort();
    }

    // ── 8. CHART.JS BUILDERS ───────────────────────────────────────────────
    function makeDataset(label, data, type, c, ctx, len) {
        let bg = c.bg;
        if (ctx && (type === 'bar' || type === 'column' || type === 'line' || type === 'area' || type === 'stepLine' || type === 'stackedArea')) {
            try {
                const g = ctx.createLinearGradient(0, 0, 0, 380);
                g.addColorStop(0, c.bg);
                g.addColorStop(1, c.bg.replace(/[\d.]+\)$/, '0.04)'));
                bg = g;
            } catch(_) {}
        }
        const isFilled = ['area','stackedArea','stackedBar'].includes(type);
        return {
            label, data,
            backgroundColor: bg,
            borderColor: c.b,
            borderWidth: (type === 'line' || type === 'area' || type === 'stepLine') ? 2.5 : 1,
            fill: isFilled,
            tension: 0.4,
            stepped: type === 'stepLine' ? 'before' : false,
            pointBackgroundColor: c.b,
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: c.b,
            pointRadius: len > 60 ? 2 : 4,
            pointHoverRadius: 6,
        };
    }

    let membersMap = {};

    function detectLabelColumn(cols, xCol) {
        const candidates = ['student_name', 'student', 'name', 'student_id', 'roll_no', 'rollnumber', 'id', 'email'];
        for (const cand of candidates) {
            const match = cols.find(c => c.toLowerCase() === cand && c !== xCol);
            if (match) return match;
        }
        const nonNumeric = cols.filter(col => !numericCols.includes(col));
        const matchFallback = nonNumeric.find(c => c !== xCol);
        if (matchFallback) return matchFallback;
        const anyMatch = cols.find(c => c !== xCol);
        return anyMatch || xCol;
    }

    function populateMembersMap(rows, xCol) {
        membersMap = {};
        if (!xCol) return;
        const labelCol = detectLabelColumn(columns, xCol);
        rows.forEach(r => {
            const lbl = String(r[xCol] ?? 'Unknown');
            if (!membersMap[lbl]) {
                membersMap[lbl] = { list: [], col: labelCol };
            }
            const nameVal = r[labelCol];
            if (nameVal !== null && nameVal !== undefined && nameVal !== '') {
                const nameStr = String(nameVal);
                if (!membersMap[lbl].list.includes(nameStr)) {
                    membersMap[lbl].list.push(nameStr);
                }
            }
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || `HTTP ${response.status}`);
        }

        const data = await response.json();
        
        const myChartCanvas = document.getElementById("myChart");
        const chartEmptyMsg = document.getElementById("chartEmptyMsg");

        if (chartEmptyMsg) chartEmptyMsg.style.display = 'none';
        
        if (currentChart) {
            currentChart.destroy();
        }

        const ctx = myChartCanvas.getContext('2d');
        
        const datasets = (data.datasets || []).map((ds, i) => ({
            label: ds.label,
            data: ds.data,
            backgroundColor: `hsla(${i * 60 + 200}, 70%, 50%, 0.6)`,
            borderColor: `hsla(${i * 60 + 200}, 70%, 50%, 1)`,
            borderWidth: 1,
            fill: chartType === 'line' || chartType === 'area',
            tension: 0.1
        }));

        let jsChartType = chartType === 'column' ? 'bar' : (chartType === 'area' ? 'line' : chartType);

        const chartConfig = {
            type: jsChartType,
            data: {
                labels: data.labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#a8a29e' } }
                }
            }
        };

        currentChart = new Chart(ctx, chartConfig);

    } catch (error) {
        console.error("Chart Rendering Error:", error);
        alert(`Failed to render chart: ${error.message}`);
    } finally {
        if (window.restoreButtonState) window.restoreButtonState(renderChartBtn);
    }

    function chartOpts(type, yLabel = '', extraOpts = {}) {
        const isCount = aggModeSel ? aggModeSel.value === 'count' : false;
        const isRadial = ['pie','doughnut','polarArea'].includes(type);
        const isRadar  = type === 'radar';

        const scales = isRadial ? {} : isRadar ? {
            r: {
                ticks: { color:'#78716c', font:{ family:'Inter', size:10 }, backdropColor:'transparent' },
                grid: { color:'rgba(255,255,255,0.07)' },
                pointLabels: { color:'#a8a29e', font:{ family:'Inter', size:11 } },
            }
        } : {
            x: {
                stacked: ['stackedBar','stackedArea'].includes(type),
                ticks: {
                    color:'#78716c', font:{ family:'Inter', size:11 },
                    maxRotation:45, minRotation:0, autoSkip:true, maxTicksLimit:25,
                    callback(val) {
                        const lbl = this.getLabelForValue(val);
                        return typeof lbl==='string' && lbl.length>16 ? lbl.slice(0,16)+'…' : lbl;
                    }
                },
                grid:{ color:'rgba(255,255,255,0.03)', drawBorder:false },
                type: type === 'scatter' ? 'linear' : 'category'
            },
            y: {
                stacked: ['stackedBar','stackedArea'].includes(type),
                ticks:{ color:'#78716c', font:{ family:'Inter', size:11 }, callback: v => typeof v==='number' ? v.toLocaleString() : v },
                grid:{ color:'rgba(255,255,255,0.05)', drawBorder:false },
                title: { display: !!yLabel, text: yLabel, color:'#78716c', font:{ family:'Inter', size:11 } }
            }
        };

        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color:'#a8a29e', font:{ family:'Inter', weight:'500' }, boxWidth:12, boxHeight:12 }, position:'top' },
                tooltip: {
                    backgroundColor:'rgba(28,25,23,0.97)',
                    titleColor:'#fff', bodyColor:'#d6d3d1',
                    borderColor:'rgba(253,186,116,0.15)', borderWidth:1,
                    padding:14, cornerRadius:10,
                    titleFont:{ family:'Inter', size:13, weight:'bold' },
                    bodyFont:{ family:'Inter', size:12 },
                    callbacks: {
                        title(items) { return items[0]?.label ?? ''; },
                        label(ctx) {
                            const v = ctx.parsed?.y ?? ctx.parsed;
                            const formatted = typeof v === 'number' ? v.toLocaleString(undefined, {maximumFractionDigits: 4}) : v;
                            if (isCount) return ` Count: ${formatted}`;
                            const colName = ctx.dataset.label || 'Value';
                            return ` ${colName}: ${formatted}`;
                        },
                        afterBody(items) {
                            const lbl = items[0]?.label ?? '';
                            const memberData = membersMap[lbl];
                            const xCol = xAxisSel ? xAxisSel.value : '';
                            const candidates = ['student_name', 'student', 'name', 'student_id', 'roll_no', 'rollnumber', 'id', 'email'];
                            if (candidates.includes(xCol.toLowerCase())) return [];
                            if (!memberData || memberData.col === xCol) return [];
                            const members = memberData.list;
                            if (!members || !Array.isArray(members)) return [];
                            const lines = members.slice(0, 10).map(n => `  • ${n}`);
                            if (members.length > 10) lines.push(`  … and ${members.length - 10} more`);
                            return ['', `  ${memberData.col}:`, ...lines];
                        }
                    }
                }
            },
            scales,
            animation:{ duration:900, easing:'easeOutQuart' },
            ...extraOpts
        };
    }

    // ── 9. POPULATE DROPDOWNS ─────────────────────────────────────────────
    if (xAxisSel) {
        xAxisSel.innerHTML = '';
        columns.forEach(col => xAxisSel.add(new Option(col, col)));
    }
    function updateYSelectText() {
        if (!yAxisPanel || !yAxisBtnText) return;
        const selected = Array.from(yAxisPanel.querySelectorAll('input:checked')).map(cb => cb.value);
        if (selected.length === 0) {
            yAxisBtnText.textContent = 'None selected';
        } else if (selected.length === 1) {
            yAxisBtnText.textContent = selected[0];
        } else {
            yAxisBtnText.textContent = `${selected.length} columns selected`;
        }
    }

    if (yAxisPanel) {
        yAxisPanel.innerHTML = '';
        numericCols.forEach((col, idx) => {
            const lbl = document.createElement('label');
            lbl.className = 'flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-stone-850 cursor-pointer text-stone-300 hover:text-stone-100 transition-colors text-sm w-full';
            const isChecked = idx === 0 ? 'checked' : '';
            lbl.innerHTML = `<input type="checkbox" value="${col}" ${isChecked} class="rounded border-stone-700 text-orange-500 focus:ring-orange-500/20 bg-stone-950 w-4 h-4 cursor-pointer"> <span class="select-none truncate">${col}</span>`;
            lbl.querySelector('input').addEventListener('change', updateYSelectText);
            yAxisPanel.appendChild(lbl);
        });
        updateYSelectText();
    }

    if (yAxisBtn && yAxisPanel) {
        yAxisBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            yAxisPanel.classList.toggle('hidden');
        });
        document.addEventListener('click', (e) => {
            if (yAxisWrapper && !yAxisWrapper.contains(e.target)) {
                yAxisPanel.classList.add('hidden');
            }
        });
    }
    if (sizeAxisSel) {
        sizeAxisSel.innerHTML = '';
        columns.forEach(col => sizeAxisSel.add(new Option(col, col)));
    }
    if (groupAxisSel) {
        groupAxisSel.innerHTML = '';
        columns.forEach(col => groupAxisSel.add(new Option(col, col)));
    }
    if (filterColSel) {
        filterColSel.innerHTML = '<option value="">— No Filter —</option>';
        columns.forEach(col => filterColSel.add(new Option(col, col)));
    }

    if (filterColSel) {
        filterColSel.addEventListener('change', () => {
            const col = filterColSel.value;
            filterValSel.innerHTML = '<option value="">— All —</option>';
            if (col) {
                const unique = [...new Set(allRows.map(r => String(r[col]??'')).filter(v => v && v !== 'null' && v !== 'undefined'))].sort();
                unique.forEach(v => filterValSel.add(new Option(v, v)));
            }
        });
    }

    if (dateCols.length && xAxisSel) {
        xAxisSel.value = dateCols[0];
    }

    // ── 10. CHART CATEGORIES & TYPES ──────────────────────────────────────
    let activeChartId = 'bar';

    function buildDropdown() {
        const catSelect = document.getElementById('chartCategorySelect');
        const chartSelect = document.getElementById('chartTypeSelect');
        if (!catSelect || !chartSelect) return;
        
        catSelect.innerHTML = '';
        const byCategory = ChartRegistry.byCategory();
        
        Object.keys(byCategory).forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat;
            opt.textContent = cat;
            catSelect.appendChild(opt);
        });

        function populateCharts(category) {
            chartSelect.innerHTML = '';
            const charts = byCategory[category] || [];
            charts.forEach(chart => {
                const opt = document.createElement('option');
                opt.value = chart.id;
                opt.textContent = `${chart.icon} ${chart.label}`;
                chartSelect.appendChild(opt);
            });
        }

        catSelect.addEventListener('change', (e) => {
            populateCharts(e.target.value);
            setActiveChart(chartSelect.value);
        });

        chartSelect.addEventListener('change', (e) => {
            setActiveChart(e.target.value);
        });

        // Initial population
        const initialMeta = ChartRegistry.get(activeChartId);
        if (initialMeta && initialMeta.cat !== 'Unavailable') {
            catSelect.value = initialMeta.cat;
            populateCharts(initialMeta.cat);
            chartSelect.value = activeChartId;
        } else {
            populateCharts(Object.keys(byCategory)[0]);
        }
    }

    function setActiveChart(id) {
        activeChartId = id;
        
        const catSelect = document.getElementById('chartCategorySelect');
        const chartSelect = document.getElementById('chartTypeSelect');
        const meta = ChartRegistry.get(id);

        if (meta && meta.cat !== 'Unavailable') {
            if (catSelect && catSelect.value !== meta.cat) {
                catSelect.value = meta.cat;
                if (chartSelect) {
                    chartSelect.innerHTML = '';
                    ChartRegistry.byCategory()[meta.cat].forEach(chart => {
                        const opt = document.createElement('option');
                        opt.value = chart.id;
                        opt.textContent = `${chart.icon} ${chart.label}`;
                        chartSelect.appendChild(opt);
                    });
                }
            }
            if (chartSelect && chartSelect.value !== id) {
                chartSelect.value = id;
            }
        }

        if ($badge) {
            $badge.textContent = meta?.label ?? id;
            $badge.classList.remove('hidden');
        }
        syncControls();
    }

    // ── 11. CONTROLS SYNCHRONIZATION ──────────────────────────────────────
    function syncControls() {
        const id = activeChartId;
        const meta = ChartRegistry.get(id) || {};
        const xCol = xAxisSel ? xAxisSel.value : '';
        const isUniqueX = uniqueColumns.includes(xCol);

        const radialLike = ['pie','doughnut','polarArea','radar','scatter','bubble',
                            'histogram','boxPlot','violin','gauge','heatmap','treemap',
                            'sunburst','packedBubble','chord','wordCloud','calendarHeatmap',
                            'mosaic','parallelCoords','hexbin','densityPlot','waterfall',
                            'funnel','pyramid','sankey','marimekko','gantt','networkGraph'].includes(id);

        const noAgg = ['histogram','violin','boxPlot','scatter','bubble','candlestick','heatmap','parallelCoords','chord','streamGraph'].includes(id);
        
        if (aggModeSel) {
            if (isUniqueX) {
                aggModeSel.value = 'none';
                aggModeSel.disabled = true;
            } else {
                if (aggModeSel.value === 'none') aggModeSel.value = 'sum';
                aggModeSel.disabled = noAgg;
            }
        }

        const agg = aggModeSel ? aggModeSel.value : 'sum';
        if (timeGroupSel) {
            timeGroupSel.disabled = radialLike || agg === 'count' || agg === 'none';
            if (timeGroupSel.disabled) timeGroupSel.value = 'none';
        }

        const needsExtra = meta.needsSize || meta.needsBins || meta.needsGroup;
        if (extraAxisRow) extraAxisRow.classList.toggle('hidden', !needsExtra);
        if (sizeAxisWrap) sizeAxisWrap.classList.toggle('hidden', !meta.needsSize);
        if (binsWrap) binsWrap.classList.toggle('hidden', !meta.needsBins);
        if (groupAxisWrap) groupAxisWrap.classList.toggle('hidden', !meta.needsGroup);

        const xAxisLabelEl = document.getElementById('xAxisLabel');
        if (xAxisLabelEl) {
            if (id === 'histogram' || id === 'gauge') {
                xAxisLabelEl.textContent = 'Value Column';
            } else {
                xAxisLabelEl.textContent = 'X-Axis';
            }
        }
        if (meta.needsSize && sizeAxisLabel) {
            sizeAxisLabel.textContent = id === 'bubble' ? 'Bubble Size' : id === 'sankey' ? 'Flow Value' : 'Size / Value';
        }

        const yAxisWrapEl = document.getElementById('yAxisWrap');
        if (yAxisWrapEl) {
            yAxisWrapEl.classList.toggle('hidden', ['histogram','wordCloud','gauge','geoMap','choropleth'].includes(id));
        }
        const xAxisWrapEl = document.getElementById('xAxisWrap');
        if (xAxisWrapEl) {
            xAxisWrapEl.classList.toggle('hidden', ['gauge','parallelCoords'].includes(id));
        }
    }

    // ── 12. UNIVERSAL RENDER FUNCTION ─────────────────────────────────────
    let currentChart = null;

    function destroyCurrentChart() {
        if (currentChart) { currentChart.destroy(); currentChart = null; }
        if (_plotlyLoaded && $advMount && $advMount._plotlyInstance) {
            try { Plotly.purge($advMount); } catch(_) {}
            $advMount._plotlyInstance = false;
        }
    }

    function applyFilter(rows, fCol, fVal) {
        if (!fCol || !fVal) return [...rows];
        return rows.filter(r => String(r[fCol]??'') === fVal);
    }

    function aggregateRows(rows, xCol, yCols, aggMode) {
        const agg = {};
        rows.forEach(r => {
            const lbl = String(r[xCol]??'Unknown');
            if (!agg[lbl]) agg[lbl] = {};
            yCols.forEach(yCol => {
                const v = parseFloat(r[yCol]) || 0;
                if (aggMode === 'none' || aggMode === 'sum')    agg[lbl][yCol] = (agg[lbl][yCol]||0) + v;
                else if (aggMode === 'count') agg[lbl][yCol] = (agg[lbl][yCol]||0) + 1;
                else if (aggMode === 'mean') { agg[lbl][yCol] = agg[lbl][yCol]||{s:0,n:0}; agg[lbl][yCol].s += v; agg[lbl][yCol].n++; }
                else if (aggMode === 'min')  agg[lbl][yCol] = agg[lbl][yCol]===undefined ? v : Math.min(agg[lbl][yCol],v);
                else if (aggMode === 'max')  agg[lbl][yCol] = agg[lbl][yCol]===undefined ? v : Math.max(agg[lbl][yCol],v);
                else if (aggMode === 'median') { agg[lbl][yCol] = agg[lbl][yCol]||[]; agg[lbl][yCol].push(v); }
            });
        });
        if (aggMode === 'mean') {
            Object.keys(agg).forEach(lbl => yCols.forEach(yCol => {
                if (agg[lbl][yCol] && typeof agg[lbl][yCol] === 'object') agg[lbl][yCol] = agg[lbl][yCol].s / agg[lbl][yCol].n;
            }));
        }
        if (aggMode === 'median') {
            Object.keys(agg).forEach(lbl => yCols.forEach(yCol => {
                const arr = (agg[lbl][yCol]||[]).sort((a,b)=>a-b);
                const n = arr.length;
                agg[lbl][yCol] = n ? (n%2===0?(arr[n/2-1]+arr[n/2])/2:arr[Math.floor(n/2)]) : 0;
            }));
        }
        return agg;
    }

    async function renderChart() {
        const type   = activeChartId;
        const meta   = ChartRegistry.get(type);
        const xCol   = xAxisSel ? xAxisSel.value : '';
        const yCols  = yAxisPanel ? Array.from(yAxisPanel.querySelectorAll('input:checked')).map(cb => cb.value) : [];
        const grp    = timeGroupSel ? timeGroupSel.value : 'none';
        const fCol   = filterColSel ? filterColSel.value : '';
        const fVal   = filterValSel ? filterValSel.value : '';
        const topN   = topNSel ? parseInt(topNSel.value) || 0 : 0;
        const aggMode = aggModeSel ? aggModeSel.value : 'sum';
        const sizeCol = sizeAxisSel ? sizeAxisSel.value : '';
        const groupCol = groupAxisSel ? groupAxisSel.value : '';
        const bins    = binsInput ? parseInt(binsInput.value) || 20 : 20;

        if (meta.engine === 'unavailable') {
            destroyCurrentChart();
            showChartState('unavailable', meta.unavailableMsg);
            return;
        }

        membersMap = {};
        showChartState('loading');
        setRenderBtnLoading(true);

        try {
            let rows = applyFilter(allRows, fCol, fVal);
            if (!rows.length) {
                if (window.showCustomAlert) window.showCustomAlert('No data matches the selected filter.');
                showChartState('empty');
                return;
            }

            const ctx = $chartCanvas ? $chartCanvas.getContext('2d') : null;

            if (meta.engine === 'chartjs') {
                await renderChartJS(type, rows, xCol, yCols, grp, topN, aggMode, sizeCol, ctx);
            } else if (meta.engine === 'plotly') {
                await renderPlotly(type, rows, xCol, yCols, topN, aggMode, sizeCol, groupCol, bins);
            } else if (meta.engine === 'd3') {
                await renderD3(type, rows, xCol, yCols, topN, aggMode);
            }
        } catch(e) {
            console.error("Render error: ", e);
            if (window.showCustomAlert) window.showCustomAlert(`Chart error: ${e.message}`);
            showChartState('empty', 'An error occurred. Try different columns or chart type.');
        } finally {
            setRenderBtnLoading(false);
        }
    }

    // ── 13. CHARTJS ENGINE IMPLEMENTATION ─────────────────────────────────
    async function renderChartJS(type, rows, xCol, yCols, grp, topN, aggMode, sizeCol, ctx) {
        destroyCurrentChart();
        showChartState('chart');

        populateMembersMap(rows, xCol);

        if (type === 'scatter' || type === 'dotPlot') {
            const yCol = yCols[0];
            if (!xCol || !yCol) {
                if (window.showCustomAlert) window.showCustomAlert('Scatter needs numeric X and Y columns.');
                return;
            }
            const pts = rows.map(r => ({ x:parseFloat(r[xCol]), y:parseFloat(r[yCol]) })).filter(p => !isNaN(p.x) && !isNaN(p.y));
            if (!pts.length) {
                if (window.showCustomAlert) window.showCustomAlert('No numeric data found for scatter.');
                return;
            }
            currentChart = new Chart(ctx, {
                type: 'scatter',
                data: { datasets:[{ label:`${xCol} vs ${yCol}`, data:pts, backgroundColor:PALETTE[0].bg, borderColor:PALETTE[0].b, pointRadius:type==='dotPlot'?6:5, pointHoverRadius:8 }] },
                options: chartOpts('scatter')
            });
            return;
        }

        if (type === 'bubble') {
            const yCol = yCols[0];
            if (!xCol || !yCol || !sizeCol) {
                if (window.showCustomAlert) window.showCustomAlert('Bubble chart needs X, Y, and Size columns.');
                return;
            }
            const rawPts = rows.map(r => ({ x:parseFloat(r[xCol]), y:parseFloat(r[yCol]), r:parseFloat(r[sizeCol]) })).filter(p => !isNaN(p.x) && !isNaN(p.y) && !isNaN(p.r));
            if (!rawPts.length) {
                if (window.showCustomAlert) window.showCustomAlert('No numeric data for bubble chart.');
                return;
            }
            const maxR = Math.max(...rawPts.map(p=>p.r));
            const pts = rawPts.map(p => ({ ...p, r: Math.max(3, (p.r/maxR)*30) }));
            currentChart = new Chart(ctx, {
                type: 'bubble',
                data: { datasets:[{ label:`${xCol} vs ${yCol}`, data:pts, backgroundColor:PALETTE[0].bg, borderColor:PALETTE[0].b }] },
                options: chartOpts('scatter', '')
            });
            return;
        }

        if (['pie','doughnut','polarArea'].includes(type)) {
            const yCol = yCols[0];
            const rawAgg = {};
            rows.forEach(r => {
                const lbl = String(r[xCol]??'Unknown');
                const v = parseFloat(r[yCol]) || 0;
                if (aggMode === 'none' || aggMode === 'sum')    rawAgg[lbl] = (rawAgg[lbl]||0) + v;
                else if (aggMode === 'mean')  { rawAgg[lbl] = rawAgg[lbl]||{s:0,n:0}; rawAgg[lbl].s+=v; rawAgg[lbl].n++; }
                else if (aggMode === 'min')   rawAgg[lbl] = rawAgg[lbl]===undefined ? v : Math.min(rawAgg[lbl],v);
                else if (aggMode === 'max')   rawAgg[lbl] = rawAgg[lbl]===undefined ? v : Math.max(rawAgg[lbl],v);
                else if (aggMode === 'count') rawAgg[lbl] = (rawAgg[lbl]||0) + 1;
                else if (aggMode === 'median') { rawAgg[lbl] = rawAgg[lbl]||[]; rawAgg[lbl].push(v); }
            });
            if (aggMode === 'mean') Object.keys(rawAgg).forEach(k => { rawAgg[k] = rawAgg[k].s/rawAgg[k].n; });
            if (aggMode === 'median') Object.keys(rawAgg).forEach(k => { const arr=(rawAgg[k]||[]).sort((a,b)=>a-b); const n=arr.length; rawAgg[k]=n?(n%2===0?(arr[n/2-1]+arr[n/2])/2:arr[Math.floor(n/2)]):0; });
            let entries = Object.entries(rawAgg).sort((a,b) => b[1]-a[1]);
            if (topN > 0) entries = entries.slice(0, topN);
            const labels = entries.map(([k]) => k.length>22 ? k.slice(0,22)+'…' : k);
            const data   = entries.map(([,v]) => typeof v==='object' ? (v.s/v.n) : v);
            currentChart = new Chart(ctx, {
                type: type === 'doughnut' ? 'doughnut' : type === 'polarArea' ? 'polarArea' : 'pie',
                data: { labels, datasets:[{ label:yCol, data, backgroundColor:data.map((_,i)=>PALETTE[i%PALETTE.length].bg), borderColor:'#1c1917', borderWidth:2 }] },
                options: chartOpts(type)
            });
            return;
        }

        if (type === 'radar') {
            if (!xCol || !yCols.length) {
                if (window.showCustomAlert) window.showCustomAlert('Radar needs X and at least one Y column.');
                return;
            }
            const agg = aggregateRows(rows, xCol, yCols, aggMode);
            let entries = Object.entries(agg).sort((a,b) => {
                const va = typeof a[1][yCols[0]] === 'number' ? a[1][yCols[0]] : 0;
                const vb = typeof b[1][yCols[0]] === 'number' ? b[1][yCols[0]] : 0;
                return vb-va;
            });
            if (topN > 0) entries = entries.slice(0, topN);
            const labels = entries.map(([k]) => k);
            const datasets = yCols.map((yCol, i) => {
                const c = PALETTE[i%PALETTE.length];
                const data = entries.map(([,v]) => typeof v[yCol]==='number' ? v[yCol] : (v[yCol]||0));
                return { label:yCol, data, backgroundColor:c.bg, borderColor:c.b, borderWidth:2, pointBackgroundColor:c.b, pointBorderColor:'#fff', pointHoverBackgroundColor:'#fff', pointHoverBorderColor:c.b, fill:true };
            });
            currentChart = new Chart(ctx, { type:'radar', data:{ labels, datasets }, options: chartOpts('radar') });
            return;
        }

        if (type === 'lollipop') {
            const yCol = yCols[0];
            const agg = aggregateRows(rows, xCol, yCols, aggMode);
            let entries = Object.entries(agg).sort((a,b) => (b[1][yCol]||0)-(a[1][yCol]||0));
            if (topN > 0) entries = entries.slice(0, topN);
            const labels = entries.map(([k]) => k);
            const data   = entries.map(([,v]) => typeof v[yCol]==='number' ? v[yCol] : (v[yCol]||0));
            const c = PALETTE[0];
            const barDs = { type:'bar', label:yCol, data, backgroundColor:'transparent', borderColor:c.b, borderWidth:1.5, barThickness:2 };
            const dotDs = { type:'scatter', label:'', data:labels.map((l,i)=>({x:l,y:data[i]})), backgroundColor:c.b, borderColor:'#1c1917', borderWidth:2, pointRadius:6, pointHoverRadius:8, showLine:false };
            currentChart = new Chart(ctx, { type:'bar', data:{ labels, datasets:[barDs, dotDs] }, options: chartOpts('bar') });
            return;
        }

        if (type === 'combo') {
            if (!xCol || yCols.length < 2) {
                if (window.showCustomAlert) window.showCustomAlert('Combo chart needs X and at least 2 Y columns.');
                return;
            }
            const agg = aggregateRows(rows, xCol, yCols, aggMode);
            let entries = Object.entries(agg).sort((a,b) => (b[1][yCols[0]]||0)-(a[1][yCols[0]]||0));
            if (topN > 0) entries = entries.slice(0, topN);
            const labels = entries.map(([k]) => k);
            const datasets = yCols.map((yCol, i) => {
                const c = PALETTE[i%PALETTE.length];
                const data = entries.map(([,v]) => typeof v[yCol]==='number' ? v[yCol] : (v[yCol]||0));
                const dsType = i === 0 ? 'bar' : 'line';
                return { type:dsType, label:yCol, data, backgroundColor:c.bg, borderColor:c.b, borderWidth:2, fill:false, tension:0.4, pointRadius:4 };
            });
            currentChart = new Chart(ctx, { type:'bar', data:{ labels, datasets }, options: chartOpts('bar') });
            return;
        }

        if (grp !== 'none') {
            const allKeys = new Set();
            const aggByCol = {};
            yCols.forEach(yCol => {
                const agg = {};
                rows.forEach(r => {
                    const k = dateKey(r[xCol], grp);
                    if (!k) return;
                    allKeys.add(k);
                    const v = parseFloat(r[yCol]) || 0;
                    if (aggMode === 'sum')    agg[k] = (agg[k]||0) + v;
                    else if (aggMode === 'count') agg[k] = (agg[k]||0) + 1;
                    else if (aggMode === 'mean')  { agg[k] = agg[k] || {s:0,n:0}; agg[k].s += v; agg[k].n++; }
                    else if (aggMode === 'min')   agg[k] = agg[k] === undefined ? v : Math.min(agg[k], v);
                    else if (aggMode === 'max')   agg[k] = agg[k] === undefined ? v : Math.max(agg[k], v);
                    else if (aggMode === 'median') { agg[k] = agg[k]||[]; agg[k].push(v); }
                });
                if (aggMode === 'mean') Object.keys(agg).forEach(k => { agg[k] = agg[k].s / agg[k].n; });
                if (aggMode === 'median') Object.keys(agg).forEach(k => { const arr=(agg[k]||[]).sort((a,b)=>a-b); const n=arr.length; agg[k]=n?(n%2===0?(arr[n/2-1]+arr[n/2])/2:arr[Math.floor(n/2)]):0; });
                aggByCol[yCol] = agg;
            });
            if (!allKeys.size) {
                if (window.showCustomAlert) window.showCustomAlert('No parseable date values in X-axis column.');
                return;
            }
            const labels = sortDateLabels([...allKeys], grp);
            const datasets = yCols.map((yCol, i) => {
                const c = PALETTE[i%PALETTE.length];
                const dsLabel = aggMode === 'count' ? `Count of ${yCol}` : yCol;
                return makeDataset(dsLabel, labels.map(k => aggByCol[yCol][k] ?? 0), type, c, ctx, labels.length);
            });
            const cjsType = ['area','stackedArea'].includes(type) ? 'line' : ['stackedBar','column'].includes(type) ? 'bar' : type === 'line' ? 'line' : 'bar';
            currentChart = new Chart(ctx, { type:cjsType, data:{ labels, datasets }, options: chartOpts(type, aggMode === 'count' ? 'Count' : '') });
            return;
        }

        const agg = aggregateRows(rows, xCol, yCols, aggMode);
        let entries = Object.entries(agg).sort((a,b) => {
            const va = typeof a[1][yCols[0]] === 'number' ? a[1][yCols[0]] : (a[1][yCols[0]]||0);
            const vb = typeof b[1][yCols[0]] === 'number' ? b[1][yCols[0]] : (b[1][yCols[0]]||0);
            return vb - va;
        });
        if (topN > 0) entries = entries.slice(0, topN);
        const labels   = entries.map(([k]) => k);
        const datasets = yCols.map((yCol, i) => {
            const c = PALETTE[i%PALETTE.length];
            const data = entries.map(([,v]) => typeof v[yCol]==='number' ? v[yCol] : (v[yCol]||0));
            const dsLabel = aggMode === 'count' ? `Count of ${yCol}` : yCol;
            return makeDataset(dsLabel, data, type, c, ctx, labels.length);
        });

        const cjsTypeMap = { bar:'bar', column:'bar', line:'line', area:'line', stepLine:'line', stackedBar:'bar', stackedArea:'line' };
        const cjsType = cjsTypeMap[type] || 'bar';

        currentChart = new Chart(ctx, { type:cjsType, data:{ labels, datasets }, options: chartOpts(type, aggMode === 'count' ? 'Count' : '') });
    }

    // ── 14. PLOTLY ENGINE IMPLEMENTATION ──────────────────────────────────
    async function renderPlotly(type, rows, xCol, yCols, topN, aggMode, sizeCol, groupCol, bins) {
        await loadPlotly();
        destroyCurrentChart();
        showChartState('advanced');
        if ($advMount) $advMount._plotlyInstance = true;

        const layout = { ...PLOTLY_LAYOUT_BASE, height: 440 };

        if (type === 'histogram') {
            const col = xCol;
            const vals = rows.map(r => parseFloat(r[col])).filter(v => !isNaN(v));
            if (!vals.length) {
                if (window.showCustomAlert) window.showCustomAlert('No numeric data for histogram.');
                return;
            }
            const trace = {
                type: 'histogram', x: vals, nbinsx: bins,
                marker: { color: PALETTE[0].bg, line: { color: PALETTE[0].b, width: 1 } },
                name: col, autobinx: false,
            };
            Plotly.react($advMount, [trace], { ...layout, bargap:0.05, xaxis:{...layout.xaxis,title:col}, yaxis:{...layout.yaxis,title:'Count'} }, PLOTLY_CONFIG);
            return;
        }

        if (type === 'boxPlot') {
            const traces = yCols.map((yCol, i) => {
                const vals = rows.map(r => parseFloat(r[yCol])).filter(v => !isNaN(v));
                return {
                    type: 'box', y: vals, name: yCol, boxpoints: 'outliers',
                    marker: { color: PALETTE[i%PALETTE.length].b, size:4 },
                    line: { color: PALETTE[i%PALETTE.length].b },
                    fillcolor: PALETTE[i%PALETTE.length].bg,
                    jitter: 0.3,
                };
            });
            Plotly.react($advMount, traces, { ...layout, yaxis:{...layout.yaxis,title:'Value'} }, PLOTLY_CONFIG);
            return;
        }

        if (type === 'violin') {
            const traces = yCols.map((yCol, i) => {
                const vals = rows.map(r => parseFloat(r[yCol])).filter(v => !isNaN(v));
                return {
                    type: 'violin', y: vals, name: yCol, box:{ visible:true }, meanline:{ visible:true },
                    fillcolor: PALETTE[i%PALETTE.length].bg,
                    line: { color: PALETTE[i%PALETTE.length].b },
                    points: 'none',
                };
            });
            Plotly.react($advMount, traces, { ...layout, yaxis:{...layout.yaxis,title:'Distribution'} }, PLOTLY_CONFIG);
            return;
        }

        if (type === 'densityPlot') {
            const vals = rows.map(r => parseFloat(r[xCol])).filter(v => !isNaN(v));
            if (!vals.length) {
                if (window.showCustomAlert) window.showCustomAlert('No numeric data for density plot.');
                return;
            }
            const trace = {
                type: 'histogram', x: vals, histnorm: 'probability density',
                marker: { color: PALETTE[0].bg, line: { color: PALETTE[0].b, width:1 } },
                name: xCol,
            };
            Plotly.react($advMount, [trace], { ...layout, bargap:0.05, xaxis:{...layout.xaxis,title:xCol}, yaxis:{...layout.yaxis,title:'Density'} }, PLOTLY_CONFIG);
            return;
        }

        if (type === 'treemap') {
            const yCol = yCols[0];
            const agg = aggregateRows(rows, xCol, [yCol], aggMode);
            let entries = Object.entries(agg).sort((a,b) => (b[1][yCol]||0)-(a[1][yCol]||0));
            if (topN > 0) entries = entries.slice(0, topN);
            const labels = entries.map(([k]) => k);
            const values = entries.map(([,v]) => Math.max(0, typeof v[yCol]==='number' ? v[yCol] : (v[yCol]||0)));
            const trace = {
                type: 'treemap', labels, values, parents: labels.map(() => ''),
                textinfo: 'label+value+percent parent',
                marker: { colorscale: [[0,'rgba(249,115,22,0.4)'], [1,'rgba(249,115,22,0.9)']] },
            };
            Plotly.react($advMount, [trace], { ...layout, margin:{t:10,r:10,b:10,l:10} }, PLOTLY_CONFIG);
            return;
        }

        if (type === 'sunburst') {
            const yCol = yCols[0];
            const agg = aggregateRows(rows, xCol, [yCol], aggMode);
            let entries = Object.entries(agg).sort((a,b) => (b[1][yCol]||0)-(a[1][yCol]||0));
            if (topN > 0) entries = entries.slice(0, topN);
            const labels = entries.map(([k]) => k);
            const values = entries.map(([,v]) => Math.max(0, typeof v[yCol]==='number' ? v[yCol] : (v[yCol]||0)));
            const trace = {
                type: 'sunburst', labels, values, parents: labels.map(() => ''),
                branchvalues: 'total',
                marker: { colors: PALETTE.map(p => p.bg) },
                textinfo: 'label+percent entry',
            };
            Plotly.react($advMount, [trace], { ...layout, margin:{t:10,r:10,b:10,l:10} }, PLOTLY_CONFIG);
            return;
        }

        if (type === 'funnel') {
            const yCol = yCols[0];
            const agg = aggregateRows(rows, xCol, [yCol], aggMode);
            let entries = Object.entries(agg).sort((a,b) => (b[1][yCol]||0)-(a[1][yCol]||0));
            if (topN > 0) entries = entries.slice(0, topN);
            const trace = {
                type: 'funnel', y: entries.map(([k])=>k), x: entries.map(([,v]) => typeof v[yCol]==='number' ? v[yCol] : (v[yCol]||0)),
                textinfo: 'value+percent initial',
                marker: { color: entries.map((_,i) => PALETTE[i%PALETTE.length].bg), line: { color: entries.map((_,i) => PALETTE[i%PALETTE.length].b), width:1 } },
            };
            Plotly.react($advMount, [trace], { ...layout, funnelmode:'stack' }, PLOTLY_CONFIG);
            return;
        }

        if (type === 'pyramid') {
            const yCol = yCols[0];
            const agg = aggregateRows(rows, xCol, [yCol], aggMode);
            let entries = Object.entries(agg).sort((a,b) => (a[1][yCol]||0)-(b[1][yCol]||0));
            if (topN > 0) entries = entries.slice(-topN);
            const vals = entries.map(([,v]) => typeof v[yCol]==='number' ? v[yCol] : (v[yCol]||0));
            const trace = {
                type: 'bar', orientation: 'h', y: entries.map(([k])=>k),
                x: vals, text: vals.map(v => v.toLocaleString()), textposition: 'auto',
                marker: { color: entries.map((_,i) => PALETTE[i%PALETTE.length].bg), line:{color:entries.map((_,i)=>PALETTE[i%PALETTE.length].b),width:1} },
            };
            Plotly.react($advMount, [trace], { ...layout, bargap:0.2 }, PLOTLY_CONFIG);
            return;
        }

        if (type === 'gauge') {
            const yCol = yCols[0];
            const vals = rows.map(r => parseFloat(r[yCol])).filter(v => !isNaN(v));
            if (!vals.length) {
                if (window.showCustomAlert) window.showCustomAlert('No numeric data for gauge.');
                return;
            }
            const current = vals.reduce((a,b)=>a+b,0)/vals.length;
            const max = Math.max(...vals);
            const trace = {
                type: 'indicator', mode: 'gauge+number+delta',
                value: current, delta: { reference: max * 0.7 },
                title: { text: yCol, font: { color: '#a8a29e' } },
                gauge: {
                    axis: { range: [null, max], tickcolor:'#78716c' },
                    bar: { color: PALETTE[0].b },
                    bgcolor: 'rgba(28,25,23,0.5)',
                    bordercolor: '#292524',
                    steps: [
                        { range:[0, max*0.4], color:'rgba(16,185,129,0.2)' },
                        { range:[max*0.4, max*0.7], color:'rgba(234,179,8,0.2)' },
                        { range:[max*0.7, max], color:'rgba(244,63,94,0.2)' },
                    ],
                    threshold: { line:{color:'#f97316',width:4}, thickness:0.75, value:max*0.85 }
                }
            };
            Plotly.react($advMount, [trace], { ...layout, margin:{t:60,r:40,b:40,l:40} }, PLOTLY_CONFIG);
            return;
        }

        if (type === 'waterfall') {
            const yCol = yCols[0];
            const agg = aggregateRows(rows, xCol, [yCol], aggMode);
            let entries = Object.entries(agg);
            if (topN > 0) entries = entries.slice(0, topN);
            const trace = {
                type: 'waterfall', x: entries.map(([k])=>k),
                y: entries.map(([,v]) => typeof v[yCol]==='number' ? v[yCol] : (v[yCol]||0)),
                connector: { line: { color: '#78716c', width:1 } },
                increasing: { marker: { color: 'rgba(16,185,129,0.7)', line:{color:'#10b981',width:1} } },
                decreasing: { marker: { color: 'rgba(244,63,94,0.7)', line:{color:'#f43f5e',width:1} } },
                totals: { marker: { color: 'rgba(249,115,22,0.7)', line:{color:'#f97316',width:1} } },
            };
            Plotly.react($advMount, [trace], layout, PLOTLY_CONFIG);
            return;
        }

        if (type === 'pareto') {
            const yCol = yCols[0];
            const agg = aggregateRows(rows, xCol, [yCol], aggMode);
            let entries = Object.entries(agg).sort((a,b) => (b[1][yCol]||0)-(a[1][yCol]||0));
            if (topN > 0) entries = entries.slice(0, topN);
            const vals = entries.map(([,v]) => typeof v[yCol]==='number' ? v[yCol] : (v[yCol]||0));
            const total = vals.reduce((a,b)=>a+b,0);
            let cumSum = 0;
            const cumPct = vals.map(v => { cumSum += v; return total > 0 ? (cumSum/total)*100 : 0; });
            const bar = { type:'bar', x:entries.map(([k])=>k), y:vals, name:yCol, marker:{color:PALETTE[0].bg, line:{color:PALETTE[0].b,width:1}}, yaxis:'y' };
            const line = { type:'scatter', x:entries.map(([k])=>k), y:cumPct, name:'Cumulative %', yaxis:'y2', mode:'lines+markers', line:{color:PALETTE[3].b,width:2}, marker:{size:5,color:PALETTE[3].b} };
            const paretoLayout = { ...layout, yaxis:{...layout.yaxis,title:yCol}, yaxis2:{title:'Cumulative %',overlaying:'y',side:'right',range:[0,100],ticksuffix:'%',gridcolor:'rgba(0,0,0,0)',tickfont:{color:'#78716c'}} };
            Plotly.react($advMount, [bar, line], paretoLayout, PLOTLY_CONFIG);
            return;
        }

        if (type === 'controlChart') {
            const yCol = yCols[0];
            const vals = rows.map(r => parseFloat(r[yCol])).filter(v => !isNaN(v));
            if (!vals.length) {
                if (window.showCustomAlert) window.showCustomAlert('No numeric data for control chart.');
                return;
            }
            const mean = vals.reduce((a,b)=>a+b,0)/vals.length;
            const std  = Math.sqrt(vals.reduce((a,b)=>a+(b-mean)**2,0)/vals.length);
            const ucl = mean + 3*std, lcl = mean - 3*std;
            const xLabels = rows.slice(0, vals.length).map((r, i) => String(r[xCol] ?? i+1));
            const dataLine  = { type:'scatter', x:xLabels, y:vals, mode:'lines+markers', name:yCol, line:{color:PALETTE[0].b,width:2}, marker:{size:5,color:PALETTE[0].b} };
            const meanLine  = { type:'scatter', x:xLabels, y:vals.map(()=>mean), mode:'lines', name:'Mean', line:{color:'rgba(234,179,8,0.8)',width:1.5,dash:'dash'} };
            const uclLine   = { type:'scatter', x:xLabels, y:vals.map(()=>ucl), mode:'lines', name:'UCL (+3σ)', line:{color:'rgba(244,63,94,0.6)',width:1,dash:'dot'} };
            const lclLine   = { type:'scatter', x:xLabels, y:vals.map(()=>lcl), mode:'lines', name:'LCL (−3σ)', line:{color:'rgba(244,63,94,0.6)',width:1,dash:'dot'} };
            Plotly.react($advMount, [dataLine,meanLine,uclLine,lclLine], layout, PLOTLY_CONFIG);
            return;
        }

        if (type === 'candlestick') {
            if (yCols.length < 4) {
                if (window.showCustomAlert) window.showCustomAlert('Candlestick needs 4 Y columns: Open, High, Low, Close.');
                return;
            }
            const [openCol, highCol, lowCol, closeCol] = yCols;
            const trace = {
                type: 'candlestick',
                x: rows.map(r => String(r[xCol])),
                open:  rows.map(r => parseFloat(r[openCol])),
                high:  rows.map(r => parseFloat(r[highCol])),
                low:   rows.map(r => parseFloat(r[lowCol])),
                close: rows.map(r => parseFloat(r[closeCol])),
                increasing: { line:{color:'#10b981'} },
                decreasing: { line:{color:'#f43f5e'} },
            };
            Plotly.react($advMount, [trace], { ...layout, xaxis:{...layout.xaxis,rangeslider:{visible:false}} }, PLOTLY_CONFIG);
            return;
        }

        if (type === 'errorBar') {
            const yCol = yCols[0];
            const agg = {};
            rows.forEach(r => {
                const lbl = String(r[xCol]??'Unknown');
                const v = parseFloat(r[yCol]);
                if (!isNaN(v)) { if (!agg[lbl]) agg[lbl] = []; agg[lbl].push(v); }
            });
            let entries = Object.entries(agg).sort((a,b)=>b[1].reduce((s,v)=>s+v,0)/b[1].length - a[1].reduce((s,v)=>s+v,0)/a[1].length);
            if (topN > 0) entries = entries.slice(0, topN);
            const means = entries.map(([,arr]) => arr.reduce((a,b)=>a+b,0)/arr.length);
            const stds  = entries.map(([,arr]) => { const m=arr.reduce((a,b)=>a+b,0)/arr.length; return Math.sqrt(arr.reduce((a,b)=>a+(b-m)**2,0)/arr.length); });
            const trace = {
                type:'bar', x:entries.map(([k])=>k), y:means, name:yCol,
                error_y: { type:'data', array:stds, visible:true, color:PALETTE[0].b },
                marker: { color:PALETTE[0].bg, line:{color:PALETTE[0].b,width:1} },
            };
            Plotly.react($advMount, [trace], layout, PLOTLY_CONFIG);
            return;
        }

        if (type === 'rangeArea') {
            const yCol = yCols[0]; const sCol = sizeCol || (yCols[1] || yCols[0]);
            const xVals = rows.map(r => String(r[xCol]??''));
            const y1 = rows.map(r => parseFloat(r[yCol])).map(v => isNaN(v)?0:v);
            const y2 = rows.map(r => parseFloat(r[sCol])).map(v => isNaN(v)?0:v);
            const traceUpper = { type:'scatter', x:xVals, y:y2, name:sCol, fill:'tonexty', fillcolor:PALETTE[0].bg, line:{color:PALETTE[0].b,width:1.5}, mode:'lines' };
            const traceLower = { type:'scatter', x:xVals, y:y1, name:yCol, fill:'tozeroy', fillcolor:'rgba(249,115,22,0.1)', line:{color:'rgba(249,115,22,0.4)',width:1.5}, mode:'lines' };
            Plotly.react($advMount, [traceLower, traceUpper], layout, PLOTLY_CONFIG);
            return;
        }

        if (type === 'heatmap') {
            const selCols = numericCols.length >= 2 ? numericCols.slice(0, Math.min(numericCols.length, 15)) : [];
            if (selCols.length < 2) {
                if (window.showCustomAlert) window.showCustomAlert('Heatmap needs at least 2 numeric columns for correlation.');
                return;
            }
            const subRows = rows.map(r => selCols.map(c => parseFloat(r[c]) || 0));
            const n = selCols.length;
            const matrix = [];
            for (let i = 0; i < n; i++) {
                const row = [];
                for (let j = 0; j < n; j++) {
                    const xi = subRows.map(r=>r[i]), xj = subRows.map(r=>r[j]);
                    const mx = xi.reduce((a,b)=>a+b,0)/xi.length, my = xj.reduce((a,b)=>a+b,0)/xj.length;
                    const num = xi.reduce((s,v,k)=>s+(v-mx)*(xj[k]-my),0);
                    const dx  = Math.sqrt(xi.reduce((s,v)=>s+(v-mx)**2,0));
                    const dy  = Math.sqrt(xj.reduce((s,v)=>s+(v-my)**2,0));
                    row.push(dx>0&&dy>0 ? Math.round(num/(dx*dy)*1000)/1000 : (i===j?1:0));
                }
                matrix.push(row);
            }
            const trace = {
                type:'heatmap', x:selCols, y:selCols, z:matrix,
                colorscale:[[0,'rgba(59,130,246,0.8)'],[0.5,'rgba(28,25,23,0.9)'],[1,'rgba(249,115,22,0.9)']],
                zmid:0, texttemplate:'%{z:.2f}', text:matrix, hovertemplate:'%{y} ↔ %{x}: %{z:.3f}<extra></extra>',
            };
            Plotly.react($advMount, [trace], { ...layout, margin:{t:20,r:20,b:120,l:120} }, PLOTLY_CONFIG);
            return;
        }

        if (type === 'hexbin') {
            const yCol = yCols[0];
            const xVals = rows.map(r => parseFloat(r[xCol])).filter((_,i) => !isNaN(parseFloat(rows[i][xCol])));
            const yVals = rows.map(r => parseFloat(r[yCol])).filter((_,i) => !isNaN(parseFloat(rows[i][yCol])));
            const trace = { type:'histogram2d', x:xVals, y:yVals, colorscale:[[0,'rgba(28,25,23,0)'],[0.5,PALETTE[1].bg],[1,PALETTE[0].b]], nbinsx:30, nbinsy:30 };
            Plotly.react($advMount, [trace], { ...layout, xaxis:{...layout.xaxis,title:xCol}, yaxis:{...layout.yaxis,title:yCol} }, PLOTLY_CONFIG);
            return;
        }

        if (type === 'parallelCoords') {
            const selCols = yCols.length ? yCols : numericCols.slice(0, 6);
            if (selCols.length < 2) {
                if (window.showCustomAlert) window.showCustomAlert('Parallel Coords needs at least 2 Y columns.');
                return;
            }
            const dims = selCols.map(c => ({
                label: c,
                values: rows.map(r => parseFloat(r[c]) || 0),
            }));
            const trace = {
                type:'parcoords',
                line: { colorscale:'Oranges', color:rows.map(r => parseFloat(r[selCols[0]])||0), showscale:true },
                dimensions: dims,
            };
            Plotly.react($advMount, [trace], { ...layout, margin:{t:50,r:20,b:30,l:20} }, PLOTLY_CONFIG);
            return;
        }

        if (type === 'sankey') {
            const yCol = yCols[0]; const valCol = sizeCol || yCol;
            const uniqueNodes = [...new Set(rows.flatMap(r => [String(r[xCol]??''), String(r[yCol]??'')]))];
            const nodeIdx = Object.fromEntries(uniqueNodes.map((n,i) => [n,i]));
            const links = { source:[], target:[], value:[] };
            rows.forEach(r => {
                const s = String(r[xCol]??''), t = String(r[yCol]??'');
                const v = parseFloat(r[valCol]) || 1;
                if (s && t && s !== t) { links.source.push(nodeIdx[s]); links.target.push(nodeIdx[t]); links.value.push(v); }
            });
            const trace = {
                type:'sankey',
                node: { pad:15, thickness:20, line:{color:'#1c1917',width:0.5}, label:uniqueNodes, color:uniqueNodes.map((_,i)=>PALETTE[i%PALETTE.length].bg) },
                link: { source:links.source, target:links.target, value:links.value, color:links.source.map(i=>PALETTE[i%PALETTE.length].bg) },
            };
            Plotly.react($advMount, [trace], { ...layout, margin:{t:10,r:10,b:10,l:10} }, PLOTLY_CONFIG);
            return;
        }

        if (type === 'timeline') {
            const startCol = xCol, endCol = sizeCol || yCols[0], taskCol = yCols[0];
            const traces = rows.slice(0, topN||50).map((r, i) => ({
                type:'scatter', mode:'lines',
                x:[String(r[startCol]??''), String(r[endCol]??'')],
                y:[String(r[taskCol]??i), String(r[taskCol]??i)],
                line: { color:PALETTE[i%PALETTE.length].b, width:8 },
                name: String(r[taskCol]??i),
            }));
            Plotly.react($advMount, traces, { ...layout, showlegend:false }, PLOTLY_CONFIG);
            return;
        }

        if (type === 'mosaic') {
            const yCol = yCols[0];
            const agg = aggregateRows(rows, xCol, [yCol], aggMode);
            let entries = Object.entries(agg).sort((a,b)=>(b[1][yCol]||0)-(a[1][yCol]||0));
            if (topN > 0) entries = entries.slice(0, topN);
            const labels = entries.map(([k])=>k);
            const values = entries.map(([,v])=>typeof v[yCol]==='number'?v[yCol]:(v[yCol]||0));
            const trace = {
                type:'treemap', labels, values, parents:labels.map(()=>''),
                branchvalues:'total', tiling:{packing:'squarify'},
                textinfo:'label+value+percent parent',
                marker:{colorscale:[[0,PALETTE[2].bg],[1,PALETTE[0].b]]},
            };
            Plotly.react($advMount, [trace], { ...layout, margin:{t:10,r:10,b:10,l:10} }, PLOTLY_CONFIG);
            return;
        }

        if (type === 'marimekko') {
            const yCol = yCols[0]; const valCol = sizeCol || yCol;
            const agg = aggregateRows(rows, xCol, [yCol, valCol], aggMode);
            let entries = Object.entries(agg).sort((a,b)=>(b[1][valCol]||0)-(a[1][valCol]||0));
            if (topN > 0) entries = entries.slice(0, topN);
            const trace = {
                type:'bar', x:entries.map(([k])=>k), y:entries.map(([,v])=>v[yCol]||0),
                width:entries.map(([,v])=>Math.max(0.1,(v[valCol]||1)/Math.max(...Object.values(agg).map(x=>x[valCol]||1)))),
                marker:{color:entries.map((_,i)=>PALETTE[i%PALETTE.length].bg), line:{color:entries.map((_,i)=>PALETTE[i%PALETTE.length].b),width:1}},
                offset:0,
            };
            Plotly.react($advMount, [trace], { ...layout, bargap:0, xaxis:{...layout.xaxis,title:xCol}, yaxis:{...layout.yaxis,title:yCol} }, PLOTLY_CONFIG);
            return;
        }

        if (type === 'packedBubble') {
            const yCol = yCols[0];
            const agg = aggregateRows(rows, xCol, [yCol], aggMode);
            let entries = Object.entries(agg).sort((a,b)=>(b[1][yCol]||0)-(a[1][yCol]||0));
            if (topN > 0) entries = entries.slice(0, topN);
            const trace = {
                type:'scatter', mode:'markers',
                x: entries.map((_,i) => Math.cos(i/entries.length*2*Math.PI)),
                y: entries.map((_,i) => Math.sin(i/entries.length*2*Math.PI)),
                text: entries.map(([k])=>k), hovertemplate:'%{text}: %{marker.size}<extra></extra>',
                marker: {
                    size: entries.map(([,v])=>{const s=typeof v[yCol]==='number'?v[yCol]:(v[yCol]||0); return Math.max(10, Math.min(80, s/Math.max(...entries.map(([,x])=>x[yCol]||0))*60));}),
                    color: entries.map((_,i)=>PALETTE[i%PALETTE.length].bg),
                    line: { color: entries.map((_,i)=>PALETTE[i%PALETTE.length].b), width:1.5 },
                    sizemode:'diameter',
                },
            };
            Plotly.react($advMount, [trace], { ...layout, showlegend:false, xaxis:{...layout.xaxis,visible:false}, yaxis:{...layout.yaxis,visible:false} }, PLOTLY_CONFIG);
            return;
        }

        if (window.showCustomAlert) window.showCustomAlert(`Chart type "${type}" not yet fully implemented for Plotly. Try another chart type.`);
        showChartState('empty', 'This chart type is coming soon.');
    }

    // ── 15. D3 ENGINE IMPLEMENTATION ──────────────────────────────────────
    async function renderD3(type, rows, xCol, yCols, topN, aggMode) {
        await loadD3();
        destroyCurrentChart();
        showChartState('advanced');
        if ($advMount) {
            $advMount.innerHTML = '';
            $advMount._plotlyInstance = false;
        }

        const w = $advMount ? $advMount.clientWidth || 800 : 800;
        const h = $advMount ? $advMount.clientHeight || 440 : 440;

        if (type === 'wordCloud') {
            const freq = {};
            rows.forEach(r => {
                const text = String(r[xCol]??'');
                text.split(/\s+/).forEach(word => {
                    const w = word.toLowerCase().replace(/[^a-z0-9]/g,'');
                    if (w.length > 2) freq[w] = (freq[w]||0) + 1;
                });
            });
            let words = Object.entries(freq).sort((a,b)=>b[1]-a[1]).slice(0, topN || 80);
            const maxFreq = words[0]?.[1] || 1;
            const svg = d3.select($advMount).append('svg').attr('width',w).attr('height',h).style('background','transparent');
            const g = svg.append('g').attr('transform',`translate(${w/2},${h/2})`);
            const fontScale = d3.scaleLinear().domain([1, maxFreq]).range([12, 55]);
            const colorFn = (i) => PALETTE[i%PALETTE.length].b;

            words.forEach(([word, count], i) => {
                const fontSize = fontScale(count);
                const angle = i * 0.5;
                const x = i * 5 * Math.cos(angle);
                const y = i * 5 * Math.sin(angle) * 0.6;
                g.append('text')
                    .attr('x', x).attr('y', y)
                    .attr('text-anchor','middle').attr('dominant-baseline','middle')
                    .style('font-size', fontSize+'px').style('font-family','Inter,sans-serif')
                    .style('font-weight', count > maxFreq*0.5 ? 'bold':'500')
                    .style('fill', colorFn(i)).style('opacity','0.85')
                    .text(word);
            });
            return;
        }

        if (type === 'streamGraph') {
            const yCol = yCols[0]; const seriesCols = yCols.length > 1 ? yCols : [yCol];
            const allXVals = [...new Set(rows.map(r => String(r[xCol]??'')))].sort();
            const agg = {};
            rows.forEach(r => {
                const x = String(r[xCol]??'');
                if (!agg[x]) agg[x] = {};
                seriesCols.forEach(c => { agg[x][c] = (agg[x][c]||0) + (parseFloat(r[c])||0); });
            });
            const stackData = d3.stack().keys(seriesCols).offset(d3.stackOffsetWiggle)(allXVals.map(x => { const obj={x}; seriesCols.forEach(c=>obj[c]=agg[x]?.[c]||0); return obj; }));
            const margin = {top:10,right:20,bottom:40,left:40};
            const innerW = w - margin.left - margin.right, innerH = h - margin.top - margin.bottom;
            const xScale = d3.scalePoint().domain(allXVals).range([0, innerW]);
            const yScale = d3.scaleLinear().domain([d3.min(stackData,l=>d3.min(l,d=>d[0])), d3.max(stackData,l=>d3.max(l,d=>d[1]))]).range([innerH,0]);
            const area = d3.area().x(d=>xScale(d.data.x)).y0(d=>yScale(d[0])).y1(d=>yScale(d[1])).curve(d3.curveCatmullRom);
            const svg = d3.select($advMount).append('svg').attr('width',w).attr('height',h).style('background','transparent');
            const g = svg.append('g').attr('transform',`translate(${margin.left},${margin.top})`);
            stackData.forEach((layer, i) => {
                g.append('path').datum(layer).attr('d',area).attr('fill',PALETTE[i%PALETTE.length].bg).attr('stroke',PALETTE[i%PALETTE.length].b).attr('stroke-width',1).attr('opacity',0.85);
            });
            g.append('g').attr('transform',`translate(0,${innerH})`).call(d3.axisBottom(xScale).tickSize(4)).selectAll('text').style('fill','#78716c').style('font-size','10px');
            g.append('g').call(d3.axisLeft(yScale).tickSize(4)).selectAll('text').style('fill','#78716c').style('font-size','10px');
            return;
        }

        if (type === 'chord') {
            const yCol = yCols[0];
            const uniqueX = [...new Set(rows.map(r => String(r[xCol]??'')))];
            const uniqueY = [...new Set(rows.map(r => String(r[yCol]??'')))];
            const nodes = [...new Set([...uniqueX, ...uniqueY])].slice(0, 20);
            const idx = Object.fromEntries(nodes.map((n,i)=>[n,i]));
            const matrix = Array.from({length:nodes.length},()=>new Array(nodes.length).fill(0));
            rows.forEach(r => {
                const s = idx[String(r[xCol]??'')], t = idx[String(r[yCol]??'')];
                if (s !== undefined && t !== undefined && s !== t) matrix[s][t]++;
            });
            const margin=30, svgSize=Math.min(w,h)-margin*2;
            const svg = d3.select($advMount).append('svg').attr('width',w).attr('height',h).style('background','transparent');
            const g = svg.append('g').attr('transform',`translate(${w/2},${h/2})`);
            const chord = d3.chord().padAngle(0.04).sortSubgroups(d3.descending)(matrix);
            const arc = d3.arc().innerRadius(svgSize/2-20).outerRadius(svgSize/2);
            const ribbon = d3.ribbon().radius(svgSize/2-20);
            g.selectAll('path.group').data(chord.groups).join('path').attr('class','group').attr('d',arc).attr('fill',d=>PALETTE[d.index%PALETTE.length].bg).attr('stroke',d=>PALETTE[d.index%PALETTE.length].b).attr('stroke-width',0.5).attr('opacity',0.85);
            g.selectAll('path.chord').data(chord).join('path').attr('class','chord').attr('d',ribbon).attr('fill',d=>PALETTE[d.source.index%PALETTE.length].bg).attr('stroke','#1c1917').attr('stroke-width',0.5).attr('opacity',0.7);
            return;
        }

        if (type === 'calendarHeatmap') {
            const yCol = yCols[0];
            const dayMap = {};
            rows.forEach(r => {
                const d = new Date(r[xCol]);
                if (isNaN(d)) return;
                const key = d.toISOString().slice(0,10);
                const v = parseFloat(r[yCol]) || 0;
                dayMap[key] = (dayMap[key]||0) + v;
            });
            const allDates = Object.keys(dayMap).sort();
            if (!allDates.length) {
                if (window.showCustomAlert) window.showCustomAlert('No parseable dates in X column.');
                return;
            }
            const maxVal = Math.max(...Object.values(dayMap));
            const colorScale = d3.scaleSequential().domain([0, maxVal]).interpolator(d3.interpolateOranges);
            const cellSize = Math.min(18, Math.floor((w-120)/55));
            const svg = d3.select($advMount).append('svg').attr('width',w).attr('height',h).style('background','transparent');
            const g = svg.append('g').attr('transform','translate(40,30)');
            allDates.forEach(dateStr => {
                const d = new Date(dateStr+'T00:00:00');
                const week = d3.timeWeek.count(d3.timeYear(d), d);
                const day = d.getDay();
                g.append('rect')
                    .attr('x', week*cellSize).attr('y', day*cellSize)
                    .attr('width', cellSize-1).attr('height', cellSize-1)
                    .attr('rx', 2).attr('ry', 2)
                    .attr('fill', colorScale(dayMap[dateStr]))
                    .attr('opacity', 0.9)
                    .append('title').text(`${dateStr}: ${dayMap[dateStr].toLocaleString()}`);
            });
            const days = ['Su','Mo','Tu','We','Th','Fr','Sa'];
            days.forEach((day,i) => g.append('text').attr('x',-5).attr('y',i*cellSize+cellSize/2).attr('text-anchor','end').attr('dominant-baseline','middle').style('fill','#78716c').style('font-size','8px').text(day));
            return;
        }

        if (window.showCustomAlert) window.showCustomAlert(`D3 chart "${type}" is not yet implemented. Try another type.`);
        showChartState('empty', 'This advanced chart type is coming soon.');
    }

    // ── 16. EXPORTS & FULLSCREEN & ZOOM ───────────────────────────────────
    const exportPngBtn = document.getElementById('exportPngBtn');
    if (exportPngBtn) {
        exportPngBtn.addEventListener('click', () => {
            if (currentChart) {
                const url = currentChart.toBase64Image('image/png', 1.0);
                const a = document.createElement('a'); a.href = url; a.download = 'chart.png'; a.click();
            } else if (_plotlyLoaded && $advMount && $advMount._plotlyInstance) {
                Plotly.downloadImage($advMount, { format:'png', filename:'chart', width:1200, height:800 });
            } else if ($advMount && $advMount.querySelector('svg')) {
                const svg = $advMount.querySelector('svg');
                const canvas = document.createElement('canvas');
                canvas.width = svg.clientWidth || 800; canvas.height = svg.clientHeight || 480;
                const ctx2 = canvas.getContext('2d');
                const data = new XMLSerializer().serializeToString(svg);
                const img = new Image();
                img.onload = () => { ctx2.drawImage(img,0,0); const a=document.createElement('a'); a.href=canvas.toDataURL('image/png'); a.download='chart.png'; a.click(); };
                img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(data)));
            } else {
                if (window.showCustomAlert) window.showCustomAlert('No chart to export. Render a chart first.');
            }
        });
    }

    const exportSvgBtn = document.getElementById('exportSvgBtn');
    if (exportSvgBtn) {
        exportSvgBtn.addEventListener('click', () => {
            const svg = $advMount ? $advMount.querySelector('svg') : null;
            if (svg) {
                const data = new XMLSerializer().serializeToString(svg);
                const blob = new Blob([data], { type: 'image/svg+xml' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a'); a.href = url; a.download = 'chart.svg'; a.click();
                URL.revokeObjectURL(url);
            } else if (currentChart) {
                const url = currentChart.toBase64Image(); const a = document.createElement('a'); a.href = url; a.download = 'chart.png'; a.click();
                if (window.showCustomAlert) window.showCustomAlert('Chart.js charts export as PNG. Use Plotly/D3 chart types for SVG export.');
            } else {
                if (window.showCustomAlert) window.showCustomAlert('No SVG chart to export. Render a chart first.');
            }
        });
    }

    const exportCsvBtn = document.getElementById('exportCsvBtn');
    if (exportCsvBtn) {
        exportCsvBtn.addEventListener('click', () => {
            const fCol = filterColSel ? filterColSel.value : '', fVal = filterValSel ? filterValSel.value : '';
            const exportRows = applyFilter(allRows, fCol, fVal);
            const csv = [columns.join(','), ...exportRows.map(row => columns.map(c => {
                const v = row[c] === null || row[c] === undefined ? '' : String(row[c]);
                return v.includes(',') || v.includes('"') ? `"${v.replace(/"/g,'""')}"` : v;
            }).join(','))].join('\n');
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a'); a.href = url; a.download = 'dataset.csv'; a.click();
            URL.revokeObjectURL(url);
        });
    }

    const fullscreenBtn = document.getElementById('fullscreenBtn');
    if (fullscreenBtn && $chartContainer) {
        fullscreenBtn.addEventListener('click', () => {
            if (!document.fullscreenElement) {
                $chartContainer.requestFullscreen().then(() => {
                    $chartContainer.style.cssText = 'height:100vh;border-radius:0;background:#0c0a09;';
                    if (currentChart) currentChart.resize();
                    if (_plotlyLoaded && $advMount && $advMount._plotlyInstance) Plotly.relayout($advMount, {});
                }).catch(() => {
                    if (window.showCustomAlert) window.showCustomAlert('Fullscreen not available.');
                });
            } else {
                document.exitFullscreen();
            }
        });
    }

    document.addEventListener('fullscreenchange', () => {
        if ($chartContainer) {
            if (!document.fullscreenElement) {
                $chartContainer.style.cssText = '';
                if (currentChart) currentChart.resize();
            }
        }
    });

    const zoomInBtn = document.getElementById('zoomInBtn');
    if (zoomInBtn && $chartCanvas) {
        zoomInBtn.addEventListener('click', () => {
            if (!currentChart) return;
            $chartCanvas.style.transform = `scale(${(parseFloat($chartCanvas.style.transform.match(/[\d.]+/)?.[0]||1)+0.1).toFixed(1)})`;
            $chartCanvas.style.transformOrigin = 'top center';
        });
    }

    const zoomOutBtn = document.getElementById('zoomOutBtn');
    if (zoomOutBtn && $chartCanvas) {
        zoomOutBtn.addEventListener('click', () => {
            if (!currentChart) return;
            const cur = parseFloat($chartCanvas.style.transform.match(/[\d.]+/)?.[0]||1);
            $chartCanvas.style.transform = `scale(${Math.max(0.3, cur-0.1).toFixed(1)})`;
            $chartCanvas.style.transformOrigin = 'top center';
        });
    }

    const resetZoomBtn = document.getElementById('resetZoomBtn');
    if (resetZoomBtn && $chartCanvas) {
        resetZoomBtn.addEventListener('click', () => {
            $chartCanvas.style.transform = 'scale(1)';
        });
    }

    // ── 17. INITIALIZATION ─────────────────────────────────────────────────
    if (aggModeSel) aggModeSel.addEventListener('change', syncControls);
    if (renderBtn) renderBtn.addEventListener('click', renderChart);

    buildDropdown();
    setActiveChart('bar');

    if (columns.length && numericCols.length) {
        showChartState('empty', 'Click "Render Chart" to visualize your data.');
        setTimeout(renderChart, 400);
    } else {
        showChartState('empty', 'This dataset has no numeric columns. Upload a dataset with numeric data to use charts.');
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAnalytics);
} else {
    initAnalytics();
}
