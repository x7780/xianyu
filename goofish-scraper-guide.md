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

## 勾选"个人闲置"
```js
// 点击 checkbox 元素（不是 label），勾选后 class 会增加 search-checkbox-checked--xxx
document.querySelectorAll('.search-checkbox-label--yt8qOVYk').forEach(l => {
  if(l.textContent.trim()==='个人闲置') {
    l.parentElement.querySelector('[class*="search-checkbox--"]').click();
  }
});
```

## 新发布 → 选择7天内
```js
// 第一步：点击"新发布"展开下拉
document.querySelector('.search-select-title-container--PqkTXn91').click();
// 第二步：点击"7天内"（选项 class: search-select-item--H_AJBURX）
document.querySelectorAll('.search-select-item--H_AJBURX').forEach(i => {
  if(i.textContent.trim()==='7天内') i.click();
});
// 可选值：最新 / 1天内 / 3天内 / 7天内 / 14天内
```

## 注意
- class 带哈希后缀，闲鱼更新后可能失效，失效时用文字内容重新查找元素
- 操作间隔 3 秒，避免验证码
