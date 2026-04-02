import React, { useState, useEffect } from 'react';
import * as API from '../api';

function EvolutionPanel() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [triggering, setTriggering] = useState(false);
  const [result, setResult] = useState(null);

  const loadEvolution = async () => {
    setLoading(true);
    try {
      const res = await API.getGrowthEvolution();
      setStatus(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const triggerEvolution = async () => {
    if (!window.confirm('Trigger self-evolution now? This will rewrite code files based on identified improvements.')) return;
    setTriggering(true);
    setResult(null);
    try {
      const res = await API.triggerEvolution();
      setResult(res);
      // Refresh status after a moment
      setTimeout(loadEvolution, 2000);
    } catch (e) {
      alert('Evolution failed: ' + (e.response?.data?.detail || e.message));
    } finally {
      setTriggering(false);
    }
  };

  useEffect(() => { loadEvolution(); }, []);

  return (
    <div>
      <h3>🧬 Self-Evolution</h3>
      {loading ? <p>Loading...</p> : status && (
        <div>
          <p><strong>Growth Stage:</strong> {status.current_stage} (Level {status.current_level})</p>
          {status.connections !== undefined && (
            <p>
              <strong>Connections:</strong> {status.connections.toLocaleString()} |
              <strong> Concepts:</strong> {status.concepts.toLocaleString()}
              {status.avg_degree && <span> | <strong>Avg Degree:</strong> {status.avg_degree.toFixed(2)}</span>}
              {status.diameter && <span> | <strong>Diameter:</strong> {status.diameter}</span>}
            </p>
          )}
          <p><strong>Last Updated:</strong> {status.last_updated ? new Date(status.last_updated).toLocaleString() : 'Never'}</p>
          
          <button 
            className="btn-primary" 
            onClick={triggerEvolution} 
            disabled={triggering || status.pending_improvements === 0}
            style={{ marginTop: '0.5rem', marginBottom: '1rem' }}
          >
            {triggering ? 'Evolving...' : 'Implement All Rewrites'}
          </button>
          
          {result && (
            <div style={{ background: '#1a1a1a', padding: '0.75rem', borderRadius: '8px', marginTop: '0.5rem' }}>
              <h4>Evolution Result</h4>
              <p>Changes made: {result.changes_made?.length || 0}</p>
              <p>Skipped: {result.skipped?.length || 0}</p>
              <p>Errors: {result.errors?.length || 0}</p>
              {result.changes_made && result.changes_made.length > 0 && (
                <ul>
                  {result.changes_made.map((c, i) => (
                    <li key={i}>{c.file}: {c.change}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
          
          <h4>Recent Growth Events</h4>
          <ul>
            {status.recent_events?.map((ev, i) => (
              <li key={i}>
                <strong>{ev.event_type}</strong> - {new Date(ev.timestamp).toLocaleString()}
                {ev.details && (
                  <span style={{ color: '#888', fontSize: '0.9em' }}>
                    {' '}{ev.details.new_stage || ''} {ev.details.connections ? `(connections: ${ev.details.connections})` : ''}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default EvolutionPanel;
