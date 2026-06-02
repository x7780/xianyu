# 数据库说明 — db/data.db

SQLite 数据库，供 AI 读写产品调研数据。网页通过 sql.js (WebAssembly) 直接在浏览器加载此文件。

---

## 表结构

### 1. meta（单行，全局配置）

```sql
SELECT * FROM meta;
```

| 字段 | 类型 | 说明 |
|------|------|------|
| exchange_rate | REAL | 人民币兑美元汇率，如 7.28 |
| shipping_base | REAL | 10台批量运费总额（元），单台 = shipping_base / 10 |
| updated | TEXT | 数据更新日期，格式 YYYY-MM-DD |

更新示例：
```python
conn.execute("UPDATE meta SET exchange_rate=?, updated=?", (7.30, '2026-06-03'))
```

---

### 2. products（产品主表）

```sql
SELECT id, name, status, recommend FROM products;
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PK | 唯一标识，如 `s905x3`、`ax3000t` |
| name | TEXT | 中文名，如 `S905X3 电视盒子` |
| name_en | TEXT | 英文名 |
| category | TEXT | 品类：TV盒子 / 路由器 / Mini PC / SBC / NAS |
| chip | TEXT | 芯片型号，如 `Amlogic S905X3` |
| firmware | TEXT | 固件：Armbian / OpenWrt / OPNsense / TrueNAS / Raspberry Pi OS |
| status | TEXT | **强烈推荐** / **推荐** / **谨慎** / **不推荐** |
| demand_trend | TEXT | **急速上升** / **上升** / **稳定** / **下降** |
| community_hotness | INTEGER | 社区热度 1–5 |
| recommend | INTEGER | 推荐度 1–5（用于排序） |
| competition | TEXT | **极低** / **低** / **中** / **高** / **极高** |
| data_updated | TEXT | 本产品数据更新日期 YYYY-MM-DD |
| xianyu | TEXT | **JSON**，见下方说明 |
| community_data | TEXT | **JSON**，见下方说明 |
| overseas | TEXT | **JSON**，见下方说明 |
| selling | TEXT | **JSON**，见下方说明 |
| demand | TEXT | **JSON**，见下方说明 |
| report | TEXT | **JSON**，见下方说明 |

#### xianyu 字段（JSON）

```json
{
  "avgPrice": 310,
  "currentListings": 180,
  "recentSold": 45,
  "marketAvgPrice": 310,
  "supplyLevel": "充足",
  "aiRecommendations": [
    {"title": "商品标题", "price": 299, "url": "https://..."}
  ]
}
```

- `supplyLevel`：充足 / 一般 / 稀缺

#### community_data 字段（JSON 数组）

```json
[
  {
    "platform": "OpenWrt Forum",
    "section": "Hardware Questions",
    "lang": "🌐 英语",
    "url": "https://...",
    "posts": 2790,
    "threads": 186,
    "stars": null,
    "pageViews": null,
    "hotKeywords": ["AX3000T", "MT7981B", "WiFi6"],
    "lastActive": "今天",
    "hotness": 5
  }
]
```

- `posts` / `threads` / `stars` / `pageViews` 填其中适用的，其余填 `null`
- `hotness`：1–5

#### overseas 字段（JSON）

```json
{
  "platforms": [
    {
      "name": "eBay UK",
      "flag": "🇬🇧",
      "type": "二手",
      "priceMin": 30,
      "priceMax": 45,
      "currency": "USD",
      "listings": 12,
      "url": "https://..."
    }
  ],
  "referenceUSD": 40,
  "competitorCount": 12,
  "note": "备注说明"
}
```

- `type`：新品 / 二手
- `priceMin` / `priceMax`：无在售时填 `null`

#### selling 字段（JSON）

```json
{
  "normalUSD": [28, 32],
  "premiumUSD": [55, 65],
  "recommendedUSD": 58,
  "suggestedPlatforms": ["eBay UK", "eBay DE", "Reddit r/openwrt [WTS]"]
}
```

- `recommendedUSD` 是利润计算的基准卖价，**必填**

#### demand 字段（JSON）

```json
{
  "useCases": ["OpenWrt路由", "VPN", "WiFi6升级"],
  "channels": ["Reddit r/openwrt", "OpenWrt论坛"],
  "links": [
    {"label": "OpenWrt论坛讨论", "url": "https://..."}
  ]
}
```

#### report 字段（JSON）

```json
{
  "demandSignals": "需求信号描述文字...",
  "targetMarkets": "目标市场描述...",
  "competitionAnalysis": "竞争分析描述...",
  "profitLogic": "利润逻辑描述...",
  "risks": "风险提示..."
}
```

---

### 3. execution（执行记录）

```sql
SELECT * FROM execution;
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PK | 如 `exec-001` |
| product_id | TEXT | 关联 products.id |
| product_name | TEXT | 产品名（冗余，方便查看） |
| status | TEXT | **在售** / **已售** / **收货中** |
| buy_price | REAL | 收购价（元） |
| buy_date | TEXT | 收购日期 YYYY-MM-DD |
| quantity | INTEGER | 收购数量 |
| sold_quantity | INTEGER | 已售数量 |
| sell_price_usd | REAL | 售价（美元） |
| platform | TEXT | 销售平台，如 `eBay UK` |
| listing_url | TEXT | 商品链接 |
| realized_profit_usd | REAL | 实际利润（美元） |
| notes | TEXT | 备注 |

---

## 常用操作示例

```python
import sqlite3, json

conn = sqlite3.connect('db/data.db')

# ── 新增产品 ──────────────────────────────
conn.execute("""
    INSERT INTO products (
        id, name, name_en, category, chip, firmware,
        status, demand_trend, community_hotness, recommend, competition, data_updated,
        xianyu, community_data, overseas, selling, demand, report
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    'product-id',
    '产品中文名',
    'Product English Name',
    '路由器',
    'MediaTek MT7981B',
    'OpenWrt',
    '推荐',
    '上升',
    4, 4, '低',
    '2026-06-03',
    json.dumps({...}, ensure_ascii=False),  # xianyu
    json.dumps([...], ensure_ascii=False),  # community_data
    json.dumps({...}, ensure_ascii=False),  # overseas
    json.dumps({...}, ensure_ascii=False),  # selling
    json.dumps({...}, ensure_ascii=False),  # demand
    json.dumps({...}, ensure_ascii=False),  # report
))

# ── 更新某个 JSON 字段中的单个值 ──────────
conn.execute("""
    UPDATE products
    SET xianyu = json_patch(xianyu, '{"avgPrice": 320}'),
        data_updated = '2026-06-03'
    WHERE id = 'product-id'
""")

# ── 更新整个 JSON 字段 ────────────────────
conn.execute(
    "UPDATE products SET xianyu = ? WHERE id = ?",
    (json.dumps({...}, ensure_ascii=False), 'product-id')
)

# ── 更新 meta ────────────────────────────
conn.execute("UPDATE meta SET exchange_rate = ?, updated = ?", (7.30, '2026-06-03'))

# ── 新增执行记录 ──────────────────────────
conn.execute("""
    INSERT INTO execution (
        id, product_id, product_name, status,
        buy_price, buy_date, quantity, sold_quantity,
        sell_price_usd, platform, listing_url, realized_profit_usd, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", ('exec-004', 'product-id', '产品名', '收货中',
      310, '2026-06-03', 2, 0, 78, 'eBay UK', '', 0, ''))

conn.commit()
conn.close()
```

---

## 注意事项

- 所有 JSON 字段写入时必须用 `json.dumps(..., ensure_ascii=False)`，确保中文正常存储
- `status` 字段的值影响网页左侧列表的颜色标记，必须严格使用规定的枚举值
- `selling.recommendedUSD` 是利润计算的关键字段，不能为空
- 修改完 `db/data.db` 后执行 `git add db/data.db && git commit -m "数据更新" && git push`，GitHub Actions 自动部署
