import sqlite3, json
from datetime import date

today = date.today().isoformat()

product = {
    'id': 'redmi-ax6000',
    'name': 'Redmi AX6000',
    'name_en': 'Xiaomi Redmi Router AX6000',
    'category': '路由器',
    'chip': 'MediaTek MT7986A',
    'firmware': 'OpenWrt / ImmortalWrt',
    'demand_score': 4,
    'signal_date': '2026-04'
}

exchange_rate = 7.28
referenceUSD = 62.0
normalUSD = [round(referenceUSD * 0.9, 2), round(referenceUSD * 1.1, 2)]
premiumUSD = [round(referenceUSD * 1.3, 2), round(referenceUSD * 1.5, 2)]
recommendedUSD = round(premiumUSD[0], 2)
sell_cny = recommendedUSD * exchange_rate
cost_cny = 330.0
shipping_cny = 2.5
fee_cny = sell_cny * 0.13
profit_cny = round(sell_cny - cost_cny - shipping_cny - fee_cny, 2)
profit_rate = round(profit_cny / cost_cny, 4)

print(f"profit_cny={profit_cny}, profit_rate={profit_rate*100:.1f}%")

status = '推荐'
competition = '低'
demand_trend = '上升'
recommend = 4

xianyu = {
    'avgPrice': 330,
    'currentListings': 30,
    'recentSold': None,
    'marketAvgPrice': 330,
    'supplyLevel': '一般',
    'aiRecommendations': [
        {'title': '自用红米ax6000，95新，穿墙信号好，4天线', 'price': 310, 'url': 'https://www.goofish.com/item?id=1055524538948'},
        {'title': '红米AX6000路由器，WiFi6千兆款，RB06型号', 'price': 300, 'url': 'https://www.goofish.com/item?id=1034192123307'},
        {'title': '红米ax6000，WiFi6，已刷immo 23.05.6', 'price': 379, 'url': 'https://www.goofish.com/item?id=1053453898870'}
    ]
}

community_data = [
    {
        'platform': 'Reddit r/openwrt',
        'section': 'Hardware Questions',
        'lang': '🌐 英语',
        'url': 'https://redditrecs.com/wifi-router/model/xiaomi-redmi-ax6000/',
        'posts': None,
        'threads': None,
        'stars': None,
        'pageViews': None,
        'hotKeywords': ['Redmi AX6000', 'MT7986A', 'OpenWrt', 'WiFi6', 'ImmortalWrt'],
        'lastActive': '本月',
        'hotness': 4
    },
    {
        'platform': 'GitHub OpenWrt',
        'section': 'MediaTek DTS',
        'lang': '🌐 英语',
        'url': 'https://github.com/openwrt/openwrt/blob/main/target/linux/mediatek/dts/mt7986a-xiaomi-redmi-router-ax6000-ubootmod.dts',
        'posts': None,
        'threads': None,
        'stars': 246,
        'pageViews': None,
        'hotKeywords': ['MT7986A', 'uboot', 'OpenWrt mainline'],
        'lastActive': '本月',
        'hotness': 4
    }
]

overseas = {
    'platforms': [
        {
            'name': 'eBay UK',
            'flag': '🇬🇧',
            'type': '二手',
            'priceMin': 50,
            'priceMax': 86,
            'currency': 'USD',
            'listings': 10,
            'url': 'https://www.ebay.co.uk/sch/i.html?_nkw=Redmi+AX6000+MT7986+router'
        },
        {
            'name': 'eBay US',
            'flag': '🇺🇸',
            'type': '二手',
            'priceMin': 45,
            'priceMax': 80,
            'currency': 'USD',
            'listings': 4,
            'url': 'https://www.ebay.com/sch/i.html?_nkw=Redmi+AX6000+router'
        },
        {
            'name': 'AliExpress',
            'flag': '🌐',
            'type': '新品',
            'priceMin': 65,
            'priceMax': 85,
            'currency': 'USD',
            'listings': 15,
            'url': 'https://www.aliexpress.com/wholesale?SearchText=Redmi+AX6000'
        }
    ],
    'referenceUSD': 62,
    'competitorCount': 14,
    'note': 'eBay UK/US均有少量在售，价格45-86美元。二手竞争不激烈，机会不错'
}

selling = {
    'normalUSD': normalUSD,
    'premiumUSD': premiumUSD,
    'recommendedUSD': recommendedUSD,
    'suggestedPlatforms': ['eBay UK', 'eBay US', 'Reddit r/openwrt [WTS]']
}

demand = {
    'useCases': ['OpenWrt路由', 'VPN节点', 'WiFi6全屋覆盖', 'ImmortalWrt家庭网关'],
    'channels': ['Reddit r/openwrt', 'GitHub OpenWrt', 'OpenWrt Forum'],
    'links': [
        {'label': 'OpenWrt官方主线MT7986A支持', 'url': 'https://github.com/openwrt/openwrt/blob/main/target/linux/mediatek/dts/mt7986a-xiaomi-redmi-router-ax6000-ubootmod.dts'},
        {'label': 'Reddit社区推荐Redmi AX6000 OpenWrt', 'url': 'https://redditrecs.com/wifi-router/model/xiaomi-redmi-ax6000/'}
    ]
}

report = {
    'demandSignals': 'OpenWrt官方主线已收录MT7986A DTS文件，Reddit r/openwrt明确推荐Redmi AX6000为MT平台首选。GitHub多个固件项目近4月仍在更新，海外DIY玩家视其为性价比最高的WiFi6 OpenWrt路由选择。',
    'targetMarkets': '主要目标eBay UK（10条在售，50-86美元）和eBay US（4条，45-80美元）。欧洲DIY玩家对OpenWrt路由需求稳定，英国市场竞品少。',
    'competitionAnalysis': '海外二手市场共14个竞品（竞争等级低）。eBay UK上多为GL.iNet品牌混搭，真正的Redmi AX6000稀少，差异化明显。',
    'profitLogic': '闲鱼收购均价330元，溢价卖价80.6美元（约587元），扣除运费2.5元、eBay手续费76元，净利润约178元/台，利润率54%。',
    'risks': '1. 海外买家对国产品牌认知度低，需主动描述OpenWrt兼容性；2. 闲鱼供货仅30条需筛选成色；3. AX6000属3年旧机型，溢价空间可能随时间缩减'
}

conn = sqlite3.connect('db/data.db')
try:
    conn.execute('''
      INSERT INTO products (
        id, name, name_en, category, chip, firmware,
        status, demand_trend, community_hotness, recommend, competition, data_updated,
        xianyu, community_data, overseas, selling, demand, report
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        product['id'], product['name'], product['name_en'],
        product['category'], product['chip'], product['firmware'],
        status, demand_trend, product['demand_score'], recommend, competition,
        today,
        json.dumps(xianyu, ensure_ascii=False),
        json.dumps(community_data, ensure_ascii=False),
        json.dumps(overseas, ensure_ascii=False),
        json.dumps(selling, ensure_ascii=False),
        json.dumps(demand, ensure_ascii=False),
        json.dumps(report, ensure_ascii=False)
    ))
    conn.commit()
    print('写入成功：redmi-ax6000')
except Exception as e:
    print(f'错误：{e}')
finally:
    conn.close()
