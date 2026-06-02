"""
write_product.py — 裁判专用写库脚本
直接读取 candidates.json，完成利润计算、准入判断、写库、更新 investigated.json、git push。
裁判只需要在 candidates.json 每个产品上补充一个 report 字段，然后运行：
    python db/write_product.py
report 字段格式：
    "report": {
        "demandSignals":      "需求信号描述，100字以内",
        "targetMarkets":      "目标市场描述，80字以内",
        "competitionAnalysis":"竞争分析，80字以内",
        "profitLogic":        "利润逻辑，引用计算数字，100字以内",
        "risks":              "2-3个主要风险"
    }
如果产品里没有 report 字段，脚本会自动生成一个基础版本。
"""
import sys
import json
import sqlite3
import os
from datetime import date, datetime
# ──────────────────────────────────────────────
# 路径和常量
# ──────────────────────────────────────────────
DB_PATH           = "db/data.db"
CANDIDATES_PATH   = "candidates.json"
INVESTIGATED_PATH = "logs/investigated.json"
PLATFORM_FEE_RATE = 0.13   # eBay 综合手续费约 13%
MIN_PROFIT_CNY    = 80     # 准入门槛：最低净利润（元）
MIN_PROFIT_RATE   = 0.30   # 准入门槛：最低利润率
MIN_PROFIT_ABS    = 200    # 高价品绝对利润门槛（元）：净利≥200可豁免利润率限制

# ──────────────────────────────────────────────
# 评分计算
# ──────────────────────────────────────────────
def calc_status(profit_cny, profit_rate):
    if profit_cny >= 300 and profit_rate >= 0.40: return "强烈推荐"
    if profit_cny >= 200 and profit_rate >= 0.30: return "强烈推荐"
    if profit_cny >= 200:                          return "推荐"       # 高绝对利润豁免利润率
    if profit_cny >= 120 and profit_rate >= 0.35: return "推荐"
    if profit_cny >= 80  and profit_rate >= 0.30: return "谨慎"
    return "不推荐"
def calc_competition(count):
    if count < 10:  return "极低"
    if count < 30:  return "低"
    if count < 80:  return "中"
    if count < 200: return "高"
    return "极高"
def calc_recommend(profit_rate, demand_score, competition, supply_level):
    base = 0.0
    if profit_rate >= 0.60:          base += 2.0
    elif profit_rate >= 0.40:        base += 1.5
    elif profit_rate >= 0.30:        base += 1.0
    if demand_score >= 4:            base += 1.5
    elif demand_score == 3:          base += 1.0
    if competition in ("极低","低"): base += 1.0
    elif competition == "中":        base += 0.5
    if supply_level == "充足":       base += 0.5
    return min(5, max(1, round(base)))
def calc_demand_trend(signal_date):
    if not signal_date:
        return "稳定"
    try:
        sig  = datetime.strptime(signal_date[:7], "%Y-%m").date()
        days = (date.today() - sig).days
        if days <= 30:  return "急速上升"
        if days <= 90:  return "上升"
        if days <= 180: return "稳定"
        return "下降"
    except Exception:
        return "稳定"

# ──────────────────────────────────────────────
# 衍生字段构造
# ──────────────────────────────────────────────
def build_selling(product, recommended_usd):
    ref = product["overseas"]["referenceUSD"]
    platforms = product["overseas"].get("platforms", [])
    top = sorted(
        [p for p in platforms if p.get("type") == "二手" and p.get("listings", 0) > 0],
        key=lambda p: p.get("listings", 0), reverse=True
    )
    suggested = [p["name"] for p in top[:3]] or ["eBay UK", "eBay DE"]
    return {
        "normalUSD":          [round(ref * 0.9, 2), round(ref * 1.1, 2)],
        "premiumUSD":         [round(ref * 1.3, 2), round(ref * 1.5, 2)],
        "recommendedUSD":     recommended_usd,
        "suggestedPlatforms": suggested,
    }
def build_community_data(product):
    links    = product.get("discovery_links", [])
    score    = product.get("demand_score", 3)
    keywords = []
    chip     = product.get("chip", "")
    firmware = product.get("firmware", "")
    if chip and chip != "unknown": keywords.append(chip)
    keywords += [f.strip() for f in firmware.split("/")][:2]
    def infer(url):
        if "reddit.com/r/" in url:
            sub = url.split("/r/")[1].split("/")[0]
            return f"Reddit r/{sub}", "General", "🌐 英语"
        if "openwrt.org"  in url: return "OpenWrt Forum",  "Hardware Questions", "🌐 英语"
        if "github.com"   in url: return "GitHub",         "Issues/Discussions", "🌐 英语"
        if "hackaday.com" in url: return "Hackaday",       "Projects",           "🌐 英语"
        if "right.com.cn" in url: return "恩山无线论坛",    "硬件讨论",            "🇨🇳 中文"
        return "海外极客社区", "General", "🌐 英语"
    result, seen = [], set()
    for url in links[:3]:
        p, sec, lang = infer(url)
        if p in seen: continue
        seen.add(p)
        result.append({"platform": p, "section": sec, "lang": lang, "url": url,
                        "posts": None, "threads": None, "stars": None, "pageViews": None,
                        "hotKeywords": keywords[:5], "lastActive": "本月", "hotness": score})
    if not result:
        result.append({"platform": "海外极客社区", "section": "General", "lang": "🌐 英语",
                        "url": links[0] if links else "", "posts": None, "threads": None,
                        "stars": None, "pageViews": None, "hotKeywords": keywords[:5],
                        "lastActive": "本月", "hotness": score})
    return result
def build_demand(product):
    play   = product.get("play_value", "")
    links  = product.get("discovery_links", [])
    kws    = ["OpenWrt","Armbian","Proxmox","TrueNAS","VPN","Docker",
              "Home Assistant","KODI","LineageOS","RetroArch","OPNsense"]
    uses   = [k for k in kws if k.lower() in play.lower()] or [play[:20] or "DIY改造"]
    chans  = []
    for url in links:
        if "reddit.com/r/" in url:
            chans.append("Reddit r/" + url.split("/r/")[1].split("/")[0])
        elif "openwrt.org"  in url: chans.append("OpenWrt Forum")
        elif "github.com"   in url: chans.append("GitHub")
        elif "hackaday.com" in url: chans.append("Hackaday")
    chans = list(dict.fromkeys(chans))
    return {
        "useCases": uses[:4],
        "channels": chans[:4],
        "links":    [{"label": f"信号来源 {i+1}", "url": u} for i, u in enumerate(links[:3])],
    }
def build_report_fallback(product, profit_cny, recommended_usd, competition):
    cost = product["xianyu"]["avgPrice"]
    cnt  = product["overseas"].get("competitorCount", 0)
    return {
        "demandSignals":      product.get("play_value", ""),
        "targetMarkets":      "海外 DIY 极客及 homelab 玩家",
        "competitionAnalysis": f"海外在售约 {cnt} 台，竞争程度{competition}",
        "profitLogic":        f"闲鱼收购约 {cost} 元，eBay 卖约 {recommended_usd} 美元，净利润约 {profit_cny:.0f} 元",
        "risks":              "货源供给波动；平台政策变化；人民币汇率波动",
    }

# ──────────────────────────────────────────────
# investigated.json 更新
# ──────────────────────────────────────────────
def update_investigated(products, added_ids):
    os.makedirs("logs", exist_ok=True)
    existing = []
    if os.path.exists(INVESTIGATED_PATH):
        try:
            with open(INVESTIGATED_PATH, encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []
    seen = {item["id"] for item in existing}
    for p in products:
        pid = p.get("id", "")
        if pid and pid not in seen:
            skip_reason = p.get("_skip_reason")
            # 判断淘汰类型：永久（无货源）还是临时（利润不足，市场可能变化）
            skip_type = None
            if skip_reason:
                if any(kw in skip_reason for kw in ["供货稀缺", "无货源", "无法货源"]):
                    skip_type = "permanent"   # 国内无货，永久排除
                elif any(kw in skip_reason for kw in ["利润率", "净利润", "无价格"]):
                    skip_type = "temporary"   # 利润问题，市场变化后可重新评估
                else:
                    skip_type = "permanent"
            existing.append({
                "id":                pid,
                "name":              p.get("name", ""),
                "name_en":           p.get("name_en", ""),
                "category":          p.get("category", ""),   # ← 品类配额统计依赖此字段
                "investigated_date": date.today().isoformat(),
                "result":            "written" if pid in added_ids else "skipped",
                "skip_reason":       skip_reason,
                "skip_type":         skip_type,  # permanent=永久黑名单 temporary=可重新评估
            })
    with open(INVESTIGATED_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    print(f"✅ investigated.json 已更新，共 {len(existing)} 条历史记录")

─────────────────────────────────────────────
# investigated.json 更新
# ──────────────────────────────────────────────
def update_investigated(products, added_ids):
    os.makedirs("logs", exist_ok=True)
    existing = []
    if os.path.exists(INVESTIGATED_PATH):
        try:
            with open(INVESTIGATED_PATH, encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []
    seen = {item["id"] for item in existing}
    for p in products:
        pid = p.get("id", "")
        if pid and pid not in seen:
            skip_reason = p.get("_skip_reason")
            # 判断淘汰类型：永久（无货源）还是临时（利润不足，市场可能变化）
            skip_type = None
            if skip_reason:
                if any(kw in skip_reason for kw in ["供货稀缺", "无货源", "无法货源"]):
                    skip_type = "permanent"   # 国内无货，永久排除
                elif any(kw in skip_reason for kw in ["利润率", "净利润", "无价格"]):
                    skip_type = "temporary"   # 利润问题，市场变化后可重新评估
                else:
                    skip_type = "permanent"
            existing.append({
                "id":                pid,
                "name":              p.get("name", ""),
                "name_en":           p.get("name_en", ""),
                "category":          p.get("category", ""),   # ← 品类配额统计依赖此字段
                "investigated_date": date.today().isoformat(),
                "result":            "written" if pid in added_ids else "skipped",
                "skip_reason":       skip_reason,
                "skip_type":         skip_type,  # permanent=永久黑名单 temporary=可重新评估
            })
    with open(INVESTIGATED_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    print(f"✅ investigated.json 已更新，共 {len(existing)} 条历史记录")

# ──────────────────────────────────────────────
# git push
# ──────────────────────────────────────────────
def git_push(added_names):
    if not added_names:
        print("⚠️  无新产品入库，跳过 git push")
        return
    msg = f"数据更新：新增{'、'.join(added_names)}等{len(added_names)}个产品"
    for cmd in [
        ["git", "add", "db/data.db", "logs/investigated.json"],
        ["git", "commit", "-m", msg],
        ["git", "push"],
    ]:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                print(f"⚠️  {' '.join(cmd)} 失败：{r.stderr.strip()}")
                print("   请手动执行 git push")
                return
        except FileNotFoundError:
            print("⚠️  找不到 git 命令，请手动执行：")
            print(f"   git add db/data.db logs/investigated.json")
            print(f"   git commit -m \"{msg}\"")
            print(f"   git push")
            return
    print(f"✅ git push 完成")

# ──────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────
def main():
    # 读 candidates.json
    if not os.path.exists(CANDIDATES_PATH):
        print(f"❌ 找不到 {CANDIDATES_PATH}，请先运行猎手生成候选清单")
        sys.exit(1)
    with open(CANDIDATES_PATH, encoding="utf-8") as f:
        products = json.load(f)
    print(f"\n📂 读取 candidates.json，共 {len(products)} 个候选\n")
    # 读 meta
    conn = sqlite3.connect(DB_PATH)
    meta = conn.execute("SELECT exchange_rate, shipping_base FROM meta").fetchone()
    if not meta:
        print("❌ 读取 meta 表失败")
        conn.close()
        sys.exit(1)
    exchange_rate     = meta[0]
    shipping_per_unit = meta[1] / 10
    print(f"   汇率 {exchange_rate}，单台运费 {shipping_per_unit:.1f} 元\n")
    added_ids, added_names, skip_reasons = [], [], {}
    for p in products:
        pid  = p.get("id", "unknown")
        name = p.get("name", pid)
        print(f"── {name} ({pid})")
        # 前序步骤已标记跳过
        if p.get("skip"):
            reason = p.get("skip_reason", "前序步骤已标记跳过")
            print(f"   ⏭  跳过：{reason}")
            skip_reasons[pid] = reason
            p["_skip_reason"] = reason
            continue
        # 检查必要字段
        if not p.get("xianyu") or not p.get("overseas"):
            reason = "缺少 xianyu 或 overseas 字段，调研未完成"
            print(f"   ⏭  跳过：{reason}")
            skip_reasons[pid] = reason
            p["_skip_reason"] = reason
            continue
        ref = p["overseas"].get("referenceUSD")
        if ref is None:
            reason = "海外无价格参考，无法定价"
            print(f"   ⏭  跳过：{reason}")
            skip_reasons[pid] = reason
            p["_skip_reason"] = reason
            continue
        # 最低可行售价检查：建议售价必须高于运费+最低手续费，否则买家没有购买动力
        # 假设国际运费约 $15，eBay 最低手续费 $0.30
        INTL_SHIPPING_USD = 15.0
        recommended_usd_pre = round(ref * 1.3, 2)
        if recommended_usd_pre < INTL_SHIPPING_USD + 5:
            reason = f"建议售价 ${recommended_usd_pre} 过低，低于国际运费 ${INTL_SHIPPING_USD}+，买家无购买动力"
            print(f"   ⏭  跳过：{reason}")
            skip_reasons[pid] = reason
            p["_skip_reason"] = reason
            continue
        # 利润计算
        recommended_usd = round(ref * 1.3, 2)
        sell_cny        = recommended_usd * exchange_rate
        cost_cny        = p["xianyu"]["avgPrice"]
        profit_cny      = sell_cny - cost_cny - shipping_per_unit - sell_cny * PLATFORM_FEE_RATE
        profit_rate     = profit_cny / cost_cny if cost_cny > 0 else 0
        supply_level    = p["xianyu"].get("supplyLevel", "稀缺")
        # 准入判断：净利润 >= MIN_PROFIT_CNY 且 利润率 >= 30%
        fails = []
        if profit_cny < MIN_PROFIT_CNY:
            fails.append(f"净利润 {profit_cny:.0f}元 < {MIN_PROFIT_CNY}元")
        if profit_rate < MIN_PROFIT_RATE:
            fails.append(f"利润率 {profit_rate:.1%} < {MIN_PROFIT_RATE:.0%}")
        if supply_level == "稀缺":
            fails.append("闲鱼供货稀缺")
        if fails:
            reason = "；".join(fails)
            print(f"   ❌ 不符合准入：{reason}")
            skip_reasons[pid] = reason
            p["_skip_reason"] = reason
            continue
        # 生成各字段
        competition  = calc_competition(p["overseas"].get("competitorCount", 0))
        status       = calc_status(profit_cny, profit_rate)
        trend        = calc_demand_trend(p.get("signal_date"))
        recommend    = calc_recommend(profit_rate, p.get("demand_score", 3), competition, supply_level)
        selling      = build_selling(p, recommended_usd)
        community    = p.get("community_data") or build_community_data(p)
        demand       = build_demand(p)
        report       = p.get("report") or build_report_fallback(p, profit_cny, recommended_usd, competition)
        # 写库
        try:
            conn.execute("""
                INSERT OR REPLACE INTO products (
                    id, name, name_en, category, chip, firmware,
                    status, demand_trend, community_hotness, recommend, competition, data_updated,
                    xianyu, community_data, overseas, selling, demand, report
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pid, p.get("name",""), p.get("name_en",""),
                p.get("category","其他"), p.get("chip","unknown"), p.get("firmware",""),
                status, trend, p.get("demand_score",3), recommend, competition,
                date.today().isoformat(),
                json.dumps(p["xianyu"],   ensure_ascii=False),
                json.dumps(community,     ensure_ascii=False),
                json.dumps(p["overseas"], ensure_ascii=False),
                json.dumps(selling,       ensure_ascii=False),
                json.dumps(demand,        ensure_ascii=False),
                json.dumps(report,        ensure_ascii=False),
            ))
            conn.commit()
            added_ids.append(pid)
            added_names.append(name)
            print(f"   ✅ 写入成功  利润 {profit_cny:.0f}元  利润率 {profit_rate:.1%}  {status}")
        except Exception as e:
            reason = f"数据库异常：{e}"
            print(f"   ❌ 写入失败：{e}")
            skip_reasons[pid] = reason
            p["_skip_reason"] = reason
    conn.close()
    # 汇总
    print(f"\n{'='*50}")
    print(f"新增 {len(added_ids)} 个 | 跳过 {len(skip_reasons)} 个")
    if added_ids:    print(f"新增：{', '.join(added_ids)}")
    if skip_reasons:
        print("跳过原因：")
        for pid, r in skip_reasons.items():
            print(f"  {pid}: {r}")
    # 更新 investigated.json
    update_investigated(products, set(added_ids))
    # 写执行日志
    os.makedirs("logs", exist_ok=True)
    log_path = f"logs/run_{date.today().isoformat()}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({
            "run_date":          date.today().isoformat(),
            "candidates_total":  len(products),
            "products_added":    added_ids,
            "skipped":           len(skip_reasons),
            "skip_reasons":      skip_reasons,
        }, f, ensure_ascii=False, indent=2)
    print(f"✅ 执行日志已写入 {log_path}")
    print(f"\n💡 数据库已更新，请手动执行 git push 同步到线上")

if __name__ == "__main__":
    main()
