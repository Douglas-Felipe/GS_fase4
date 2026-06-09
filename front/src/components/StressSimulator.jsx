import { useState } from 'react';
import { sendSimulation, sendCommand } from '../services/api';
import './StressSimulator.css';

const PRESETS = [
  { label: '🌑 Noite Total',            values: { solar_generation: 0,  battery_level: null, lunar_hour: 360 } },
  { label: '🌪️ Tempestade de Poeira', values: { solar_generation: 10, battery_level: 40,   lunar_hour: null } },
  { label: '🚨 Emergência Crítica',     values: { solar_generation: 0,  battery_level: 15,   lunar_hour: 400 } },
];

const RISK_COLORS = {
  low: 'badge-green',
  medium: 'badge-amber',
  high: 'badge-red',
  critical: 'badge-red',
};

const ACTION_ICONS = {
  off: '🔴',
  on: '🟢',
};

const SECTOR_NAMES = {
  1: 'Suporte à Vida',
  2: 'Comunicações',
  3: 'Laboratório',
  4: 'Rovers / Mineração',
};

export default function StressSimulator({ onRefetch }) {
  const [solar, setSolar] = useState(70);
  const [battery, setBattery] = useState(80);
  const [lunarHour, setLunarHour] = useState(180);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function applyPreset(preset) {
    if (preset.solar_generation !== null) setSolar(preset.solar_generation);
    if (preset.battery_level !== null) setBattery(preset.battery_level);
    if (preset.lunar_hour !== null) setLunarHour(preset.lunar_hour);
  }

  async function simulate() {
    setLoading(true);
    setError(null);

    try {
      const data = await sendSimulation({
        solar_generation: solar,
        battery_level: battery,
        lunar_hour: lunarHour,
      });
      setResult(data);

      // Forçar atualização do status global da base e dos setores
      if (onRefetch) {
        onRefetch();
      }
    } catch (err) {
      setError(err.message || 'Falha na simulação');
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="stress-simulator animate-slide-up" style={{ animationDelay: '0.3s' }}>
      <div className="sim-card glass-card">
        <h2 className="section-title">🧪 Simulador de Estresse</h2>
        <p className="sim-description">
          Simule cenários extremos e observe as decisões de gerenciamento energético da IA.
        </p>

        {/* Sliders */}
        <div className="sim-sliders">
          <SliderControl
            label="Geração Solar"
            icon="☀️"
            value={solar}
            onChange={setSolar}
            min={0}
            max={100}
            unit="%"
            gradientClass="slider-solar"
          />
          <SliderControl
            label="Nível da Bateria"
            icon="🔋"
            value={battery}
            onChange={setBattery}
            min={0}
            max={100}
            unit="%"
            gradientClass="slider-battery"
          />
          <SliderControl
            label="Hora Lunar"
            icon="🌙"
            value={lunarHour}
            onChange={setLunarHour}
            min={0}
            max={720}
            unit="h"
            gradientClass="slider-lunar"
          />
        </div>

        {/* Presets */}
        <div className="sim-presets">
          {PRESETS.map((p) => (
            <button
              key={p.label}
              className="btn btn-ghost btn-sm"
              onClick={() => applyPreset(p.values)}
            >
              {p.label}
            </button>
          ))}
        </div>

        {/* Simulate Button */}
        <button className="btn btn-primary sim-run-btn" onClick={simulate} disabled={loading}>
          {loading ? (
            <>
              <span className="spinner" /> Executando Simulação…
            </>
          ) : (
            '⚡ Simular Cenário'
          )}
        </button>

        {/* Error */}
        {error && (
          <div className="sim-error">
            <span>⚠️</span> {error}
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="sim-results animate-fade-in">
            <div className="sim-results-header">
              <h3>Análise da IA</h3>
              <span className={`badge ${RISK_COLORS[result.risk_level] || 'badge-purple'}`}>
                🎯 {(result.risk_level || 'unknown').toUpperCase()}
              </span>
            </div>

            {result.predicted_autonomy_hours != null && (
              <div className="sim-autonomy">
                <span className="sim-autonomy-label">Autonomia Prevista</span>
                <span className="sim-autonomy-value font-mono text-cyan">
                  {result.predicted_autonomy_hours} h
                </span>
              </div>
            )}

            {result.message && (
              <div className="sim-message">
                <span className="sim-message-icon">🤖</span>
                <p>{result.message}</p>
              </div>
            )}

            {result.sector_commands?.length > 0 && (
              <div className="sim-actions">
                <h4 className="sim-actions-title">Ações nos Setores</h4>
                <ul className="sim-actions-list">
                  {result.sector_commands.map((cmd, i) => (
                    <li key={i} className="sim-action-item">
                      <span>{ACTION_ICONS[cmd.action] || '⚙️'}</span>
                      <span className="sim-action-sector">{SECTOR_NAMES[cmd.sector_id] || `Setor ${cmd.sector_id}`}</span>
                      <span className={`sim-action-type ${cmd.action === 'off' ? 'text-red' : 'text-green'}`}>{cmd.action.toUpperCase()}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

/* ----- Slider Sub-Component ----- */
function SliderControl({ label, icon, value, onChange, min, max, unit, gradientClass }) {
  const pct = ((value - min) / (max - min)) * 100;

  return (
    <div className="slider-group">
      <div className="slider-header">
        <span className="slider-label">
          {icon} {label}
        </span>
        <span className="slider-value font-mono">
          {value}{unit}
        </span>
      </div>
      <div className="slider-track-wrapper">
        <input
          type="range"
          min={min}
          max={max}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className={gradientClass}
          style={{
            background: `linear-gradient(to right, var(--slider-start) 0%, var(--slider-end) ${pct}%, rgba(148,163,184,0.12) ${pct}%)`,
          }}
        />
      </div>
    </div>
  );
}
