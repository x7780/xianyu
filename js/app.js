// ══════════════════════════════════════════
// 全局状态
// ══════════════════════════════════════════
let D = null;
let activeFirmware = 'all';
let activeSort = 'recommend';
let activeSearch = '';

// ══════════════════════════════════════════
// Helper 函数
// ══════════════════════════════════════════

function profit10est(p) {
  const fx = D.meta.exchangeRate;
  const buyUSD = p.xianyu.avgPrice / fx;
  const ship = D.meta.shippingBase / 10;
  const sell = p.selling.recommendedUSD;
  return Math.round((sell - buyUSD - ship) * 10);
}

function trendBadge(t) {
  if (t === '急速上升') return `<span class="trend-badge fast">🚀 急速上升</span>`;
  if (t === '上升')     return `<span class="trend-badge up">↑ 上升</span>`;
  if (t === '稳定')     return `<span class="trend-badge stable">→ 稳定</span>`;
  return `<span class="trend-badge down">↓ 下降</span>`;
}

function hotDots(n) {
  let h = '<span class="hotdots">';
  for (let i = 1; i <= 5; i++) h += `<span class="hotdot ${i <= n ? 'on' : ''}"></span>`;
  return h + '</span>';
}

// ══════════════════════════════════════════
// 加载数据（SQLite via sql.js）
// ══════════════════════════════════════════
initSqlJs({ locateFile: () => 'js/sql-wasm.wasm' }).then(SQL => {
  return fetch('db/data.db')
    .then(r => r.arrayBuffer())
    .then(buf => {
      const db = new SQL.Database(new Uint8Array(buf));

      // 读取 meta
      const metaRow = db.exec('SELECT exchange_rate, shipping_base, updated FROM meta')[0].values[0];
      const meta = {
        exchangeRate: metaRow[0],
        shippingBase: metaRow[1],
        updated:      metaRow[2]
      };

      // 读取 products，JSON字段直接 parse 还原成对象
      const prodRes = db.exec(`
        SELECT id, name, name_en, category, chip, firmware,
               status, demand_trend, community_hotness, recommend, competition, data_updated,
               xianyu, community_data, overseas, selling, demand, report
        FROM products
      `);
      const products = (prodRes[0]?.values || []).map(r => ({
        id:               r[0],
        name:             r[1],
        nameEn:           r[2],
        category:         r[3],
        chip:             r[4],
        firmware:         r[5],
        status:           r[6],
        demandTrend:      r[7],
        communityHotness: r[8],
        recommend:        r[9],
        competition:      r[10],
        dataUpdated:      r[11],
        xianyu:           JSON.parse(r[12]),
        communityData:    JSON.parse(r[13]),
        overseas:         JSON.parse(r[14]),
        selling:          JSON.parse(r[15]),
        demand:           JSON.parse(r[16]),
        report:           JSON.parse(r[17]),
      }));

      db.close();

      // 组装成和原来 data.json 完全一致的结构，其余代码零改动
      D = { meta, products };

      const metaStr = `更新：${meta.updated}  ·  汇率 $1 = ¥${meta.exchangeRate}`;
      document.getElementById('top-meta').textContent = metaStr;
      const footerMeta = document.getElementById('footer-meta');
      if (footerMeta) footerMeta.textContent = metaStr;
      renderToolbar();
      renderProductList();
      if (products.length > 0) showReport(products[0].id);
    });
}).catch(err => {
  console.error('数据库加载失败', err);
  document.getElementById('report-panel').innerHTML =
    `<div class="report-empty" style="color:var(--red)">⚠️ 数据库加载失败：${err.message}</div>`;
});

// ══════════════════════════════════════════
// 工具栏（筛选 + 排序）
// ══════════════════════════════════════════
function renderToolbar() {
  const fws = ['all', ...new Set(D.products.map(p => p.firmware))];
  let html = '';

  html += `<div style="position:relative;width:100%;margin-bottom:6px">
    <span style="position:absolute;left:9px;top:50%;transform:translateY(-50%);color:var(--text3);font-size:13px;pointer-events:none">🔍</span>
    <input id="search-input" type="text" placeholder="搜索产品名、芯片、品类…" value="${activeSearch}"
      style="width:100%;background:var(--bg3);border:1px solid var(--border);border-radius:6px;padding:6px 10px 6px 30px;color:var(--text);font-size:13px;outline:none;"
      onfocus="this.style.borderColor='var(--blue)'" onblur="this.style.borderColor='var(--border)'">
    ${activeSearch ? `<button onclick="clearSearch()" style="position:absolute;right:8px;top:50%;transform:translateY(-50%);background:none;border:none;color:var(--text3);cursor:pointer;font-size:14px;line-height:1">✕</button>` : ''}
  </div>`;

  html += `<div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;width:100%;margin-top:2px">`;
  html += `<span style="font-size:11px;color:var(--text3);flex-shrink:0">固件：</span>`;
  html += fws.map(f => `<button class="pill ${f === activeFirmware ? 'active' : ''}" data-fw="${f}">${f === 'all' ? '全部' : f}</button>`).join('');
  html += `</div>`;

  html += `<div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;width:100%;margin-top:2px">`;
  html += `<span style="font-size:11px;color:var(--text3);flex-shrink:0">排序：</span>`;
  [['recommend', '推荐度'], ['profit', '1台利润'], ['hotness', '社区热度']].forEach(([k, l]) => {
    html += `<button class="pill ${activeSort === k ? 'active' : ''}" data-sort="${k}">${l}</button>`;
  });
  html += `</div>`;

  document.getElementById('toolbar').innerHTML = html;

  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.addEventListener('input', e => {
      activeSearch = e.target.value.trim().toLowerCase();
      renderProductList();
      const clearBtn = document.querySelector('#search-input + button');
      if (activeSearch && !clearBtn) renderToolbar();
      if (!activeSearch && clearBtn) clearBtn.remove();
    });
  }

  document.querySelectorAll('[data-fw]').forEach(b => b.addEventListener('click', () => {
    activeFirmware = b.dataset.fw;
    document.querySelectorAll('[data-fw]').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    renderProductList();
  }));

  document.querySelectorAll('[data-sort]').forEach(b => b.addEventListener('click', () => {
    activeSort = b.dataset.sort;
    document.querySelectorAll('[data-sort]').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    renderProductList();
  }));
}

function clearSearch() {
  activeSearch = '';
  renderToolbar();
  renderProductList();
  document.getElementById('search-input')?.focus();
}

// ══════════════════════════════════════════
// 产品列表（左面板）
// ══════════════════════════════════════════
function renderProductList() {
  let prods = D.products.filter(p => {
    const matchFw  = activeFirmware === 'all' || p.firmware === activeFirmware;
    const matchSrc = !activeSearch ||
      p.name.toLowerCase().includes(activeSearch) ||
      (p.nameEn || '').toLowerCase().includes(activeSearch) ||
      p.chip.toLowerCase().includes(activeSearch) ||
      p.category.toLowerCase().includes(activeSearch) ||
      (p.firmware || '').toLowerCase().includes(activeSearch) ||
      (p.status || '').toLowerCase().includes(activeSearch);
    return matchFw && matchSrc;
  });

  prods = prods.slice().sort((a, b) => {
    if (activeSort === 'recommend') return b.recommend - a.recommend;
    if (activeSort === 'profit')    return profit10est(b) - profit10est(a);
    if (activeSort === 'hotness')   return b.communityHotness - a.communityHotness;
    return 0;
  });

  if (prods.length === 0) {
    document.getElementById('product-list').innerHTML =
      `<div style="text-align:center;padding:32px 12px;color:var(--text3);font-size:13px">
        😶 没有匹配的产品<br>
        <button onclick="clearSearch()" style="margin-top:10px;padding:4px 14px;border-radius:16px;border:1px solid var(--border);background:var(--bg2);color:var(--text2);cursor:pointer;font-size:12px">清除搜索</button>
      </div>`;
    return;
  }

  const countEl = document.getElementById('list-count');
  if (countEl) {
    const total = D.products.length;
    countEl.textContent = prods.length < total ? `${prods.length} / ${total} 个产品` : `${total} 个产品`;
    countEl.style.display = '';
  }

  document.getElementById('product-list').innerHTML = prods.map(p => {
    const p10 = profit10est(p);
    const hl = (str) => {
      if (!activeSearch) return str;
      const re = new RegExp(`(${activeSearch.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
      return String(str).replace(re, `<mark style="background:#2d3f1a;color:#7ee787;border-radius:2px;padding:0 1px">$1</mark>`);
    };
    return `<div class="prow s-${p.status}" data-id="${p.id}" onclick="showReport('${p.id}')">
      <div class="prow-top">
        <div class="prow-name">${hl(p.name)}&ensp;<span class="sbadge s-${p.status}" style="font-size:10px;padding:1px 6px;vertical-align:middle">${p.status}</span></div>
        ${p.dataUpdated ? `<span class="prow-trend" style="flex-shrink:0;margin-left:8px">${p.dataUpdated}</span>` : ''}
      </div>
      <div class="prow-nums">
        <span class="prow-chip" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0;flex-shrink:1">🔧 ${hl(p.chip)}</span>
        <span style="color:var(--border);flex-shrink:0">·</span>
        <span class="prow-buy" style="flex-shrink:0">¥${p.xianyu.avgPrice}</span>
        <span class="prow-profit" style="flex-shrink:0">$${p10}</span>
        <span style="flex-shrink:0">${trendBadge(p.demandTrend)}</span>
      </div>
    </div>`;
  }).join('');
}

// ══════════════════════════════════════════
// 产品报告面板（右面板）
// ══════════════════════════════════════════
function showReport(id) {
  const p = D.products.find(x => x.id === id);
  if (!p) return;
  const rp = document.getElementById('report-panel');
  if (rp) rp.style.visibility = '';
  document.querySelectorAll('.prow').forEach(r => r.classList.toggle('active', r.dataset.id === id));

  const fx  = D.meta.exchangeRate;
  const p10 = profit10est(p);
  const spread = p.overseas.referenceUSD
    ? '+$' + (p.overseas.referenceUSD - p.xianyu.avgPrice / fx).toFixed(0)
    : '—';

  const commRows = (p.communityData || []).map(c => {
    let countStr = '—', countType = '';
    if (c.stars) {
      countStr = `<strong style="color:var(--yellow)">${c.stars.toLocaleString()}</strong>`;
      countType = 'Stars';
    } else if (c.pageViews) {
      countStr = `<strong>${c.pageViews.toLocaleString()}</strong>`;
      countType = '页面浏览';
    } else if (c.posts) {
      countStr = `<strong class="${c.posts > 1000 ? 'comm-num big' : ''}">${c.posts.toLocaleString()}</strong>`;
      countType = '回复数';
      if (c.threads) {
        countStr += ` <span style="color:var(--text3);font-size:11px">/ ${c.threads} 帖</span>`;
        countType = '回复 / 帖子';
      }
    }
    const kws = (c.hotKeywords || []).map(k => `<span class="kw">${k}</span>`).join('');
    return `<tr>
      <td style="max-width:160px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
        <a class="comm-link" href="${c.url}" target="_blank">${c.platform}</a>
        ${c.section ? `<br><small style="color:var(--text3)">${c.section}</small>` : ''}</td>
      <td style="white-space:nowrap;font-size:11px;color:var(--text2)">${c.lang || '—'}</td>
      <td>${countStr}<br><span style="font-size:10px;color:var(--text3)">${countType}</span></td>
      <td><div class="comm-keywords">${kws}</div></td>
      <td>${hotDots(c.hotness)}</td>
      <td style="color:var(--text3);font-size:11px;white-space:nowrap">${c.lastActive}</td>
    </tr>`;
  }).join('');

  const xyAvgUSD  = p.xianyu.avgPrice ? (p.xianyu.avgPrice / fx) : null;
  const priceRows = (p.overseas.platforms || []).map(pl => {
    const hasPrice     = pl.priceMin !== null;
    const priceStr     = hasPrice ? `$${pl.priceMin}–${pl.priceMax}` : '无在售';
    const spreadVal    = hasPrice ? (pl.priceMin - p.xianyu.avgPrice / fx) : null;
    const spreadStr    = spreadVal !== null ? `${spreadVal >= 0 ? '+' : ''}$${spreadVal.toFixed(0)}` : '—';
    const spreadCls    = spreadVal !== null ? (spreadVal > 30 ? 'pos' : spreadVal > 0 ? '' : 'neg') : '';
    const avgSpreadVal = (hasPrice && xyAvgUSD) ? (pl.priceMin - xyAvgUSD) : null;
    const avgSpreadStr = avgSpreadVal !== null ? `${avgSpreadVal >= 0 ? '+' : ''}$${avgSpreadVal.toFixed(0)}` : '—';
    const avgSpreadCls = avgSpreadVal !== null ? (avgSpreadVal > 30 ? 'pos' : avgSpreadVal > 0 ? '' : 'neg') : '';
    const listCls = pl.listings === 0 ? 'zero' : pl.listings < 10 ? 'few' : 'many';
    const listStr = pl.listings === 0 ? '0条 🎯竞争空白' : `${pl.listings}条在售`;
    return `<tr>
      <td>${pl.flag} <strong style="font-size:12px">${pl.name}</strong></td>
      <td><span class="pt-type ${pl.type === '新品' ? 'new' : 'used'}">${pl.type}</span></td>
      <td class="pt-price">${priceStr}</td>
      <td style="white-space:nowrap;font-size:11px;color:var(--orange)">${p.xianyu.avgPrice ? '¥' + p.xianyu.avgPrice : '—'}</td>
      <td class="pt-spread ${spreadCls}">${spreadStr}</td>
      <td class="pt-spread ${avgSpreadCls}">${avgSpreadStr}</td>
      <td class="pt-listings ${listCls}">${listStr}</td>
      <td><a class="pt-link" href="${pl.url}" target="_blank">查看 →</a></td>
    </tr>`;
  }).join('');

  const shipUnit   = D.meta.shippingBase / 10;
  const buyUSDNum  = p.xianyu.avgPrice / fx;
  const sellUSD    = p.selling.recommendedUSD;
  const feeRate    = 0.13;
  const feeUSD     = sellUSD * feeRate;
  const profitUnit = sellUSD - buyUSDNum - shipUnit - feeUSD;
  const profitPct  = ((profitUnit / sellUSD) * 100).toFixed(0);
  const barW       = Math.min(Math.max((profitUnit / sellUSD) * 100, 0), 100).toFixed(0);
  const suggestedPlatforms = (p.selling.suggestedPlatforms || []).map(s => `<span class="sc-tag">${s}</span>`).join('');

  document.getElementById('report-panel').innerHTML = `
  <div class="rpt-header">
    <div class="rpt-title-row">
      <div>
        <div class="rpt-title">
          ${p.name}
          ${p.firmware ? `<span class="fw-badge" style="font-size:13px;vertical-align:middle;margin-left:8px">${p.firmware}</span>` : ''}
          ${trendBadge(p.demandTrend)}
        </div>
        <div class="rpt-chip">🔧 ${p.chip} &nbsp;·&nbsp; ${p.category} &nbsp;·&nbsp; <span style="color:var(--text3)">${p.nameEn}</span>${p.dataUpdated ? `&nbsp;·&nbsp; 🕐 ${p.dataUpdated}` : ''}</div>
      </div>
      <div class="rpt-badges">
        <span class="sbadge s-${p.status}">${p.status}</span>
        <span class="cbadge ${p.competition}">竞争${p.competition}</span>
      </div>
    </div>
    <div class="rpt-prices">
      <div class="rpbox xianyu-buy"><div class="rl">闲鱼市场均价</div><div class="rv">¥${p.xianyu.avgPrice}</div></div>
      <div class="rpbox overseas-ref"><div class="rl">海外参考价</div><div class="rv">${p.overseas.referenceUSD ? '$' + p.overseas.referenceUSD : '—'}</div></div>
      <div class="rpbox sell-rec"><div class="rl">建议卖价</div><div class="rv">$${p.selling.normalUSD[0]}–${p.selling.normalUSD[1]}</div></div>
      <div class="rpbox profit-est"><div class="rl">1台利润</div><div class="rv">$${p10}</div></div>
      <div class="rpbox spread"><div class="rl">价差</div><div class="rv">${spread}</div></div>
    </div>
    ${suggestedPlatforms ? `<div class="rpt-channels">
      <span style="font-size:11px;color:var(--text3);flex-shrink:0">建议销售渠道：</span>
      <div class="sell-channels">${suggestedPlatforms}</div>
    </div>` : ''}
  </div>

  <div class="rpt-body">
    <div class="rpt-section full">
      <div class="rs-title"><span class="rs-icon">🌐</span> 社区/论坛需求数据</div>
      <div style="overflow-x:auto">
        <table class="comm-table">
          <thead><tr><th>平台/社区</th><th>语言/国家</th><th>数据量</th><th>热门关键词</th><th>热度</th><th>最后活跃</th></tr></thead>
          <tbody>${commRows}</tbody>
        </table>
      </div>
    </div>

    <div class="rpt-section full">
      <div class="rs-title"><span class="rs-icon">💱</span> 国外平台价格（新品/二手）</div>
      <div style="overflow-x:auto">
        <table class="price-table">
          <thead><tr><th>平台</th><th>类型</th><th>价格区间</th><th>闲鱼均价</th><th>vs收购价差</th><th>vs均价差</th><th>在售数量</th><th>链接</th></tr></thead>
          <tbody>${priceRows}</tbody>
        </table>
      </div>
    </div>

    <div class="rpt-section">
      <div class="rs-title"><span class="rs-icon">🐟</span> 闲鱼供货分析</div>
      <div class="xianyu-stats">
        <div class="xy-box"><div class="xl">在售商品数量</div><div class="xv ${p.xianyu.currentListings > 100 ? 'good' : 'warn'}">${p.xianyu.currentListings}</div></div>
        <div class="xy-box"><div class="xl">近7天成交</div><div class="xv">${p.xianyu.recentSold} 件</div></div>
        <div class="xy-box"><div class="xl">市场均价</div><div class="xv" style="color:var(--orange)">¥${p.xianyu.marketAvgPrice}</div></div>
      </div>
      ${p.xianyu.aiRecommendations && p.xianyu.aiRecommendations.length ? `
      <div style="margin-top:12px;padding-top:10px;border-top:1px solid var(--border);display:flex;flex-direction:column;gap:6px">
        ${p.xianyu.aiRecommendations.map(rec => `
        <a href="${rec.url}" target="_blank" style="display:flex;justify-content:space-between;align-items:center;padding:7px 10px;background:var(--bg3);border-radius:6px;border:1px solid var(--border);text-decoration:none;transition:border-color .15s" onmouseover="this.style.borderColor='var(--blue)'" onmouseout="this.style.borderColor='var(--border)'">
          <span style="font-size:12px;color:var(--text);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:180px">${rec.title}</span>
          <span style="font-size:13px;font-weight:700;color:var(--orange);margin-left:10px;flex-shrink:0">¥${rec.price}</span>
          <span style="font-size:11px;color:var(--blue);margin-left:8px;flex-shrink:0">查看 →</span>
        </a>`).join('')}
      </div>` : ''}
    </div>

    <div class="rpt-section">
      <div class="rs-title"><span class="rs-icon">📊</span> 利润拆解（单台估算）</div>
      <div class="profit-breakdown">
        <div class="pbl"><span class="plbl">收购成本</span><span class="pamnt" style="color:var(--orange)">¥${p.xianyu.avgPrice} ($${buyUSDNum.toFixed(0)})</span></div>
        <div class="pbl"><span class="plbl">运费（分摊单台）</span><span class="pamnt" style="color:var(--text2)">$${shipUnit.toFixed(1)}</span></div>
        <div class="pbl"><span class="plbl">平台手续费（eBay ~13%）</span><span class="pamnt" style="color:var(--red)">−$${feeUSD.toFixed(1)}</span></div>
        <div class="pbl total"><span class="plbl">总成本</span><span class="pamnt">$${(buyUSDNum + shipUnit + feeUSD).toFixed(1)}</span></div>
        <div class="pbl"><span class="plbl">建议卖价</span><span class="pamnt" style="color:var(--green)">$${sellUSD}</span></div>
        <div class="pbl profit-line"><span class="plbl">单台净利润</span><span class="pamnt">$${profitUnit.toFixed(1)} (${profitPct}%)</span></div>
      </div>
      <div class="profit-bar-wrap">
        <div class="pb-labels"><span>成本 ${100 - parseInt(profitPct)}%</span><span>利润 ${profitPct}%</span></div>
        <div class="pb-bg"><div class="pb-fill" style="width:${barW}%"></div></div>
      </div>
    </div>

    <div class="rpt-section">
      <div class="rs-title"><span class="rs-icon">📡</span> 需求信号</div>
      <div class="signal-box">${p.report.demandSignals}</div>
      <div class="tags" style="margin-top:10px">${p.demand.useCases.map(t => `<span class="tag">${t}</span>`).join('')}</div>
    </div>

    <div class="rpt-section half">
      <div class="rs-title"><span class="rs-icon">🏁</span> 竞争分析</div>
      <div class="signal-box">${p.report.competitionAnalysis}</div>
    </div>

    <div class="rpt-section">
      <div class="rs-title"><span class="rs-icon">🌍</span> 目标市场</div>
      <div class="signal-box">${p.report.targetMarkets}</div>
    </div>
  </div>`;
}
