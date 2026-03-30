import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = '/api';

function DreamPanel() {
  const [numSentences, setNumSentences] = useState(3);
  const [dream, setDream] = useState(null);
  const [status, setStatus] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const loadStatusAndHistory = async () => {
    setRefreshing(true);
    try {
      const [statusRes, histRes] = await Promise.all([
        axios.get(`${API_BASE}/dream/status`),
        axios.get(`${API_BASE}/dream/history`, { params: { limit: 10 } })
      ]);
      setStatus(statusRes.data);
      setHistory(histRes.data.dreams || []);
    } catch (e) {
      console.error('Failed to load dream data:', e);
    } finally {
      setRefreshing(false);
    }
  };

  const generateDream = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/dream/generate`, { params: { num_sentences: numSentences } });
      setDream(res.data);
      // Refresh history after generation
      loadStatusAndHistory();
    } catch (e) {
      alert('Dream generation failed: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatusAndHistory();
    // Optional: auto-refresh every 30s to show live dreams
    const interval = setInterval(loadStatusAndHistory, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="panel-dream">
      <h3>🌙 Dream Engine</h3>
      
      <div style={{ marginBottom: '1rem' }}>
        <strong>Status:</strong> {status?.is_dreaming ? '🌙 Dreaming' : '☀️ Awake'} 
        {status?.current_dream && status.current_dream.activities && (
          <span> — Current: {status.current_dream.activities[status.current_dream.activities.length-1]?.activity || 'idle'}</span>
        )}
      </div>
      
      <div className="control-group" style={{ marginBottom: '1rem' }}>
        <label>
          Sentences:
          <input 
            type="number" 
            min="1" 
            max="10" 
            value={numSentences} 
            onChange={e => setNumSentences(parseInt(e.target.value) || 3)} 
            style={{ marginLeft: '0.5rem', padding: '0.25rem' }}
          />
        </label>
        <button 
          className="btn-primary" 
          onClick={generateDream} 
          disabled={loading}
          style={{ marginLeft: '1rem' }}
        >
          {loading ? 'Generating...' : 'Generate Dream'}
        </button>
        <button 
          className="btn-secondary"
          onClick={loadStatusAndHistory}
          disabled={refreshing}
          style={{ marginLeft: '0.5rem' }}
        >
          {refreshing ? '...' : 'Refresh'}
        </button>
      </div>

      {dream && (
        <div className="dream-result" style={{ background: 'var(--bg-surface)', padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem' }}>
          <p className="dream-text">{dream.dream}</p>
          <div className="dream-meta" style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
            <span>Method: {dream.method}</span>
            <span style={{ marginLeft: '1rem' }}>Concepts: {dream.concepts_used?.join(', ')}</span>
          </div>
        </div>
      )}

      <div>
        <h4>Dream History</h4>
        {history.length === 0 ? (
          <p style={{ color: '#666' }}>No dreams recorded yet.</p>
        ) : (
          <ul style={{ maxHeight: '300px', overflowY: 'auto', paddingRight: '0.5rem' }}>
            {history.map((h, i) => (
              <li key={i} style={{ marginBottom: '0.75rem', background: '#111', padding: '0.5rem', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.85rem', color: '#00d4ff' }}>
                  {new Date(h.started_at).toLocaleString()}
                </div>
                {h.activities && h.activities.length > 0 && (
                  <div>Activities: {h.activities.map(a => a.activity).join(', ')}</div>
                )}
                {h.insights && h.insights.length > 0 && (
                  <div>Insights: {h.insights.slice(0,3).join('; ')}</div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default DreamPanel;
