# Ripple Desktop (Tauri 2)

> macOS / Windows / Linux 桌面端 — V2 完整实现路线图

## 当前状态(V1)

V1 阶段使用 **Streamlit Demo + 静态 Web 页面** 作为桌面入口替代,
保证大赛 Demo 可用性。Tauri 桌面端在复赛/决赛阶段完整实现。

## V2 完整规划

### 技术栈
- **Tauri 2.0** (Rust 后端 + Web 前端,体积小 10 倍 vs Electron)
- **React + TypeScript + Vite**(前端)
- **TanStack Query**(数据管理)
- **shadcn/ui**(UI 组件)
- **Tauri Plugin SQL**(本地 SQLite)
- **Tauri Plugin Global Shortcut**(全局快捷键)
- **Tauri Plugin Tray**(系统托盘)

### 核心功能

#### 1. 全局快捷键 - 灵感捕捉

```typescript
// src-tauri/src/main.rs
use tauri::{Manager, GlobalShortcutManager};

fn main() {
  tauri::Builder::default()
    .setup(|app| {
      let mut shortcut_manager = app.global_shortcut_manager();
      shortcut_manager.register("Cmd+Shift+I", move || {
        // 弹出灵感捕捉浮窗
        app.emit_all("inspiration-trigger", ()).ok();
      })?;
      Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
```

#### 2. macOS Menu Bar 图标

```rust
// src-tauri/src/menu_bar.rs
use tauri::SystemTray;

let tray = SystemTray::new()
    .with_tooltip("Ripple - 一键记录灵感")
    .with_icon_path("icons/menu-bar-icon.png");
```

#### 3. Windows System Tray

```rust
// 同 macOS,Tauri 跨平台抽象一致
```

#### 4. 本地 SQLite + Outbox 队列

```sql
-- ~/Library/Application Support/Ripple/local.db (macOS)
-- C:\Users\xxx\AppData\Roaming\Ripple\local.db (Windows)

CREATE TABLE inspirations (
  id INTEGER PRIMARY KEY,
  content TEXT NOT NULL,
  source TEXT,  -- desktop / mobile / shortcut
  created_at TEXT NOT NULL,
  synced INTEGER DEFAULT 0  -- 0=待同步, 1=已同步
);

CREATE TABLE outbox (
  id INTEGER PRIMARY KEY,
  endpoint TEXT NOT NULL,
  payload TEXT NOT NULL,
  retries INTEGER DEFAULT 0,
  created_at TEXT NOT NULL
);
```

### V2 开发路线

| Week | 里程碑 |
|------|--------|
| W1 | Tauri 基础项目 + 全局快捷键 + 浮窗输入 |
| W2 | 本地 SQLite + 灵感库 CRUD |
| W3 | 与 FastAPI 后端同步(Outbox 模式) |
| W4 | macOS Menu Bar 优化 + Windows Tray |
| W5 | Cmd+K 命令面板 + 多 Agent 触发 |
| W6 | 自动更新链路(electron-updater 等价) |
| W7 | macOS 公证 + Windows 签名 |
| W8 | 应用商店上架(可选) |

## 安装(开发版)

```bash
# 前置:安装 Rust + Node
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
nvm install 20

# 安装 Tauri CLI
cargo install tauri-cli --version "^2.0.0"

# 启动开发
cd apps/desktop
npm install
cargo tauri dev

# 打包发布
cargo tauri build
# 产物: src-tauri/target/release/bundle/
```

## 设计原则

1. **Local-First**: 灵感先存本地 SQLite,后台异步同步
2. **0 启动延迟**: 全局快捷键 → 浮窗 < 100ms
3. **离线可用**: 无网络也能记录灵感
4. **隐私优先**: API Key 用 macOS Keychain / Windows DPAPI 加密
