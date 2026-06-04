import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import Chart from "react-apexcharts";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";
import { datasetAPI } from "../api";
import {
  BarChart2, TrendingUp, PieChart, Table2, RefreshCw,
  Download, AlertCircle, Database, Loader2,
  ArrowUpRight, ArrowDownRight, Layers,
  Activity, BarChart, Globe, Lightbulb, Hash,
} from "lucide-react";

/* ═══════════════════════════════════════════════════════════
   Uses the same CSS variables as the rest of the app
   --bg-app: #E0E7FF  (lavender background)
   --bg-surface: #FFFFFF  (white cards)
   --accent-indigo: #4F46E5  (primary colour)
═══════════════════════════════════════════════════════════ */

const INDIGO   = "#4F46E5";
const INDIGO_S = "#818CF8";   // soft indigo
const PALETTE  = [
  "#4F46E5","#06B6D4","#8B5CF6","#10B981",
  "#F59E0B","#EF4444","#EC4899","#3B82F6","#F97316","#14B8A6",
];

/* ── light chart defaults (matches rest of app) ── */
const CHART_BASE = {
  chart: {
    background: "transparent",
    foreColor:  "#475569",
    toolbar:    { show: false },
    animations: { enabled: true, speed: 600 },
  },
  grid:    { borderColor: "rgba(0,0,0,0.06)", strokeDashArray: 4 },
  tooltip: { theme: "light" },
  legend:  { labels: { colors: "#475569" }, fontSize: "12px" },
};

/* ── helpers ── */
function fmt(v) {
  if (v == null || v === "") return "—";
  if (typeof v !== "number") return String(v);
  if (Math.abs(v) >= 1e9)  return (v / 1e9).toFixed(2)  + "B";
  if (Math.abs(v) >= 1e6)  return (v / 1e6).toFixed(2)  + "M";
  if (Math.abs(v) >= 1e3)  return (v / 1e3).toFixed(2)  + "K";
  return v.toLocaleString("en-IN", { maximumFractionDigits: 2 });
}

/* ── auto-insights (no AI API) ── */
function buildInsights(d) {
  if (!d) return [];
  const { meta, kpis, pie_chart, bar_chart, line_chart } = d;
  const ins = [];
  ins.push({ icon: "🗂️", text: `Dataset has ${(meta?.rows||0).toLocaleString()} rows and ${meta?.cols} columns.` });
  const np = meta?.null_pct || 0;
  ins.push({ icon: np > 5 ? "⚠️" : "✅",
    text: np > 5 ? `${np.toFixed(1)}% null values — consider cleaning first.`
                 : `Great data quality — only ${np.toFixed(1)}% nulls.` });
  if (kpis?.[0]) {
    const k = kpis[0];
    const dp = k.mean && k.max ? (((k.max-k.mean)/k.mean)*100).toFixed(0) : null;
    ins.push({ icon: "📈", text: `"${k.column}" peaks at ${fmt(k.max)}${dp ? ` — ${dp}% above average (${fmt(k.mean)})` : ""}.` });
  }
  if (pie_chart?.labels?.length) {
    const tot = pie_chart.values.reduce((a,b)=>a+b,0);
    const tp  = tot ? ((pie_chart.values[0]/tot)*100).toFixed(1) : null;
    ins.push({ icon: "🏆", text: `"${pie_chart.labels[0]}" is the top ${pie_chart.column}${tp ? ` (${tp}%)` : ""}.` });
  }
  if (bar_chart?.labels?.length)
    ins.push({ icon: "🥇", text: `Top ${bar_chart.x_col}: "${bar_chart.labels[0]}" with ${fmt(bar_chart.values[0])} in ${bar_chart.y_col}.` });
  if (line_chart?.series?.[0]?.data?.length > 1) {
    const data  = line_chart.series[0].data;
    const trend = data[data.length-1] > data[0] ? "📈 upward" : data[data.length-1] < data[0] ? "📉 downward" : "➡️ flat";
    ins.push({ icon: "🕐", text: `${line_chart.y_col} shows a ${trend} trend over ${data.length} periods.` });
  }
  return ins.slice(0, 6);
}

/* ══════════════════════════════════════════════════════════
   KPI CARD  — white card, indigo accent, matches app style
══════════════════════════════════════════════════════════ */
function KpiCard({ label, value, sub, icon: Icon, accent = INDIGO, trendLabel, trendUp }) {
  return (
    <div style={{
      background:   "#fff",
      borderRadius: 12,
      padding:      "18px 20px",
      border:       `1px solid rgba(0,0,0,0.08)`,
      boxShadow:    "0 4px 12px rgba(0,0,0,0.05)",
      display:      "flex",
      flexDirection:"column",
      gap:          8,
      flex:         "1 1 190px",
      minWidth:     185,
      transition:   "transform .18s, box-shadow .18s",
      cursor:       "default",
    }}
    onMouseEnter={e => { e.currentTarget.style.transform="translateY(-2px)"; e.currentTarget.style.boxShadow=`0 8px 24px ${accent}22`; }}
    onMouseLeave={e => { e.currentTarget.style.transform="translateY(0)";    e.currentTarget.style.boxShadow="0 4px 12px rgba(0,0,0,0.05)"; }}
    >
      {/* Top row */}
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between" }}>
        <span style={{ fontSize:10, fontWeight:700, color:"#94A3B8", textTransform:"uppercase", letterSpacing:".08em" }}>
          {sub}
        </span>
        <div style={{ width:32, height:32, borderRadius:8, background:`${accent}15`, display:"flex", alignItems:"center", justifyContent:"center", color:accent }}>
          {Icon && <Icon size={16} />}
        </div>
      </div>
      {/* Value */}
      <div style={{ fontSize:28, fontWeight:800, color:"#0F172A", letterSpacing:"-1px", lineHeight:1 }}>
        {fmt(value)}
      </div>
      {/* Label */}
      <div style={{ fontSize:12, color:"#64748B", fontWeight:500, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>
        {label}
      </div>
      {/* Trend */}
      {trendLabel && (
        <div style={{ display:"flex", alignItems:"center", gap:4, fontSize:11, fontWeight:600,
          color: trendUp !== false ? "#10B981" : "#EF4444",
          background: trendUp !== false ? "rgba(16,185,129,0.1)" : "rgba(239,68,68,0.1)",
          borderRadius:999, padding:"2px 8px", alignSelf:"flex-start" }}>
          {trendUp !== false ? <ArrowUpRight size={11}/> : <ArrowDownRight size={11}/>}
          {trendLabel}
        </div>
      )}
    </div>
  );
}

/* ══════════════════════════════════════════════════════════
   CHART CARD  — white card with indigo header accent
══════════════════════════════════════════════════════════ */
function ChartCard({ title, subtitle, icon: Icon, accent = INDIGO, children }) {
  return (
    <div style={{
      background:   "#fff",
      borderRadius: 12,
      border:       "1px solid rgba(0,0,0,0.08)",
      boxShadow:    "0 4px 12px rgba(0,0,0,0.05)",
      overflow:     "hidden",
    }}>
      {/* Card header strip */}
      <div style={{ padding:"14px 18px 0", display:"flex", alignItems:"center", gap:10, marginBottom:4 }}>
        <div style={{ width:30, height:30, borderRadius:8, background:`${accent}15`, display:"flex", alignItems:"center", justifyContent:"center", color:accent }}>
          {Icon && <Icon size={15}/>}
        </div>
        <div>
          <div style={{ fontSize:13, fontWeight:700, color:"#0F172A" }}>{title}</div>
          {subtitle && <div style={{ fontSize:11, color:"#94A3B8" }}>{subtitle}</div>}
        </div>
        {/* Accent dot */}
        <div style={{ marginLeft:"auto", width:8, height:8, borderRadius:"50%", background:accent, boxShadow:`0 0 6px ${accent}88` }}/>
      </div>
      <div style={{ padding:"0 8px 8px" }}>{children}</div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════
   MAIN COMPONENT
══════════════════════════════════════════════════════════ */
/* ══════════════════════════════════════════════════════════
   CREATIVE LOADING SCREEN
══════════════════════════════════════════════════════════ */
const STEPS = [
  { icon: "📂", label: "Reading dataset…"          },
  { icon: "🔍", label: "Detecting column types…"   },
  { icon: "🧮", label: "Computing KPIs…"            },
  { icon: "📊", label: "Building charts…"           },
  { icon: "💡", label: "Generating insights…"       },
  { icon: "✨", label: "Finalising dashboard…"      },
];

/* Mini animated bar — one of the 8 equalizer bars */
function Bar({ delay, height }) {
  return (
    <div style={{
      width: 6, borderRadius: 3,
      background: `linear-gradient(180deg, ${INDIGO}, ${INDIGO_S})`,
      animationName: "barBounce",
      animationDuration: "1s",
      animationTimingFunction: "ease-in-out",
      animationIterationCount: "infinite",
      animationDirection: "alternate",
      animationDelay: delay,
      height, minHeight: 4,
    }} />
  );
}

function DashboardLoader() {
  const [stepIdx, setStepIdx] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const step = setInterval(() => {
      setStepIdx(i => (i + 1) % STEPS.length);
    }, 900);
    const prog = setInterval(() => {
      setProgress(p => Math.min(p + Math.random() * 4, 95));
    }, 120);
    return () => { clearInterval(step); clearInterval(prog); };
  }, []);

  const bars = [28, 44, 36, 52, 32, 48, 38, 44];

  return (
    <div style={{
      flex: 1, display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center",
      background: "var(--bg-app)", gap: 0,
      userSelect: "none",
    }}>

      {/* ── Equalizer animation ── */}
      <div style={{ display: "flex", alignItems: "flex-end", gap: 5, height: 60, marginBottom: 28 }}>
        {bars.map((h, i) => (
          <Bar key={i} height={h} delay={`${i * 0.12}s`} />
        ))}
      </div>

      {/* ── Icon + Step label ── */}
      <div key={stepIdx} style={{
        display: "flex", flexDirection: "column", alignItems: "center", gap: 10,
        animation: "stepFade 0.4s ease forwards",
      }}>
        <div style={{
          width: 56, height: 56, borderRadius: 16,
          background: "#fff",
          border: `1.5px solid rgba(79,70,229,0.18)`,
          boxShadow: `0 8px 24px rgba(79,70,229,0.15)`,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 26,
        }}>
          {STEPS[stepIdx].icon}
        </div>
        <div style={{ fontSize: 14, fontWeight: 700, color: INDIGO }}>
          {STEPS[stepIdx].label}
        </div>
      </div>

      {/* ── Progress bar ── */}
      <div style={{
        width: 260, marginTop: 28,
        height: 4, borderRadius: 999,
        background: "rgba(79,70,229,0.12)",
        overflow: "hidden",
      }}>
        <div style={{
          height: "100%", borderRadius: 999,
          background: `linear-gradient(90deg, ${INDIGO}, ${INDIGO_S})`,
          width: `${progress}%`,
          transition: "width 0.12s linear",
          boxShadow: `0 0 8px ${INDIGO}88`,
        }} />
      </div>
      <div style={{ fontSize: 11, color: "#94A3B8", marginTop: 8, fontWeight: 500 }}>
        {Math.round(progress)}% complete
      </div>

      {/* ── Floating data chips ── */}
      <div style={{ display: "flex", gap: 8, marginTop: 24, flexWrap: "wrap", justifyContent: "center", maxWidth: 320 }}>
        {["Rows","Columns","KPIs","Bar Chart","Pie Chart","Trend","Insights"].map((chip, i) => (
          <span key={chip} style={{
            fontSize: 10, fontWeight: 600,
            padding: "3px 10px", borderRadius: 999,
            background: i <= Math.floor(progress / 14) ? `${INDIGO}18` : "rgba(0,0,0,0.04)",
            color:      i <= Math.floor(progress / 14) ? INDIGO : "#C1C9D9",
            border:     `1px solid ${i <= Math.floor(progress / 14) ? `${INDIGO}30` : "rgba(0,0,0,0.06)"}`,
            transition: "all 0.4s ease",
          }}>
            {i <= Math.floor(progress / 14) ? "✓ " : ""}{chip}
          </span>
        ))}
      </div>

      <style>{`
        @keyframes barBounce {
          from { transform: scaleY(0.3); opacity: 0.5; }
          to   { transform: scaleY(1);   opacity: 1; }
        }
        @keyframes stepFade {
          from { opacity: 0; transform: translateY(6px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}

export function AutoDashboard({ datasets, activeDataset }) {
  const [dashData,   setDashData]   = useState(null);
  const [loading,    setLoading]    = useState(false);
  const [exporting,  setExporting]  = useState(false);
  const [error,      setError]      = useState(null);
  const [selectedId, setSelectedId] = useState(activeDataset?.id ?? null);
  const dashRef = useRef(null);

  useEffect(() => { if (activeDataset?.id) setSelectedId(activeDataset.id); }, [activeDataset]);
  useEffect(() => { selectedId ? fetchDashboard(selectedId) : setDashData(null); }, [selectedId]);

  const fetchDashboard = useCallback(async (id) => {
    setLoading(true); setError(null);
    try   { const { data } = await datasetAPI.autoDashboard(id); setDashData(data); }
    catch (e) { setError(e.response?.data?.error || e.message || "Failed to load"); }
    setLoading(false);
  }, []);

  /* ── PDF export ── */
  const exportPDF = useCallback(async () => {
    const el = dashRef.current;
    if (!el) return;
    setExporting(true);
    const ov = document.createElement("style");
    ov.id = "__pdf_ov__";
    ov.textContent = `
      #dash-content { overflow:visible!important;height:auto!important;max-height:none!important; }
      #dash-toolbar  { display:none!important; }
      #dash-content .apexcharts-canvas { background:#fff!important; }
    `;
    document.head.appendChild(ov);
    const origOv = el.style.overflow, origH = el.style.height, origMH = el.style.maxHeight;
    el.style.overflow = "visible"; el.style.height = "auto"; el.style.maxHeight = "none";
    await new Promise(r => setTimeout(r, 400));
    try {
      const canvas = await html2canvas(el, { scale:2, useCORS:true, backgroundColor:"#E0E7FF", logging:false, scrollX:0, scrollY:0, windowWidth:el.scrollWidth, windowHeight:el.scrollHeight, ignoreElements: n => n.id==="dash-toolbar" });
      const pdf = new jsPDF({ orientation:"landscape", unit:"mm", format:"a4" });
      const pw = pdf.internal.pageSize.getWidth(), ph = pdf.internal.pageSize.getHeight();
      const iw = pw, ih = (canvas.height * iw) / canvas.width;
      for (let p = 0; p < Math.ceil(ih/ph); p++) {
        if (p > 0) pdf.addPage();
        pdf.addImage(canvas.toDataURL("image/png",1.0),"PNG",0,-(p*ph),iw,ih);
      }
      pdf.save(`datapro_${(dashData?.meta?.name||"dashboard").replace(/[^a-zA-Z0-9_-]/g,"_")}.pdf`);
    } catch(err) { alert("PDF failed: "+err.message); }
    finally {
      document.head.removeChild(ov);
      el.style.overflow=origOv; el.style.height=origH; el.style.maxHeight=origMH;
      setExporting(false);
    }
  }, [dashData]);

  const readyDS  = datasets.filter(d => d.status === "ready");
  const insights = useMemo(() => buildInsights(dashData), [dashData]);

  /* ── EMPTY STATE ── */
  if (!selectedId) return (
    <div className="animate-fade-in" style={{ flex:1, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", padding:48, gap:28, background:"var(--bg-app)" }}>
      <div style={{ width:72, height:72, borderRadius:20, background:`linear-gradient(135deg,${INDIGO},${INDIGO_S})`, display:"flex", alignItems:"center", justifyContent:"center", color:"#fff", boxShadow:`0 0 32px ${INDIGO}44` }}>
        <Activity size={38}/>
      </div>
      <div style={{ textAlign:"center" }}>
        <h1 style={{ fontSize:30, fontWeight:800, color:"#0F172A", margin:"0 0 8px", letterSpacing:"-0.5px" }}>Auto Dashboard</h1>
        <p style={{ fontSize:14, color:"#475569", maxWidth:460, lineHeight:1.7, margin:0 }}>
          Instantly generate KPI cards, charts &amp; insights from any dataset — powered by pure Python / Pandas. No AI API needed.
        </p>
      </div>
      {readyDS.length === 0
        ? <div style={{ background:"rgba(245,158,11,0.1)", border:"1px solid rgba(245,158,11,0.3)", borderRadius:10, padding:"14px 22px", color:"#92400E", fontSize:14 }}>⚠️ No ready datasets. Upload a dataset first!</div>
        : <div style={{ display:"flex", flexWrap:"wrap", gap:12, justifyContent:"center", maxWidth:680 }}>
            {readyDS.map(ds => (
              <button key={ds.id} onClick={() => setSelectedId(ds.id)} style={{ padding:"12px 20px", borderRadius:10, border:"1.5px solid rgba(79,70,229,0.2)", background:"#fff", cursor:"pointer", fontSize:13, fontWeight:600, color:"#0F172A", display:"flex", alignItems:"center", gap:10, boxShadow:"0 2px 8px rgba(0,0,0,0.06)", transition:"all .18s" }}
                onMouseEnter={e=>{e.currentTarget.style.borderColor=INDIGO;e.currentTarget.style.color=INDIGO;e.currentTarget.style.boxShadow=`0 4px 16px ${INDIGO}22`;}}
                onMouseLeave={e=>{e.currentTarget.style.borderColor="rgba(79,70,229,0.2)";e.currentTarget.style.color="#0F172A";e.currentTarget.style.boxShadow="0 2px 8px rgba(0,0,0,0.06)";}}>
                <Database size={16} style={{color:INDIGO}}/>{ds.name}
                <span style={{fontSize:11,color:"#94A3B8",fontWeight:400}}>{ds.row_count?.toLocaleString()} rows</span>
              </button>
            ))}
          </div>
      }
    </div>
  );

  /* ── LOADING ── */
  if (loading) return <DashboardLoader />;

  /* ── ERROR ── */
  if (error) return (
    <div style={{ flex:1, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", gap:16, background:"var(--bg-app)" }}>
      <AlertCircle size={40} color="#EF4444"/>
      <div style={{ fontSize:14, color:"#EF4444", fontWeight:600 }}>{error}</div>
      <button onClick={()=>fetchDashboard(selectedId)} style={{ padding:"9px 20px", borderRadius:8, background:INDIGO, color:"#fff", border:"none", cursor:"pointer", fontWeight:600, fontSize:13 }}>Retry</button>
    </div>
  );

  if (!dashData) return null;
  const { meta, kpis, bar_chart, line_chart, pie_chart, top_performers } = dashData;
  const k0 = kpis?.[0];

  /* ── CHART OPTIONS ── */
  const barOpts = bar_chart ? {
    ...CHART_BASE,
    colors: PALETTE,
    chart:  { ...CHART_BASE.chart, type:"bar" },
    plotOptions: { bar:{ distributed:true, borderRadius:5, columnWidth:"58%" } },
    dataLabels:  { enabled:false },
    xaxis: { categories:bar_chart.labels, labels:{ style:{ fontSize:"10px", colors:"#64748B" }, rotate:-30, hideOverlappingLabels:true }, axisBorder:{color:"rgba(0,0,0,0.06)"} },
    yaxis: { labels:{ style:{ colors:"#64748B" }, formatter: v=>fmt(v) } },
    legend: { show:false },
    fill:  { type:"gradient", gradient:{ shade:"light", type:"vertical", shadeIntensity:0.2, gradientToColors:[INDIGO_S,...PALETTE.slice(1)], stops:[0,100] } },
  } : null;

  const donutOpts = pie_chart ? {
    ...CHART_BASE,
    colors: PALETTE,
    chart:  { ...CHART_BASE.chart, type:"donut" },
    labels: pie_chart.labels,
    plotOptions: { pie:{ donut:{ size:"60%", labels:{ show:true, total:{ show:true, label:"Total", color:"#475569", fontSize:"12px", fontWeight:600, formatter: w=>w.globals.seriesTotals.reduce((a,b)=>a+b,0).toLocaleString() } } } } },
    legend: { position:"bottom", labels:{ colors:"#64748B" }, fontSize:"11px" },
    dataLabels: { enabled:true, formatter:v=>`${Math.round(v)}%`, style:{ fontSize:"11px", colors:["#fff"] }, dropShadow:{ enabled:false } },
    stroke: { show:false },
  } : null;

  const lineOpts = line_chart ? {
    ...CHART_BASE,
    colors: [INDIGO, INDIGO_S],
    chart:  { ...CHART_BASE.chart, type:"area" },
    stroke: { curve:"smooth", width:[2.5, 1.5], dashArray:[0, 5] },
    markers: { size: line_chart.labels.length<=30 ? 3 : 0, colors:[INDIGO], strokeColors:"#fff", strokeWidth:2 },
    fill:  { type:"gradient", gradient:{ shade:"light", type:"vertical", gradientToColors:[`${INDIGO}00`], stops:[0,100], opacityFrom:0.35, opacityTo:0 } },
    xaxis: { categories:line_chart.labels, labels:{ style:{ fontSize:"10px", colors:"#64748B" }, rotate:-30, hideOverlappingLabels:true }, axisBorder:{color:"rgba(0,0,0,0.06)"} },
    yaxis: { labels:{ style:{ colors:"#64748B" }, formatter:v=>fmt(v) } },
    dataLabels: { enabled:false },
  } : null;

  const hbarLabels = top_performers?.map((r,i)=>String(Object.values(r)[0]??`Row ${i+1}`).slice(0,22))||[];
  const hbarVals   = top_performers?.map(r=>{ const v=r[k0?.column]; return typeof v==="number"?v:parseFloat(v)||0; })||[];
  const hbarOpts   = top_performers?.length && k0 ? {
    ...CHART_BASE,
    colors: PALETTE,
    chart:  { ...CHART_BASE.chart, type:"bar" },
    plotOptions: { bar:{ distributed:true, borderRadius:4, horizontal:true, barHeight:"58%" } },
    dataLabels: { enabled:true, style:{ fontSize:"11px", colors:["#fff"] }, formatter:v=>fmt(v) },
    xaxis: { labels:{ style:{ fontSize:"10px", colors:"#64748B" }, formatter:v=>fmt(v) }, axisBorder:{color:"rgba(0,0,0,0.06)"} },
    yaxis: { labels:{ style:{ colors:"#475569", fontSize:"11px" } } },
    legend: { show:false },
    fill:  { type:"gradient", gradient:{ shade:"light", type:"horizontal", gradientToColors:[INDIGO_S,...PALETTE.slice(1)], stops:[0,100] } },
  } : null;

  /* KPI row */
  const kpiRow = [
    { label:"Total Records", value:meta?.rows, sub:"Dataset Size", icon:Globe,      accent:INDIGO,          trendLabel:`${meta?.cols} columns`,         trendUp:true  },
    k0&&{ label:k0.column,   value:k0.sum,     sub:"Total SUM",   icon:Layers,     accent:"#8B5CF6",        trendLabel:`Avg ${fmt(k0.mean)}`,            trendUp:true  },
    k0&&{ label:k0.column,   value:k0.mean,    sub:"Average",     icon:Activity,   accent:"#10B981",        trendLabel:`Max ${fmt(k0.max)}`,             trendUp:k0.max>k0.mean },
    k0&&{ label:k0.column,   value:k0.max,     sub:"Peak Value",  icon:TrendingUp, accent:"#F59E0B",        trendLabel:`Min ${fmt(k0.min)}`,             trendUp:true  },
  ].filter(Boolean);

  /* ── RENDER ── */
  return (
    <div style={{ display:"flex", flexDirection:"column", flex:1, overflow:"hidden", background:"var(--bg-app)" }}>

      {/* ═══ TOOLBAR ═══ */}
      <div id="dash-toolbar" style={{
        display:"flex", alignItems:"center", justifyContent:"space-between",
        padding:"12px 24px",
        background:"rgba(255,255,255,0.75)",
        backdropFilter:"blur(16px)",
        borderBottom:"1px solid rgba(0,0,0,0.06)",
        flexShrink:0, flexWrap:"wrap", gap:12,
      }}>
        {/* Left */}
        <div style={{ display:"flex", alignItems:"center", gap:12 }}>
          <div style={{ width:34, height:34, borderRadius:9, background:`linear-gradient(135deg,${INDIGO},${INDIGO_S})`, display:"flex", alignItems:"center", justifyContent:"center", color:"#fff", boxShadow:`0 4px 12px ${INDIGO}40` }}>
            <BarChart2 size={17}/>
          </div>
          <div>
            <div style={{ fontSize:15, fontWeight:800, color:"#0F172A", letterSpacing:"-0.3px" }}>Auto Dashboard</div>
            <div style={{ fontSize:11, color:"#94A3B8" }}>{meta?.name} · {meta?.rows?.toLocaleString()} rows × {meta?.cols} cols</div>
          </div>
        </div>

        {/* Center: type pills */}
        <div style={{ display:"flex", gap:6, flexWrap:"wrap" }}>
          {[
            { label:`${meta?.numeric_cols?.length||0} Numeric`,      color:INDIGO        },
            { label:`${meta?.categorical_cols?.length||0} Category`,  color:"#8B5CF6"     },
            { label:meta?.date_cols?.length?`${meta.date_cols.length} Date`:"No Date",color:"#06B6D4"},
            { label:`${(meta?.null_pct||0).toFixed(1)}% Null`,        color:(meta?.null_pct||0)>5?"#F59E0B":"#10B981" },
          ].map(p=>(
            <span key={p.label} style={{ padding:"3px 10px", borderRadius:999, background:`${p.color}15`, color:p.color, fontSize:11, fontWeight:600, border:`1px solid ${p.color}30` }}>
              {p.label}
            </span>
          ))}
        </div>

        {/* Right: controls */}
        <div style={{ display:"flex", gap:8, alignItems:"center" }}>
          <select value={selectedId} onChange={e=>setSelectedId(+e.target.value)} style={{ padding:"7px 12px", borderRadius:8, border:"1px solid rgba(0,0,0,0.1)", background:"#fff", color:"#0F172A", fontSize:12, fontWeight:500, cursor:"pointer", outline:"none" }}>
            {readyDS.map(ds=><option key={ds.id} value={ds.id}>{ds.name}</option>)}
          </select>

          <button onClick={()=>fetchDashboard(selectedId)} style={{ display:"flex", alignItems:"center", gap:6, padding:"7px 14px", borderRadius:8, border:"1px solid rgba(0,0,0,0.1)", background:"#fff", color:"#475569", fontSize:12, cursor:"pointer", fontWeight:500, transition:"color .15s" }}
            onMouseEnter={e=>e.currentTarget.style.color=INDIGO}
            onMouseLeave={e=>e.currentTarget.style.color="#475569"}>
            <RefreshCw size={13}/> Refresh
          </button>

          <button onClick={exportPDF} disabled={exporting} style={{ display:"flex", alignItems:"center", gap:7, padding:"7px 16px", borderRadius:8, background:INDIGO, color:"#fff", border:"none", fontSize:12, cursor:exporting?"not-allowed":"pointer", fontWeight:700, opacity:exporting?0.8:1, boxShadow:`0 4px 12px ${INDIGO}44`, transition:"opacity .2s" }}>
            {exporting ? <><Loader2 size={13} style={{animation:"spin 1s linear infinite"}}/> Generating…</> : <><Download size={13}/> Export PDF</>}
          </button>
        </div>
      </div>

      {/* ═══ SCROLLABLE CONTENT ═══ */}
      <div id="dash-content" ref={dashRef} className="animate-fade-in"
        style={{ flex:1, overflowY:"auto", padding:"20px 24px", background:"var(--bg-app)" }}>

        {/* ── KPI Row ── */}
        <div style={{ display:"flex", gap:14, flexWrap:"wrap", marginBottom:20 }}>
          {kpiRow.map((c,i)=><KpiCard key={i} {...c}/>)}
        </div>

        {/* ── Charts 2×2 ── */}
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:16, marginBottom:16 }}>

          {bar_chart && barOpts && (
            <ChartCard title="Category Analysis" subtitle={`${bar_chart.y_col} by ${bar_chart.x_col}`} icon={BarChart2} accent={INDIGO}>
              <Chart options={barOpts} series={[{name:bar_chart.y_col,data:bar_chart.values}]} type="bar" height={240}/>
            </ChartCard>
          )}

          {pie_chart && donutOpts && (
            <ChartCard title="Distribution" subtitle={`By ${pie_chart.column}`} icon={PieChart} accent="#8B5CF6">
              <Chart options={donutOpts} series={pie_chart.values} type="donut" height={240}/>
            </ChartCard>
          )}

          {line_chart && lineOpts && (
            <ChartCard title="Trend Analysis" subtitle={`${line_chart.y_col} over time`} icon={TrendingUp} accent="#10B981">
              <Chart options={lineOpts} series={line_chart.series.map(s=>({name:s.name,data:s.data}))} type="area" height={240}/>
            </ChartCard>
          )}

          {top_performers?.length>0 && hbarOpts && k0 && (
            <ChartCard title="Top Performers" subtitle={`Ranked by ${k0.column}`} icon={BarChart} accent="#F59E0B">
              <Chart options={hbarOpts} series={[{name:k0.column,data:hbarVals}]} type="bar" height={240}/>
            </ChartCard>
          )}
        </div>

        {/* ── Bottom: Table + Insights ── */}
        <div style={{ display:"grid", gridTemplateColumns:"1.2fr 1fr", gap:16 }}>

          {/* Top-5 Table */}
          {top_performers?.length>0 && (
            <div style={{ background:"#fff", border:"1px solid rgba(0,0,0,0.08)", borderRadius:12, boxShadow:"0 4px 12px rgba(0,0,0,0.05)", padding:"18px 20px" }}>
              <div style={{ display:"flex", alignItems:"center", gap:9, marginBottom:14 }}>
                <div style={{ width:30, height:30, borderRadius:8, background:"rgba(16,185,129,0.12)", display:"flex", alignItems:"center", justifyContent:"center", color:"#10B981" }}>
                  <Table2 size={15}/>
                </div>
                <span style={{ fontSize:13, fontWeight:700, color:"#0F172A" }}>Top 5 Performers</span>
                <div style={{ marginLeft:"auto", width:8, height:8, borderRadius:"50%", background:"#10B981", boxShadow:"0 0 6px #10B98166" }}/>
              </div>
              <div style={{ overflowX:"auto" }}>
                <table style={{ width:"100%", borderCollapse:"collapse", fontSize:12 }}>
                  <thead>
                    <tr style={{ background:"#F8FAFC" }}>
                      <th style={{ padding:"8px 12px", textAlign:"left", color:"#94A3B8", fontWeight:600, fontSize:10, textTransform:"uppercase", letterSpacing:".06em", borderBottom:"1.5px solid rgba(0,0,0,0.06)" }}>#</th>
                      {top_performers[0] && Object.keys(top_performers[0]).map(col=>(
                        <th key={col} style={{ padding:"8px 12px", textAlign:"left", color:"#94A3B8", fontWeight:600, fontSize:10, textTransform:"uppercase", letterSpacing:".06em", borderBottom:"1.5px solid rgba(0,0,0,0.06)" }}>{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {top_performers.map((row,ri)=>(
                      <tr key={ri} style={{ transition:"background .15s" }}
                        onMouseEnter={e=>e.currentTarget.style.background=`${INDIGO}08`}
                        onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
                        <td style={{ padding:"9px 12px", borderBottom:"1px solid rgba(0,0,0,0.04)" }}>
                          <span style={{ display:"inline-flex", alignItems:"center", justifyContent:"center", width:20, height:20, borderRadius:6,
                            background: ri===0?`${INDIGO}18`:ri===1?"rgba(0,0,0,0.05)":"rgba(0,0,0,0.03)",
                            color: ri===0?INDIGO:"#94A3B8", fontSize:10, fontWeight:800 }}>
                            {ri+1}
                          </span>
                        </td>
                        {Object.values(row).map((val,vi)=>(
                          <td key={vi} style={{ padding:"9px 12px", color: vi===Object.keys(row).length-1?INDIGO:"#0F172A", fontWeight: vi===Object.keys(row).length-1?700:400, borderBottom:"1px solid rgba(0,0,0,0.04)", fontSize:12 }}>
                            {typeof val==="number" ? val.toLocaleString("en-IN",{maximumFractionDigits:2}) : String(val??"—")}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Smart Insights */}
          <div style={{ background:"#fff", border:"1px solid rgba(0,0,0,0.08)", borderRadius:12, boxShadow:"0 4px 12px rgba(0,0,0,0.05)", padding:"18px 20px" }}>
            <div style={{ display:"flex", alignItems:"center", gap:9, marginBottom:14 }}>
              <div style={{ width:30, height:30, borderRadius:8, background:"rgba(245,158,11,0.12)", display:"flex", alignItems:"center", justifyContent:"center", color:"#F59E0B" }}>
                <Lightbulb size={15}/>
              </div>
              <span style={{ fontSize:13, fontWeight:700, color:"#0F172A" }}>Smart Insights</span>
              <span style={{ fontSize:10, padding:"2px 7px", borderRadius:999, background:`${INDIGO}12`, color:INDIGO, fontWeight:700 }}>AUTO</span>
              <div style={{ marginLeft:"auto", width:8, height:8, borderRadius:"50%", background:"#F59E0B", boxShadow:"0 0 6px #F59E0B66" }}/>
            </div>
            <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
              {insights.map((ins,i)=>(
                <div key={i} style={{ display:"flex", alignItems:"flex-start", gap:10, padding:"9px 12px", borderRadius:9, background:"#F8FAFC", border:"1px solid rgba(0,0,0,0.04)", transition:"background .15s", cursor:"default" }}
                  onMouseEnter={e=>e.currentTarget.style.background=`${INDIGO}08`}
                  onMouseLeave={e=>e.currentTarget.style.background="#F8FAFC"}>
                  <span style={{ fontSize:15, flexShrink:0, marginTop:1 }}>{ins.icon}</span>
                  <span style={{ fontSize:12, color:"#475569", lineHeight:1.6 }}>{ins.text}</span>
                </div>
              ))}
              {insights.length===0 && <div style={{ textAlign:"center", padding:"24px 0", color:"#94A3B8", fontSize:13 }}>No insights available.</div>}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div style={{ marginTop:18, textAlign:"center", fontSize:11, color:"#94A3B8", padding:"10px 0", borderTop:"1px solid rgba(0,0,0,0.06)" }}>
          DATA PRO · Auto Dashboard · {meta?.name} · {new Date().toLocaleDateString("en-IN",{dateStyle:"long"})}
        </div>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        #dash-content::-webkit-scrollbar { width: 6px; }
        #dash-content::-webkit-scrollbar-track { background: transparent; }
        #dash-content::-webkit-scrollbar-thumb { background: rgba(79,70,229,0.25); border-radius: 3px; }
        #dash-content::-webkit-scrollbar-thumb:hover { background: rgba(79,70,229,0.45); }
        @media print {
          * { -webkit-print-color-adjust:exact!important; print-color-adjust:exact!important; }
          nav, #dash-toolbar { display:none!important; }
          #dash-content { overflow:visible!important; height:auto!important; background:#E0E7FF!important; }
          .apexcharts-canvas { background:#fff!important; }
        }
      `}</style>
    </div>
  );
}
