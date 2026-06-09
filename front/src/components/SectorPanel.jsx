import { useState } from 'react';
import { sendCommand } from '../services/api';
import './SectorPanel.css';

const SECTOR_META = {
  1: { icon: '🫁', label: 'Suporte à Vida',         priority: 'crítica' },
  2: { icon: '📡', label: 'Comunicações com a Terra', priority: 'alta' },
  3: { icon: '🔬', label: 'Laboratório de Pesquisa', priority: 'média' },
  4: { icon: '🔋', label: 'Rovers / Mineração',     priority: 'baixa' },
};

const PRIORITY_BADGE = {
  'crítica': 'badge-red',
  'alta':    'badge-amber',
  'média':   'badge-cyan',
  'baixa':   'badge-purple',
};

function getStatus(sector) {
  if (sector.status) return sector.status;
  if (sector.active === true || sector.active === 1) return 'active';
  return 'off';
}

function statusColor(st) {
  if (st === 'active') return 'green';
  if (st === 'ai_shutoff') return 'red';
  if (st === 'manual_shutoff') return 'amber';
  return 'red';
}

function statusLabel(st) {
  if (st === 'active') return 'Ativo';
  if (st === 'off') return 'Desligado';
  if (st === 'ai_shutoff') return 'Desligado pela IA';
  if (st === 'manual_shutoff') return 'Desligado Manual';
  return st || 'Desconhecido';
}

export default function SectorPanel({ status, onRefetch }) {
  const [loading, setLoading] = useState({});
  const [cmdError, setCmdError] = useState(null);

  // Fallback padrão caso a API não tenha dados ainda
  const defaultSectors = [
    { id: 1, name: 'Suporte de Vida',    priority: 1, active: true,  consumption: 30.0 },
    { id: 2, name: 'Comunicações',        priority: 2, active: true,  consumption: 20.0 },
    { id: 3, name: 'Laboratório',          priority: 3, active: true,  consumption: 25.0 },
    { id: 4, name: 'Recarga Rovers',       priority: 4, active: true,  consumption: 25.0 },
  ];

  const sectors = status?.sectors || defaultSectors;

  async function handleToggle(sectorId, currentStatus) {
    const action = currentStatus === 'active' ? 'off' : 'on';
    setLoading((prev) => ({ ...prev, [sectorId]: true }));
    setCmdError(null);

    try {
      await sendCommand(sectorId, action);
      // Forçar atualização do status após comando
      if (onRefetch) setTimeout(() => onRefetch(), 300);
    } catch (err) {
      setCmdError(`Falha ao ${action === 'off' ? 'desligar' : 'ligar'} setor ${sectorId}: ${err.message}`);
    } finally {
      setLoading((prev) => ({ ...prev, [sectorId]: false }));
    }
  }

  return (
    <section className="sector-panel animate-slide-up" style={{ animationDelay: '0.2s' }}>
      <h2 className="section-title">🏗️ Controle de Setores</h2>

      {cmdError && (
        <div className="sector-error">
          <span>⚠️</span> {cmdError}
        </div>
      )}

      <div className="sector-grid">
        {sectors.map((sector, i) => {
          const meta = SECTOR_META[sector.id] || { icon: '❓', label: sector.name || `Setor ${sector.id}`, priority: 'baixa' };
          const sectorStatus = getStatus(sector);
          const color = statusColor(sectorStatus);
          const isActive = sectorStatus === 'active';
          const isLoading = loading[sector.id];

          return (
            <div
              key={sector.id}
              className={`sector-card glass-card ${isActive ? '' : 'sector-inactive'}`}
              style={{ animationDelay: `${0.3 + i * 0.08}s` }}
            >
              <div className="sector-top">
                <div className="sector-info">
                  <span className="sector-icon">{meta.icon}</span>
                  <div>
                    <h4 className="sector-name">{meta.label}</h4>
                    <span className={`badge ${PRIORITY_BADGE[meta.priority]}`}>
                      {meta.priority}
                    </span>
                  </div>
                </div>
                <div className={`sector-status-circle ${color} ${isActive ? 'animate-pulse' : ''}`} />
              </div>

              <div className="sector-body">
                <div className="sector-stat">
                  <span className="sector-stat-label">Status</span>
                  <span className={`sector-stat-value text-${color}`}>
                    {statusLabel(sectorStatus)}
                  </span>
                </div>
                <div className="sector-stat">
                  <span className="sector-stat-label">Consumo</span>
                  <span className="sector-stat-value font-mono">
                    {sector.consumption ?? '—'} W
                  </span>
                </div>
              </div>

              <button
                className={`btn btn-sm ${isActive ? 'btn-danger' : 'btn-primary'} sector-toggle`}
                onClick={() => handleToggle(sector.id, sectorStatus)}
                disabled={isLoading}
              >
                {isLoading ? '⏳' : isActive ? '⏻ Desligar' : '▶ Ligar'}
              </button>
            </div>
          );
        })}
      </div>
    </section>
  );
}
