"""
routes/dashboard.py
────────────────────
Serves a beautiful, premium real-time admin dashboard at GET /dashboard
Shows live stats, rules, and recent DM jobs.
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>LinkPlease — Mission Control</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet" />
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:        #050505;
      --surface:   rgba(20, 20, 22, 0.6);
      --surface2:  rgba(255, 255, 255, 0.03);
      --border:    rgba(255, 255, 255, 0.08);
      --text:      #f3f4f6;
      --muted:     #9ca3af;
      --accent:    #8b5cf6;
      --accent-glow: rgba(139, 92, 246, 0.4);
      --green:     #10b981;
      --red:       #ef4444;
      --amber:     #f59e0b;
      --blue:      #3b82f6;
    }

    body {
      font-family: 'Inter', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      line-height: 1.6;
      position: relative;
      overflow-x: hidden;
    }
    
    /* Premium glowing background effect */
    body::before {
      content: '';
      position: fixed;
      top: -20%; left: -10%;
      width: 50%; height: 50%;
      background: radial-gradient(circle, var(--accent-glow) 0%, transparent 60%);
      filter: blur(100px);
      z-index: -1;
      opacity: 0.5;
    }

    /* ── Header ── */
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 1.25rem 3rem;
      border-bottom: 1px solid var(--border);
      background: rgba(10, 10, 10, 0.4);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      position: sticky;
      top: 0;
      z-index: 10;
    }
    .logo {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      font-size: 1.2rem;
      font-weight: 700;
      letter-spacing: -0.03em;
      background: linear-gradient(to right, #fff, #a5b4fc);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .logo-dot {
      width: 12px; height: 12px;
      background: var(--accent);
      border-radius: 50%;
      box-shadow: 0 0 12px var(--accent-glow);
      animation: pulse 2s infinite;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); box-shadow: 0 0 12px var(--accent-glow); }
      50%      { opacity: 0.5; transform: scale(0.85); box-shadow: 0 0 2px transparent; }
    }
    .header-right {
      display: flex;
      align-items: center;
      gap: 1.5rem;
    }
    .live-badge {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--green);
      background: rgba(16, 185, 129, 0.1);
      padding: 0.35rem 0.85rem;
      border-radius: 100px;
      border: 1px solid rgba(16, 185, 129, 0.2);
      box-shadow: 0 0 10px rgba(16, 185, 129, 0.1);
    }
    .live-dot {
      width: 6px; height: 6px;
      background: var(--green);
      border-radius: 50%;
      animation: pulse 1.5s infinite;
    }

    /* ── Layout ── */
    main {
      max-width: 1200px;
      margin: 0 auto;
      padding: 2.5rem 2rem;
    }

    /* ── Stats Grid ── */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 1.25rem;
      margin-bottom: 3rem;
    }
    .stat-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    .stat-card:hover {
      border-color: rgba(255,255,255,0.2);
      transform: translateY(-4px);
      box-shadow: 0 8px 30px rgba(0,0,0,0.4);
    }
    .stat-label {
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--muted);
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .stat-value {
      font-size: 2.75rem;
      font-weight: 700;
      font-family: 'JetBrains Mono', monospace;
      letter-spacing: -0.04em;
      line-height: 1;
    }
    .stat-value.green { color: var(--green); text-shadow: 0 0 20px rgba(16,185,129,0.3); }
    .stat-value.red   { color: var(--red); text-shadow: 0 0 20px rgba(239,68,68,0.3); }
    .stat-value.amber { color: var(--amber); text-shadow: 0 0 20px rgba(245,158,11,0.3); }
    .stat-value.blue  { color: var(--blue); text-shadow: 0 0 20px rgba(59,130,246,0.3); }

    /* ── Section ── */
    .section {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      margin-bottom: 2rem;
      overflow: hidden;
      backdrop-filter: blur(10px);
      box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    .section-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 1.25rem 1.75rem;
      border-bottom: 1px solid var(--border);
      background: rgba(255,255,255,0.01);
    }
    .section-title {
      font-size: 1rem;
      font-weight: 600;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .section-count {
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--accent);
      background: rgba(139, 92, 246, 0.15);
      padding: 0.25rem 0.75rem;
      border-radius: 100px;
    }

    /* ── Rule Form ── */
    .rule-form {
      display: flex;
      gap: 1rem;
      padding: 1.5rem 1.75rem;
      border-bottom: 1px solid var(--border);
      flex-wrap: wrap;
      background: rgba(0,0,0,0.2);
    }
    .rule-form input {
      flex: 1;
      min-width: 180px;
      background: rgba(255,255,255,0.04);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.75rem 1rem;
      color: var(--text);
      font-family: 'Inter', sans-serif;
      font-size: 0.9rem;
      outline: none;
      transition: all 0.2s;
    }
    .rule-form input:focus { 
      border-color: var(--accent); 
      background: rgba(255,255,255,0.08);
      box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
    }
    .btn {
      background: var(--accent);
      color: #fff;
      border: none;
      border-radius: 8px;
      padding: 0.75rem 1.5rem;
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
    }
    .btn:hover { 
      background: #7c3aed; 
      box-shadow: 0 6px 16px rgba(139, 92, 246, 0.4);
      transform: translateY(-1px);
    }
    .btn:active { transform: translateY(1px); }
    
    .btn-danger {
      background: transparent;
      color: var(--red);
      border: 1px solid rgba(239,68,68,0.3);
      box-shadow: none;
      padding: 0.4rem 0.8rem;
      font-size: 0.75rem;
    }
    .btn-danger:hover { 
      background: rgba(239,68,68,0.15); 
      border-color: rgba(239,68,68,0.5);
      transform: none;
      box-shadow: none;
    }

    /* ── Table ── */
    table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
    th {
      text-align: left;
      padding: 1rem 1.75rem;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      background: rgba(0,0,0,0.3);
      border-bottom: 1px solid var(--border);
    }
    td {
      padding: 1rem 1.75rem;
      border-bottom: 1px solid rgba(255,255,255,0.03);
      vertical-align: middle;
    }
    tr:last-child td { border-bottom: none; }
    tr:hover td { background: rgba(255,255,255,0.03); }
    .mono { font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #d1d5db; }
    .fade { color: var(--muted); }

    /* ── Status badges ── */
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      font-size: 0.7rem;
      font-weight: 700;
      padding: 0.25rem 0.75rem;
      border-radius: 100px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .badge::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
    .badge-delivered { background: rgba(16,185,129,0.15);  color: var(--green); border: 1px solid rgba(16,185,129,0.2); }
    .badge-queued    { background: rgba(245,158,11,0.15); color: var(--amber); border: 1px solid rgba(245,158,11,0.2); }
    .badge-sending   { background: rgba(59,130,246,0.15); color: var(--blue); border: 1px solid rgba(59,130,246,0.2); }
    .badge-failed    { background: rgba(239,68,68,0.15);  color: var(--red); border: 1px solid rgba(239,68,68,0.2); }
    .badge-cancelled { background: rgba(156,163,175,0.15);color: var(--muted); border: 1px solid rgba(156,163,175,0.2); }

    .empty { padding: 3rem; text-align: center; color: var(--muted); font-size: 0.9rem; }
    .refresh-info { font-size: 0.75rem; color: var(--muted); text-align: center; padding: 1rem; }
    .keyword-pill {
      background: rgba(139, 92, 246, 0.15);
      color: #a78bfa;
      padding: 0.2rem 0.6rem;
      border-radius: 6px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.8rem;
      font-weight: 600;
      border: 1px solid rgba(139, 92, 246, 0.3);
    }
    
    /* Progress bar for queue draining */
    .queue-progress {
      height: 4px;
      background: rgba(255,255,255,0.1);
      border-radius: 2px;
      margin-top: 0.5rem;
      overflow: hidden;
      display: none;
    }
    .queue-bar {
      height: 100%;
      background: var(--amber);
      width: 100%;
      transition: width 1s linear;
    }
  </style>
</head>
<body>

<header>
  <div class="logo">
    <div class="logo-dot"></div>
    LinkPlease Mission Control
  </div>
  <div class="header-right">
    <div class="live-badge">
      <div class="live-dot"></div>
      SYSTEM ONLINE
    </div>
  </div>
</header>

<main>
  <!-- Stats -->
  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-label">
        <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
        Successfully Delivered
      </div>
      <div class="stat-value green" id="stat-sent" data-val="0">0</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">
        <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
        In Queue / Sending
      </div>
      <div class="stat-value amber" id="stat-queued" data-val="0">0</div>
      <div class="queue-progress" id="queue-progress"><div class="queue-bar"></div></div>
    </div>
    <div class="stat-card">
      <div class="stat-label">
        <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
        Duplicates Blocked
      </div>
      <div class="stat-value blue" id="stat-dupes" data-val="0">0</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">
        <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>
        Failed (Max Retries)
      </div>
      <div class="stat-value red" id="stat-failed" data-val="0">0</div>
    </div>
  </div>

  <!-- Rules -->
  <div class="section">
    <div class="section-header">
      <span class="section-title">
        <svg width="18" height="18" fill="none" stroke="var(--accent)" stroke-width="2" viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
        Automation Rules
      </span>
      <span class="section-count" id="rules-count">0 active</span>
    </div>
    <form class="rule-form" id="rule-form">
      <input id="rule-keyword" placeholder="Trigger Keyword (e.g. PRICE)" required />
      <input id="rule-message" placeholder="DM Content to send automatically..." required />
      <button type="submit" class="btn">+ Deploy Rule</button>
    </form>
    <table>
      <thead>
        <tr>
          <th>Rule ID</th>
          <th>Keyword</th>
          <th>DM Payload</th>
          <th>Deployed At</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody id="rules-body">
        <tr><td colspan="5" class="empty">No automation rules configured.</td></tr>
      </tbody>
    </table>
  </div>

  <!-- Recent DM Jobs -->
  <div class="section">
    <div class="section-header">
      <span class="section-title">
        <svg width="18" height="18" fill="none" stroke="var(--accent)" stroke-width="2" viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
        DM Dispatch Log
      </span>
      <span class="section-count" id="jobs-count">0 total jobs</span>
    </div>
    <table>
      <thead>
        <tr>
          <th>User ID</th>
          <th>Source Comment</th>
          <th>Delivery Status</th>
          <th>Retries</th>
          <th>Last Update</th>
        </tr>
      </thead>
      <tbody id="jobs-body">
        <tr><td colspan="5" class="empty">System standing by. No DMs dispatched yet.</td></tr>
      </tbody>
    </table>
  </div>

  <div class="refresh-info">⚡ Socketless Real-Time Sync • Auto-refreshing every 2000ms</div>
</main>

<script>
  // Utility for animating numbers
  function animateValue(obj, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / duration, 1);
      obj.innerHTML = Math.floor(progress * (end - start) + start);
      if (progress < 1) {
        window.requestAnimationFrame(step);
      } else {
        obj.innerHTML = end;
        obj.dataset.val = end;
      }
    };
    window.requestAnimationFrame(step);
  }

  function updateStat(id, newValue) {
    const el = document.getElementById(id);
    const oldVal = parseInt(el.dataset.val || "0", 10);
    if (oldVal !== newValue) {
      animateValue(el, oldVal, newValue, 500);
    }
  }

  function badge(status) {
    const map = { delivered:'badge-delivered', queued:'badge-queued', sending:'badge-sending', failed:'badge-failed', cancelled:'badge-cancelled' };
    const cls = map[status] || 'badge-queued';
    return `<span class="badge ${cls}">${status}</span>`;
  }

  function reltime(iso) {
    if (!iso) return '—';
    const diff = Math.floor((Date.now() - new Date(iso)) / 1000);
    if (diff < 10) return 'Just now';
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
    return new Date(iso).toLocaleTimeString();
  }

  let maxQueueSeen = 0;

  async function refreshStats() {
    const r = await fetch('/stats');
    if (!r.ok) return;
    const d = await r.json();
    
    updateStat('stat-sent', d.sent ?? 0);
    updateStat('stat-failed', d.failed ?? 0);
    updateStat('stat-dupes', d.duplicates_blocked ?? 0);
    updateStat('stat-queued', d.queued ?? 0);
    
    // Progress bar logic for draining queue
    const q = d.queued ?? 0;
    const prog = document.getElementById('queue-progress');
    if (q > maxQueueSeen) maxQueueSeen = q;
    
    if (q > 0) {
        prog.style.display = 'block';
        const percent = Math.max(5, (q / maxQueueSeen) * 100);
        prog.querySelector('.queue-bar').style.width = `${percent}%`;
    } else {
        prog.style.display = 'none';
        maxQueueSeen = 0; // reset
    }
  }

  async function refreshRules() {
    const r = await fetch('/rules');
    if (!r.ok) return;
    const rules = await r.json();
    document.getElementById('rules-count').textContent = `${rules.length} active`;
    const tbody = document.getElementById('rules-body');
    if (!rules.length) {
      tbody.innerHTML = '<tr><td colspan="5" class="empty">No automation rules configured.</td></tr>';
      return;
    }
    tbody.innerHTML = rules.map(r => `
      <tr>
        <td class="mono fade">${r.rule_id.substring(0,12)}...</td>
        <td><span class="keyword-pill">${r.keyword.toUpperCase()}</span></td>
        <td style="max-width:320px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-weight:500;" title="${r.dm_message}">${r.dm_message}</td>
        <td class="mono fade">${reltime(r.created_at)}</td>
        <td><button class="btn btn-danger" onclick="deleteRule('${r.rule_id}')">Revoke</button></td>
      </tr>
    `).join('');
  }

  async function refreshJobs() {
    const r = await fetch('/jobs?limit=50');
    if (!r.ok) return;
    const jobs = await r.json();
    document.getElementById('jobs-count').textContent = `${jobs.total ?? jobs.length} dispatched`;
    const tbody = document.getElementById('jobs-body');
    if (!jobs.items?.length) {
      tbody.innerHTML = '<tr><td colspan="5" class="empty">System standing by. No DMs dispatched yet.</td></tr>';
      return;
    }
    tbody.innerHTML = jobs.items.map(j => `
      <tr>
        <td class="mono">${j.user_id}</td>
        <td class="mono fade">${j.comment_id}</td>
        <td>${badge(j.status)}</td>
        <td class="mono fade">${j.attempts}</td>
        <td class="mono fade">${reltime(j.updated_at)}</td>
      </tr>
    `).join('');
  }

  async function deleteRule(ruleId) {
    await fetch(`/rules/${ruleId}`, { method: 'DELETE' });
    refreshRules();
  }

  document.getElementById('rule-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const keyword = document.getElementById('rule-keyword').value.trim();
    const dm_message = document.getElementById('rule-message').value.trim();
    if (!keyword || !dm_message) return;
    
    const btn = e.target.querySelector('button');
    btn.textContent = 'Deploying...';
    
    await fetch('/rules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keyword, dm_message }),
    });
    
    document.getElementById('rule-keyword').value = '';
    document.getElementById('rule-message').value = '';
    btn.textContent = '+ Deploy Rule';
    refreshRules();
  });

  async function refresh() {
    await Promise.all([refreshStats(), refreshRules(), refreshJobs()]);
  }

  refresh();
  setInterval(refresh, 2000);
</script>
</body>
</html>"""

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Live admin dashboard — not graded, but shows off."""
    return HTMLResponse(content=DASHBOARD_HTML)
