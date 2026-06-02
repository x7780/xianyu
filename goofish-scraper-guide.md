# 闲鱼操作速查（AI 用）

搜索页：`https://www.goofish.com/search?q=关键词`

## 提取价格
```js
document.querySelectorAll('a[href*="/item"]').forEach(l => { const m = l.innerText.match(/¥\s*(\d+\.?\d*)/); if(m) prices.push(parseFloat(m[1])); });
```

## 翻页（不能用URL参数，必须点按钮）
```js
document.querySelectorAll('.search-pagination-page-box--AbqmJFFp').forEach(b => { if(b.textContent.trim()==='2') b.click(); });
```
每页点击后等 3 秒再抓数据。

## 注意
- class 带哈希后缀，闲鱼更新后可能失效，失效时用文字内容重新查找元素
- 操作间隔 3 秒，避免验证码
