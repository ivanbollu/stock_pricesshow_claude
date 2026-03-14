#!/usr/bin/env python3
"""
股票价格查看器 - 使用 Alpha Vantage API
运行: python stock_viewer.py
然后在浏览器打开: http://localhost:8080

免费申请 API Key: https://www.alphavantage.co/support/#api-key
将下方 API_KEY 替换为你的真实 Key（免费额度：每分钟25次，每天500次）
demo Key 仅支持查询: IBM
"""

import json
import http.server
import threading
import webbrowser
import urllib.request
import urllib.parse

# ⬇️ 替换为你的 Alpha Vantage API Key
API_KEY = "HR92OTJD4THLCOYR"

HTML_PAGE = '''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>股票价格看板</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Mono:ital,wght@0,400;0,500;1,400&family=Noto+Sans+SC:wght@300;400;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #07080d;
    --panel: #0e0f18;
    --border: #1a1b2e;
    --accent: #00e5ff;
    --gold: #fbbf24;
    --green: #34d399;
    --red: #f87171;
    --text: #e2e8f0;
    --muted: #475569;
    --muted2: #334155;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Noto Sans SC', sans-serif;
    min-height: 100vh;
  }

  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
      radial-gradient(ellipse 80% 50% at 50% -20%, rgba(0,229,255,0.07) 0%, transparent 60%),
      linear-gradient(rgba(0,229,255,0.025) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,229,255,0.025) 1px, transparent 1px);
    background-size: auto, 48px 48px, 48px 48px;
    pointer-events: none;
    z-index: 0;
  }

  .wrap {
    position: relative;
    z-index: 1;
    max-width: 900px;
    margin: 0 auto;
    padding: 48px 24px 80px;
  }

  .header { margin-bottom: 44px; }

  .logo-row {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 6px;
  }

  .logo-icon {
    width: 42px; height: 42px;
    border: 1.5px solid var(--accent);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
  }

  .logo-icon svg { width: 22px; height: 22px; }

  .logo {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 44px;
    letter-spacing: 6px;
    background: linear-gradient(100deg, var(--accent) 0%, var(--gold) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .tagline {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: var(--muted);
    letter-spacing: 3px;
    text-transform: uppercase;
    padding-left: 56px;
  }

  .search-row { display: flex; gap: 10px; margin-bottom: 20px; }

  .search-box { flex: 1; position: relative; }

  .search-box input {
    width: 100%;
    background: var(--panel);
    border: 1px solid var(--border);
    color: var(--text);
    font-family: 'DM Mono', monospace;
    font-size: 14px;
    letter-spacing: 1px;
    padding: 13px 16px 13px 44px;
    outline: none;
    transition: border-color 0.25s, box-shadow 0.25s;
  }

  .search-box input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(0,229,255,0.08);
  }

  .search-box input::placeholder { color: var(--muted); }

  .search-icon {
    position: absolute; left: 14px; top: 50%; transform: translateY(-50%);
    color: var(--accent); font-size: 16px; font-family: 'DM Mono', monospace;
    pointer-events: none;
  }

  .btn-search {
    background: var(--accent); color: #000; border: none;
    padding: 13px 26px;
    font-family: 'DM Mono', monospace; font-size: 12px; font-weight: 500;
    letter-spacing: 2px; text-transform: uppercase; cursor: pointer;
    transition: background 0.2s, transform 0.15s; white-space: nowrap;
  }

  .btn-search:hover { background: var(--gold); transform: translateY(-1px); }
  .btn-search:active { transform: translateY(0); }

  .chips { display: flex; flex-wrap: wrap; gap: 7px; margin-bottom: 40px; }

  .chip {
    background: transparent; border: 1px solid var(--muted2);
    color: var(--muted); padding: 5px 13px;
    font-family: 'DM Mono', monospace; font-size: 11px; letter-spacing: 1px;
    cursor: pointer; transition: all 0.2s;
  }

  .chip:hover {
    border-color: var(--accent); color: var(--accent);
    background: rgba(0,229,255,0.04); transform: none;
  }

  .card {
    border: 1px solid var(--border); background: var(--panel);
    position: relative; overflow: hidden; animation: fadeUp 0.35s ease;
  }

  .card-glow { position: absolute; top: 0; left: 0; right: 0; height: 1px; }
  .card-glow.up   { background: linear-gradient(90deg, transparent, var(--green), transparent); }
  .card-glow.down { background: linear-gradient(90deg, transparent, var(--red), transparent); }

  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .card-top {
    display: flex; justify-content: space-between; align-items: flex-start;
    padding: 24px 28px 20px; border-bottom: 1px solid var(--border);
  }

  .sym {
    font-family: 'Bebas Neue', sans-serif; font-size: 42px;
    letter-spacing: 3px; line-height: 1;
  }

  .company { font-size: 12px; color: var(--muted); margin-top: 5px; font-weight: 300; }

  .price-col { text-align: right; }

  .price {
    font-family: 'DM Mono', monospace; font-size: 36px;
    font-weight: 500; letter-spacing: -1px; line-height: 1;
  }

  .badge {
    display: inline-block; margin-top: 6px; padding: 3px 10px;
    font-family: 'DM Mono', monospace; font-size: 12px; font-weight: 500;
  }

  .up   { color: var(--green); }
  .down { color: var(--red); }
  .badge.up   { background: rgba(52,211,153,0.1); }
  .badge.down { background: rgba(248,113,113,0.1); }

  .stats { display: grid; grid-template-columns: repeat(4, 1fr); }

  .stat {
    padding: 18px 28px;
    border-right: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
  }

  .stat:nth-child(4n) { border-right: none; }

  .stat-label {
    font-family: 'DM Mono', monospace; font-size: 10px;
    color: var(--muted); letter-spacing: 2px; text-transform: uppercase; margin-bottom: 5px;
  }

  .stat-val { font-family: 'DM Mono', monospace; font-size: 14px; color: var(--text); }

  .loading {
    padding: 56px; text-align: center;
    font-family: 'DM Mono', monospace; font-size: 12px;
    color: var(--muted); letter-spacing: 3px; text-transform: uppercase;
  }

  .bar-anim {
    width: 48px; height: 2px; background: var(--accent);
    margin: 14px auto 0; animation: pulse 0.9s ease-in-out infinite alternate;
  }

  @keyframes pulse {
    from { opacity: 0.2; transform: scaleX(0.4); }
    to   { opacity: 1;   transform: scaleX(1); }
  }

  .error {
    padding: 18px 24px; border: 1px solid rgba(248,113,113,0.3);
    background: rgba(248,113,113,0.05); color: var(--red);
    font-family: 'DM Mono', monospace; font-size: 13px;
  }

  footer {
    margin-top: 40px; padding-top: 18px; border-top: 1px solid var(--border);
    display: flex; justify-content: space-between;
    font-family: 'DM Mono', monospace; font-size: 11px; color: var(--muted); letter-spacing: 1px;
  }

  @media (max-width: 580px) {
    .stats { grid-template-columns: repeat(2, 1fr); }
    .stat:nth-child(4n) { border-right: 1px solid var(--border); }
    .stat:nth-child(2n) { border-right: none; }
    .price { font-size: 28px; } .sym { font-size: 32px; }
  }
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <div class="logo-row">
      <div class="logo-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="#00e5ff" stroke-width="1.5">
          <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
          <polyline points="16 7 22 7 22 13"/>
        </svg>
      </div>
      <div class="logo">STOCKWATCH</div>
    </div>
    <div class="tagline">实时行情 · Alpha Vantage API</div>
  </div>

  <div class="search-row">
    <div class="search-box">
      <span class="search-icon">$</span>
      <input id="inp" type="text" placeholder="输入股票代码，如 AAPL · TSLA · IBM"
             onkeydown="if(event.key==='Enter') go()">
    </div>
    <button class="btn-search" onclick="go()">查询</button>
  </div>

  <div class="chips">
    <span class="chip" onclick="q('IBM')">IBM ★demo可用</span>
    <span class="chip" onclick="q('AAPL')">AAPL</span>
    <span class="chip" onclick="q('MSFT')">MSFT</span>
    <span class="chip" onclick="q('TSLA')">TSLA</span>
    <span class="chip" onclick="q('NVDA')">NVDA</span>
    <span class="chip" onclick="q('GOOGL')">GOOGL</span>
    <span class="chip" onclick="q('AMZN')">AMZN</span>
    <span class="chip" onclick="q('META')">META</span>
  </div>

  <div id="out"></div>

  <footer>
    <span>Alpha Vantage · 免费额度 25次/分钟 · 500次/天</span>
    <span id="ts">—</span>
  </footer>
</div>

<script>
function q(s){ document.getElementById('inp').value=s; go(); }

function fmt(v, d=2){
  if(v===null||v===undefined||v===''||isNaN(v)) return '—';
  const n = parseFloat(v);
  if(Math.abs(n)>=1e12) return (n/1e12).toFixed(2)+'T';
  if(Math.abs(n)>=1e9)  return (n/1e9).toFixed(2)+'B';
  if(Math.abs(n)>=1e6)  return (n/1e6).toFixed(2)+'M';
  return n.toFixed(d);
}

function fmtP(v){
  if(!v||isNaN(v)) return '—';
  return parseFloat(v).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
}

async function go(){
  const sym = document.getElementById('inp').value.trim().toUpperCase();
  if(!sym) return;
  const out = document.getElementById('out');
  out.innerHTML = '<div class="loading">获取行情中<div class="bar-anim"></div></div>';

  try {
    const r = await fetch('/api/stock?symbol='+encodeURIComponent(sym));
    const d = await r.json();
    if(d.error){ out.innerHTML=`<div class="error">× ${d.error}</div>`; return; }

    const chg = parseFloat(d.change)||0;
    const dir = chg>=0 ? 'up' : 'down';
    const sign = chg>=0 ? '+' : '';

    out.innerHTML = `
    <div class="card">
      <div class="card-glow ${dir}"></div>
      <div class="card-top">
        <div>
          <div class="sym ${dir}">${d.symbol}</div>
          <div class="company">${d.name||'—'} &nbsp;·&nbsp; ${d.exchange||'—'}</div>
        </div>
        <div class="price-col">
          <div class="price ${dir}">${fmtP(d.price)} <span style="font-size:16px;color:var(--muted)">${d.currency||'USD'}</span></div>
          <span class="badge ${dir}">${sign}${fmtP(d.change)} (${sign}${fmt(d.change_pct)}%)</span>
        </div>
      </div>
      <div class="stats">
        <div class="stat"><div class="stat-label">今日开盘</div><div class="stat-val">${fmtP(d.open)}</div></div>
        <div class="stat"><div class="stat-label">昨日收盘</div><div class="stat-val">${fmtP(d.prev_close)}</div></div>
        <div class="stat"><div class="stat-label">今日最高</div><div class="stat-val">${fmtP(d.high)}</div></div>
        <div class="stat"><div class="stat-label">今日最低</div><div class="stat-val">${fmtP(d.low)}</div></div>
        <div class="stat"><div class="stat-label">成交量</div><div class="stat-val">${fmt(d.volume,0)}</div></div>
        <div class="stat"><div class="stat-label">52周最高</div><div class="stat-val">${fmtP(d.week52_high)}</div></div>
        <div class="stat"><div class="stat-label">52周最低</div><div class="stat-val">${fmtP(d.week52_low)}</div></div>
        <div class="stat"><div class="stat-label">市盈率 P/E</div><div class="stat-val">${fmt(d.pe_ratio)}</div></div>
        <div class="stat"><div class="stat-label">EPS</div><div class="stat-val">${fmt(d.eps)}</div></div>
        <div class="stat"><div class="stat-label">Beta</div><div class="stat-val">${fmt(d.beta)}</div></div>
        <div class="stat"><div class="stat-label">分析师目标价</div><div class="stat-val">${fmtP(d.target_price)}</div></div>
        <div class="stat"><div class="stat-label">分析师评级</div><div class="stat-val">${d.analyst_rating||'—'}</div></div>
      </div>
    </div>`;

    document.getElementById('ts').textContent = '更新于 ' + new Date().toLocaleTimeString('zh-CN');
  } catch(e) {
    out.innerHTML = `<div class="error">× 请求失败: ${e.message}</div>`;
  }
}
</script>
</body>
</html>'''


def fetch_alpha(function, symbol):
    params = {"function": function, "symbol": symbol, "apikey": API_KEY}
    url = "https://www.alphavantage.co/query?" + urllib.parse.urlencode(params)
    proxy = urllib.request.ProxyHandler({
        "http":  "http://127.0.0.1:7892",
        "https": "http://127.0.0.1:7892",
    })
    opener = urllib.request.build_opener(proxy)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with opener.open(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


class StockHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
            return

        if self.path.startswith('/api/stock'):
            from urllib.parse import urlparse, parse_qs
            sym = parse_qs(urlparse(self.path).query).get('symbol', [''])[0].strip().upper()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            if not sym:
                self.wfile.write(json.dumps({'error': '请输入股票代码'}).encode())
                return

            try:
                print(f"  → 查询: {sym}")

                # 实时报价
                quote_data = fetch_alpha("GLOBAL_QUOTE", sym)
                q = quote_data.get("Global Quote", {})

                if not q or not q.get("05. price"):
                    note = quote_data.get("Note") or quote_data.get("Information", "")
                    if note:
                        self.wfile.write(json.dumps({'error': f'API限制: {note[:120]}'}).encode())
                    else:
                        self.wfile.write(json.dumps({'error': f'未找到股票: {sym}'}).encode())
                    return

                price      = float(q.get("05. price", 0))
                open_      = float(q.get("02. open", 0))
                high       = float(q.get("03. high", 0))
                low        = float(q.get("04. low", 0))
                prev_close = float(q.get("08. previous close", 0))
                volume     = int(q.get("06. volume", 0))
                change     = float(q.get("09. change", 0))
                change_pct = q.get("10. change percent", "0%").replace("%", "")

                # 公司概览
                overview = {}
                try:
                    overview = fetch_alpha("OVERVIEW", sym)
                except Exception:
                    pass

                result = {
                    "symbol":         sym,
                    "name":           overview.get("Name", ""),
                    "exchange":       overview.get("Exchange", ""),
                    "currency":       overview.get("Currency", "USD"),
                    "price":          price,
                    "open":           open_,
                    "high":           high,
                    "low":            low,
                    "prev_close":     prev_close,
                    "volume":         volume,
                    "change":         change,
                    "change_pct":     float(change_pct) if change_pct else 0,
                    "week52_high":    overview.get("52WeekHigh"),
                    "week52_low":     overview.get("52WeekLow"),
                    "pe_ratio":       overview.get("TrailingPE"),
                    "eps":            overview.get("EPS"),
                    "beta":           overview.get("Beta"),
                    "target_price":   overview.get("AnalystTargetPrice"),
                    "analyst_rating": overview.get("AnalystRatingStrongBuy") and "Strong Buy",
                }
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))

            except Exception as e:
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
            return

        self.send_response(404)
        self.end_headers()


if __name__ == '__main__':
    PORT = 8080
    server = http.server.HTTPServer(('0.0.0.0', PORT), StockHandler)

    print("=" * 54)
    print("  📈  股票价格看板 · Alpha Vantage 版")
    print("=" * 54)
    print(f"  ✅  服务启动: http://localhost:{PORT}")
    print(f"  🔑  当前 Key : {API_KEY}")
    if API_KEY == "demo":
        print("  ⚠️   Demo Key 仅支持查询 IBM")
        print("  👉  免费申请: https://www.alphavantage.co/support/#api-key")
        print("      将代码第 16 行 API_KEY 改为你的真实 Key 即可")
    print(f"  ⏹   退出: Ctrl + C")
    print("=" * 54)

    threading.Timer(1.0, lambda: webbrowser.open(f'http://localhost:{PORT}')).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  服务已停止")
