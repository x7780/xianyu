# Playwright MCP 配置记录

## 目标
让 Kiro 能直接控制本机 Chrome 浏览器，通过 MCP 协议操作网页。

---

## 环境
- OS: Windows
- Chrome 路径: `D:\Program Files (x86)\Google\Chrome\Application\chrome.exe`
- v2rayN 路径: `D:\Program Files\v2rayn`
- Node.js: v20+

---

## 第一步：安装 playwright-mcp

```bash
npm install -g @playwright/mcp@0.0.75
```

验证安装：
```bash
where playwright-mcp
# 应该输出 C:\Users\Administrator\AppData\Roaming\npm\playwright-mcp
```

---

## 第二步：设置 PowerShell 执行策略

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
```

不设置的话 playwright-mcp.ps1 会被拒绝运行。

---

## 第三步：安装 Chrome 插件

Chrome 商店搜索安装：**Playwright MCP Bridge**
- 插件 ID: `mmlmfjhmonkocbjadbfplnigmagldckm`
- 安装后打开插件页面，记录显示的 `PLAYWRIGHT_MCP_EXTENSION_TOKEN`

**注意：每次重装插件 token 会变，需要更新 mcp.json**

---

## 第四步：配置 Kiro MCP

工作区配置文件路径：`{workspace}\.kiro\settings\mcp.json`

```json
{
  "mcpServers": {
    "playwright": {
      "command": "playwright-mcp",
      "args": [
        "--extension",
        "--executable-path",
        "D:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        "--proxy-bypass",
        "localhost,127.0.0.1,<-loopback>"
      ],
      "env": {
        "PLAYWRIGHT_MCP_EXTENSION_TOKEN": "从插件页面复制token填这里"
      },
      "disabled": false,
      "autoApprove": [
        "browser_navigate",
        "browser_snapshot",
        "browser_click",
        "browser_type",
        "browser_take_screenshot"
      ]
    }
  }
}
```

---

## 第五步：v2rayN 路由配置（关键）

**必须关闭 Tun 模式**，只用系统代理 + 绕过大陆模式。
Tun 模式会拦截 playwright-mcp 和 Chrome 插件之间的本地 WebSocket 通信，导致 "Failed to connect to MCP relay: WebSocket error"。

路由规则集用 **V4-绕过大陆(Whitelist)**，额外添加一条规则：

| 字段 | 值 |
|------|---|
| 别名 | 代理Kiro |
| outboundTag | proxy |
| Domain | amazonaws.com / anthropic.com / kiro.dev / github.com / copilot.github.com |
| 进程(Tun模式) | Kiro.exe / Kiro Helper.exe |

"绕过局域网IP"规则里确保有：
- Domain: `localhost`
- IP: `geoip:private` / `127.0.0.1/8` / `::1/128`

**底部状态栏设置：**
- Tun 开关：**关闭**
- 系统代理：**自动配置系统代理**
- 路由：**V4-绕过大陆(Whitelist)**

---

## 第六步：启动流程

1. 启动 v2rayN（绕过大陆模式，不开 Tun）
2. 打开 Chrome，登录闲鱼
3. 打开 Kiro，MCP SERVERS 里 playwright 显示绿色 Connected
4. Chrome 插件显示 "1 client connected"

---

## 常见问题

### MCP 绿色但插件显示 "No clients connected"
→ token 变了，更新 mcp.json 里的 token，重启 MCP server

### "Failed to connect to MCP relay: WebSocket error"
→ Tun 模式开着，关掉 Tun

### "MCP error -32000: Connection closed"
→ mcp.json 参数有误（比如 --port 和 --extension 不能同时用）

### playwright-mcp 无法运行（脚本被禁止）
→ 执行 `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force`

### Kiro 连不上（绕过大陆模式下）
→ v2rayN 路由里"代理Kiro"规则没生效，检查规则顺序是否在 direct 规则前面
