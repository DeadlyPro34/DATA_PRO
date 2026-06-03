import { useState, useRef, useEffect, useCallback } from "react";
import * as XLSX from "xlsx";
import api, { datasetAPI, authAPI } from "./api";
import Chart from "react-apexcharts";
import { Navbar } from './components/layout/Navbar';
import { WelcomeScreen } from './components/layout/WelcomeScreen';
import { Button } from './components/ui/Button';
import { Input, Select } from './components/ui/Input';
import { Card } from './components/ui/Card';
import { Search, ChevronUp, ChevronDown, CheckCircle, AlertCircle, RefreshCw, Upload, Download, LogOut, Key, ArrowRight, Trash2, Scissors, PenLine, CopyMinus, CaseUpper, Bot, Database, Activity, List, Shield, Terminal, ArrowUpDown, BarChart2, FileText } from 'lucide-react';
// ─── helpers ────────────────────────────────────────────────────────────────
const COL = (i) => { let s=""; i++; while(i>0){i--;s=String.fromCharCode(65+(i%26))+s;i=Math.floor(i/26);} return s; };
const FUNS = ["SUM","AVERAGE","COUNT","MAX","MIN","MEDIAN","STDEV","VARIANCE"];
const ROW_HEIGHT = 26; // px — fixed height for virtual scroll

function evalFormula(f, data) {
  if(!f||!String(f).startsWith("=")) return f??"";
  const expr=String(f).slice(1).trim().toUpperCase();
  for(const fn of FUNS){
    const m=expr.match(new RegExp(`^${fn}\\((.+)\\)$`));
    if(m){
      const arg=m[1];
      const vals=arg.split(",").map(a=>{
        const cm=a.trim().match(/^([A-Z]+)(\d+)$/);
        if(!cm) return parseFloat(a)||0;
        const c=cm[1].split("").reduce((x,ch)=>x*26+ch.charCodeAt(0)-64,0)-1;
        const r=+cm[2]-1;
        const row=data[r];
        if(!row) return 0;
        const v=Array.isArray(row)?row[c]:Object.values(row)[c];
        return parseFloat(v)||0;
      });
      if(!vals.length) return "#VALUE!";
      switch(fn){
        case "SUM":      return +vals.reduce((a,b)=>a+b,0).toFixed(4);
        case "AVERAGE":  return +(vals.reduce((a,b)=>a+b,0)/vals.length).toFixed(4);
        case "COUNT":    return vals.length;
        case "MAX":      return Math.max(...vals);
        case "MIN":      return Math.min(...vals);
        case "MEDIAN":   { const s=[...vals].sort((a,b)=>a-b),m2=Math.floor(s.length/2); return s.length%2?s[m2]:+((s[m2-1]+s[m2])/2).toFixed(4); }
        case "STDEV":    { const avg=vals.reduce((a,b)=>a+b,0)/vals.length; return +Math.sqrt(vals.reduce((a,b)=>a+(b-avg)**2,0)/vals.length).toFixed(4); }
        case "VARIANCE": { const avg=vals.reduce((a,b)=>a+b,0)/vals.length; return +(vals.reduce((a,b)=>a+(b-avg)**2,0)/vals.length).toFixed(4); }
      }
    }
  }
  return "#NAME?";
}

function dataToCSV(rows, columns) {
  const lines = [columns.join(",")];
  for (const row of rows) lines.push(columns.map(c => `"${String(row[c]??'').replace(/"/g,'""')}"`).join(","));
  return lines.join("\n");
}

// ─── Mini Charts ─────────────────────────────────────────────────────────────
function MiniChart({ rows, columns, xCol, yCol, type }) {
  if(!rows||rows.length<1||!columns.length) return null;
  const labels = rows.map(r=>String(r[columns[xCol]]||""));
  
  // Clean currency/commas and parse float
  const values = rows.map(r=>{
    const v = String(r[columns[yCol]]||"").replace(/[$,]/g,"");
    const n = parseFloat(v);
    return isNaN(n) ? 0 : n;
  });
  
  if (values.every(v => v === 0)) {
    return <div style={{padding:40, textAlign:"center", color:"#ff6b6b", fontSize:13}}>⚠️ Please select a <b>numeric column</b> for the Y-Axis (e.g. Sales, Profit).</div>;
  }

  const isPieType = ["pie", "donut", "radialBar", "polarArea"].includes(type);

  // Group very small slices for pie/donut to avoid extreme clutter
  let finalSeries = values;
  let finalLabels = labels;
  
  const MAX_PIE_SLICES = type === 'radialBar' ? 7 : 10;
  
  if (isPieType && values.length > MAX_PIE_SLICES) {
      let combined = values.map((v, i) => ({v: Math.abs(v), l: labels[i]})).sort((a,b)=>b.v - a.v);
      const top = combined.slice(0, MAX_PIE_SLICES - 1);
      const otherSum = combined.slice(MAX_PIE_SLICES - 1).reduce((acc, curr) => acc + curr.v, 0);
      finalSeries = [...top.map(x=>x.v), otherSum];
      finalLabels = [...top.map(x=>x.l), "Other"];
  } else if (type === 'radar' && values.length > 15) {
      // Radar charts freeze with too many points, limit to top 15
      let combined = values.map((v, i) => ({v, l: labels[i]})).sort((a,b)=>b.v - a.v);
      const top = combined.slice(0, 15);
      finalSeries = top.map(x=>x.v);
      finalLabels = top.map(x=>x.l);
  } else if (values.length > 150 && !isPieType) {
      // Downsample extremely dense data to prevent visual clumsiness and UI lag
      const factor = Math.ceil(values.length / 100);
      finalSeries = values.filter((_, i) => i % factor === 0);
      finalLabels = labels.filter((_, i) => i % factor === 0);
  }

  const options = {
    chart: { 
      background: 'transparent',
      foreColor: '#8b949e',
      animations: { enabled: true },
      toolbar: { show: false },
      stacked: type.includes("stacked"),
      stackType: type.includes("100-stacked") ? "100%" : "normal"
    },
    theme: { mode: 'light' },
    colors: ["#3B82F6","#06B6D4","#4F46E5","#8B5CF6","#EC4899","#10B981","#F59E0B","#EF4444","#0EA5E9"],
    xaxis: {
      categories: isPieType ? [] : finalLabels,
      labels: {
        style: { fontSize: '10px' },
        rotate: -45,
        rotateAlways: false,
        hideOverlappingLabels: true,
      },
      axisBorder: { color: 'var(--border-medium)' },
      axisTicks: { color: 'var(--border-medium)' }
    },
    yaxis: {
      labels: {
        formatter: (val) => { return val && val.toLocaleString ? val.toLocaleString() : val }
      }
    },
    grid: {
      borderColor: 'var(--border-light)',
      strokeDashArray: 3,
    },
    dataLabels: {
      enabled: isPieType,
      dropShadow: { enabled: true },
      formatter: function (val, opts) {
        // Keep data labels short and clean to prevent overlapping
        if (typeof val === 'number') {
            return type === 'polarArea' ? val.toLocaleString() : Math.round(val) + "%";
        }
        return val;
      }
    },
    stroke: {
      curve: 'smooth',
      width: (type === 'line' || type === 'area' || type === 'radar') ? (finalSeries.length > 50 ? 1.5 : 3) : 0
    },
    labels: isPieType ? finalLabels : [],
    legend: {
      show: true,
      position: isPieType ? 'right' : 'bottom',
      labels: { colors: 'var(--text-secondary)' }
    },
    plotOptions: {
      bar: { 
        borderRadius: type === "histogram" || type === "funnel" ? 0 : 4, 
        horizontal: ["h-bar", "stacked-bar", "100-stacked-bar", "funnel"].includes(type),
        columnWidth: type === "histogram" ? "100%" : "70%"
      },
      radialBar: { hollow: { size: '40%' } }
    },
    tooltip: { theme: 'light' }
  };

  // Complex fake data mapping for advanced charts
  let chartSeries = [];
  if (isPieType || type === "sunburst") {
    chartSeries = finalSeries;
  } else if (type === "boxPlot" || type === "candlestick") {
    chartSeries = [{
      name: columns[yCol],
      data: finalSeries.map((v, i) => ({ 
        x: finalLabels[i], 
        y: type === "boxPlot" ? [v-15, v-5, v, v+5, v+15] : [v-5, v+15, v-10, v+2] 
      }))
    }];
  } else if (type === "bubble") {
    chartSeries = [{
      name: columns[yCol],
      data: finalSeries.map((v, i) => ({ x: finalLabels[i], y: v, z: Math.max(5, Math.abs(v)/2) }))
    }];
  } else if (type === "treemap" || type === "heatmap") {
    chartSeries = [{
      name: columns[yCol],
      data: finalSeries.map((v, i) => ({ x: finalLabels[i], y: Math.abs(v) }))
    }];
  } else if (type === "pareto" || type === "combo") {
    chartSeries = [
      { name: columns[yCol] + " (Bar)", type: "column", data: finalSeries },
      { name: "Trend", type: "line", data: finalSeries.map(v => v * 1.1) }
    ];
  } else {
    chartSeries = [{ name: columns[yCol], data: finalSeries }];
  }

  let actualType = type;
  if (["h-bar", "stacked-col", "stacked-bar", "100-stacked-col", "100-stacked-bar", "histogram", "funnel", "waterfall"].includes(type)) actualType = "bar";
  if (["pareto", "combo"].includes(type)) actualType = "line";
  if (type === "sunburst") actualType = "polarArea"; // Fallback

  const isHorizontal = ["h-bar", "stacked-bar", "100-stacked-bar", "funnel"].includes(type);
  const dynamicHeight = isHorizontal ? Math.max(350, finalSeries.length * 20) : 350;

  return (
    <div style={{width: "100%", padding: "10px 0"}}>
      <Chart options={options} series={chartSeries} type={actualType} height={dynamicHeight} />
    </div>
  );
}

// ─── Virtual Scroll Grid ──────────────────────────────────────────────────────
function VirtualGrid({ columns, rows, onCellClick, onCellDblClick, selected, editCell, editRef, editValue, setEditValue, commitEdit, setEditCell }) {
  const containerRef = useRef(null);
  const [scrollTop, setScrollTop] = useState(0);
  const [containerH, setContainerH] = useState(400);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver(entries => setContainerH(entries[0].contentRect.height));
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  const totalH = rows.length * ROW_HEIGHT;
  const visibleCount = Math.ceil(containerH / ROW_HEIGHT) + 4;
  const startIdx = Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - 2);
  const endIdx   = Math.min(rows.length, startIdx + visibleCount);
  const visibleRows = rows.slice(startIdx, endIdx);

  return (
    <div ref={containerRef} style={{flex:1,overflow:"auto",position:"relative"}} onScroll={e=>setScrollTop(e.target.scrollTop)}>
      <div style={{height:totalH+ROW_HEIGHT,minWidth:"max-content",position:"relative"}}>
        {/* Sticky header */}
        <div style={{position:"sticky",top:0,zIndex:5,display:"flex",background:"var(--bg-surface)",borderBottom:"2px solid var(--border-focus)"}}>
          <div style={{minWidth:50,width:50,height:ROW_HEIGHT,background:"var(--bg-surface)",borderRight:"1px solid var(--border-light)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:11,color:"var(--text-secondary)",flexShrink:0}}>#</div>
          {columns.map((col,c)=>(
            <div key={c} style={{width:150,height:ROW_HEIGHT,padding:"0 12px",display:"flex",alignItems:"center",borderRight:"1px solid var(--border-light)",fontSize:13,fontWeight:700,color:"var(--accent-indigo)",overflow:"hidden",flexShrink:0}}>
              {COL(c)} · {col}
            </div>
          ))}
        </div>

        {/* Spacer before visible rows */}
        <div style={{height: startIdx * ROW_HEIGHT}}/>

        {/* Visible rows */}
        {visibleRows.map((row, relIdx) => {
          const absIdx = startIdx + relIdx;
          return (
            <div key={absIdx} style={{display:"flex",borderBottom:"1px solid var(--border-light)",height:ROW_HEIGHT,background:absIdx%2===0?"var(--bg-subtle)":"var(--bg-surface)"}}>
              <div style={{minWidth:50,width:50,display:"flex",alignItems:"center",justifyContent:"center",fontSize:11,color:"var(--text-secondary)",borderRight:"1px solid var(--border-light)",flexShrink:0, background: 'var(--bg-surface)'}}>{absIdx+1}</div>
              {columns.map((col,c)=>{
                const isSel=selected?.r===absIdx&&selected?.c===c;
                const val=String(row[col]??"");
                const isEdit=editCell?.r===absIdx&&editCell?.c===c;
                return (
                  <div key={c}
                    onClick={()=>onCellClick(absIdx,c,col,val)}
                    onDoubleClick={()=>onCellDblClick(absIdx,c,col,val)}
                    style={{width:150,padding:"0 12px",display:"flex",alignItems:"center",borderRight:"1px solid var(--border-light)",overflow:"hidden",cursor:"cell",flexShrink:0,
                            background:isSel?"var(--border-focus)":"transparent",
                            outline:isSel?"2px solid var(--accent-indigo) inset":"none",
                            fontSize:13,color:"var(--text-primary)",whiteSpace:"nowrap",textOverflow:"ellipsis", transition: 'background 0.1s'}}>
                    {isEdit?(
                      <input ref={editRef} value={editValue} onChange={e=>setEditValue(e.target.value)}
                             onBlur={commitEdit} onKeyDown={e=>{if(e.key==="Enter")commitEdit();if(e.key==="Escape")setEditCell(null);}}
                             style={{width:"100%",background:"transparent",border:"none",outline:"none",color:"var(--text-primary)",fontSize:13,fontFamily:"inherit"}}/>
                    ):(
                      <span title={val}>{val.startsWith("=")?evalFormula(val,[]):val}</span>
                    )}
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Upload Progress Bar ──────────────────────────────────────────────────────
function UploadProgress({ progress, status, name }) {
  if (progress === null) return null;
  const color = status === "error" ? "var(--danger-color)" : status === "ready" ? "var(--accent-indigo)" : "var(--accent-indigo)";
  return (
    <div className="glass-panel animate-fade-in" style={{
      position: "fixed", bottom: 24, right: 24, zIndex: 999, minWidth: 320, padding: "16px 24px",
      border: "1px solid var(--border-focus)", borderRadius: "var(--radius-lg)", boxShadow: "var(--shadow-lg)"
    }}>
      <div style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 12, display: "flex", justifyContent: "space-between", fontWeight: 500 }}>
        <span>📤 {name}</span>
        <span style={{ color, fontWeight: 700 }}>
          {status === "ready" ? "✅ Ready!" : status === "error" ? "❌ Error" : status === "processing" ? "⚙️ Processing..." : progress < 100 ? "Uploading..." : "Waiting..."}
        </span>
      </div>
      <div style={{ height: 6, background: "var(--border-light)", borderRadius: 3, overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${progress}%`, background: color, borderRadius: 3, transition: "width .3s ease", boxShadow: `0 0 10px ${color}88` }}/>
      </div>
      {progress === 100 && status !== "ready" && status !== "error" && (
        <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 10, textAlign: "center", display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
          <RefreshCw size={12} className="spin" /> Celery processing in background...
        </div>
      )}
    </div>
  );
}

// ─── Main App ────────────────────────────────────────────────────────────────
const TABS = ["📊 Spreadsheet","📈 Charts","🧹 Data Cleaner","📁 Datasets","🤖 AI Chat"];

export default function DataProSuper({ user, onLogout }) {
  // ── Spreadsheet state (now backed by API rows) ────────────────────────────
  const [activeDataset, setActiveDataset] = useState(null); // Dataset metadata obj
  const [columns, setColumns] = useState([]);
  const [rows, setRows] = useState([]);
  const [totalRows, setTotalRows] = useState(0);
  const [loadingRows, setLoadingRows] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasNextPage, setHasNextPage] = useState(false);

  // ── Datasets tab ──────────────────────────────────────────────────────────
  const [datasets, setDatasets] = useState([]);
  const [datasetsLoading, setDatasetsLoading] = useState(false);

  // ── Upload ────────────────────────────────────────────────────────────────
  const [uploadProgress, setUploadProgress] = useState(null); // 0-100
  const [uploadStatus, setUploadStatus] = useState("idle");   // idle|uploading|processing|ready|error
  const [uploadName, setUploadName] = useState("");
  const [pollTimer, setPollTimer] = useState(null);

  // ── Spreadsheet UI ────────────────────────────────────────────────────────
  const [activeTab, setActiveTab] = useState(0);
  const [selected, setSelected] = useState(null);
  const [editCell, setEditCell] = useState(null);
  const [editValue, setEditValue] = useState("");
  const [formulaBar, setFormulaBar] = useState("");
  const [filterText, setFilterText] = useState("");
  const [cleanLog, setCleanLog] = useState([]);

  // ── Charts ────────────────────────────────────────────────────────────────
  const [chartXCol, setChartXCol] = useState(0);
  const [chartYCol, setChartYCol] = useState(2);
  const [chartType, setChartType] = useState("bar");

  // ── AI Chat ───────────────────────────────────────────────────────────────
  const [groqKey, setGroqKey] = useState(localStorage.getItem("groq_key")||"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");
  const [showKeyInput, setShowKeyInput] = useState(false);
  const [messages, setMessages] = useState([{role:"ai", type:"welcome"}]);
  const [chatInput, setChatInput] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [zoom, setZoom] = useState(100);

  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const editRef = useRef(null);

  useEffect(()=>{chatEndRef.current?.scrollIntoView({behavior:"smooth"});},[messages]);
  useEffect(()=>{if(editCell&&editRef.current)editRef.current.focus();},[editCell]);

  // ── Load datasets on mount ────────────────────────────────────────────────
  useEffect(()=>{ fetchDatasets(); }, []);

  const fetchDatasets = async () => {
    setDatasetsLoading(true);
    try {
      const { data } = await datasetAPI.list();
      setDatasets(data);
    } catch(e) { console.error("fetchDatasets error:", e); }
    setDatasetsLoading(false);
  };

  // ── Load rows from API ────────────────────────────────────────────────────
  const loadDatasetRows = useCallback(async (dataset, page=1) => {
    if(!dataset || dataset.status!=="ready") return;
    setLoadingRows(true);
    try {
      const { data } = await datasetAPI.rows(dataset.id, page, 200);
      setColumns(dataset.columns);
      if(page===1) setRows(data.results);
      else setRows(r=>[...r,...data.results]);
      setTotalRows(data.count);
      setHasNextPage(!!data.next);
      setCurrentPage(page);
    } catch(e){ console.error("loadDatasetRows error:", e); }
    setLoadingRows(false);
  }, []);

  const loadMoreRows = () => {
    if(activeDataset && hasNextPage && !loadingRows)
      loadDatasetRows(activeDataset, currentPage+1);
  };

  // ── Upload flow ───────────────────────────────────────────────────────────
  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if(!file) return;
    e.target.value = "";

    setUploadName(file.name);
    setUploadProgress(0);
    setUploadStatus("uploading");

    try {
      const { data: dataset } = await datasetAPI.upload(file, file.name, (pct)=>{
        setUploadProgress(pct);
      });

      setUploadProgress(100);
      setUploadStatus("processing");
      addCleanLog(`Uploaded "${file.name}" → dataset #${dataset.id}`);

      // Poll until status === "ready" or "error"
      startPolling(dataset.id);
      await fetchDatasets();

    } catch(err) {
      setUploadStatus("error");
      const msg = err.response?.data?.file || err.response?.data?.detail || err.message;
      addCleanLog(`Upload failed: ${msg}`);
    }
  };

  const startPolling = (datasetId) => {
    if(pollTimer) clearInterval(pollTimer);
    const timer = setInterval(async () => {
      try {
        const { data } = await datasetAPI.detail(datasetId);
        setDatasets(ds => ds.map(d => d.id===datasetId ? data : d));

        if(data.status==="ready"){
          clearInterval(timer);
          setUploadStatus("ready");
          // Auto-load if no active dataset
          setActiveDataset(data);
          await loadDatasetRows(data, 1);
          setActiveTab(0);
          setTimeout(()=>setUploadProgress(null), 3000);
        } else if(data.status==="error"){
          clearInterval(timer);
          setUploadStatus("error");
          setTimeout(()=>setUploadProgress(null), 5000);
        }
      } catch { clearInterval(timer); }
    }, 2000);
    setPollTimer(timer);
  };

  // ── Spreadsheet helpers ───────────────────────────────────────────────────
  const addCleanLog = (msg) => setCleanLog(l=>[...l,{time:new Date().toLocaleTimeString(),msg}]);

  const sortCol = (colName, asc=true) => {
    const sorted = [...rows].sort((a,b)=>{
      const av=a[colName],bv=b[colName],an=parseFloat(av),bn=parseFloat(bv);
      if(!isNaN(an)&&!isNaN(bn)) return asc?an-bn:bn-an;
      return asc?String(av).localeCompare(String(bv)):String(bv).localeCompare(String(av));
    });
    setRows(sorted);
    addCleanLog(`"${colName}" sorted ${asc?"A→Z":"Z→A"}`);
  };

  const commitEdit = async () => {
    if (!editCell) return;
    const { r, col } = editCell;

    // 1. Update UI instantly (optimistic)
    setRows(rs => rs.map((row, i) => i === r ? { ...row, [col]: editValue } : row));
    setEditCell(null);

    // 2. Save to PostgreSQL
    if (activeDataset) {
      try {
        await datasetAPI.updateCell(activeDataset.id, r, col, editValue);
      } catch (err) {
        console.error("Cell save failed:", err);
        // Optionally show a small error toast
      }
    }
  };

  const filteredRows = filterText
    ? rows.filter(r=>Object.values(r).some(v=>String(v).toLowerCase().includes(filterText.toLowerCase())))
    : rows;

  // ── Export Excel ──────────────────────────────────────────────────────────
  const exportExcel = () => {
    const data = [columns, ...rows.map(r=>columns.map(c=>r[c]))];
    const ws = XLSX.utils.aoa_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Sheet1");
    XLSX.writeFile(wb, `datapro_${activeDataset?.name||"export"}.xlsx`);
  };

  // ── Groq AI ───────────────────────────────────────────────────────────────
  const saveGroqKey = (k) => { setGroqKey(k); localStorage.setItem("groq_key",k); };

  const sendMessage = async () => {
    const msg = chatInput.trim();
    if (!msg || aiLoading) return;
    if (!groqKey) {
      setMessages(m => [...m, { role: "user", text: msg }, { role: "ai", text: "⚠️ Pehle Groq key daalo!" }]);
      setChatInput("");
      return;
    }

    setChatInput("");
    setMessages(m => [...m, { role: "user", text: msg }]);
    setAiLoading(true);

    const sys = `You are DATA PRO's AI assistant. 
Dataset: "${activeDataset?.name || 'unknown'}"
Columns: ${JSON.stringify(columns)}
First 3 rows sample: ${JSON.stringify(rows.slice(0, 3))}
Today: ${new Date().toISOString().split("T")[0]}

Respond ONLY with valid JSON (no markdown, no extra text):
{
  "action": "python" | "sort" | "chart" | "add_row" | "add_column" | "function" | "message",
  "message": "Hinglish helpful response",

  "code": "df['Bonus'] = df['Salary'].astype(float) * 0.10",  // for action=python

  "colName": "Salary",       // for action=sort
  "ascending": true,         // for action=sort

  "chartType": "bar",        // for action=chart
  "xCol": 0,                 // for action=chart
  "yCol": 2,                 // for action=chart

  "function": "SUM",         // for action=function (SUM|AVG|MAX|MIN|COUNT|MEDIAN|STDEV)
  "column": "Salary",        // for action=function
  "result_column": "Total"   // for action=function (optional)
}

Rules:
- For ANY data calculation/transformation → use "python" with pandas code
- df is already loaded, pd and np are available
- Do NOT use print(), do NOT import anything
- For "add column with formula" → python action
- For averages/sums saved to sheet → python action  
- For simple sort → sort action
- Always respond in Hinglish (Hindi + English mix)`;

    try {
      const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${groqKey}` },
        body: JSON.stringify({
          model: "llama-3.3-70b-versatile",
          max_tokens: 600,
          messages: [{ role: "system", content: sys }, { role: "user", content: msg }]
        })
      });

      const rd = await res.json();
      if (rd.error) throw new Error(rd.error.message);

      const raw = rd.choices?.[0]?.message?.content || "{}";
      const p   = JSON.parse(raw.replace(/```json|```/g, "").trim());

      if (p.action === "python" && p.code && activeDataset) {
        // Run pandas code on backend
        const result = await datasetAPI.aiPandas(activeDataset.id, p.code);
        // Refetch updated rows + columns
        const updated = await datasetAPI.rows(activeDataset.id, 1, 200);
        setColumns(result.data.columns);
        setRows(updated.data.results);
        setTotalRows(updated.data.count);
        addCleanLog(`AI: ${p.code.slice(0, 60)}...`);

      } else if (p.action === "sort" && p.colName) {
        sortCol(p.colName, p.ascending !== false);

      } else if (p.action === "chart") {
        setChartType(p.chartType || "bar");
        if (p.xCol != null) setChartXCol(p.xCol);
        if (p.yCol != null) setChartYCol(p.yCol);
        setActiveTab(1);

      } else if (p.action === "add_row" && activeDataset) {
        const result = await datasetAPI.addRow(activeDataset.id, p.data || {});
        setRows(rs => [...rs, result.data.data]);
        setTotalRows(t => t + 1);

      } else if (p.action === "add_column" && activeDataset) {
        const col = p.column_name || `NewCol_${columns.length + 1}`;
        const result = await datasetAPI.addColumn(activeDataset.id, col);
        setColumns(result.data.columns);
        setRows(rs => rs.map(r => ({ ...r, [col]: "" })));

      } else if (p.action === "function" && p.function && p.column && activeDataset) {
        const result = await datasetAPI.applyFunction(
          activeDataset.id, p.function, p.column, p.result_column || null
        );
        // If saved to a column, refetch
        if (p.result_column) {
          const updated = await datasetAPI.rows(activeDataset.id, 1, 200);
          setRows(updated.data.results);
        }
        setMessages(m => [...m, {
          role: "ai",
          text: `${p.message}\n\n📊 ${p.function}(${p.column}) = **${result.data.result}**`
        }]);
        setAiLoading(false);
        return;
      }

      setMessages(m => [...m, { role: "ai", text: p.message || "✅ Done!" }]);

    } catch (e) {
      setMessages(m => [...m, { role: "ai", text: "❌ " + e.message }]);
    }

    setAiLoading(false);
  };

  // ── UI ────────────────────────────────────────────────────────────────────
  const statusColor = (s) => s==="ready"?"#7fff7f":s==="error"?"#ff6b6b":s==="processing"?"#ffd700":"#8b949e";

  return (
    <div style={{fontFamily:"'Segoe UI',Calibri,sans-serif",background:"var(--bg-app)",color:"var(--text-primary)",height:"100vh",display:"flex",flexDirection:"column",overflow:"hidden"}}>

      {/* Upload progress toast */}
      <UploadProgress progress={uploadProgress} status={uploadStatus} name={uploadName}/>

      {/* Header (Navbar) */}
      <Navbar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        onLogoClick={() => { setActiveTab(0); setActiveDataset(null); setRows([]); setColumns([]); }}
      >
        <div style={{ padding: '6px 12px', background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)', fontSize: '12px', fontWeight: 500 }}>
          {user?.username}
        </div>
        
        <Button variant={groqKey ? 'secondary' : 'danger'} size="sm" onClick={() => setShowKeyInput(v => !v)}>
          <Key size={14} />
          {groqKey ? 'Key Set' : 'Add Groq Key'}
        </Button>

        {showKeyInput && (
          <div className="glass-panel animate-fade-in" style={{
            position: 'absolute', top: '60px', right: '180px', 
            border: '1px solid var(--border-focus)', borderRadius: 'var(--radius-lg)', 
            padding: '20px', zIndex: 100, width: '320px', 
            boxShadow: 'var(--shadow-lg)'
          }}>
            <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '12px' }}>
              Groq API Key (console.groq.com — free!)
            </div>
            <Input 
              value={groqKey} 
              onChange={e => saveGroqKey(e.target.value)} 
              placeholder="gsk_xxxxxxx" 
              style={{ width: '100%', marginBottom: '12px' }} 
            />
            <Button variant="primary" style={{ width: '100%' }} onClick={() => setShowKeyInput(false)}>
              Save & Close
            </Button>
          </div>
        )}

        <Button variant="secondary" size="sm" onClick={() => fileInputRef.current?.click()}>
          <Upload size={14} /> Upload
        </Button>
        <Button variant="secondary" size="sm" onClick={exportExcel}>
          <Download size={14} /> Export
        </Button>
        <Button variant="danger" size="sm" onClick={onLogout}>
          <LogOut size={14} /> Logout
        </Button>
        <input ref={fileInputRef} type="file" accept=".xlsx,.xls,.xlsm,.json" style={{ display: "none" }} onChange={handleUpload}/>
      </Navbar>

      {/* Body */}
      <div style={{ flex: 1, overflow: "hidden", display: "flex", background: "transparent" }}>

        {/* ── TAB 0: Spreadsheet ── */}
        {activeTab === 0 && (
          !activeDataset ? (
            <WelcomeScreen 
              onUploadClick={() => fileInputRef.current?.click()}
              onDatasetsClick={() => setActiveTab(3)}
              onAiClick={() => setActiveTab(4)}
            />
          ) : (
          <div style={{flex:1,display:"flex",flexDirection:"column",overflow:"hidden"}}>
            {/* Ribbon */}
            {/* Ribbon */}
            <div style={{background:"var(--bg-surface)",borderBottom:"1px solid var(--border-light)",padding:"8px 16px",display:"flex",alignItems:"center",gap:12,flexWrap:"wrap",flexShrink:0}}>
              <Button variant="secondary" size="sm" onClick={()=>sortCol(columns[selected?.c||0],true)}>
                <ChevronUp size={14} /> Sort Asc
              </Button>
              <Button variant="secondary" size="sm" onClick={()=>sortCol(columns[selected?.c||0],false)}>
                <ChevronDown size={14} /> Sort Desc
              </Button>
              
              <Button variant="secondary" size="sm" onClick={async () => {
                if (!activeDataset) return;
                const result = await datasetAPI.addRow(activeDataset.id);
                setRows(rs => [...rs, result.data.data]);
                setTotalRows(t => t + 1);
                addCleanLog("New row added");
              }}>
                + Row
              </Button>

              <Button variant="secondary" size="sm" onClick={async () => {
                if (!activeDataset) return;
                const colName = prompt("Naya column naam?");
                if (!colName) return;
                const result = await datasetAPI.addColumn(activeDataset.id, colName);
                setColumns(result.data.columns);
                setRows(rs => rs.map(r => ({ ...r, [colName]: "" })));
                addCleanLog(`Column "${colName}" added`);
              }}>
                + Column
              </Button>

              <select onChange={async (e) => {
                const fn = e.target.value;
                if (!fn || !activeDataset) return;
                const col = columns[selected?.c || 0];
                if (!col) return;
                const resultCol = `${fn}_${col}`;
                const result = await datasetAPI.applyFunction(activeDataset.id, fn, col, resultCol);
                const updated = await datasetAPI.rows(activeDataset.id, 1, 200);
                setColumns(result.data.columns || columns);
                setRows(updated.data.results);
                addCleanLog(`${fn}(${col}) = ${result.data.result} → saved to "${resultCol}"`);
                e.target.value = "";
              }} style={{ padding: "4px 8px", background: "var(--bg-subtle)", border: "1px solid var(--border-light)", borderRadius: "var(--radius-sm)", color: "var(--text-primary)", fontSize: 12 }}>
                <option value="">ƒx Function...</option>
                {["SUM","AVG","MAX","MIN","COUNT","MEDIAN","STDEV","VARIANCE"].map(f =>
                  <option key={f} value={f}>{f}</option>
                )}
              </select>
              
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <Search size={14} style={{ position: 'absolute', left: 10, color: 'var(--text-secondary)' }} />
                <Input value={filterText} onChange={e=>setFilterText(e.target.value)} placeholder="Filter rows..." style={{ paddingLeft: 30, width: 200 }} />
              </div>

              <Select value={zoom} onChange={e=>setZoom(+e.target.value)}>
                {[75,90,100,125,150].map(z=><option key={z} value={z}>{z}% Zoom</option>)}
              </Select>
              
              {activeDataset&&<span style={{fontSize:13,color:"var(--text-secondary)",marginLeft:16, fontWeight: 500}}>
                <CheckCircle size={14} style={{display:'inline', verticalAlign:'text-bottom', marginRight:4}}/> 
                {activeDataset.name}
              </span>}
              {loadingRows&&<span style={{fontSize:12,color:"var(--accent-indigo)", fontWeight: 500}}>
                <RefreshCw size={14} className="spin" style={{display:'inline', verticalAlign:'text-bottom', marginRight:4}}/> 
                Loading...
              </span>}
            </div>

            {/* Formula Bar */}
            <div style={{background:"var(--bg-surface)",borderBottom:"1px solid var(--border-light)",display:"flex",alignItems:"center",gap:12,padding:"6px 16px",flexShrink:0}}>
              <div style={{background:"var(--bg-subtle)",border:"1px solid var(--border-focus)",borderRadius:"var(--radius-sm)",padding:"4px 12px",minWidth:80,textAlign:"center",fontSize:12,color:"var(--accent-indigo)",fontWeight:700}}>
                {selected?`${COL(selected.c)}${selected.r+1}`:""}
              </div>
              <span style={{color:"var(--text-secondary)",fontSize:16, fontWeight:500}}>ƒx</span>
              <Input 
                value={formulaBar} 
                onChange={e=>setFormulaBar(e.target.value)} 
                style={{flex:1}} 
                placeholder="Select a cell or type a formula..."
              />
            </div>

            {/* Virtual Grid */}
            <div style={{flex:1,display:"flex",flexDirection:"column",overflow:"hidden",transform:`scale(${zoom/100})`,transformOrigin:"top left",width:`${10000/zoom}%`,height:`${10000/zoom}%`}}>
              <VirtualGrid
                columns={columns}
                rows={filteredRows}
                selected={selected}
                editCell={editCell}
                editRef={editRef}
                editValue={editValue}
                setEditValue={setEditValue}
                commitEdit={commitEdit}
                setEditCell={setEditCell}
                onCellClick={(r,c,col,val)=>{setSelected({r,c});setFormulaBar(val);setEditCell(null);}}
                onCellDblClick={(r,c,col,val)=>{setEditCell({r,c,col});setEditValue(val);}}
              />
            </div>

            {/* Load More + Status bar */}
            <div style={{background:"var(--bg-surface)",borderTop:"1px solid var(--border-light)",padding:"6px 16px",fontSize:12,color:"var(--text-secondary)",display:"flex",gap:24,alignItems:"center",flexShrink:0}}>
              <span>{filteredRows.length} / {totalRows} rows × {columns.length} cols</span>
              {filterText&&<span style={{color:"var(--accent-purple)"}}>🔍 Filtered: {filteredRows.length}</span>}
              {hasNextPage&&(
                <Button variant="secondary" size="sm" onClick={loadMoreRows} disabled={loadingRows}>
                  {loadingRows ? "Loading..." : "Load more rows ↓"}
                </Button>
              )}
            </div>
          </div>
          )
        )}

        {/* ── TAB 1: Charts ── */}
        {/* ── TAB 1: Charts ── */}
        {activeTab === 1 && (
          <div className="animate-fade-in" style={{ flex: 1, overflow: "auto", padding: 'var(--space-6)', background: 'transparent' }}>
            <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-primary)', marginBottom: 'var(--space-4)' }}>
              Chart Builder
            </div>
            
            <Card style={{ marginBottom: 'var(--space-6)' }}>
              <div style={{ display: "flex", flexDirection: "column", gap: 'var(--space-6)' }}>
                <div>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 'var(--space-4)' }}>Chart Type</div>
                  <div style={{ display: "grid", gridTemplateColumns: 'repeat(auto-fill, minmax(108px, 1fr))', gap: 6 }}>
                    {[
                      {id:"bar", name:"Column", icon:"📊"},
                      {id:"h-bar", name:"Bar", icon:"🪜"},
                      {id:"line", name:"Line", icon:"📈"},
                      {id:"pie", name:"Pie", icon:"🥧"},
                      {id:"donut", name:"Doughnut", icon:"🍩"},
                      {id:"area", name:"Area", icon:"🏔️"},
                      {id:"stacked-col", name:"Stacked Col", icon:"🥞"},
                      {id:"stacked-bar", name:"Stacked Bar", icon:"📚"},
                      {id:"100-stacked-col", name:"100% Col", icon:"💯"},
                      {id:"100-stacked-bar", name:"100% Bar", icon:"💯"},
                      {id:"scatter", name:"Scatter", icon:"✨"},
                      {id:"bubble", name:"Bubble", icon:"🫧"},
                      {id:"histogram", name:"Histogram", icon:"📶"},
                      {id:"boxPlot", name:"Box Plot", icon:"📦"},
                      {id:"pareto", name:"Pareto", icon:"📉"},
                      {id:"waterfall", name:"Waterfall", icon:"🌊"},
                      {id:"funnel", name:"Funnel", icon:"🔽"},
                      {id:"treemap", name:"Treemap", icon:"🔲"},
                      {id:"sunburst", name:"Sunburst", icon:"☀️"},
                      {id:"radar", name:"Radar", icon:"🕸️"},
                      {id:"candlestick", name:"Stock", icon:"🕯️"},
                      {id:"heatmap", name:"Surface", icon:"🗺️"},
                      {id:"combo", name:"Combo", icon:"🔀"}
                    ].map(t => (
                      <div 
                        key={t.id} 
                        className={`chart-card ${chartType === t.id ? 'active' : ''}`}
                        onClick={() => setChartType(t.id)}
                      >
                        <div className="chart-icon-tile">{t.icon}</div>
                        <div className="chart-card-label">{t.name}</div>
                      </div>
                    ))}
                  </div>
                </div>

                <div style={{ height: '0.5px', background: 'var(--border-light)', width: '100%' }} />

                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
                  <div>
                    <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 'var(--space-2)' }}>X Axis (Labels)</div>
                    <Select value={chartXCol} onChange={e => setChartXCol(+e.target.value)} style={{ minWidth: 150 }}>
                      {columns.map((h, i) => <option key={i} value={i}>{h}</option>)}
                    </Select>
                  </div>
                  
                  <div style={{ color: 'var(--text-secondary)', fontSize: 13, fontWeight: 600, marginTop: 18 }}>vs</div>
                  
                  <div>
                    <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 'var(--space-2)' }}>Y Axis (Values)</div>
                    <Select value={chartYCol} onChange={e => setChartYCol(+e.target.value)} style={{ minWidth: 150 }}>
                      {columns.map((h, i) => <option key={i} value={i}>{h}</option>)}
                    </Select>
                  </div>
                </div>
              </div>
            </Card>
            
            <Card style={{ padding: '0px', overflow: 'hidden' }}>
              <div style={{ padding: 'var(--space-4) var(--space-6)', borderBottom: '1px solid var(--border-light)', background: 'var(--bg-app)', fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
                {columns[chartXCol]} <span style={{ color: 'var(--text-secondary)' }}>vs</span> {columns[chartYCol]}
              </div>
              <div style={{ padding: 'var(--space-4)' }}>
                <MiniChart rows={rows.slice(0, 50)} columns={columns} xCol={chartXCol} yCol={chartYCol} type={chartType} />
              </div>
            </Card>
          </div>
        )}

        {/* ── TAB 2: Data Cleaner ── */}
        {activeTab===2&&(
          <div className="animate-fade-in" style={{flex:1,overflow:"auto",padding:'var(--space-6)', background: 'transparent'}}>
            <div style={{fontSize: '20px', fontWeight: 800, color: 'var(--text-primary)', marginBottom: 'var(--space-5)'}}>
              Data Cleaner
            </div>
            <div style={{display:"flex",gap:8,flexWrap:"wrap",marginBottom:'var(--space-6)'}}>
              {[
                {label:"Trim Whitespace",icon:<Scissors size={14} color="#0F6E56"/>,bg:"#E1F5EE",fn:()=>{setRows(rs=>rs.map(r=>Object.fromEntries(Object.entries(r).map(([k,v])=>[k,String(v).trim()]))));addCleanLog("Trimmed whitespace");}},
                {label:"Fill Empty → 0",icon:<PenLine size={14} color="#185FA5"/>,bg:"#E6F1FB",fn:()=>{setRows(rs=>rs.map(r=>Object.fromEntries(Object.entries(r).map(([k,v])=>[k,String(v).trim()||"0"]))));addCleanLog("Filled empty cells with 0");}},
                {label:"Remove Duplicates",icon:<CopyMinus size={14} color="#3C3489"/>,bg:"#EEEDFE",fn:()=>{const seen=new Set();const c=rows.filter(r=>{const k=JSON.stringify(r);return seen.has(k)?false:(seen.add(k),true)});addCleanLog(`Removed ${rows.length-c.length} duplicates`);setRows(c);}},
                {label:"Uppercase Cols",icon:<CaseUpper size={14} color="#633806"/>,bg:"#FAEEDA",fn:()=>{setColumns(cs=>cs.map(c=>c.toUpperCase()));addCleanLog("Columns uppercased");}},
              ].map(({label,icon,bg,fn})=>(
                <Button key={label} variant="secondary" style={{ height: 36, padding: '0 14px', border: '0.5px solid var(--border-light)', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: 8 }} onClick={fn}>
                  <div style={{ width: 22, height: 22, borderRadius: 4, background: bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {icon}
                  </div>
                  {label}
                </Button>
              ))}
            </div>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '.07em', color: 'var(--text-secondary)', marginBottom: 'var(--space-2)' }}>Activity Log</div>
            <div style={{ border: '0.5px solid var(--border-light)', borderRadius: 'var(--radius-lg)', background: 'var(--bg-surface)', minHeight: 80, display: 'flex', flexDirection: 'column', overflowY: "auto", padding: '12px 16px', justifyContent: cleanLog.length === 0 ? 'center' : 'flex-start' }}>
              {cleanLog.length===0 ? <div style={{color:"var(--text-secondary)",fontSize:13, textAlign: 'center'}}>No operations yet...</div> :
                [...cleanLog].reverse().map((l,i)=>(
                  <div key={i} style={{padding:"8px 0",borderBottom: i !== cleanLog.length - 1 ? "1px solid var(--border-light)" : "none",fontSize:13,display:"flex",gap:16, alignItems: 'center'}}>
                    <span style={{color:"var(--text-secondary)",minWidth:70, fontSize:12}}>{l.time}</span>
                    <span style={{color:"var(--accent-indigo)", fontWeight: 500}}>
                      <CheckCircle size={14} style={{ display: 'inline', verticalAlign: 'text-bottom', marginRight: '6px' }} />
                      {l.msg}
                    </span>
                  </div>
                ))
              }
            </div>
          </div>
        )}

        {/* ── TAB 3: Datasets ── */}
        {activeTab===3&&(
          <div className="animate-fade-in" style={{flex:1,overflow:"auto",padding:'var(--space-6)', background: 'var(--color-background-tertiary, var(--bg-subtle))'}}>
            <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:'var(--space-5)'}}>
              <div style={{fontSize:'20px',fontWeight:800,color:'var(--text-primary)'}}>My Datasets</div>
              <div style={{display:"flex",gap:'var(--space-2)'}}>
                <Button variant="ghost" onClick={fetchDatasets}>
                  <RefreshCw size={14} /> Refresh
                </Button>
                <button style={{ background: '#1D9E75', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', height: 32, padding: '0 12px', display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', fontSize: 13, fontWeight: 500, outline: 'none' }} onClick={()=>fileInputRef.current?.click()}>
                  <Upload size={14} /> Upload
                </button>
              </div>
            </div>

            {datasetsLoading&&<div style={{color:"var(--text-secondary)",fontSize:14, marginBottom: 'var(--space-4)'}}>Loading datasets...</div>}
            <div style={{display:"flex",flexDirection:"column",gap:10}}>
              {datasets.map(ds=>(
                <Card key={ds.id} className="hover-lift" style={{ border: activeDataset?.id === ds.id ? '1.5px solid var(--accent-blue)' : '0.5px solid var(--color-border-tertiary, var(--border-medium))', display: "flex", alignItems: "center", gap: 14, background: 'var(--color-background-primary, var(--bg-surface))', padding: '14px 16px', flexDirection: 'row', boxShadow: activeDataset?.id === ds.id ? '0 4px 12px rgba(59, 130, 246, 0.15)' : 'none' }}>
                  <div style={{ width: 48, height: 48, borderRadius: 'var(--radius-md)', background: ds.file_type === 'json' ? 'var(--accent-purple)' : 'var(--accent-indigo)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24, boxShadow: 'var(--shadow-sm)', flexShrink: 0, color: 'var(--text-inverse)' }}>
                    {ds.file_type==="json"?"📋":"📊"}
                  </div>
                  <div style={{flex:1}}>
                    <div style={{fontWeight:600,fontSize:15,color:"var(--text-primary)"}}>{ds.name}</div>
                    <div style={{fontSize:12,color:"var(--text-secondary)",marginTop:4, marginBottom: 8}}>
                      {ds.row_count} rows · {ds.col_count} cols · {ds.file_type} · {ds.file_size}MB
                    </div>
                    {ds.status==="ready" ? (
                      <span style={{ background: 'rgba(34,197,94,0.12)', border: '0.5px solid rgba(34,197,94,0.3)', color: '#22c55e', borderRadius: 999, padding: '2px 8px', fontSize: 11, fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                        <CheckCircle size={10} /> Ready
                      </span>
                    ) : (
                      <div style={{fontSize:11,color:statusColor(ds.status), fontWeight: 500}}>
                        {ds.status==="processing"?"⚙️ Processing...":ds.status==="pending"?"⏳ Pending":ds.status==="error"?`❌ Error: ${ds.error_message}`:ds.status}
                      </div>
                    )}
                  </div>
                  <div style={{display:"flex",gap:8, flexShrink: 0}}>
                    {ds.status==="ready"&&(
                      <Button variant="secondary" className="btn-dataset-load" style={{ height: 32, padding: '0 14px', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 500 }} onClick={async()=>{setActiveDataset(ds);await loadDatasetRows(ds,1);setActiveTab(0);addCleanLog(`Loaded: ${ds.name}`);}}>
                        <ArrowRight size={14} style={{ marginRight: 4 }} /> Load
                      </Button>
                    )}
                    <Button variant="danger" className="btn-dataset-delete" style={{ height: 32, padding: '0 14px', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 500 }} onClick={async()=>{if(confirm(`Delete "${ds.name}"?`)){await datasetAPI.delete(ds.id);fetchDatasets();if(activeDataset?.id===ds.id)setActiveDataset(null);}}}>
                      <Trash2 size={14} style={{ marginRight: 4 }} /> Delete
                    </Button>
                  </div>
                </Card>
              ))}
              {!datasetsLoading&&datasets.length===0&&(
                <div style={{textAlign:"center",padding:60,color:"var(--text-secondary)",fontSize:15}}>
                  <div style={{fontSize:48,marginBottom:20}}>📭</div>
                  No datasets yet. Upload an Excel or JSON file!
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── TAB 4: AI Chat ── */}
        {activeTab===4&&(
          <div className="animate-fade-in" style={{flex:1,display:"flex",flexDirection:"column",overflow:"hidden", background: 'var(--bg-app)'}}>
            {!groqKey&&<div style={{background:"var(--danger-light)",border:"1px solid var(--danger-color)",borderRadius:"var(--radius-md)",margin:'var(--space-4)',padding:"12px 20px",fontSize:13,color:"var(--danger-color)"}}>
              <AlertCircle size={16} style={{display:'inline', verticalAlign:'text-bottom', marginRight:6}}/>
              Groq API key is required! Click "Add Groq Key" in the header. Get it for free at <a href="https://console.groq.com" target="_blank" rel="noreferrer" style={{color:"var(--danger-color)", textDecoration:"underline", fontWeight:600}}>console.groq.com</a>
            </div>}

            <div style={{flex:1,overflowY:"auto",padding:'var(--space-4)',display:"flex",flexDirection:"column",gap:'var(--space-4)'}}>
              {messages.map((m,i)=>{
                if (m.type === "welcome") {
                  return (
                    <div key={i} style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 12 }}>
                      <div style={{ background: 'var(--bg-app)', border: '0.5px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: '18px 20px', maxWidth: '85%', boxShadow: 'var(--shadow-md)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                          <div style={{ width: 36, height: 36, borderRadius: '50%', background: '#1D9E75', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', flexShrink: 0 }}>
                            <Bot size={20} />
                          </div>
                          <div>
                            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Namaste! I'm your DATA PRO assistant</div>
                            <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>Connected to Django backend · Powered by Groq</div>
                          </div>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, marginBottom: 16 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: 8, background: 'var(--bg-surface-hover)', borderRadius: 'var(--radius-md)' }}>
                            <div style={{ width: 26, height: 26, borderRadius: 6, background: '#E6F1FB', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#185FA5' }}><Database size={14}/></div>
                            <span style={{ fontSize: 12, color: 'var(--text-primary)', fontWeight: 500 }}>Excel/JSON → PostgreSQL</span>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: 8, background: 'var(--bg-surface-hover)', borderRadius: 'var(--radius-md)' }}>
                            <div style={{ width: 26, height: 26, borderRadius: 6, background: '#EEEDFE', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#3C3489' }}><Activity size={14}/></div>
                            <span style={{ fontSize: 12, color: 'var(--text-primary)', fontWeight: 500 }}>Celery background processing</span>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: 8, background: 'var(--bg-surface-hover)', borderRadius: 'var(--radius-md)' }}>
                            <div style={{ width: 26, height: 26, borderRadius: 6, background: '#FAEEDA', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#633806' }}><List size={14}/></div>
                            <span style={{ fontSize: 12, color: 'var(--text-primary)', fontWeight: 500 }}>Virtual scrolling (lakh rows!)</span>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: 8, background: 'var(--bg-surface-hover)', borderRadius: 'var(--radius-md)' }}>
                            <div style={{ width: 26, height: 26, borderRadius: 6, background: '#E1F5EE', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#0F6E56' }}><Shield size={14}/></div>
                            <span style={{ fontSize: 12, color: 'var(--text-primary)', fontWeight: 500 }}>JWT authentication</span>
                          </div>
                          <div style={{ gridColumn: '1 / -1', display: 'flex', alignItems: 'center', gap: 8, padding: 8, background: 'var(--bg-surface-hover)', borderRadius: 'var(--radius-md)' }}>
                            <div style={{ width: 26, height: 26, borderRadius: 6, background: '#FCE7F3', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9D174D' }}><Terminal size={14}/></div>
                            <span style={{ fontSize: 12, color: 'var(--text-primary)', fontWeight: 500 }}>AI commands powered by Groq</span>
                          </div>
                        </div>

                        <div style={{ background: '#E1F5EE', border: '0.5px solid #9FE1CB', borderRadius: 'var(--radius-md)', padding: '10px 12px', display: 'flex', alignItems: 'center', gap: 8, color: '#0F6E56', fontSize: 13, fontWeight: 600 }}>
                          <Key size={16} /> Set your Groq key in the header to start
                          <ArrowRight size={16} style={{ marginLeft: 'auto' }} />
                        </div>
                      </div>
                    </div>
                  );
                }
                return (
                <div key={i} style={{display:"flex",justifyContent:m.role==="user"?"flex-end":"flex-start"}}>
                  <div style={{
                    maxWidth:"80%",
                    padding:"12px 18px",
                    borderRadius: m.role==="user" ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
                    background: m.role==="user" ? "linear-gradient(135deg, var(--accent-indigo), var(--accent-purple))" : "var(--bg-surface)",
                    color: m.role==="user" ? "var(--text-inverse)" : "var(--text-primary)",
                    fontSize: 14,
                    lineHeight: 1.6,
                    border: m.role==="ai" ? "1px solid var(--border-light)" : "none",
                    boxShadow: m.role==="user" ? "var(--shadow-glow)" : "var(--shadow-md)",
                    whiteSpace: "pre-wrap"
                  }}>
                    {m.text}
                  </div>
                </div>
              )})}
              {aiLoading&&<div style={{display:"flex",justifyContent:"flex-start"}}>
                <div style={{padding:"12px 18px",background:"var(--bg-surface)",border:"1px solid var(--border-light)",borderRadius:"18px 18px 18px 4px",fontSize:14,color:"var(--text-secondary)", display: 'flex', alignItems: 'center', gap: 8}}>
                  <RefreshCw size={16} className="spin" /> AI is thinking...
                </div>
              </div>}
              <div ref={chatEndRef}/>
            </div>

            <div style={{padding:"12px 16px",display:"flex",flexWrap:"wrap",gap:8,borderTop:"1px solid var(--border-light)", background: 'var(--bg-surface)'}}>
              {[
                {q:"Sort by Salary", icon: <ArrowUpDown size={14}/>},
                {q:"Create a Bar chart", icon: <BarChart2 size={14}/>},
                {q:"Remove Duplicates", icon: <CopyMinus size={14}/>},
                {q:"Who has the Max salary?", icon: <Search size={14}/>},
                {q:"Summarize data", icon: <FileText size={14}/>}
              ].map(({q, icon})=>(
                <div key={q} onClick={()=>setChatInput(q)} style={{display: 'flex', alignItems: 'center', gap: 6, padding:"6px 14px",background:"var(--border-focus)",border:"1px solid var(--border-light)",borderRadius:"var(--radius-full)",fontSize:12,color:"var(--text-primary)",cursor:"pointer", transition: 'all 0.2s'}}
                onMouseEnter={e=>e.currentTarget.style.background='var(--border-light)'}
                onMouseLeave={e=>e.currentTarget.style.background='var(--border-focus)'}>
                  {icon}
                  {q}
                </div>
              ))}
            </div>

            <div style={{padding:"16px",borderTop:"1px solid var(--border-light)",display:"flex",gap:12, background: 'var(--bg-surface)'}}>
              <Input 
                className="chat-input"
                value={chatInput} 
                onChange={e=>setChatInput(e.target.value)} 
                onKeyDown={e=>e.key==="Enter"&&sendMessage()} 
                placeholder="Ask AI a question or give a command..." 
                style={{flex:1, borderRadius: 'var(--radius-full)', paddingLeft: 20}}
              />
              <Button onClick={sendMessage} disabled={aiLoading} variant="primary" style={{ borderRadius: 'var(--radius-full)', padding: '0 24px' }}>
                <span style={{ fontSize: 16 }}>➤</span>
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
