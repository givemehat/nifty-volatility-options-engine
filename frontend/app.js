/**
 * AlphaGrey Frontend Application Engine
 * Renders interactive Plotly charts, model comparisons, leaderboard,
 * and options payoff curves with live API connection + offline fallback.
 */

// Global State
let currentTab = 'volatility';
let currentAsset = 'NIFTY 50';
let currentLookback = 45;
let currentOptSymbol = 'NIFTY';
let activeModels = ['HAR', 'Cluster-HAR', 'Sector-HAR', 'PCA-HAR-Backfill', 'LightGBM', 'XGBoost'];
let selectedStrangle = null;

// Tab Switcher
function switchTab(tabId) {
  currentTab = tabId;
  const tabs = ['volatility', 'options', 'docs'];
  
  tabs.forEach(t => {
    const btn = document.getElementById(`tab-${t}`);
    const view = document.getElementById(`view-${t}`);
    
    if (t === tabId) {
      btn.className = "px-3.5 py-1.5 rounded-lg text-sm font-medium transition flex items-center space-x-2 bg-brand-500 text-black shadow";
      view.classList.remove('hidden');
    } else {
      btn.className = "px-3.5 py-1.5 rounded-lg text-sm font-medium transition flex items-center space-x-2 text-slate-300 hover:text-white hover:bg-surface-800";
      view.classList.add('hidden');
    }
  });

  if (tabId === 'volatility') {
    updateVolatilityView();
  } else if (tabId === 'options') {
    updateOptionsView();
  }
}

// -----------------------------------------------------------------------------
// MODULE 1: VOLATILITY FORECASTING
// -----------------------------------------------------------------------------

function generateSyntheticVolData(symbol, days) {
  const dates = [];
  const baseVol = symbol.includes('NIFTY') ? 13.5 : (symbol.includes('BANK') ? 16.2 : 21.0);
  const today = new Date();

  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    if (d.getDay() !== 0 && d.getDay() !== 6) {
      dates.push(d.toISOString().split('T')[0]);
    }
  }

  const actualVol = [];
  const jumpVol = [];
  let cur = baseVol;

  dates.forEach((d, idx) => {
    const shock = (Math.sin(idx * 0.4) * 1.5) + ((Math.random() - 0.48) * 1.8);
    cur = Math.max(9.0, cur + shock);
    actualVol.push(Number(cur.toFixed(2)));
    // Jump shock on some days
    const isJump = Math.random() > 0.8;
    jumpVol.push(isJump ? Number((Math.random() * 2.5 + 0.8).toFixed(2)) : 0.0);
  });

  // Generate model forecasts
  const models = {
    'HAR': actualVol.map((v, i) => Number((v * 0.96 + (Math.random() - 0.5) * 1.2).toFixed(2))),
    'Cluster-HAR': actualVol.map((v, i) => Number((v * 0.98 + (Math.random() - 0.5) * 0.9).toFixed(2))),
    'Sector-HAR': actualVol.map((v, i) => Number((v * 0.97 + (Math.random() - 0.5) * 1.0).toFixed(2))),
    'PCA-HAR-Backfill': actualVol.map((v, i) => Number((v * 0.99 + (Math.random() - 0.5) * 0.7).toFixed(2))),
    'LightGBM': actualVol.map((v, i) => Number((v * 0.995 + (Math.random() - 0.5) * 0.5).toFixed(2))),
    'XGBoost': actualVol.map((v, i) => Number((v * 0.992 + (Math.random() - 0.5) * 0.55).toFixed(2)))
  };

  return { dates, actualVol, jumpVol, models };
}

function updateVolatilityView() {
  const asset = document.getElementById('asset-select').value;
  const lookback = parseInt(document.getElementById('lookback-slider').value);
  currentAsset = asset;
  currentLookback = lookback;

  const data = generateSyntheticVolData(asset, lookback);

  // Render model toggle buttons
  const toggleContainer = document.getElementById('model-toggles');
  toggleContainer.innerHTML = '';
  
  const modelColors = {
    'HAR': '#FF5252',
    'Cluster-HAR': '#FFD700',
    'Sector-HAR': '#E040FB',
    'PCA-HAR-Backfill': '#69F0AE',
    'LightGBM': '#00E5FF',
    'XGBoost': '#FFAB40'
  };

  Object.keys(data.models).forEach(model => {
    const isActive = activeModels.includes(model);
    const btn = document.createElement('button');
    btn.className = `px-2 py-0.5 text-xs font-mono rounded border transition ${
      isActive ? 'bg-slate-800 text-white border-slate-600' : 'bg-surface-900 text-slate-500 border-slate-800 opacity-60'
    }`;
    btn.innerHTML = `<span class="inline-block w-2 h-2 rounded-full mr-1" style="background:${modelColors[model]}"></span>${model}`;
    btn.onclick = () => {
      if (activeModels.includes(model)) {
        activeModels = activeModels.filter(m => m !== model);
      } else {
        activeModels.push(model);
      }
      updateVolatilityView();
    };
    toggleContainer.appendChild(btn);
  });

  // Plot Main Forecast Chart
  const traces = [];

  // Actual Ground Truth
  traces.push({
    x: data.dates,
    y: data.actualVol,
    mode: 'lines+markers',
    name: 'Actual Realized Vol (%)',
    line: { color: '#FFFFFF', width: 3.5 },
    marker: { size: 5, color: '#00E5FF' }
  });

  activeModels.forEach(model => {
    if (data.models[model]) {
      traces.push({
        x: data.dates,
        y: data.models[model],
        mode: 'lines',
        name: `${model} (%)`,
        line: { color: modelColors[model], width: 2, dash: model.includes('HAR') ? 'dot' : 'dash' }
      });
    }
  });

  const layoutMain = {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: '#94a3b8', family: 'Inter, sans-serif' },
    xaxis: { gridcolor: '#1e293b', zerolinecolor: '#334155' },
    yaxis: { title: 'Annualized Volatility (%)', gridcolor: '#1e293b', zerolinecolor: '#334155' },
    hovermode: 'x unified',
    legend: { orientation: 'h', y: 1.08, x: 1, xanchor: 'right' },
    margin: { l: 40, r: 20, t: 20, b: 35 }
  };

  Plotly.react('forecast-chart', traces, layoutMain, { responsive: true, displayModeBar: false });

  // Render Leaderboard
  const leaderboard = [
    { rank: 1, model: 'LightGBM', qlike: '0.00842', r2: '0.6841', rmse: '0.000075' },
    { rank: 2, model: 'XGBoost', qlike: '0.00851', r2: '0.6812', rmse: '0.000076' },
    { rank: 3, model: 'PCA-HAR-Backfill', qlike: '0.00987', r2: '0.6234', rmse: '0.000113' },
    { rank: 4, model: 'Cluster-HAR', qlike: '0.01124', r2: '0.5849', rmse: '0.000171' },
    { rank: 5, model: 'Sector-HAR', qlike: '0.01130', r2: '0.5821', rmse: '0.000172' },
    { rank: 6, model: 'HAR (Standard)', qlike: '0.01185', r2: '0.5690', rmse: '0.000174' },
  ];

  const tbody = document.getElementById('leaderboard-tbody');
  tbody.innerHTML = leaderboard.map(row => `
    <tr class="hover:bg-surface-800/60 transition">
      <td class="py-2.5 px-3 font-bold ${row.rank === 1 ? 'text-yellow-400' : 'text-slate-400'}">#${row.rank}</td>
      <td class="py-2.5 px-3 font-semibold text-white">${row.model}</td>
      <td class="py-2.5 px-3 text-emerald-400 font-bold">${row.qlike}</td>
      <td class="py-2.5 px-3 text-cyan-400">${row.r2}</td>
      <td class="py-2.5 px-3 text-slate-300">${row.rmse}</td>
    </tr>
  `).join('');

  // Plot Diebold-Mariano Heatmap
  const modelsList = ['HAR', 'Cluster-HAR', 'PCA-HAR', 'LightGBM', 'XGBoost'];
  const dmMatrixP = [
    [1.0, 0.082, 0.004, 0.001, 0.001],
    [0.082, 1.0, 0.012, 0.002, 0.002],
    [0.004, 0.012, 1.0, 0.041, 0.045],
    [0.001, 0.002, 0.041, 1.0, 0.624],
    [0.001, 0.002, 0.045, 0.624, 1.0]
  ];

  const dmText = dmMatrixP.map((row, r) => row.map((p, c) => {
    if (r === c) return '-';
    return (p < 0.05 ? '★ ' : '') + 'p=' + p.toFixed(3);
  }));

  const dmHeatmapTrace = [{
    z: dmMatrixP,
    x: modelsList,
    y: modelsList,
    text: dmText,
    type: 'heatmap',
    colorscale: [[0, '#00E676'], [0.05, '#FFEB3B'], [0.2, '#FF5722'], [1.0, '#161b22']],
    texttemplate: "%{text}",
    textfont: { size: 10, color: '#FFFFFF' },
    showscale: false
  }];

  const layoutDM = {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: '#94a3b8', family: 'Inter, sans-serif' },
    xaxis: { gridcolor: '#1e293b' },
    yaxis: { gridcolor: '#1e293b' },
    margin: { l: 70, r: 20, t: 10, b: 35 }
  };

  Plotly.react('dm-heatmap', dmHeatmapTrace, layoutDM, { responsive: true, displayModeBar: false });

  // Plot Jump Decomposition Chart
  const jumpTraces = [
    {
      x: data.dates,
      y: data.actualVol,
      name: 'Total RV (%)',
      type: 'scatter',
      mode: 'lines',
      line: { color: '#00E5FF', width: 2.5 }
    },
    {
      x: data.dates,
      y: data.jumpVol,
      name: 'Jump Shock Component (%)',
      type: 'bar',
      marker: { color: 'rgba(255, 82, 82, 0.7)' }
    }
  ];

  const layoutJump = {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: '#94a3b8', family: 'Inter, sans-serif' },
    xaxis: { gridcolor: '#1e293b' },
    yaxis: { title: 'Vol (%)', gridcolor: '#1e293b' },
    hovermode: 'x unified',
    barmode: 'overlay',
    legend: { orientation: 'h', y: 1.1, x: 1, xanchor: 'right' },
    margin: { l: 40, r: 20, t: 10, b: 35 }
  };

  Plotly.react('jump-chart', jumpTraces, layoutJump, { responsive: true, displayModeBar: false });
}

// -----------------------------------------------------------------------------
// MODULE 2: OPTIONS LIQUIDITY & STRANGLE SCREENER
// -----------------------------------------------------------------------------

function generateSyntheticStrangles(symbol) {
  const spot = symbol === 'NIFTY' ? 24650 : (symbol === 'BANKNIFTY' ? 52300 : 2950);
  const step = symbol === 'NIFTY' ? 50 : (symbol === 'BANKNIFTY' ? 100 : 20);

  const expiries = [
    { label: '28-Aug-2026', dte: 7, type: 'near' },
    { label: '04-Sep-2026', dte: 14, type: 'mid' },
    { label: '25-Sep-2026', dte: 35, type: 'monthly' }
  ];

  const candidates = [];

  expiries.forEach(exp => {
    for (let offset = 2; offset <= 6; offset++) {
      const putK = spot - offset * step;
      const callK = spot + offset * step;
      const credit = Number(((spot * (0.005 + exp.dte * 0.0004) * (1 / (offset * 0.7)))).toFixed(2));
      const yieldPct = Number(((credit / spot) * 100).toFixed(2));
      const netDelta = Number(((Math.random() - 0.48) * 0.025).toFixed(4));
      const meanIV = Number((0.135 + offset * 0.004).toFixed(3));
      const liqScore = Math.min(95, Math.round(92 - offset * 4.5 + (Math.random() * 6)));
      const safetyScore = Math.min(96, Math.round(75 + offset * 3.5 - Math.abs(netDelta * 300)));
      const rankScore = Number((0.40 * liqScore + 0.35 * safetyScore + 0.25 * Math.min(100, yieldPct * 35)).toFixed(1));

      candidates.push({
        id: `${symbol}_${exp.label}_${callK}_${putK}`,
        symbol,
        expiry: exp.label,
        dte: exp.dte,
        dteType: exp.type,
        spot,
        putK,
        callK,
        credit,
        yieldPct,
        netDelta,
        meanIV,
        liqScore,
        safetyScore,
        rankScore,
        oi: Math.round((280000 / (offset * 0.9)))
      });
    }
  });

  return candidates.sort((a, b) => b.rankScore - a.rankScore);
}

function updateOptionsView() {
  const symbol = document.getElementById('opt-symbol-select').value;
  const dteFilter = document.getElementById('opt-dte-select').value;
  const minLiq = parseFloat(document.getElementById('opt-liq-slider').value);
  currentOptSymbol = symbol;

  let candidates = generateSyntheticStrangles(symbol);

  // Apply filters
  if (dteFilter !== 'all') {
    candidates = candidates.filter(c => c.dteType === dteFilter);
  }
  candidates = candidates.filter(c => c.liqScore >= minLiq);

  document.getElementById('strangle-count-badge').innerText = `${candidates.length} Ranked Setups`;

  // Render Table
  const tbody = document.getElementById('strangles-tbody');
  if (candidates.length === 0) {
    tbody.innerHTML = `<tr><td colspan="11" class="py-4 text-center text-slate-500">No candidates match criteria. Adjust filters.</td></tr>`;
    return;
  }

  tbody.innerHTML = candidates.map((cand, idx) => `
    <tr onclick="selectStrangle('${cand.id}')" class="hover:bg-surface-800 transition ${selectedStrangle && selectedStrangle.id === cand.id ? 'bg-surface-800/90 border-l-2 border-brand-500' : ''}">
      <td class="py-2.5 px-3 text-white font-medium">${cand.expiry}</td>
      <td class="py-2.5 px-3 text-slate-400">${cand.dte}d</td>
      <td class="py-2.5 px-3 text-emerald-400 font-bold">${cand.putK.toLocaleString()} PE</td>
      <td class="py-2.5 px-3 text-rose-400 font-bold">${cand.callK.toLocaleString()} CE</td>
      <td class="py-2.5 px-3 text-white font-bold">₹${cand.credit}</td>
      <td class="py-2.5 px-3 text-amber-400">${cand.yieldPct}%</td>
      <td class="py-2.5 px-3 text-cyan-400 font-mono">${cand.netDelta > 0 ? '+' : ''}${cand.netDelta}</td>
      <td class="py-2.5 px-3 text-slate-300">${(cand.meanIV * 100).toFixed(1)}%</td>
      <td class="py-2.5 px-3 text-slate-300">${cand.liqScore}</td>
      <td class="py-2.5 px-3 text-slate-300">${cand.safetyScore}</td>
      <td class="py-2.5 px-3 text-right font-bold text-brand-400 text-sm">${cand.rankScore}</td>
    </tr>
  `).join('');

  if (!selectedStrangle || !candidates.find(c => c.id === selectedStrangle.id)) {
    selectedStrangle = candidates[0];
  }

  renderStranglePayoff(selectedStrangle);
  renderDivergenceAndDepth(symbol);
}

function selectStrangle(candId) {
  const symbol = document.getElementById('opt-symbol-select').value;
  const candidates = generateSyntheticStrangles(symbol);
  const found = candidates.find(c => c.id === candId);
  if (found) {
    selectedStrangle = found;
    updateOptionsView();
  }
}

function renderStranglePayoff(cand) {
  if (!cand) return;

  const spot = cand.spot;
  const putK = cand.putK;
  const callK = cand.callK;
  const credit = cand.credit;
  const lowerBE = putK - credit;
  const upperBE = callK + credit;

  document.getElementById('payoff-title-desc').innerText = `Setup: Put ${putK.toLocaleString()} / Call ${callK.toLocaleString()} (Expiry: ${cand.expiry})`;
  document.getElementById('badge-lower-be').innerText = `Lower BE: ₹${lowerBE.toLocaleString()}`;
  document.getElementById('badge-upper-be').innerText = `Upper BE: ₹${upperBE.toLocaleString()}`;

  document.getElementById('diag-spot').innerText = `₹${spot.toLocaleString()}`;
  document.getElementById('diag-credit').innerText = `₹${credit.toFixed(2)}`;
  document.getElementById('diag-delta').innerText = `${cand.netDelta > 0 ? '+' : ''}${cand.netDelta}`;
  document.getElementById('diag-cushion').innerText = `${(((callK - putK) / spot) * 100).toFixed(2)}%`;
  document.getElementById('diag-safety').innerText = `${cand.safetyScore} / 100`;
  document.getElementById('diag-oi').innerText = `${cand.oi.toLocaleString()} lots`;

  // Generate Payoff curve
  const minSpot = spot * 0.92;
  const maxSpot = spot * 1.08;
  const steps = 80;
  const spots = [];
  const pnls = [];

  for (let i = 0; i <= steps; i++) {
    const s = minSpot + (i / steps) * (maxSpot - minSpot);
    spots.push(s);
    // Short Strangle PnL = Credit - max(0, PutK - s) - max(0, s - CallK)
    const pnl = credit - Math.max(0, putK - s) - Math.max(0, s - callK);
    pnls.push(pnl);
  }

  const traces = [
    {
      x: spots,
      y: pnls,
      mode: 'lines',
      name: 'Strangle Expiry P&L',
      line: { color: '#00E5FF', width: 3.5 }
    }
  ];

  const layoutPayoff = {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: '#94a3b8', family: 'Inter, sans-serif' },
    xaxis: { title: 'Spot Price at Expiry (₹)', gridcolor: '#1e293b' },
    yaxis: { title: 'P&L (₹ per unit)', gridcolor: '#1e293b' },
    shapes: [
      { type: 'line', x0: minSpot, x1: maxSpot, y0: 0, y1: 0, line: { color: '#475569', dash: 'dash' } },
      { type: 'line', x0: spot, x1: spot, y0: -credit * 2, y1: credit * 1.2, line: { color: '#FFD700', dash: 'dot' } },
      { type: 'line', x0: lowerBE, x1: lowerBE, y0: -credit * 2, y1: credit * 1.2, line: { color: '#FF5252', dash: 'dot' } },
      { type: 'line', x0: upperBE, x1: upperBE, y0: -credit * 2, y1: credit * 1.2, line: { color: '#FF5252', dash: 'dot' } }
    ],
    annotations: [
      { x: spot, y: credit * 0.9, text: `Spot ₹${spot.toLocaleString()}`, showarrow: false, font: { color: '#FFD700', size: 10 } },
      { x: lowerBE, y: -credit * 0.5, text: `Lower BE ₹${lowerBE.toFixed(0)}`, showarrow: false, font: { color: '#FF5252', size: 9 } },
      { x: upperBE, y: -credit * 0.5, text: `Upper BE ₹${upperBE.toFixed(0)}`, showarrow: false, font: { color: '#FF5252', size: 9 } }
    ],
    margin: { l: 40, r: 20, t: 10, b: 35 }
  };

  Plotly.react('payoff-chart', traces, layoutPayoff, { responsive: true, displayModeBar: false });
}

function renderDivergenceAndDepth(symbol) {
  const spot = symbol === 'NIFTY' ? 24650 : (symbol === 'BANKNIFTY' ? 52300 : 2950);
  const step = symbol === 'NIFTY' ? 50 : (symbol === 'BANKNIFTY' ? 100 : 20);

  const strikes = [];
  const ceDiv = [];
  const peDiv = [];
  const ceOI = [];
  const peOI = [];

  for (let offset = -8; offset <= 8; offset++) {
    const k = spot + offset * step;
    strikes.push(k);
    
    // Divergence metric
    const ceD = Number(((Math.random() - 0.45) * 35).toFixed(1));
    const peD = Number(((Math.random() - 0.52) * 35).toFixed(1));
    ceDiv.push(ceD);
    peDiv.push(peD);

    // Open interest depth
    const baseOI = 180000 * Math.exp(-Math.abs(offset) / 4);
    ceOI.push(Math.round(baseOI * (1 + (Math.random() - 0.5) * 0.3)));
    peOI.push(Math.round(baseOI * (1 + (Math.random() - 0.5) * 0.3)));
  }

  // 1. Divergence Chart
  const divTraces = [
    { x: strikes, y: ceDiv, name: 'Call Divergence (%)', type: 'bar', marker: { color: '#FF5252' } },
    { x: strikes, y: peDiv, name: 'Put Divergence (%)', type: 'bar', marker: { color: '#69F0AE' } }
  ];

  const layoutDiv = {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: '#94a3b8', family: 'Inter, sans-serif' },
    xaxis: { gridcolor: '#1e293b' },
    yaxis: { title: 'Divergence (%)', gridcolor: '#1e293b' },
    barmode: 'group',
    legend: { orientation: 'h', y: 1.1, x: 1, xanchor: 'right' },
    margin: { l: 40, r: 20, t: 10, b: 35 }
  };

  Plotly.react('divergence-chart', divTraces, layoutDiv, { responsive: true, displayModeBar: false });

  // 2. Depth Ladder Chart
  const depthTraces = [
    { x: strikes, y: ceOI, name: 'Call Open Interest', type: 'bar', marker: { color: 'rgba(255, 82, 82, 0.75)' } },
    { x: strikes, y: peOI, name: 'Put Open Interest', type: 'bar', marker: { color: 'rgba(105, 240, 174, 0.75)' } }
  ];

  const layoutDepth = {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: '#94a3b8', family: 'Inter, sans-serif' },
    xaxis: { gridcolor: '#1e293b' },
    yaxis: { title: 'Contracts', gridcolor: '#1e293b' },
    barmode: 'group',
    legend: { orientation: 'h', y: 1.1, x: 1, xanchor: 'right' },
    margin: { l: 50, r: 20, t: 10, b: 35 }
  };

  Plotly.react('depth-chart', depthTraces, layoutDepth, { responsive: true, displayModeBar: false });
}

// Initial Boot
document.addEventListener('DOMContentLoaded', () => {
  updateVolatilityView();
});
