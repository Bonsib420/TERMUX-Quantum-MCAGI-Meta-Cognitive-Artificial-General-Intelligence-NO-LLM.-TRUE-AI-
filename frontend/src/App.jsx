import React, { useState, useEffect, useRef } from 'react';
import { Capacitor } from '@capacitor/core';
import { Clipboard } from '@capacitor/clipboard';

// Use the local development server when running in a browser, 
// and localhost:8000 when running as a native Android app (backend on same device)
const API_BASE = Capacitor.isNativePlatform() ? 'http://localhost:8000' : '/api';

// Panels
import CistercianPanel from './components/CistercianPanel';
import ImageGenPanel from './components/ImageGenPanel';
import SettingsPanel from './components/SettingsPanel';
import GrowthPanel from './components/GrowthPanel';
import DreamPanel from './components/DreamPanel';
import LearnPanel from './components/LearnPanel';
import EvolutionPanel from './components/EvolutionPanel';
// AccountPanel removed (no user accounts)

/* ── helpers ── */
const post = (url, body) =>
  fetch(`${API_BASE}${url}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(r => r.json());
const get = (url) => fetch(`${API_BASE}${url}`).then(r => r.json());
const del = (url) => fetch(`${API_BASE}${url}`, { method: 'DELETE' });

/* ── styles ── */
const css = `
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

:root {
  --bg-deep: #050a0f;
  --bg-main: #0a1018;
  --bg-surface: #0f1923;
  --bg-raised: #142030;
  --bg-hover: #1a2a3e;
  --border: #1a2a3e;
  --border-bright: #2a4a6e;
  --text-primary: #c8d6e5;
  --text-secondary: #6b8299;
  --text-muted: #3d5570;
  --accent: #00e5a0;
  --accent-dim: #00e5a022;
  --accent-glow: #00e5a044;
  --quantum: #a855f7;
  --quantum-dim: #a855f722;
  --quantum-glow: #a855f744;
  --danger: #ef4444;
  --warning: #f59e0b;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  background: var(--bg-deep);
  color: var(--text-primary);
  font-family: 'Space Grotesk', sans-serif;
  overflow: hidden;
  height: 100vh;
  height: 100dvh; /* Dynamic viewport height for mobile */
}

#root { height: 100vh; height: 100dvh; }

.app {
  display: grid;
  grid-template-columns: auto 1fr auto;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
}

/* ── LEFT SIDEBAR: Chat History ── */
.sidebar {
  width: 260px;
  background: var(--bg-main);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  transition: width 0.3s, opacity 0.3s;
  overflow: hidden;
}
.sidebar.collapsed {
  width: 0;
  opacity: 0;
  border: none;
}
.sidebar-header {
  padding: 1rem;
  border-bottom: 1px solid var(--border);
}
.sidebar-header h1 {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--accent);
  letter-spacing: 0.15em;
  margin-bottom: 0.75rem;
}
.btn-new {
  width: 100%;
  padding: 0.6rem;
  background: transparent;
  border: 1px solid var(--accent);
  color: var(--accent);
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  letter-spacing: 0.1em;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-new:hover {
  background: var(--accent-dim);
  box-shadow: 0 0 20px var(--accent-glow);
}
.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}
.session-list::-webkit-scrollbar { width: 3px; }
.session-list::-webkit-scrollbar-thumb { background: var(--border-bright); }
.session-item {
  padding: 0.6rem 0.75rem;
  margin-bottom: 2px;
  cursor: pointer;
  border-left: 2px solid transparent;
  transition: all 0.15s;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.session-item:hover { background: var(--bg-hover); }
.session-item.active {
  background: var(--bg-raised);
  border-left-color: var(--accent);
}
.session-id {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: var(--text-secondary);
}
.session-meta {
  font-size: 0.65rem;
  color: var(--text-muted);
  margin-top: 2px;
}
.btn-del {
  background: none;
  border: none;
  color: var(--danger);
  cursor: pointer;
  font-size: 0.9rem;
  opacity: 0;
  transition: opacity 0.15s;
}
.session-item:hover .btn-del { opacity: 1; }

/* ── Sidebar Toggle ── */
.sidebar-toggle {
  position: fixed;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  z-index: 200;
  background: var(--bg-raised);
  border: 1px solid var(--border);
  border-left: none;
  color: var(--text-secondary);
  padding: 0.75rem 0.3rem;
  cursor: pointer;
  font-size: 0.7rem;
  transition: all 0.2s;
  border-radius: 0 4px 4px 0;
}
.sidebar-toggle:hover {
  color: var(--accent);
  background: var(--bg-hover);
}
.sidebar.collapsed ~ .main-area .sidebar-toggle { left: 0; }
.sidebar:not(.collapsed) ~ .main-area .sidebar-toggle { left: 260px; }

/* ── MAIN CHAT AREA ── */
.main-area {
  display: flex;
  flex-direction: column;
  background: var(--bg-deep);
  position: relative;
  min-width: 0;
  height: 100%;
  min-height: 0;
}
.chat-header {
  padding: 0.6rem 1rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-main);
}
.chat-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: var(--text-secondary);
}
.stage-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  padding: 0.2rem 0.6rem;
  background: var(--quantum-dim);
  border: 1px solid var(--quantum);
  color: var(--quantum);
  letter-spacing: 0.05em;
}

/* Messages */
.messages {
  flex: 1 1 0;
  min-height: 0;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.messages::-webkit-scrollbar { width: 4px; }
.messages::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 2px; }

.msg {
  max-width: 85%;
  animation: msgIn 0.3s ease;
}
@keyframes msgIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.msg.user {
  align-self: flex-end;
}
.msg.assistant {
  align-self: flex-start;
}
.msg-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  letter-spacing: 0.1em;
  margin-bottom: 0.25rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.msg.user .msg-label { color: var(--accent); text-align: right; }
.msg.assistant .msg-label { color: var(--quantum); }

.msg-bubble {
  padding: 0.75rem 1rem;
  line-height: 1.6;
  font-size: 0.9rem;
  position: relative;
}
.msg.user .msg-bubble {
  background: var(--bg-raised);
  border: 1px solid var(--border-bright);
  color: var(--text-primary);
}
.msg.assistant .msg-bubble {
  background: linear-gradient(135deg, var(--bg-surface), var(--bg-raised));
  border: 1px solid var(--quantum-dim);
  color: var(--text-primary);
  box-shadow: 0 0 30px var(--quantum-glow);
}
.msg-copy {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 1rem;
  padding: 2px 6px;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
}
.msg-copy:hover { color: var(--accent); transform: scale(1.1); }

/* Typing indicator */
.typing {
  display: flex;
  gap: 4px;
  padding: 0.5rem 0;
}
.typing span {
  width: 6px;
  height: 6px;
  background: var(--quantum);
  border-radius: 50%;
  animation: pulse 1.4s infinite;
}
.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes pulse {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1.2); }
}

/* Input Area */
.input-area {
  padding: 0.25rem 1rem env(safe-area-inset-bottom, 0.5rem);
  border-top: 1px solid var(--border);
  background: var(--bg-main);
}
.input-row {
  display: flex;
  gap: 0.5rem;
  align-items: flex-end;
}
.input-row textarea {
  flex: 1;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  color: var(--text-primary);
  font-family: 'Space Grotesk', sans-serif;
  font-size: 0.9rem;
  padding: 0.65rem 0.75rem;
  resize: none;
  outline: none;
  transition: border-color 0.2s;
  min-height: 42px;
  max-height: 120px;
}
.input-row textarea:focus {
  border-color: var(--accent);
  box-shadow: 0 0 15px var(--accent-glow);
}
.input-row textarea::placeholder {
  color: var(--text-muted);
}
.btn-send {
  padding: 0.65rem 1.2rem;
  background: var(--accent);
  border: none;
  color: var(--bg-deep);
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
  letter-spacing: 0.05em;
}
.btn-send:hover {
  box-shadow: 0 0 25px var(--accent-glow);
}
.btn-send:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.btn-attach {
  padding: 0.65rem 0.75rem;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.15s;
}
.btn-attach:hover {
  border-color: var(--accent);
  color: var(--accent);
}
.file-chips {
  display: flex;
  gap: 0.25rem;
  flex-wrap: wrap;
  margin-bottom: 0.5rem;
}
.file-chip {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  padding: 0.2rem 0.5rem;
  background: var(--bg-raised);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 0.3rem;
}
.file-chip button {
  background: none;
  border: none;
  color: var(--danger);
  cursor: pointer;
  font-size: 0.7rem;
}

/* ── RIGHT PANEL ── */
.panel {
  width: 0;
  background: var(--bg-main);
  border-left: none;
  transition: width 0.3s;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.panel.open {
  width: 320px;
  border-left: 1px solid var(--border);
}
.panel-header {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.panel-header h2 {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: var(--quantum);
  letter-spacing: 0.1em;
}
.btn-close-panel {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 1.1rem;
  transition: color 0.15s;
}
.btn-close-panel:hover { color: var(--danger); }

.panel-toggle-btn {
  position: fixed;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  z-index: 200;
  background: var(--bg-raised);
  border: 1px solid var(--border);
  border-right: none;
  color: var(--text-secondary);
  padding: 0.75rem 0.3rem;
  cursor: pointer;
  font-size: 0.7rem;
  transition: all 0.2s;
  border-radius: 4px 0 0 4px;
}
.panel-toggle-btn:hover {
  color: var(--quantum);
  background: var(--bg-hover);
}
.panel.open ~ .panel-toggle-btn { right: 320px; }

.panel-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
  padding: 0.75rem;
}
.panel-tile {
  padding: 1rem 0.5rem;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  cursor: pointer;
  text-align: center;
  transition: all 0.2s;
  font-size: 0.75rem;
}
.panel-tile:hover {
  background: var(--bg-hover);
  border-color: var(--quantum);
  color: var(--quantum);
  box-shadow: 0 0 15px var(--quantum-glow);
}
.panel-tile .tile-icon {
  font-size: 1.4rem;
  display: block;
  margin-bottom: 0.4rem;
}
.panel-tile .tile-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  letter-spacing: 0.1em;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 0.75rem;
}
.panel-body::-webkit-scrollbar { width: 3px; }
.panel-body::-webkit-scrollbar-thumb { background: var(--border-bright); }

.panel-back {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  margin-bottom: 0.5rem;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  transition: color 0.15s;
}
.panel-back:hover { color: var(--accent); }

/* ── GROWTH PANEL ── */
.growth-section {
  margin-bottom: 1.25rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border);
}
.growth-section:last-child { border-bottom: none; }
.growth-section h4 {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: var(--quantum);
  letter-spacing: 0.1em;
  margin-bottom: 0.6rem;
  text-transform: uppercase;
}
.growth-stage {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}
.growth-stage .label { color: var(--text-secondary); font-size: 0.8rem; }
.growth-stage .value { font-size: 1.1rem; font-weight: 600; }
.growth-stage .stage-level { color: var(--text-muted); font-size: 0.75rem; }
.next-stage { color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 0.5rem; }
.limiting-factor { font-weight: 600; margin-top: 0.5rem; }

/* Metrics Grid */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
}
.metric-item {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  padding: 0.6rem;
  text-align: center;
}
.metric-label {
  display: block;
  font-size: 0.65rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}
.metric-value {
  display: block;
  font-size: 1rem;
  font-weight: 600;
  color: var(--accent);
  font-family: 'JetBrains Mono', monospace;
}

/* Progress Bars */
.progress-item { margin-bottom: 0.6rem; }
.progress-header {
  display: flex;
  justify-content: space-between;
  font-size: 0.7rem;
  margin-bottom: 0.2rem;
}
.progress-label { color: var(--text-secondary); }
.progress-value { color: var(--accent); font-family: 'JetBrains Mono', monospace; }
.progress-bar {
  height: 6px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 3px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  transition: width 0.5s ease;
  border-radius: 2px;
}

/* Thresholds Table */
.thresholds-table {
  overflow-x: auto;
  font-size: 0.75rem;
}
.thresholds-table table {
  width: 100%;
  border-collapse: collapse;
}
.thresholds-table th,
.thresholds-table td {
  padding: 0.4rem 0.5rem;
  text-align: left;
  border-bottom: 1px solid var(--border);
}
.thresholds-table th {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: var(--bg-surface);
}
.thresholds-table tr.current-stage {
  background: var(--quantum-dim);
  border-left: 2px solid var(--quantum);
}
.thresholds-table tr.current-stage td {
  color: var(--quantum);
  font-weight: 600;
}

/* Events List */
.events-list {
  list-style: none;
  padding: 0;
}
.events-list li {
  padding: 0.5rem;
  margin-bottom: 0.4rem;
  background: var(--bg-surface);
  border-left: 2px solid var(--accent);
  font-size: 0.8rem;
}
.event-type {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: var(--accent);
  display: block;
  margin-bottom: 0.2rem;
}
.event-time {
  display: block;
  font-size: 0.65rem;
  color: var(--text-muted);
  margin-bottom: 0.2rem;
}
.event-details {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.3rem;
}
.event-details .detail {
  font-size: 0.65rem;
  color: var(--text-secondary);
  background: var(--bg-raised);
  padding: 0.15rem 0.4rem;
  border-radius: 2px;
}
.no-events {
  color: var(--text-muted);
  font-style: italic;
  text-align: center;
  padding: 1rem;
}

/* Explain toggle in header */
.explain-toggle {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  padding: 0.2rem 0.6rem;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s;
  letter-spacing: 0.05em;
}
.explain-toggle.active {
  background: var(--accent-dim);
  border-color: var(--accent);
  color: var(--accent);
  box-shadow: 0 0 10px var(--accent-glow);
}

/* Responsive */
@media (max-width: 768px) {
  .app { grid-template-columns: 1fr; }
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 200;
    box-shadow: 4px 0 20px rgba(0,0,0,0.5);
  }
  .sidebar.collapsed { width: 0; }
  .panel {
    position: fixed;
    right: 0;
    top: 0;
    bottom: 0;
    z-index: 200;
    box-shadow: -4px 0 20px rgba(0,0,0,0.5);
  }
  /* Dynamic toggle position based on sidebar state */
  .sidebar.collapsed ~ .main-area .sidebar-toggle { left: 0; }
  .sidebar:not(.collapsed) ~ .main-area .sidebar-toggle { left: 260px; }
}
`;

/* ── Panel Content Components (minimal) ── */
function PanelPlaceholder({ title }) {
  return <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem', fontFamily: 'JetBrains Mono, monospace', fontSize: '0.75rem' }}>
    {title} panel — coming soon
  </div>;
}

/* ── Main App ── */
export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [panelOpen, setPanelOpen] = useState(false);
  const [panelView, setPanelView] = useState(null); // null = grid, string = specific panel
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [explainMode, setExplainMode] = useState(false);
  const [files, setFiles] = useState([]);
  const messagesEnd = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => { loadSessions(); }, []);
  useEffect(() => { messagesEnd.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const loadSessions = async () => {
    try {
      const data = await get('/chat/sessions');
      setSessions(data.sessions || []);
    } catch (e) { console.error(e); }
  };

  const loadSession = async (id) => {
    try {
      const data = await get(`/chat/history/${id}`);
      setMessages((data.messages || []).map(m => ({ role: m.role, content: m.content })));
      setCurrentSession(id);
    } catch (e) { console.error(e); }
  };

  const deleteSession = async (id, e) => {
    e.stopPropagation();
    if (!confirm('Delete this session?')) return;
    try {
      await del(`/chat/history/${id}`);
      setSessions(s => s.filter(x => x.session_id !== id));
      if (currentSession === id) { setCurrentSession(null); setMessages([]); }
    } catch (e) { console.error(e); }
  };

  const newChat = () => { setCurrentSession(null); setMessages([]); };

  const send = async () => {
    const text = input.trim();
    if (!text && !files.length) return;

    const userMsg = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setFiles([]);
    setLoading(true);

    try {
      const data = await post('/quantum/chat', {
        content: text,
        mode: 'quantum',
        session_id: currentSession,
        explain_mode: explainMode,
        files: files.map(f => ({ filename: f.name, size: f.size }))
      });

      let content = data.response;
      if (explainMode && data.explanation) {
        const exp = data.explanation;
        content += `\n\n═══ PIPELINE ═══\n`;
        content += `Path: ${exp.reasoning_path?.join(' → ') || '—'}\n`;
        content += `Confidence: ${((exp.confidence_score || 0) * 100).toFixed(0)}%\n`;
        content += `Engines: ${exp.engines_used?.join(', ') || '—'}`;
        if (exp.entelechy) {
          const ent = exp.entelechy;
          content += `\n\n═══ ENTELECHY CASCADE ═══\n`;
          content += `[THE_LOOK]: ${ent.look?.concept || ent.look} (${ent.look?.description || 'Realizing Potential'})\n`;
          content += `[THE_SAW]: ${ent.saw?.concept || ent.saw} (${ent.saw?.description || 'Bridging the Void'})\n`;
          content += `[THE_BEAUTIFUL]: ${ent.beautiful?.concept || ent.beautiful} (${ent.beautiful?.description || 'Actualizing the Work'})\n`;
          content += `[PROJECTION]: ${ent.projection}`;
        }
      }

      setMessages(prev => [...prev, { role: 'assistant', content }]);
      if (!currentSession && data.session_id) {
        setCurrentSession(data.session_id);
        loadSessions();
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${e.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  };

  const handleFile = (e) => {
    setFiles(prev => [...prev, ...Array.from(e.target.files)]);
  };

  const copy = async (text) => {
    try {
      if (Capacitor.isNativePlatform()) {
        // Use Capacitor Clipboard plugin for native Android/iOS
        await Clipboard.write({ string: text });
      } else if (navigator.clipboard) {
        // Use Web Clipboard API for browsers
        await navigator.clipboard.writeText(text);
      } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
      }
    } catch (err) {
      console.error('Clipboard copy failed:', err);
      // Try alternative method as last resort
      try {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        document.body.appendChild(textArea);
        textArea.select();
        const success = document.execCommand('copy');
        document.body.removeChild(textArea);
        if (!success) throw new Error('Fallback copy failed');
      } catch (e) {
        console.error('All clipboard methods failed:', e);
      }
    }
  };

  const openPanel = (view) => {
    setPanelView(view);
    setPanelOpen(true);
  };

  const panelTiles = [
    { id: 'numerals', icon: '🔢', label: 'NUMERALS' },
    { id: 'images', icon: '🎨', label: 'IMAGES' },
    { id: 'dream', icon: '🌙', label: 'DREAM' },
    { id: 'growth', icon: '📈', label: 'GROWTH' },
    { id: 'learn', icon: '🎓', label: 'LEARN' },
    { id: 'evolve', icon: '🧬', label: 'EVOLVE' },
    { id: 'settings', icon: '⚙️', label: 'SETTINGS' },
    // 'account' tile removed
  ];

  return (
    <>
      <style>{css}</style>
      <div className="app">

        {/* LEFT: Chat History */}
        <aside className={`sidebar ${sidebarOpen ? '' : 'collapsed'}`}>
          <div className="sidebar-header">
            <h1>QUANTUM MCAGI</h1>
            <button className="btn-new" onClick={newChat}>+ NEW CHAT</button>
          </div>
          <div className="session-list">
            {sessions.map(s => (
              <div
                key={s.session_id}
                className={`session-item ${currentSession === s.session_id ? 'active' : ''}`}
                onClick={() => loadSession(s.session_id)}
              >
                <div>
                  <div className="session-id">{s.session_id.slice(0, 8)}…</div>
                  <div className="session-meta">
                    {new Date(s.last_message).toLocaleDateString()} · {s.message_count} msgs
                  </div>
                </div>
                <button className="btn-del" onClick={(e) => deleteSession(s.session_id, e)}>×</button>
              </div>
            ))}
          </div>
        </aside>

        {/* CENTER: Chat */}
        <main className="main-area">
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? '◀' : '▶'}
          </button>

          <div className="chat-header">
            <div className="chat-title">
              {currentSession ? `Session ${currentSession.slice(0, 8)}…` : 'New conversation'}
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <button
                className={`explain-toggle ${explainMode ? 'active' : ''}`}
                onClick={() => setExplainMode(!explainMode)}
              >
                {explainMode ? '◉ EXPLAIN' : '○ EXPLAIN'}
              </button>
              <span className="stage-badge">STAGE 5</span>
            </div>
          </div>

          <div className="messages">
            {messages.map((m, i) => (
              <div key={i} className={`msg ${m.role}`}>
                <div className="msg-label">
                  <span>{m.role === 'user' ? 'YOU' : 'QUANTUM AI'}</span>
                  <button className="msg-copy" onClick={() => copy(m.content)} title="Copy message">📋</button>
                </div>
                <div className="msg-bubble">
                  { (typeof m.content === "string" ? m.content : String(m.content || "")).split('\n').map((line, j) => (
                    <React.Fragment key={j}>{line}<br /></React.Fragment>
                  ))}
                </div>
              </div>
            ))}
            {loading && (
              <div className="msg assistant">
                <div className="msg-label"><span>QUANTUM AI</span></div>
                <div className="msg-bubble">
                  <div className="typing"><span /><span /><span /></div>
                </div>
              </div>
            )}
            <div ref={messagesEnd} />
          </div>

          {/* Input */}
          <div className="input-area">
            {files.length > 0 && (
              <div className="file-chips">
                {files.map((f, i) => (
                  <div key={i} className="file-chip">
                    {f.name}
                    <button onClick={() => setFiles(prev => prev.filter((_, idx) => idx !== i))}>×</button>
                  </div>
                ))}
              </div>
            )}
            <div className="input-row">
              <label className="btn-attach" title="Attach file">
                +
                <input type="file" multiple onChange={handleFile} style={{ display: 'none' }} />
              </label>
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKey}
                placeholder="Ask anything…"
                disabled={loading}
                rows={1}
              />
              <button className="btn-send" onClick={send} disabled={loading || (!input.trim() && !files.length)}>
                
{loading ? '···' : '→'}
              </button>
            </div>
          </div>
        </main>

        {/* RIGHT: Feature Panel */}
        <aside className={`panel ${panelOpen ? 'open' : ''}`}>
          <div className="panel-header">
            <h2>{panelView ? panelView.toUpperCase() : 'PANEL'}</h2>
            <button className="btn-close-panel" onClick={() => { setPanelOpen(false); setPanelView(null); }}>×</button>
          </div>
          <div className="panel-body">
            {!panelView ? (
              <div className="panel-grid">
                {panelTiles.map(t => (
                  <div key={t.id} className="panel-tile" onClick={() => setPanelView(t.id)}>
                    <span className="tile-icon">{t.icon}</span>
                    <span className="tile-label">{t.label}</span>
                  </div>
                ))}
              </div>
            ) : (
              <>
                <button className="panel-back" onClick={() => setPanelView(null)}>← back</button>
                <div className="panel-content">
                  {panelView === 'numerals' && <CistercianPanel />}
                  {panelView === 'images' && <ImageGenPanel />}
                  {panelView === 'dream' && <DreamPanel />}
                  {panelView === 'growth' && <GrowthPanel />}
                  {panelView === 'learn' && <LearnPanel />}
                  {panelView === 'evolve' && <EvolutionPanel />}
                  {panelView === 'settings' && <SettingsPanel />}
                  {/* AccountView removed */}
                </div>
              </>
            )}
          </div>
        </aside>

        {!panelOpen && (
          <button
            className="panel-toggle-btn"
            onClick={() => setPanelOpen(true)}
            style={{ position: 'fixed', right: 0 }}
          >
            ◀
          </button>
        )}
      </div>
    </>
  );
}
