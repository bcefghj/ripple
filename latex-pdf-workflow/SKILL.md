---
name: latex-pdf-workflow
description: 生成中文 LaTeX 技术/比赛 PDF 的完整工作流，包括安装 tectonic、模板选型、中文排版、TikZ 绘图、表格防溢出、常见编译错误修复。当用户需要写 LaTeX、编译 PDF、制作技术白皮书/比赛文档时使用。
---

# LaTeX PDF 完整工作流（中文技术文档）

适用场景：比赛材料、技术白皮书、产品报告；中文 + 英文混排；需要 TikZ 图表。

## 快速参考

- 编译器：**tectonic**（一次性安装，自动下载宏包，无需 TeX Live）
- 文档类：`\documentclass[12pt,a4paper]{ctexart}`（中文优先）
- 完整踩坑记录：[PITFALLS.md](PITFALLS.md)
- 一键编译：[scripts/compile.sh](scripts/compile.sh)

---

## 1. 环境安装

```bash
# 安装 tectonic（macOS）
curl --proto '=https' --tlsv1.2 -fsSL https://drop.axado.rs/tectonic.sh | sh
# 或
brew install tectonic

# 验证
tectonic --version
```

> 如果 PATH 未自动更新，tectonic 通常在 `/tmp/tectonic` 或 `~/.cargo/bin/tectonic`。

---

## 2. 文档类与中文支持

```latex
\documentclass[12pt,a4paper]{ctexart}
% ctexart 自动处理中文字体，无需额外 \usepackage{CJK}
```

**常用宏包组合**（直接复制到 preamble）：

```latex
\usepackage{geometry}     % 页边距
\usepackage{graphicx}     % 插图
\usepackage{xcolor}       % 颜色
\usepackage{tcolorbox}    % 彩色框
\usepackage{booktabs}     % 专业表格线
\usepackage{tabularx}     % 自动宽度表格
\usepackage{array}        % 高级列格式
\usepackage{tikz}         % 流程图
\usepackage{hyperref}     % 超链接
\usepackage{titlesec}     % 自定义标题格式
\usepackage{enumitem}     % 列表格式
\usepackage{microtype}    % 微排版优化
```

---

## 3. 比赛/白皮书文档结构

```
封面页 1：logo + 项目名 + 一句话 pitch + 日期
封面页 2：三个志愿/赛道 + 链接 + 作者信息
目录
Part 1 产品
  § 背景与痛点
  § 产品概述
  § 核心功能
Part 2 技术
  § 系统架构（TikZ 图）
  § 模块对照表
  § 安全设计
  § 测试与部署
Part 3 团队
  § 成员介绍
附录
  § API 清单
  § 代码统计
```

---

## 4. 表格防溢出（最常见问题）

### 4.1 含长路径/URL 的表格

**错误做法**（固定列宽不够，内容溢出）：
```latex
\begin{tabular}{lll}
```

**正确做法**：
```latex
{\small
\begin{tabular}{p{0.5cm} p{3.0cm} >{\raggedright\arraybackslash}p{5.8cm} p{4.8cm}}
```

关键点：
- 用 `p{宽度}` 替换 `l`/`r`/`c`
- 长路径列加 `>{\raggedright\arraybackslash}` 允许自动换行
- 整个表格包在 `{\small ... }` 里缩小字号
- 长路径用 `\newline` 主动断行：`\texttt{core/security/}\newline\texttt{permission\_manager.py}`

### 4.2 含 URL 的列

```latex
% URL 列使用 \url{} 并限制列宽
>{\raggedright\arraybackslash}p{4cm}
```

### 4.3 列宽分配原则

| 场景 | 参考分配（总宽 ~15cm） |
|------|----------------------|
| 4列（编号+名称+路径+说明） | 0.5 + 3.0 + 5.8 + 4.8 |
| 3列（API+文件+功能） | 2.5 + 5.0 + 6.0 |
| 双列（名称+说明） | 5.0 + 9.0 |

---

## 5. TikZ 流程图

### 5.1 基础节点风格定义

```latex
\usetikzlibrary{shapes.geometric,arrows.meta,positioning,fit,backgrounds}

\begin{tikzpicture}[
  font=\small,
  box/.style={draw, rounded corners=3pt, fill=blue!10,
              minimum width=3cm, minimum height=0.8cm, align=center},
  arr/.style={-Latex, thick},
]
\node[box] (a) {节点 A};
\node[box, right=1.5cm of a] (b) {节点 B};
\draw[arr] (a) -- (b);
\end{tikzpicture}
```

> ⚠️ 样式名不能用 `step`（pgfkeys 保留字），改用 `proc`/`box`/`blk`。

### 5.2 竖排层级图（架构图）

```latex
\node[layer] (api) {接口层};
\node[layer, below=0.5cm of api] (dom) {Domain};
\node[layer, below=0.5cm of dom] (mem) {Memory};
\draw[-Latex,thick] (api.south) -- (dom.north);
\draw[-Latex,thick] (dom.south) -- (mem.north);
```

### 5.3 决策流（菱形）

```latex
\node[diamond, draw, aspect=2] (dec) {专注中？};
```

---

## 6. 封面设计要点

```latex
\begin{titlepage}
  \centering
  \includegraphics[width=4cm]{logo.png}  % logo 放工作目录或相对路径
  \vspace{1.5cm}
  {\Huge\bfseries\color{primary} 项目名称}\\[0.8cm]
  {\large 一句话 pitch}\\[2cm]
  {\normalsize 2026 年 4 月}
  \vfill
\end{titlepage}
```

**注意**：
- `logo.png` 路径相对于 `.tex` 文件位置
- `\includegraphics[width=4cm]{../../logo.png}` 跨目录时用相对路径
- 封面内容多时拆成两页（第二页放作者、链接、赛道信息）

---

## 7. 自定义章节标题格式

```latex
% 正确写法（block 格式，rule 在 after-code 里）
\titleformat{\section}[block]
  {\Large\bfseries\color{primary}}
  {\thesection}{0.6em}{}
  [\vspace{-0.4em}{\color{primary}\rule{\linewidth}{1.2pt}}]
```

> ⚠️ `#1`（标题文本）只在第 5 个参数（before-code）里用，不能放在其他位置，否则报 `Illegal parameter number`。

---

## 8. 编译命令

```bash
# 单次编译（推荐，tectonic 自动多次运行直到稳定）
tectonic -X compile your_file.tex

# 如果 tectonic 在 /tmp/tectonic
/tmp/tectonic -X compile your_file.tex

# 查看详细输出
tectonic -X compile --keep-logs your_file.tex 2>&1 | tee build.log
```

---

## 9. 快速检查清单

编译前：
- [ ] 无 emoji（改用文字，如 `[AI]` 代替 🤖）
- [ ] TikZ 样式名不含保留字（`step` → `proc`）
- [ ] 所有 `\begin` 有对应 `\end`
- [ ] `\end{tcolorbox}` 后不直接 `\\`，改 `\vspace{1cm}`

编译后：
- [ ] 表格无文字溢出
- [ ] URL 没覆盖到中文
- [ ] 图表箭头正常显示

---

## 更多内容

- 详细踩坑：[PITFALLS.md](PITFALLS.md)
- 一键编译脚本：[scripts/compile.sh](scripts/compile.sh)
