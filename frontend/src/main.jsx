import { StrictMode, useState, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import Auth from './Auth.jsx'
import { authAPI } from './api.js'

function Root() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    // Try to restore session from stored token
    const token = localStorage.getItem('access_token');
    if (!token) { setChecking(false); return; }
    authAPI.me()
      .then(({ data }) => setUser(data))
      .catch(() => { localStorage.clear(); })
      .finally(() => setChecking(false));
  }, []);

  const handleLogin = async () => {
    try {
      const { data } = await authAPI.me();
      setUser(data);
    } catch { localStorage.clear(); }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  if (checking) {
    return (
      <div style={{minHeight:"100vh",display:"flex",alignItems:"center",justifyContent:"center",background:"#0d1117",color:"#00d4ff",fontFamily:"'Segoe UI',sans-serif",fontSize:14}}>
        ⚡ Loading DataPro...
      </div>
    );
  }

  if (!user) return <Auth onLogin={handleLogin} />;
  return <App user={user} onLogout={handleLogout} />;
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Root />
  </StrictMode>
)
