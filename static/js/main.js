/* ── GLOBAL UTILS ── */

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

// Live clock
function updateClock() {
  const el = document.getElementById('topbar-time');
  if (el) {
    el.textContent = new Date().toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }) + ' IST';
  }
}
setInterval(updateClock, 1000);
updateClock();

// Load global stats into nav/topbar
async function loadGlobalStats() {
  try {
    const r = await fetch('/api/dashboard/summary');
    const d = await r.json();
    const riskEl = document.getElementById('global-risk-val');
    if (riskEl) {
      riskEl.textContent = (d.global_risk_score || 0).toFixed(0);
      const v = d.global_risk_score || 0;
      riskEl.style.color = v >= 70 ? '#ef4444' : v >= 50 ? '#f59e0b' : '#10b981';
    }
    const newsBadge = document.getElementById('nav-news-count');
    if (newsBadge) newsBadge.textContent = d.total_news || 0;
    const alertBadge = document.getElementById('nav-alert-count');
    if (alertBadge) alertBadge.textContent = d.active_alerts || 0;
  } catch(e) {}
}
loadGlobalStats();

// Toast notification
function showToast(msg, type = 'info') {
  const id = 'toast-' + Date.now();
  const colors = { info:'#0ea5e9', success:'#10b981', error:'#ef4444', warning:'#f59e0b' };
  const html = `
    <div id="${id}" class="toast align-items-center border-0 show" style="background:#111827;border-left:3px solid ${colors[type]}!important;color:#e2e8f0;">
      <div class="d-flex"><div class="toast-body">${msg}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>
    </div>`;
  document.getElementById('toast-container').insertAdjacentHTML('beforeend', html);
  setTimeout(() => { const t = document.getElementById(id); if(t) t.remove(); }, 4000);
}

// Severity badge helper
function severityBadge(sev) {
  if (sev >= 8) return '<span class="badge-severity sev-critical">Critical</span>';
  if (sev >= 6) return '<span class="badge-severity sev-high">High</span>';
  if (sev >= 4) return '<span class="badge-severity sev-medium">Medium</span>';
  return '<span class="badge-severity sev-low">Low</span>';
}

// Shock tag helper
function shockTag(type) {
  const cls = {
    'Oil Shock':'shock-oil','Semiconductor Shortage':'shock-semi',
    'Trade Restriction':'shock-trade','Shipping Crisis':'shock-shipping',
    'Climate Event':'shock-climate','Currency Volatility':'shock-currency'
  };
  return `<span class="shock-tag ${cls[type]||'shock-trade'}">${type||'Unknown'}</span>`;
}

// Format date
function fmtDate(iso) {
  if (!iso) return '--';
  return new Date(iso).toLocaleDateString('en-US', {month:'short',day:'numeric',year:'numeric'});
}

// Chart defaults
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = '#1e2d42';
Chart.defaults.plugins.legend.labels.color = '#94a3b8';
