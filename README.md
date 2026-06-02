# 闲鱼出海选品看板

这个仓库工作原理很简单，就是让ai分析需求，在去闲鱼对比价格，是否有套利空间，现在使用的电脑硬件，你可以可以根据自己行业修改ai提示词和网站相关设置。程序分为俩部分，前端负责显示给你看，后端是ai控制浏览器，收集数据。

---

## 项目思路

核心逻辑是三个条件叠加：

```
固件社区在讨论某个硬件（需求信号）
+
eBay / Amazon 上这个硬件稀缺或价格高（供给缺口）
+
闲鱼上有大量便宜货（货源充足）
= 值得操作的套利机会
```

目标买家是海外 DIY 玩家——会折腾 OpenWrt、Armbian、OPNsense 这类固件的人。他们对品牌不敏感，只看硬件能不能跑对应固件，愿意从个人卖家购买。

---

## 项目结构

```
xianyu/
├── index.html      # 前台看板页面
├── app.js          # 前台渲染逻辑
├── data.json       # 后台 AI 更新的数据文件
└── README.md       # 本文件
```

**前台只负责展示**，不做任何数据处理。所有数据由后台 AI 程序写入 `data.json`。

---

## data.json 数据结构

### meta（全局配置）

```json
{
  "meta": {
    "updated": "2026-06-02",
    "exchangeRate": 7.28,
    "shippingBase": 25
  }
}
```

| 字段 | 说明 |
|------|------|
| `updated` | 数据最后更新时间 |
| `exchangeRate` | 人民币兑美元汇率，影响利润计算 |
| `shippingBase` | 每单运费基准（元），利润拆解用 |

---

### products（选品列表）

每个产品对象的完整字段：

```json
{
  "id": "ax3000t",
  "name": "小米 AX3000T",
  "nameEn": "Xiaomi AX3000T (OpenWrt)",
  "dataUpdated": "2026-06-02",
  "category": "路由器",
  "chip": "MediaTek MT7981B",
  "firmware": "OpenWrt",
  "status": "推荐",
  "demandTrend": "稳定",
  "communityHotness": 5,
  "recommend": 4,
  "competition": "低"
}
```

**状态（status）枚举：**
- `强烈推荐` — 价差大、供货充足、竞争极低
- `推荐` — 条件良好，可以操作
- `谨慎` — 有一定风险，需注意
- `不推荐` — 暂时跳过

**需求趋势（demandTrend）枚举：**
- `急速上升` / `上升` / `稳定` / `下降`

---

#### xianyu（闲鱼供货数据）

```json
"xianyu": {
  "avgPrice": 70,
  "currentListings": 510,
  "recentSold": 140,
  "marketAvgPrice": 70,
  "supplyLevel": "充足",
  "aiRecommendations": [
    { "title": "小米AX3000T 无线路由器", "price": 68, "url": "https://..." }
  ]
}
```

| 字段 | 说明 |
|------|------|
| `avgPrice` | 收购价参考（元） |
| `currentListings` | 当前在售数量 |
| `recentSold` | 近7天成交数量 |
| `marketAvgPrice` | 市场均价 |
| `supplyLevel` | 供货水位：充足 / 一般 / 紧缺 |
| `aiRecommendations` | AI 从闲鱼找到的具体商品链接 |

---

#### overseas（海外市场数据）

```json
"overseas": {
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

`listings` 为 0 时前台会标注"竞争空白"。

---

#### selling（销售建议）

```json
"selling": {
  "normalUSD": [28, 32],
  "premiumUSD": [55, 65],
  "recommendedUSD": 58,
  "suggestedPlatforms": ["eBay UK", "eBay DE", "Reddit r/openwrt [WTS]"]
}
```

`recommendedUSD` 用于利润计算，`suggestedPlatforms` 显示在报告顶部。

---

#### communityData（社区热度数据）

```json
"communityData": [
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

`posts` / `stars` / `pageViews` 三选一填写，前台会自动判断展示方式。

---

#### report（AI 分析报告）

```json
"report": {
  "demandSignals": "需求信号分析文本...",
  "targetMarkets": "目标市场说明...",
  "competitionAnalysis": "竞争分析文本...",
  "profitLogic": "利润逻辑说明...",
  "risks": "风险提示..."
}
```

---

## 前台功能

**左侧产品列表：**
- 搜索（产品名、芯片、品类、固件）
- 按固件筛选
- 按推荐度 / 1台利润 / 社区热度排序
- 左侧色条指示推荐等级

**右侧产品报告：**
- 价格总览（闲鱼均价、海外参考价、建议卖价、利润、价差）
- 建议销售渠道
- 社区/论坛需求数据表
- 国外平台价格对比表（含竞争空白标注）
- 闲鱼供货分析 + AI 推荐商品直链
- 利润拆解（收购成本、运费、手续费、净利润、利润率）
- 需求信号、竞争分析、目标市场

---

## 后台 AI 工作流（待开发）

后台程序需要完成：

1. **扫描固件社区** — OpenWrt、Armbian、OPNsense 等论坛和 GitHub，识别高热度硬件
2. **查闲鱼供货** — 搜索对应硬件，抓取在售数量、价格区间、成交记录
3. **查海外价格** — eBay UK/DE、Amazon UK/DE 搜索，记录在售数量和价格
4. **验证套利空间** — 三个条件同时满足才写入 `products`
5. **更新 data.json** — 写入数据，更新 `meta.updated` 时间戳

前台刷新页面即可看到最新数据，无需其他操作。

---

## 目标市场

| 国家 | 优先级 | 原因 |
|------|--------|------|
| 🇬🇧 英国 | ⭐⭐⭐⭐⭐ | SBC / OpenWrt 文化浓厚 |
| 🇩🇪 德国 | ⭐⭐⭐⭐⭐ | 欧洲最大极客社区，溢价意愿高 |
| 🇫🇷 法国 | ⭐⭐⭐⭐ | 活跃 DIY 社区 |
| 🇵🇱 波兰/捷克 | ⭐⭐⭐ | 二手电子经销商活跃 |
| 🇺🇸 美国 | ❌ | 关税政策混乱，暂时跳过 |

---

## 主要销售渠道

- **eBay UK / DE** — 主力平台，支持个人卖家，买家习惯二手交易
- **Reddit [WTS]** — r/openwrt、r/homelab、r/selfhosted 的买卖版块，精准触达目标用户
- **Kleinanzeigen** — 德国本地二手平台，竞争少
- **Tindie** — 小众硬件平台，DIY 买家集中
