import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = '/api';

function LearnPanel() {
  const [activeTab, setActiveTab] = useState('algorithms');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  // --- Algorithmic tab state ---
  const [markovLength, setMarkovLength] = useState(30);
  const [markovSeed, setMarkovSeed] = useState('quantum');
  const [tfidfText, setTfidfText] = useState('Consciousness is the subjective experience of awareness.');
  const [bm25Query, setBm25Query] = useState('free will');
  const [pmiWord1, setPmiWord1] = useState('quantum');
  const [pmiWord2, setPmiWord2] = useState('consciousness');
  const [hebbianPairs, setHebbianPairs] = useState('consciousness,quantum\nfree,will');

  // --- Research tab state ---
  const [researchStatus, setResearchStatus] = useState(null);
  const [researchHistory, setResearchHistory] = useState([]);
  const [researchDuration, setResearchDuration] = useState(30);
  const [refreshingResearch, setRefreshingResearch] = useState(false);

  const refreshResearchStatus = async () => {
    setRefreshingResearch(true);
    try {
      const [statusRes, histRes] = await Promise.all([
        axios.get(`${API_BASE}/research/status`),
        axios.get(`${API_BASE}/research/history?limit=10`)
      ]);
      setResearchStatus(statusRes.data);
      setResearchHistory(histRes.data.history || []);
    } catch (e) {
      console.error('Research fetch error:', e);
    } finally {
      setRefreshingResearch(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'research') {
      refreshResearchStatus();
      const interval = setInterval(refreshResearchStatus, 10000);
      return () => clearInterval(interval);
    }
  }, [activeTab]);

  const launchResearch = async () => {
    if (!window.confirm(`Start autonomous research for ${researchDuration} minutes?`)) return;
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/research/launch?duration_minutes=${researchDuration}`);
      alert(`Research launched: ${res.data.status}`);
      setTimeout(refreshResearchStatus, 2000);
    } catch (e) {
      alert('Failed: ' + (e.response?.data?.detail || e.message));
    } finally {
      setLoading(false);
    }
  };

  // --- Cloud tab state ---
  const [cloudStatus, setCloudStatus] = useState(null);
  const [cloudMessage, setCloudMessage] = useState(null);
  const [cloudPreview, setCloudPreview] = useState(null);
  const [refreshingCloud, setRefreshingCloud] = useState(false);

  const refreshCloudStatus = async () => {
    setRefreshingCloud(true);
    try {
      const res = await axios.get(`${API_BASE}/cloud/status`);
      setCloudStatus(res.data.status);
    } catch (e) {
      console.error(e);
    } finally {
      setRefreshingCloud(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'cloud') {
      refreshCloudStatus();
    }
  }, [activeTab]);

  const saveToCloud = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/cloud/save`);
      setCloudMessage(res.data.message);
      setTimeout(refreshCloudStatus, 1000);
    } catch (e) {
      setCloudMessage('Error: ' + (e.response?.data?.detail || e.message));
    } finally {
      setLoading(false);
    }
  };

  const loadPreview = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/cloud/load`);
      setCloudPreview(res.data.data);
      setCloudMessage('Preview loaded (not restored).');
    } catch (e) {
      setCloudMessage('Error: ' + (e.response?.data?.detail || e.message));
    } finally {
      setLoading(false);
    }
  };

  const restoreFromCloud = async () => {
    if (!window.confirm('Restore state from cloud? This will overwrite local concepts.')) return;
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/cloud/restore`);
      setCloudMessage(res.data.message);
      setCloudPreview(null);
      setTimeout(refreshCloudStatus, 1000);
    } catch (e) {
      setCloudMessage('Error: ' + (e.response?.data?.detail || e.message));
    } finally {
      setLoading(false);
    }
  };

  // --- Algorithmic runner ---
  const runAlgorithm = async (algo) => {
    setLoading(true);
    setResult(null);
    try {
      if (algo === 'markov') {
        const res = await axios.get(`${API_BASE}/algorithmic/markov`, {
          params: { length: markovLength, seed: markovSeed }
        });
        setResult(res.data);
      } else if (algo === 'tfidf') {
        const res = await axios.get(`${API_BASE}/algorithmic/tfidf`, {
          params: { text: tfidfText, top_n: 10 }
        });
        setResult(res.data);
      } else if (algo === 'bm25') {
        const res = await axios.get(`${API_BASE}/algorithmic/bm25`, {
          params: { query: bm25Query, corpus_size: 5 }
        });
        setResult(res.data);
      } else if (algo === 'pmi') {
        const res = await axios.get(`${API_BASE}/algorithmic/pmi`, {
          params: { word1: pmiWord1, word2: pmiWord2 }
        });
        setResult(res.data);
      } else if (algo === 'hebbian') {
        const pairs = hebbianPairs.split('\n').filter(l => l.trim());
        const associations = pairs.map(p => {
          const [w1, w2] = p.split(',');
          return { word1: w1?.trim(), word2: w2?.trim() };
        }).filter(a => a.word1 && a.word2);
        const res = await axios.post(`${API_BASE}/algorithmic/hebbian/learn`, { associations, rate: 0.1 });
        setResult(res.data);
      }
    } catch (e) {
      alert('Error: ' + e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  };

  // --- Render helpers ---
  const renderAlgorithmsTab = () => (
    <div className="algo-tabs">
      {['markov', 'tfidf', 'bm25', 'pmi', 'hebbian'].map(tab => (
        <button key={tab} className={`algo-tab ${activeTab === tab ? 'active' : ''}`} onClick={() => setActiveTab(tab)}>
          {tab.toUpperCase()}
        </button>
      ))}
    </div>
  );

  const renderAlgoControls = () => {
    switch (activeTab) {
      case 'markov':
        return (
          <>
            <input type="number" value={markovLength} onChange={e => setMarkovLength(parseInt(e.target.value))} placeholder="Length" />
            <input type="text" value={markovSeed} onChange={e => setMarkovSeed(e.target.value)} placeholder="Seed words" />
          </>
        );
      case 'tfidf':
        return <textarea value={tfidfText} onChange={e => setTfidfText(e.target.value)} placeholder="Text to analyze" rows={3} />;
      case 'bm25':
        return <input type="text" value={bm25Query} onChange={e => setBm25Query(e.target.value)} placeholder="Search query" />;
      case 'pmi':
        return (
          <div className="pmi-inputs">
            <input value={pmiWord1} onChange={e => setPmiWord1(e.target.value)} placeholder="Word 1" />
            <span>vs</span>
            <input value={pmiWord2} onChange={e => setPmiWord2(e.target.value)} placeholder="Word 2" />
          </div>
        );
      case 'hebbian':
        return <textarea value={hebbianPairs} onChange={e => setHebbianPairs(e.target.value)} placeholder="word1,word2&#10;consciousness,quantum" rows={4} />;
      default:
        return null;
    }
  };

  const renderResearchTab = () => (
    <div className="research-controls">
      <h4>Autonomous Research</h4>
      <div className="control-row">
        <label>Duration (minutes):</label>
        <input type="number" min="5" max="180" value={researchDuration} onChange={e => setResearchDuration(parseInt(e.target.value))} />
        <button className="btn-primary" onClick={launchResearch} disabled={loading || researchStatus?.is_running}>
          {loading ? 'Launching...' : 'Start Research'}
        </button>
        <button className="btn-secondary" onClick={refreshResearchStatus} disabled={refreshingResearch}>
          Refresh
        </button>
      </div>

      {researchStatus && (
        <div className="research-status">
          <p><strong>Status:</strong> {researchStatus.is_running ? '🔄 Running' : '⚪ Idle'}</p>
          <p><strong>Duration:</strong> {researchStatus.duration_minutes} min</p>
          {researchStatus.is_running && (
            <p><strong>Current:</strong> {researchStatus.progress?.status || 'Initializing...'}</p>
          )}
          <p><strong>Total Researches:</strong> {researchStatus.total_researches}</p>
        </div>
      )}

      {researchHistory.length > 0 && (
        <div className="research-history">
          <h5>Recent Sessions</h5>
          <ul>
            {researchHistory.map((h, i) => (
              <li key={i}>
                <span className="topic">{h.topic}</span>
                <span className="time">{new Date(h.timestamp).toLocaleString()}</span>
                <span className="concepts">{h.concepts?.length || 0} concepts</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );

  const renderCloudTab = () => (
    <div className="cloud-controls">
      <h4>Wolfram Cloud Storage</h4>
      <div className="control-row">
        <button className="btn-primary" onClick={saveToCloud} disabled={loading}>
          Save to Cloud
        </button>
        <button className="btn-secondary" onClick={loadPreview} disabled={refreshingCloud}>
          Load Preview
        </button>
        <button className="btn-secondary" onClick={restoreFromCloud} disabled={loading || !cloudPreview}>
          Restore
        </button>
      </div>
      {cloudMessage && <p className="msg">{cloudMessage}</p>}
      {cloudStatus && (
        <pre style={{ fontSize: '0.8rem', color: '#888' }}>
          Cloud objects: {JSON.stringify(cloudStatus, null, 2)}
        </pre>
      )}
      {cloudPreview && (
        <div className="cloud-preview">
          <h5>Preview ({cloudPreview.concepts ? Object.keys(cloudPreview.concepts).length : 0} concepts)</h5>
          <pre>{JSON.stringify(cloudPreview, null, 2)}</pre>
        </div>
      )}
    </div>
  );

  return (
    <div className="panel-learn">
      <h3>🎓 Learn & Research</h3>

      {/* Tabs */}
      <div className="tabs">
        {['algorithms', 'research', 'cloud'].map(tab => (
          <button key={tab} className={`tab ${activeTab === tab ? 'active' : ''}`} onClick={() => setActiveTab(tab)}>
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'algorithms' && (
        <>
          {renderAlgorithmsTab()}
          <div className="algo-controls">{renderAlgoControls()}</div>
          <button className="btn-primary" onClick={() => runAlgorithm(activeTab)} disabled={loading}>
            {loading ? 'Processing...' : `Run ${activeTab}`}
          </button>
        </>
      )}

      {activeTab === 'research' && renderResearchTab()}
      {activeTab === 'cloud' && renderCloudTab()}

      {result && activeTab === 'algorithms' && (
        <div className="algo-result">
          <h4>Result:</h4>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default LearnPanel;
