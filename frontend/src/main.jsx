import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import Chart from 'chart.js/auto';
import './styles.css';

const API = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000/api').replace(/\/$/, '');
const money = value => `₹${Number(value || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const todayMonth = () => new Date().toISOString().slice(0, 7);
const categories = ['Food & drink', 'Transport', 'Home', 'Bills', 'Shopping', 'Health', 'Entertainment', 'Education', 'Travel', 'Salary', 'Freelance', 'Other'];

async function api(path, { token, ...options } = {}) {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options?.headers },
  });
  const type = response.headers.get('content-type') || '';
  const data = type.includes('json') ? await response.json() : await response.text();
  if (!response.ok) throw new Error(data?.message || data?.msg || 'Something went wrong. Please try again.');
  return data;
}

function TrendChart({ trend }) {
  const canvas = useRef(null);
  useEffect(() => {
    if (!canvas.current) return;
    const chart = new Chart(canvas.current, {
      type: 'line',
      data: { labels: trend.map(point => point.month), datasets: [{ data: trend.map(point => point.total), borderColor: '#718568', backgroundColor: 'rgba(113,133,104,.11)', fill: true, tension: .4, borderWidth: 2.5, pointRadius: 3, pointBackgroundColor: '#718568', pointBorderColor: '#fff', pointBorderWidth: 2 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { displayColors: false, backgroundColor: '#29352c', padding: 12, callbacks: { label: item => ` ${money(item.raw)}` } } }, scales: { x: { grid: { display: false }, border: { display: false }, ticks: { color: '#9a9c95', font: { family: 'DM Sans' } } }, y: { beginAtZero: true, grid: { color: '#f0f0ea', drawTicks: false }, border: { display: false, dash: [3, 4] }, ticks: { color: '#9a9c95', padding: 10, font: { family: 'DM Sans' }, callback: value => `₹${Number(value).toLocaleString('en-IN')}` } } } },
    });
    return () => chart.destroy();
  }, [trend]);
  return <div className="chart-wrap"><canvas ref={canvas} aria-label="Monthly spending trend" /></div>;
}

function CategoryChart({ totals }) {
  const canvas = useRef(null);
  const entries = Object.entries(totals).sort((a, b) => b[1] - a[1]);
  const colors = ['#7c916e', '#df927c', '#dfbc69', '#8ca7b7', '#aaa0ca', '#d29caa', '#91b7a5', '#c39c72'];
  useEffect(() => {
    if (!canvas.current || !entries.length) return;
    const chart = new Chart(canvas.current, { type: 'doughnut', data: { labels: entries.map(([name]) => name), datasets: [{ data: entries.map(([, value]) => value), backgroundColor: entries.map((_, index) => colors[index % colors.length]), borderWidth: 3, borderColor: '#fff', hoverOffset: 5 }] }, options: { responsive: true, maintainAspectRatio: false, cutout: '72%', plugins: { legend: { display: false }, tooltip: { callbacks: { label: item => ` ${money(item.raw)}` } } } } });
    return () => chart.destroy();
  }, [JSON.stringify(entries)]);
  return <div className="category-chart"><div className="donut-wrap"><canvas ref={canvas} aria-label="Spending by category" /><div className="donut-center"><strong>{entries.length}</strong><span>categories</span></div></div><div className="legend-list">{entries.slice(0, 8).map(([name, amount], index) => <div className="legend-row" key={name}><span><i className={`legend-swatch swatch-${index % 8}`} />{name}</span><strong>{money(amount)}</strong></div>)}</div></div>;
}

function AuthScreen({ onAuth }) {
  const [mode, setMode] = useState('login');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function submit(event) {
    event.preventDefault(); setError(''); setBusy(true);
    const form = new FormData(event.currentTarget);
    try {
      const result = await api(`/auth/${mode === 'register' ? 'register' : 'login'}`, { method: 'POST', body: JSON.stringify(Object.fromEntries(form)) });
      onAuth(result);
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  }
  return <div className="auth-shell"><section className="auth-visual"><a className="brand light-brand" href="#"><span className="brand-mark">p</span><span>Pennywise</span></a><div className="auth-art"><div className="art-kicker">YOUR MONEY, IN GOOD COMPANY</div><h1>A calmer way<br />to spend <em>mindfully.</em></h1><p>Know where it goes. Feel good about where it’s going.</p><div className="art-card"><div className="art-card-top"><span>MONTHLY OVERVIEW</span><span className="art-dot">●</span></div><div className="art-amount">₹ 24,680<span>.00</span></div><div className="art-sub">Total spending this month</div><div className="art-bars">{[34,48,41,68,54,83,62,94,72,100,71,84].map((height, i) => <i key={i} style={{ height: `${height}%` }} />)}</div><div className="art-months"><span>JAN</span><span>DEC</span></div></div></div><div className="auth-visual-foot">A little more clarity, every day.</div></section><section className="auth-form-side"><div className="auth-form-wrap"><div className="mobile-brand brand"><span className="brand-mark">p</span><span>Pennywise</span></div><div className="auth-eyebrow">{mode === 'register' ? 'A FRESH START' : 'WELCOME BACK'}</div><h2>{mode === 'register' ? 'Create your account' : 'Sign in to Pennywise'}</h2><p className="auth-intro">{mode === 'register' ? 'Your finances deserve a little breathing room.' : 'Pick up right where you left off.'}</p><form onSubmit={submit}>
    {mode === 'register' && <div className="field-wrap"><label htmlFor="name">Your name</label><input id="name" className="form-control" name="name" placeholder="e.g. Alex Morgan" minLength="2" maxLength="80" required autoComplete="name" /></div>}
    <div className="field-wrap"><label htmlFor="email">Email address</label><input id="email" className="form-control" name="email" type="email" placeholder="you@example.com" required autoComplete="email" /></div>
    <div className="field-wrap"><label htmlFor="password">Password</label><input id="password" className="form-control" name="password" type="password" placeholder={mode === 'register' ? 'At least 8 characters' : 'Your password'} minLength={mode === 'register' ? 8 : undefined} required autoComplete={mode === 'register' ? 'new-password' : 'current-password'} /></div>
    {error && <div className="field-error mb-3">{error}</div>}<button className="btn-primary-app w-100" type="submit" disabled={busy}>{busy ? 'Please wait…' : mode === 'register' ? 'Create account' : 'Sign in'} <span>→</span></button>
  </form><div className="auth-switch">{mode === 'register' ? 'Already have an account?' : 'New to Pennywise?'} <button type="button" className="link-button" onClick={() => { setError(''); setMode(mode === 'register' ? 'login' : 'register'); }}>{mode === 'register' ? 'Sign in' : 'Create an account'}</button></div><div className="auth-privacy">🔒 &nbsp;Your financial data stays private to you.</div></div></section></div>;
}

function TransactionEditor({ entry, onClose, onSave }) {
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(event) {
    event.preventDefault(); setError(''); setBusy(true);
    const form = new FormData(event.currentTarget);
    const values = Object.fromEntries(form); values.amount = Number(values.amount);
    try { await onSave(values, entry?.id); onClose(); } catch (err) { setError(err.message); } finally { setBusy(false); }
  }
  return <div className="overlay" onMouseDown={event => event.target === event.currentTarget && onClose()}><div className="editor-card panel"><button className="close-button" onClick={onClose} aria-label="Close">×</button><div className="auth-eyebrow">KEEP THE PICTURE CLEAR</div><h2>{entry ? 'Edit transaction' : 'Add a transaction'}</h2><p className="editor-intro">Every little detail helps you see where your money goes.</p><form onSubmit={submit}><div className="editor-grid"><div className="field-wrap full-field"><label>Description</label><input name="title" className="form-control" maxLength="120" placeholder="e.g. Saturday groceries" defaultValue={entry?.title || ''} required /></div><div className="field-wrap"><label>Amount</label><div className="amount-input"><span>₹</span><input name="amount" className="form-control" type="number" min="0.01" max="9999999999.99" step="0.01" placeholder="0.00" defaultValue={entry?.amount ?? ''} required /></div></div><div className="field-wrap"><label>Type</label><select name="kind" className="form-select" defaultValue={entry?.kind || 'expense'}><option value="expense">Expense</option><option value="income">Income</option></select></div><div className="field-wrap"><label>Category</label><select name="category" className="form-select" defaultValue={entry?.category || 'Food & drink'}>{categories.map(value => <option key={value}>{value}</option>)}</select></div><div className="field-wrap"><label>Date</label><input name="spent_on" className="form-control" type="date" defaultValue={entry?.spent_on || new Date().toISOString().slice(0, 10)} required /></div><div className="field-wrap full-field"><label>Note <span className="optional-label">OPTIONAL</span></label><textarea name="note" className="form-control" maxLength="280" rows="3" placeholder="A note for future you…" defaultValue={entry?.note || ''} /></div></div>{error && <div className="field-error">{error}</div>}<div className="form-actions"><button type="button" className="btn-outline-app" onClick={onClose}>Cancel</button><button disabled={busy} className="btn-primary-app">{busy ? 'Saving…' : entry ? 'Save changes' : 'Save transaction'} <span>→</span></button></div></form></div></div>;
}

function App() {
  const [token, setToken] = useState(() => localStorage.getItem('pennywise_token'));
  const [user, setUser] = useState(null);
  const [data, setData] = useState(null);
  const [month, setMonth] = useState(todayMonth());
  const [filters, setFilters] = useState({ category: '', kind: '', sort: 'newest', from: '', to: '' });
  const [form, setForm] = useState(null);
  const [toast, setToast] = useState('');
  const [loading, setLoading] = useState(Boolean(token));
  const [budgetOpen, setBudgetOpen] = useState(false);
  const query = useMemo(() => { const params = new URLSearchParams({ month }); Object.entries(filters).forEach(([key, value]) => value && params.set(key, value)); return params.toString(); }, [month, filters]);
  const loadDashboard = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try { const result = await api(`/dashboard?${query}`, { token }); setData(result); }
    catch (err) { if (err.message.toLowerCase().includes('token') || err.message.toLowerCase().includes('authorization')) signOut(); else setToast(err.message); }
    finally { setLoading(false); }
  }, [token, query]);
  useEffect(() => {
    if (!token) { setLoading(false); return; }
    api('/auth/me', { token }).then(result => setUser(result.user)).catch(() => signOut()).finally(() => setLoading(false));
  }, [token]);
  useEffect(() => { loadDashboard(); }, [loadDashboard]);
  useEffect(() => { if (!toast) return; const timer = setTimeout(() => setToast(''), 3200); return () => clearTimeout(timer); }, [toast]);
  function onAuth(result) { localStorage.setItem('pennywise_token', result.access_token); setToken(result.access_token); setUser(result.user); }
  function signOut() { localStorage.removeItem('pennywise_token'); setToken(null); setUser(null); setData(null); }
  async function saveTransaction(values, id) { await api(id ? `/transactions/${id}` : '/transactions', { token, method: id ? 'PATCH' : 'POST', body: JSON.stringify(values) }); setToast(id ? 'Transaction updated.' : 'Transaction saved.'); await loadDashboard(); }
  async function deleteTransaction(id) { if (!window.confirm('Delete this transaction?')) return; try { await api(`/transactions/${id}`, { token, method: 'DELETE' }); setToast('Transaction deleted.'); await loadDashboard(); } catch (err) { setToast(err.message); } }
  async function saveBudget(event) { event.preventDefault(); const values = Object.fromEntries(new FormData(event.currentTarget)); try { await api('/budget', { token, method: 'PUT', body: JSON.stringify({ month: values.month, amount: Number(values.amount) }) }); setMonth(values.month); setBudgetOpen(false); setToast('Monthly budget updated.'); } catch (err) { setToast(err.message); } }
  async function exportCsv() { try { const response = await fetch(`${API}/export.csv`, { headers: { Authorization: `Bearer ${token}` } }); if (!response.ok) throw new Error('Could not export transactions.'); const blob = await response.blob(); const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = 'transactions.csv'; link.click(); URL.revokeObjectURL(url); } catch (err) { setToast(err.message); } }
  function applyFilters(event) { event.preventDefault(); const formData = new FormData(event.currentTarget); setFilters({ category: formData.get('category'), kind: formData.get('kind'), sort: formData.get('sort'), from: formData.get('from'), to: formData.get('to') }); }

  if (!token) return <AuthScreen onAuth={onAuth} />;
  if (loading && !data) return <div className="loading-screen"><span className="brand-mark">p</span><span>Getting your money picture…</span></div>;
  if (!user) return <div className="loading-screen"><span className="brand-mark">p</span><span>Checking your account…</span></div>;
  const spent = data?.spent || 0, budget = data?.budget;
  const displayDate = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
  const greeting = new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 18 ? 'afternoon' : 'evening';
  const getBudget = async event => { await saveBudget(event); await loadDashboard(); };

  return <><aside className="sidebar"><a className="brand" href="#"><span className="brand-mark">p</span><span>Pennywise</span></a><div className="side-label">WORKSPACE</div><a className="side-link active" href="#overview"><span className="nav-icon">◫</span> Overview</a><a className="side-link" href="#transactions"><span className="nav-icon">↕</span> Transactions</a><a className="side-link" href="#insights"><span className="nav-icon">◒</span> Insights</a><div className="sidebar-bottom"><div className="sidebar-tip"><div className="tip-icon">✳</div><strong>Small steps add up.</strong><p>A little awareness goes a long way with your money.</p></div><div className="profile-mini"><div className="avatar">{user.name[0]?.toUpperCase()}</div><div className="profile-copy"><strong>{user.name}</strong><span>Personal account</span></div><button className="icon-button" onClick={signOut} aria-label="Sign out" title="Sign out">↗</button></div></div></aside>
  <main className="main-area" id="overview"><header className="topbar"><div><div className="date-kicker">{displayDate}</div><h1>Good {greeting}, {user.name.split(' ')[0]} <span className="wave">✳</span></h1><p>Here’s how your money is moving this month.</p></div><button className="btn-primary-app add-top" onClick={() => setForm({ entry: null })}><span>＋</span> Add transaction</button></header>
  <section className="summary-grid"><article className="summary-card"><div className="summary-head"><span>Money in</span><span className="summary-icon green">↙</span></div><div className="summary-value">{money(data?.income)}</div><div className="summary-foot"><span className="status-dot green-dot" /> Income this month</div></article><article className="summary-card"><div className="summary-head"><span>Money out</span><span className="summary-icon coral">↗</span></div><div className="summary-value">{money(spent)}</div><div className="summary-foot"><span className="status-dot coral-dot" /> Spending this month</div></article><article className="summary-card balance-card"><div className="summary-head"><span>Available balance</span><span className="summary-icon cream">◈</span></div><div className="summary-value">{money(data?.balance)}</div><div className="summary-foot">Income minus spending</div></article></section>
  <section className="dashboard-grid" id="insights"><article className="panel trend-panel"><div className="panel-heading"><div><h2>Spending trend</h2><p>A little perspective over time</p></div><span className="panel-tag"><i /> Expenses</span></div><TrendChart trend={data?.trend || []} /></article><article className="panel budget-panel"><div className="panel-heading"><div><h2>Monthly budget</h2><p>A gentle guide for your spending</p></div><button className="text-button" onClick={() => setBudgetOpen(true)}>{budget ? 'Edit' : 'Set budget'} ↗</button></div>{budget ? <><div className="budget-amount">{money(spent)} <span>of {money(budget)}</span></div><div className="progress budget-progress"><div className={`progress-bar ${spent >= budget ? 'over-budget' : ''}`} style={{ width: `${Math.min(spent / budget * 100, 100)}%` }} /></div><div className="budget-foot"><span>{Math.floor(spent / budget * 100)}% used</span><span>{spent > budget ? `${money(spent - budget)} over budget` : `${money(budget - spent)} remaining`}</span></div></> : <div className="budget-empty"><div className="budget-illustration">◎</div><strong>Make room for what matters.</strong><p>Set a monthly spending guide and keep your goals in sight.</p><button className="btn-outline-app" onClick={() => setBudgetOpen(true)}>Set a monthly budget <span>→</span></button></div>}</article></section>
  <section className="dashboard-grid lower-grid"><article className="panel category-panel"><div className="panel-heading"><div><h2>Where it goes</h2><p>Spending by category · {data?.month}</p></div><span className="panel-more">•••</span></div>{Object.keys(data?.category_totals || {}).length ? <CategoryChart totals={data.category_totals} /> : <div className="chart-empty"><div className="empty-orbit">◒</div><strong>Your story starts here</strong><p>Add a few expenses and your spending breakdown will show up.</p></div>}</article><article className="panel insight-panel"><div className="panel-heading"><div><h2>A small insight</h2><p>One thing to keep in mind</p></div><span className="sparkle">✳</span></div><div className="insight-content"><div className="insight-mark">✦</div><h3>{spent === 0 ? 'Every good habit starts with noticing.' : budget && spent > budget ? 'You’ve passed your monthly guide.' : budget ? 'You’re keeping your goals in view.' : 'Your money is finding its rhythm.'}</h3><p>{spent === 0 ? 'Log your first transaction to see your monthly picture take shape.' : budget && spent > budget ? 'A quick look at your categories can help you decide what feels right for next month.' : budget ? `You’ve spent ${Math.floor(spent / budget * 100)}% of your monthly guide. Keep checking in as the month unfolds.` : 'Set a monthly budget to give your plans a little more direction.'}</p><a href="#transactions">View transactions <span>→</span></a></div></article></section>
  <section className="panel transactions-panel" id="transactions"><div className="transactions-heading"><div><h2>Recent transactions</h2><p>Your latest money moves, all in one place</p></div><div className="transaction-actions"><button className="text-button export-link" onClick={exportCsv}>↓ &nbsp;Export CSV</button><button className="btn-outline-app compact" onClick={() => setForm({ entry: null })}>＋ &nbsp;Add new</button></div></div><form key={JSON.stringify(filters)} className="filter-row" onSubmit={applyFilters}><input type="month" name="month" value={month} onChange={event => setMonth(event.target.value)} aria-label="Summary month" title="Summary month" className="filter-control" /><select name="category" defaultValue={filters.category} className="filter-control" aria-label="Category"><option value="">All categories</option>{categories.map(category => <option key={category}>{category}</option>)}</select><select name="kind" defaultValue={filters.kind} className="filter-control" aria-label="Type"><option value="">Income & expenses</option><option value="expense">Expenses</option><option value="income">Income</option></select><select name="sort" defaultValue={filters.sort} className="filter-control" aria-label="Sort"><option value="newest">Newest first</option><option value="oldest">Oldest first</option><option value="amount_desc">Highest amount</option><option value="amount_asc">Lowest amount</option></select><input type="date" name="from" defaultValue={filters.from} aria-label="From date" title="From date" className="filter-control" /><input type="date" name="to" defaultValue={filters.to} aria-label="To date" title="To date" className="filter-control" /><button className="filter-submit">Apply filters</button><button type="button" className="filter-reset" onClick={() => { setFilters({ category: '', kind: '', sort: 'newest', from: '', to: '' }); setMonth(todayMonth()); }}>Reset</button></form>
  {loading && <div className="inline-loading">Refreshing transactions…</div>}{data?.transactions?.length ? <div className="table-responsive"><table className="table transaction-table"><thead><tr><th>TRANSACTION</th><th>CATEGORY</th><th>DATE</th><th>AMOUNT</th><th /></tr></thead><tbody>{data.transactions.map((entry, index) => <tr key={entry.id}><td><div className="transaction-name"><span className={`transaction-icon icon-${index % 6}`}>{({ 'Food & drink': '♨', Transport: '↗', Home: '⌂', Bills: '▤', Shopping: '◇', Health: '✚', Entertainment: '♫', Education: '▱', Travel: '✈', Salary: '↙', Freelance: '✳', Other: '·' })[entry.category] || '·'}</span><span><strong>{entry.title}</strong>{entry.note && <small>{entry.note}</small>}</span></div></td><td><span className="category-pill">{entry.category}</span></td><td className="transaction-date">{new Date(`${entry.spent_on}T00:00:00`).toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' })}</td><td className={`transaction-amount ${entry.kind === 'income' ? 'income-amount' : ''}`}>{entry.kind === 'income' ? '+' : '−'}{money(entry.amount)}</td><td><div className="row-actions"><button onClick={() => setForm({ entry })} aria-label={`Edit ${entry.title}`} title="Edit">✎</button><button onClick={() => deleteTransaction(entry.id)} aria-label={`Delete ${entry.title}`} title="Delete">×</button></div></td></tr>)}</tbody></table></div> : <div className="transactions-empty"><div className="empty-orbit">↕</div><strong>No transactions found</strong><p>Try another filter or add your first transaction.</p><button className="btn-primary-app" onClick={() => setForm({ entry: null })}>＋ Add transaction</button></div>}</section><footer className="page-footer"><span>Made for a clearer relationship with money.</span><span>© {new Date().getFullYear()} Pennywise</span></footer></main>
  {form && <TransactionEditor entry={form.entry} onClose={() => setForm(null)} onSave={saveTransaction} />}
  {budgetOpen && <div className="overlay" onMouseDown={event => event.target === event.currentTarget && setBudgetOpen(false)}><div className="budget-modal modal-content"><form onSubmit={getBudget}><div className="modal-header"><div><div className="auth-eyebrow">A GUIDE, NOT A RULE</div><h2>Monthly spending guide</h2></div><button type="button" className="close-button" onClick={() => setBudgetOpen(false)}>×</button></div><div className="modal-body"><label htmlFor="budget-month">Month</label><input id="budget-month" className="form-control" type="month" name="month" defaultValue={month} required /><label htmlFor="budget-amount">Budget amount</label><div className="amount-input"><span>₹</span><input id="budget-amount" className="form-control" name="amount" type="number" min="0.01" step="0.01" placeholder="e.g. 30000" defaultValue={budget || ''} required /></div></div><div className="modal-footer"><button type="button" className="btn-outline-app" onClick={() => setBudgetOpen(false)}>Cancel</button><button className="btn-primary-app">Save budget <span>→</span></button></div></form></div></div>}
  {toast && <div className="toast-stack"><div className="app-toast">{toast}<button onClick={() => setToast('')}>×</button></div></div>}</>;
}

createRoot(document.getElementById('root')).render(<App />);
