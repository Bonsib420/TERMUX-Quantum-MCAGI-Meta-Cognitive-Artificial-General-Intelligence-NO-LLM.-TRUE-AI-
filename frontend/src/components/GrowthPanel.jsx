import React, { useState, useEffect } from 'react';
import * as API from '../api';

function ProgressBar({ label, value, color = 'var(--accent)' }) {
  return (
    <div className="progress-item">
      <div className="progress-header">
        <span className="progress-label">{label}</span>
        <span className="progress-value">{value}%</span>
      </div>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${value}%`, backgroundColor: color }}></div>
      </div>
    </div>
  );
}

function GrowthPanel() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadGrowth = async () => {
    setLoading(true);
    try {
      const res = await API.getGrowthStats();
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadGrowth(); }, []);

  const formatNumber = (num) => new Intl.NumberFormat().format(num);

  const topology = data?.stage?.metrics?.topology || {};
  const progress = data?.stage?.progress_to_next || {};
  const metrics = data?.metrics || {};
  const stage = data?.stage || {};

  return (
    <div className="panel-growth">
      <h3>📈 Growth & Evolution</h3>
      <button className="btn-secondary" onClick={loadGrowth} disabled={loading}>Refresh</button>
      {loading && <p>Loading...</p>}

      {data && (
        <div className="growth-info">

          {/* Current Stage */}
          <div className="growth-section">
            <div className="growth-stage">
              <span className="label">Current Stage:</span>
              <span className="value neon-text">{stage.name}</span>
              <span className="stage-level"> (Level {stage.stage})</span>
            </div>
            {stage.next_stage && (
              <p className="next-stage">Next: {stage.next_stage}</p>
            )}
            {stage.limiting_factor && (
              <p className="limiting-factor" style={{ color: 'var(--warning)' }}>
                ⚠️ Limiting: {stage.limiting_factor}
              </p>
            )}
          </div>

          {/* Core Metrics */}
          <div className="growth-section">
            <h4>Knowledge Graph</h4>
            <div className="metrics-grid">
              <div className="metric-item">
                <span className="metric-label">Concepts</span>
                <span className="metric-value">{formatNumber(metrics.total_concepts)}</span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Connections</span>
                <span className="metric-value">{formatNumber(metrics.total_connections)}</span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Avg Degree</span>
                <span className="metric-value">{topology.avg_degree || 0}</span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Diameter</span>
                <span className="metric-value">{topology.diameter || 0}</span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Components</span>
                <span className="metric-value">{topology.component_count || 0}</span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Domains</span>
                <span className="metric-value">{metrics.distinct_domains || 0}</span>
              </div>
            </div>
          </div>

          {/* Progress to Next Stage */}
          {stage.next_stage && progress && (
            <div className="growth-section">
              <h4>Progress to {stage.next_stage}</h4>
              <ProgressBar label="Connections" value={progress.connections} color="var(--quantum)" />
              <ProgressBar label="Concepts" value={progress.concepts} color="var(--accent)" />
              <ProgressBar label="Avg Degree" value={progress.avg_degree} color="#ec4899" />
              <ProgressBar label="Diameter" value={progress.diameter} color="#f59e0b" />
              <ProgressBar label="Domains" value={progress.domains} color="#10b981" />
            </div>
          )}

          {/* Thresholds Reference */}
          <div className="growth-section">
            <h4>Stage Thresholds</h4>
            <div className="thresholds-table">
              <table>
                <thead>
                  <tr>
                    <th>Stage</th>
                    <th>Conns</th>
                    <th>Concepts</th>
                    <th>Avg°</th>
                    <th>Diam</th>
                    <th>Domains</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { n: 'Nascent', c: 0, cp: 0, ad: 1, d: 0, dm: 0 },
                    { n: 'Curious', c: 15, cp: 12, ad: 1.5, d: 2, dm: 3 },
                    { n: 'Inquisitive', c: 45, cp: 25, ad: 2.5, d: 4, dm: 6 },
                    { n: 'Understanding', c: 135, cp: 50, ad: 3.5, d: 6, dm: 10 },
                    { n: 'Philosophical', c: 405, cp: 100, ad: 5, d: 8, dm: 15 },
                    { n: 'Theory Building', c: 1215, cp: 200, ad: 7, d: 12, dm: 20 },
                    { n: 'Transcendent', c: 3645, cp: 400, ad: 10, d: 16, dm: 30 },
                  ].map((s) => (
                    <tr key={s.n} className={stage.name === s.n ? 'current-stage' : ''}>
                      <td>{s.n}</td>
                      <td>{formatNumber(s.c)}</td>
                      <td>{formatNumber(s.cp)}</td>
                      <td>{s.ad}</td>
                      <td>{s.d}</td>
                      <td>{s.dm}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Recent Events */}
          <div className="growth-section">
            <h4>Recent Events</h4>
            {data.recent_events?.length > 0 ? (
              <ul className="events-list">
                {data.recent_events.map((ev, i) => (
                  <li key={i}>
                    <span className="event-type">{ev.event_type}</span>
                    <span className="event-time">{new Date(ev.timestamp).toLocaleString()}</span>
                    {ev.details && (
                      <span className="event-details">
                        {Object.entries(ev.details)
                          .filter(([k]) => k !== 'timestamp')
                          .map(([k, v]) => (
                            <span key={k} className="detail">{k}: {JSON.stringify(v)}</span>
                          ))
                        }
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="no-events">No stage advancements yet. Keep building your knowledge graph!</p>
            )}
          </div>

        </div>
      )}
    </div>
  );
}

export default GrowthPanel;
