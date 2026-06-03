import { useState } from "react";
import { authAPI } from "./api";

const S = {
  wrap: { minHeight:"100vh", display:"flex", alignItems:"center", justifyContent:"center",
          background:"#0d1117", fontFamily:"'Segoe UI',sans-serif" },
  card: { width:380, background:"#161b22", border:"1px solid #30363d", borderRadius:16,
          padding:"36px 32px", boxShadow:"0 8px 40px rgba(0,0,0,0.6)" },
  logo: { display:"flex", alignItems:"center", gap:10, marginBottom:28, justifyContent:"center" },
  logoBox: { width:40,height:40, background:"linear-gradient(135deg,#00d4ff,#0099cc)",
             borderRadius:10, display:"flex", alignItems:"center", justifyContent:"center",
             fontSize:22, fontWeight:900, color:"#000" },
  title: { fontSize:20, fontWeight:800, color:"#00d4ff", letterSpacing:1 },
  sub:   { fontSize:10, color:"#8b949e", letterSpacing:2, textAlign:"center", marginTop:2 },
  tabs:  { display:"flex", gap:0, marginBottom:24, background:"#0d1117",
           borderRadius:8, padding:3, border:"1px solid #30363d" },
  tab:   (active) => ({ flex:1, padding:"8px 0", border:"none", borderRadius:6, cursor:"pointer",
           fontWeight:600, fontSize:13, transition:"all .2s",
           background: active?"#00d4ff22":"transparent",
           color: active?"#00d4ff":"#8b949e",
           boxShadow: active?"inset 0 0 0 1px #00d4ff44":"none" }),
  label: { fontSize:12, color:"#8b949e", marginBottom:5, display:"block" },
  input: { width:"100%", padding:"9px 12px", background:"#0d1117", border:"1px solid #30363d",
           borderRadius:8, color:"#e6edf3", fontSize:13, outline:"none", marginBottom:14,
           boxSizing:"border-box", transition:"border-color .2s" },
  btn:   { width:"100%", padding:"11px", background:"#00d4ff", border:"none", borderRadius:8,
           color:"#000", fontWeight:800, fontSize:14, cursor:"pointer",
           transition:"opacity .2s", marginTop:4 },
  err:   { background:"#ff6b6b22", border:"1px solid #ff6b6b44", borderRadius:8,
           padding:"9px 12px", fontSize:12, color:"#ff6b6b", marginBottom:12 },
  ok:    { background:"#7fff7f22", border:"1px solid #7fff7f44", borderRadius:8,
           padding:"9px 12px", fontSize:12, color:"#7fff7f", marginBottom:12 },
};

export default function Auth({ onLogin }) {
  const [tab, setTab]   = useState("login");
  const [form, setForm] = useState({ username:"", email:"", password:"", password2:"" });
  const [error, setError] = useState("");
  const [ok, setOk]     = useState("");
  const [loading, setLoading] = useState(false);

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setError(""); setOk(""); setLoading(true);

    try {
      if (tab === "login") {
        const { data } = await authAPI.login({
          username: form.username,
          password: form.password,
        });
        localStorage.setItem("access_token",  data.access);
        localStorage.setItem("refresh_token", data.refresh);
        onLogin();
      } else {
        await authAPI.register({
          username:  form.username,
          email:     form.email,
          password:  form.password,
          password2: form.password2,
        });
        setOk("Account created! Ab login karo.");
        setTab("login");
        setForm(f => ({ ...f, password:"", password2:"" }));
      }
    } catch (err) {
      const d = err.response?.data;
      if (typeof d === "object") {
        setError(Object.values(d).flat().join(" "));
      } else {
        setError("Something went wrong. Check backend connection.");
      }
    }
    setLoading(false);
  };

  return (
    <div style={S.wrap}>
      <div style={S.card}>
        {/* Logo */}
        <div style={S.logo}>
          <div style={S.logoBox}>D</div>
          <div>
            <div style={S.title}>DATA PRO</div>
            <div style={S.sub}>SUPER EDITION</div>
          </div>
        </div>

        {/* Tabs */}
        <div style={S.tabs}>
          <button style={S.tab(tab==="login")}    onClick={()=>{setTab("login");setError("");}}>Login</button>
          <button style={S.tab(tab==="register")} onClick={()=>{setTab("register");setError("");}}>Register</button>
        </div>

        {error && <div style={S.err}>⚠️ {error}</div>}
        {ok    && <div style={S.ok}>✅ {ok}</div>}

        <form onSubmit={submit}>
          <label style={S.label}>Username</label>
          <input style={S.input} value={form.username} onChange={set("username")}
                 placeholder="your_username" required autoComplete="username"/>

          {tab==="register" && <>
            <label style={S.label}>Email</label>
            <input style={S.input} type="email" value={form.email} onChange={set("email")}
                   placeholder="you@example.com" required/>
          </>}

          <label style={S.label}>Password</label>
          <input style={S.input} type="password" value={form.password} onChange={set("password")}
                 placeholder="••••••••" required autoComplete="current-password"/>

          {tab==="register" && <>
            <label style={S.label}>Confirm Password</label>
            <input style={S.input} type="password" value={form.password2} onChange={set("password2")}
                   placeholder="••••••••" required/>
          </>}

          <button style={{...S.btn, opacity: loading?0.7:1}} disabled={loading}>
            {loading ? "⏳ Please wait..." : tab==="login" ? "🚀 Login" : "✨ Create Account"}
          </button>
        </form>

        <div style={{marginTop:16,textAlign:"center",fontSize:11,color:"#8b949e"}}>
          Backend: <span style={{color:"#00d4ff"}}>http://localhost:8000</span>
        </div>
      </div>
    </div>
  );
}
