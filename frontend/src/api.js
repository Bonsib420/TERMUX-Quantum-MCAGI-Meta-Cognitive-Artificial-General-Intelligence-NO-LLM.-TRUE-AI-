/**
 * Quantum MCAGI - Complete API Service Layer
 * Wires all frontend components to real backend endpoints.
 * Drop this file into: frontend/src/api.js
 * Then import in each component: import * as API from '../api.js'
 */

const BASE = 'http://localhost:8000/api';

async function request(method, path, body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${BASE}${path}`, opts);
  if (!res.ok) throw new Error(`API ${method} ${path} → ${res.status}`);
  return res.json();
}

const get  = (path)        => request('GET',    path);
const post = (path, body)  => request('POST',   path, body);
const del  = (path)        => request('DELETE', path);

// ─── CHAT (ChatInterface.jsx) ────────────────────────────────────────────────
// REPLACE generateStructuredResponse() with API.chat()
export const chat = (message, session_id = null, explain = false) =>
  post('/quantum/chat', { message, session_id, explain_mode: explain });

export const getChatHistory    = (session_id, limit = 50) => get(`/chat/history/${session_id}?limit=${limit}`);
export const deleteChatHistory = (session_id)              => del(`/chat/history/${session_id}`);
export const listChatSessions  = ()                        => get('/chat/sessions');
export const exportChat        = (session_id)              => get(`/chat/export/${session_id}`);

// ─── SETTINGS (SettingsPanel.jsx) ───────────────────────────────────────────
export const getSettingsStatistics = () => get('/settings/statistics');

// ─── COGNITIVE STATUS (GrowthPanel.jsx, SettingsPanel.jsx) ──────────────────
export const getQuantumStatus     = () => get('/quantum/status');
export const getGrowthStats       = () => get('/quantum/growth');
export const getGrowthNotifications = () => get('/growth/notifications');
export const getGrowthEvolution   = () => get('/growth/evolution');
export const getGrowthStatsAlt    = () => get('/growth/stats');
export const getKnowledgeGraph    = () => get('/knowledge/graph');

// ─── MEMORIES (GrowthPanel.jsx, AccountPanel.jsx) ───────────────────────────
export const getSemanticMemories     = () => get('/quantum/memories/semantic');
export const getEpisodicMemories     = () => get('/quantum/memories/episodic');
export const getProceduralMemories   = () => get('/quantum/memories/procedural');
export const getPhilosophicalMemories = () => get('/quantum/memories/philosophical');
export const exportMemory            = () => get('/memory/export');
export const importMemory            = (data) => post('/memory/import', data);

// ─── DREAM ENGINE (DreamPanel.jsx) ──────────────────────────────────────────
export const getDreamStatus   = () => get('/dream/status');
export const getDreamHistory  = () => get('/dream/history');
export const getDreamInsights = () => get('/dream/insights');
export const enterDream       = () => post('/dream/enter', {});
export const wakeDream        = () => post('/dream/wake', {});
export const synthesizeDream  = () => get('/dream/synthesize');
export const synthesizeBatch  = () => get('/dream/synthesize/batch');
export const generateDream    = (sentences = 3) => get(`/dream/generate?sentences=${sentences}`);
export const generateDreamPost = (params)        => post('/dream/generate', params);

// ─── EVOLUTION (EvolutionPanel.jsx) ─────────────────────────────────────────
export const getEvolutionStatus  = () => get('/evolution/status');
export const triggerEvolution    = () => post('/evolution/trigger', {});
export const analyzeAllFiles     = () => get('/evolution/analyze-all');
export const analyzeFile         = (filename) => get(`/evolution/analyze/${filename}`);

// ─── BRAIN / LEARNING (LearnPanel.jsx) ──────────────────────────────────────
export const getBrainStatus   = () => get('/brain/status');
export const learnWord        = (word, context = '') => post('/brain/learn-word', { word, context });
export const learnConcept     = (concept, data)      => post('/brain/learn-concept', { concept, ...data });

// Algorithmic engines — map to MARKOV / TFIDF / BM25 / PMI / HEBBIAN buttons
export const runMarkov  = (query, n = 30) => get(`/algorithmic/markov?query=${encodeURIComponent(query)}&n=${n}`);
export const runTFIDF   = (query)          => get(`/algorithmic/tfidf?query=${encodeURIComponent(query)}`);
export const runBM25    = (query)          => get(`/algorithmic/bm25?query=${encodeURIComponent(query)}`);
export const runPMI     = (query)          => get(`/algorithmic/pmi?query=${encodeURIComponent(query)}`);
export const runHebbian = (concepts)       => post('/algorithmic/hebbian/learn', { concepts });

// ─── IMAGE GENERATION (ImageGenPanel.jsx) ───────────────────────────────────
export const generateImage   = (prompt, width = 512, height = 512) =>
  post('/image/generate', { prompt, width, height });
export const analyzeImage    = (image_data) => post('/image/analyze', { image_data });
export const generateSVG     = (prompt)     => post('/image/quantum-svg', { prompt });

// ─── CISTERCIAN (CistercianPanel.jsx, CistercianExplorer.jsx) ───────────────
export const getCistercianNumeral = (n) => get(`/cistercian/numeral?n=${n}`);
export const getCistercianData    = ()  => get('/cistercian/data');
export const getCistercianBatch   = (numbers) => get(`/cistercian/batch?numbers=${numbers.join(',')}`);
export const getCistercianFont    = ()  => get('/cistercian/font');

// ─── ACCOUNT (AccountPanel.jsx) ─────────────────────────────────────────────
// Sessions count + memory export = real account data
export const getAccountData = async () => {
  const [sessions, memory] = await Promise.all([
    listChatSessions(),
    exportMemory(),
  ]);
  return { sessions, memory };
};

// ─── QUANTUM CORE ────────────────────────────────────────────────────────────
export const applyQuantumGate = (gate, params) => post('/quantum/gate', { gate, ...params });
export const getQuantumState  = ()              => get('/quantum/state');

// ─── RESEARCH ────────────────────────────────────────────────────────────────
export const queryResearch      = (query) => post('/research/query', { query });
export const getResearchStats   = ()       => get('/research/stats');
export const getResearchStatus  = ()       => get('/research/status');
export const getResearchHistory = ()       => get('/research/history');
export const startAutonomousResearch = ()  => post('/research/autonomous/start', {});
export const stopAutonomousResearch  = ()  => post('/research/autonomous/stop', {});
export const getAutonomousProgress   = ()  => get('/research/autonomous/progress');

// ─── PERSONALITY / ANALYSIS ──────────────────────────────────────────────────
export const getPersonalitySummary = ()       => get('/personality/summary');
export const getPersonalityOpinion = (topic)  => post('/personality/opinion', { topic });
export const analyzeText           = (text)   => post('/analyze/text', { text });
export const humanizeText          = (text)   => post('/analyze/humanize', { text });

// ─── HEALTH CHECK ────────────────────────────────────────────────────────────
export const healthCheck = () => get('/health');
