import { useState, useEffect, useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { fetchTelemetryHistory } from '../services/api';
import './Dashboard.css';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

const FALLBACK_STATUS = {
  solar_generation: 72,
  battery_level: 85,
  consumption: 3400,
  lunar_hour: 180,
};

export default function Dashboard({ status }) {
  const [history, setHistory] = useState([]);
  const [historyError, setHistoryError] = useState(false);

  const telemetry = status || FALLBACK_STATUS;

  // Fetch history for chart
  useEffect(() => {
    let cancelled = false;

    async function loadHistory() {
      try {
        const data = await fetchTelemetryHistory();
        if (!cancelled) {
          // A API retorna { data: [...], count: N }
          const records = Array.isArray(data) ? data : data?.data || [];
          setHistory(records);
          setHistoryError(false);
        }
      } catch {
        if (!cancelled) setHistoryError(true);
      }
    }

    loadHistory();
    const iv = setInterval(loadHistory, 15000);
    return () => { cancelled = true; clearInterval(iv); };
  }, []);

  // Metric cards
  const metrics = [
    {
      id: 'solar',
      icon: '☀️',
      label: 'Geração Solar',
      value: `${telemetry.solar_generation ?? 0}%`,
      accent: 'cyan',
      detail: telemetry.solar_generation >= 50 ? 'Normal' : 'Baixa geração',
    },
    {
      id: 'battery',
      icon: '🔋',
      label: 'Nível da Bateria',
      value: `${telemetry.battery_level ?? 0}%`,
      accent: (telemetry.battery_level ?? 0) > 60 ? 'green' : (telemetry.battery_level ?? 0) > 25 ? 'amber' : 'red',
      detail: (telemetry.battery_level ?? 0) > 60 ? 'Saudável' : (telemetry.battery_level ?? 0) > 25 ? 'Atenção' : 'Crítico',
    },
    {
      id: 'consumption',
      icon: '⚡',
      label: 'Consumo da Base',
      value: `${telemetry.base_consumption ?? 0} W`,
      accent: 'purple',
      detail: 'Consumo total',
    },
    {
      id: 'lunar',
      icon: '🌙',
      label: 'Hora Lunar',
      value: `${telemetry.lunar_hour ?? 0} h`,
      accent: (telemetry.lunar_hour ?? 0) <= 354 ? 'cyan' : 'purple',
      detail: (telemetry.lunar_hour ?? 0) <= 354 ? 'Fase Diurna' : 'Fase Noturna',
    },
  ];

  // Chart data
  const chartData = useMemo(() => {
    if (!history.length) return null;

    const labels = history.map((_, i) => `T-${history.length - i}`);

    return {
      labels,
      datasets: [
        {
          label: 'Geração Solar (%)',
          data: history.map((h) => h.solar_generation),
          borderColor: '#00d4ff',
          backgroundColor: 'rgba(0, 212, 255, 0.08)',
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 5,
          pointHoverBackgroundColor: '#00d4ff',
          borderWidth: 2,
        },
        {
          label: 'Nível Bateria (%)',
          data: history.map((h) => h.battery_level),
          borderColor: '#7c3aed',
          backgroundColor: 'rgba(124, 58, 237, 0.08)',
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 5,
          pointHoverBackgroundColor: '#7c3aed',
          borderWidth: 2,
        },
        {
          label: 'Consumo (W)',
          data: history.map((h) => h.base_consumption),
          borderColor: '#f59e0b',
          backgroundColor: 'rgba(245, 158, 11, 0.05)',
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 5,
          pointHoverBackgroundColor: '#f59e0b',
          borderWidth: 2,
          yAxisID: 'y1',
        },
      ],
    };
  }, [history]);

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: '#94a3b8',
          font: { family: "'Inter', sans-serif", size: 11 },
          usePointStyle: true,
          pointStyleWidth: 8,
          padding: 20,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        titleColor: '#e2e8f0',
        bodyColor: '#94a3b8',
        borderColor: 'rgba(148, 163, 184, 0.15)',
        borderWidth: 1,
        cornerRadius: 8,
        padding: 12,
        titleFont: { family: "'Inter', sans-serif", weight: '600' },
        bodyFont: { family: "'Inter', sans-serif" },
      },
    },
    scales: {
      x: {
        ticks: { color: '#64748b', font: { size: 10 } },
        grid: { color: 'rgba(148, 163, 184, 0.05)' },
        border: { color: 'transparent' },
      },
      y: {
        position: 'left',
        min: 0,
        max: 100,
        ticks: { color: '#64748b', font: { size: 10 }, stepSize: 25 },
        grid: { color: 'rgba(148, 163, 184, 0.06)' },
        border: { color: 'transparent' },
      },
      y1: {
        position: 'right',
        min: 0,
        ticks: { color: '#64748b', font: { size: 10 } },
        grid: { drawOnChartArea: false },
        border: { color: 'transparent' },
      },
    },
  };

  return (
    <section className="dashboard animate-slide-up">
      {/* Metric Cards */}
      <div className="metrics-grid">
        {metrics.map((m, i) => (
          <div
            key={m.id}
            className={`metric-card glass-card accent-${m.accent}`}
            style={{ animationDelay: `${i * 0.1}s` }}
          >
            <div className="metric-icon">{m.icon}</div>
            <div className="metric-body">
              <span className="metric-label">{m.label}</span>
              <span className={`metric-value text-${m.accent}`}>{m.value}</span>
              <span className="metric-detail">{m.detail}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Chart */}
      <div className="chart-card glass-card">
        <div className="chart-header">
          <h3 className="chart-title">📈 Histórico de Telemetria</h3>
          {historyError && (
            <span className="badge badge-amber">⚠ Sem dados ao vivo</span>
          )}
        </div>
        <div className="chart-container">
          {chartData ? (
            <Line data={chartData} options={chartOptions} />
          ) : (
            <div className="chart-placeholder">
              <div className="chart-placeholder-icon">📊</div>
              <p>Aguardando dados de telemetria…</p>
              <p className="text-muted" style={{ fontSize: '0.75rem' }}>
                O gráfico será preenchido quando a API enviar registros históricos
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
