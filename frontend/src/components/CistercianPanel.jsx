import React, { useState } from 'react';
import axios from 'axios';

const API_BASE = '/api';

function CistercianPanel() {
  const [number, setNumber] = useState(2024);
  const [size, setSize] = useState(120);
  const [color, setColor] = useState('#00ff88');
  const [svg, setSvg] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchNumeral = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/cistercian/download`, {
        params: { number, size, color },
        responseType: 'text'
      });
      setSvg(res.data);
    } catch (e) {
      alert('Failed to load numeral: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadSVG = () => {
    if (!svg) return;
    const blob = new Blob([svg], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cistercian_${number.toString().padStart(4, '0')}.svg`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="panel-cistercian">
      <h3>🔢 Cistercian Numerals</h3>
      <div className="control-group">
        <label>
          Number (0-9999):
          <input type="number" min="0" max="9999" value={number} onChange={e => setNumber(parseInt(e.target.value) || 0)} />
        </label>
      </div>
      <div className="control-group">
        <label>
          Size: {size}px
          <input type="range" min="40" max="300" value={size} onChange={e => setSize(parseInt(e.target.value))} />
        </label>
      </div>
      <div className="control-group">
        <label>
          Color:
          <input type="color" value={color} onChange={e => setColor(e.target.value)} />
        </label>
      </div>
      <div className="button-row">
        <button className="btn-primary" onClick={fetchNumeral} disabled={loading}>Generate</button>
        {svg && <button className="btn-secondary" onClick={downloadSVG}>Download SVG</button>}
      </div>
      {svg && (
        <div className="numeral-preview" dangerouslySetInnerHTML={{ __html: svg }} />
      )}
    </div>
  );
}

export default CistercianPanel;
