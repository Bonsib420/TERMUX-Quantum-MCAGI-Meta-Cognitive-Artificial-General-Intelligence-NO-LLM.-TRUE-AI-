import React, { useState, useEffect } from 'react';
import * as API from '../api';

function SettingsPanel() {
  const [stats, setStats] = useState(null);
  const [growth, setGrowth] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadStats = async () => {
    setLoading(true);
    try {
      const res = await API.getSettingsStatistics(); // we need to add this to api.js
      setStats(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadGrowth = async () => {
    try {
      const res = await API.getGrowthStats();
      setGrowth(res);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadStats();
    loadGrowth();
  }, []);

  return (
    <div className="panel-settings">
      <h3>⚙️ Settings & Statistics</h3>
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        <button className="btn-secondary" onClick={loadStats} disabled={loading}>Refresh Stats</button>
        <button className="btn-secondary" onClick={loadGrowth} disabled={loading}>Refresh Growth</button>
      </div>

      {loading && <p>Loading...</p>}

      {stats && (
        <div className="stats-grid">
          <div className="stat-item">
            <span className="stat-label">Conversations</span>
            <span className="stat-value">{stats.total_conversations}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Messages</span>
            <span className="stat-value">{stats.total_messages}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Users</span>
            <span className="stat-value">{stats.users}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Growth Events</span>
            <span className="stat-value">{stats.growth_events || 'N/A'}</span>
          </div>
        </div>
      )}

      {growth && (
        <div className="growth-section" style={{ marginTop: '1.5rem' }}>
          <h4>Growth Status</h4>
          <p><strong>Stage:</strong> {growth.stage?.name} (Level {growth.stage?.stage})</p>
          <p><strong>Concepts:</strong> {growth.metrics?.total_concepts} | <strong>Connections:</strong> {growth.metrics?.total_connections}</p>
          {growth.stage?.progress_to_next && (
            <div>
              <p>Progress to {growth.stage.next_stage}:</p>
              <ul style={{ paddingLeft: '1.2rem' }}>
                <li>Connections: {growth.stage.progress_to_next.connections}%</li>
                <li>Concepts: {growth.stage.progress_to_next.concepts}%</li>
                <li>Avg Degree: {growth.stage.progress_to_next.avg_degree}%</li>
                <li>Diameter: {growth.stage.progress_to_next.diameter}%</li>
              </ul>
            </div>
          )}
          {growth.stage?.limiting_factor && (
            <p style={{ color: 'var(--warning)' }}>Limiting factor: {growth.stage.limiting_factor}</p>
          )}
        </div>
      )}

      <div className="settings-section">
        <h4>Appearance</h4>
        <p>Theme: Dark Neon (fixed)</p>
      </div>
    </div>
  );
}

export default SettingsPanel;
