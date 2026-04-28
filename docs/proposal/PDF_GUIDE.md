# PDF 编译完整指引

> 本文是 Ripple 提案 PDF 的编译手册,从 0 到 1 教会任何人在自己电脑上生成 PDF。

---

## 1. 一键编译(已配置好的环境)

```bash
cd ripple/docs/proposal
./build.sh                # 编译 PDF
./build.sh check          # 仅检查环境
./build.sh clean          # 清理中间文件
```

成功后产出:`docs/proposal/main.pdf`(约 500KB - 50MB,24 页起)

---

## 2. 环境准备

### 2.1 安装 LaTeX(三选一)

#### macOS(推荐)
```bash
# 完整版(约 4GB,推荐评审期一次性安装)
brew install --cask mactex

# 精简版(约 100MB)
brew install --cask basictex
sudo tlmgr update --self
sudo tlmgr install ctex collection-fontsrecommended titlesec tcolorbox \
    pgfplots booktabs colortbl tabularx multirow listings enumitem \
    fontawesome5 newunicodechar pifont latexmk
```

#### Ubuntu / Debian / WSL2
```bash
sudo apt update
sudo apt install -y texlive-full texlive-xetex texlive-lang-chinese latexmk
```

#### Windows
1. 下载 [MiKTeX](https://miktex.org/download)
2. 安装时勾选「自动按需安装缺失包」
3. 在 PowerShell 中运行 `xelatex --version` 验证

### 2.2 字体安装(可选,但推荐)

PDF 默认会用系统中文字体(macOS=PingFang/Songti, Linux=Noto, Windows=YaHei),即装即用。

**如要更美观**,推荐安装思源字体:
- **思源宋体 SC**:<https://github.com/adobe-fonts/source-han-serif/releases>
- **思源黑体 SC**:<https://github.com/adobe-fonts/source-han-sans/releases>
- **思源等宽 SC**:<https://github.com/adobe-fonts/source-han-mono/releases>

或用 Google Noto CJK SC(完全等价开源版本)。

安装后 build 脚本会自动检测并使用。

---

## 3. 在线编译(无需本地安装)

### 3.1 Overleaf(推荐评审期备份方案)

1. <https://www.overleaf.com> 注册免费账号
2. New Project → Upload Project
3. 把 `docs/proposal/` 整个目录打包为 zip 上传
4. Menu → Settings → Compiler 选 **XeLaTeX**
5. 点击「Recompile」

> Overleaf 已内置思源字体,可直接编译完美版本。

### 3.2 GitHub Codespaces

```bash
# 启动 codespace 后
sudo apt install -y texlive-full
cd ripple/docs/proposal
./build.sh
```

---

## 4. 文件结构

```
docs/proposal/
├── main.tex                    ← 主文档(字体配置 + \input 模块)
├── build.sh                    ← 一键编译脚本
├── cover.tex                   ← 封面
├── 00-executive-summary.tex    ← 执行摘要
├── 01-insight.tex              ← 模块 1: 用户洞察
├── 02-product.tex              ← 模块 2: 产品方案
├── 03-ai-native.tex            ← 模块 3: AI 原生能力
├── 04-bonus.tex                ← 模块 4: 加分项
├── 05-appendix.tex             ← 附录
├── PDF_GUIDE.md                ← 本文件
├── figures/                    ← 图片资源
└── main.pdf                    ← 编译产物(gitignore)
```

---

## 5. 修改与定制

### 5.1 修改封面信息(选手 / 学校)

编辑 `cover.tex`,把以下占位符替换:
```latex
选手 & \texttt{[选手姓名]} \\
学校 & \texttt{[学校名称]} \\
Demo 链接 & \url{http://localhost:3000} \\
备用链接 & \url{https://ripple-demo.vercel.app} \\
```

### 5.2 修改主题色

编辑 `main.tex` 的颜色定义:
```latex
\definecolor{ripple-primary}{HTML}{1E40AF}
\definecolor{ripple-accent}{HTML}{0EA5E9}
\definecolor{ripple-dark}{HTML}{0F172A}
```

### 5.3 修改字体

编辑 `main.tex` 文档类参数:
```latex
\documentclass[11pt, a4paper, fontset=mac, ...]{ctexart}
% fontset 可选: mac / ubuntu / windows / fandol / none
```

如要强制用思源:把 `fontset=mac` 改为 `fontset=none`,然后取消注释字体设置(参考 git 历史 `IfFontExistsTF` 版本)。

---

## 6. 常见问题

### Q1:`./build.sh` 报 `xelatex: command not found`
**解** 见 §2.1 安装 LaTeX。

### Q2:报 `Package ctex Error: Font not found`
**解** 安装思源字体(§2.2),或在 main.tex 用 `fontset=mac/windows/ubuntu` 自动选系统字体。

### Q3:zsh 报 `no matches found: *.out`
**解** 是 zsh 通配符问题,改用 `bash ./build.sh` 或 `./build.sh clean` 后再 build。

### Q4:报 `LaTeX Error: Missing \begin{document}`
**解** 通常是 preamble 中某个命令引发了排版操作。最常见:
- `\titleformat` 中的 `\titlerule[1pt]` 方括号歧义 → 改为 `[{\hrule height 1pt}]`
- 字体配置 `\IfFontExistsTF` 套层过深 → 改为 `fontset=mac` 一键搞定

### Q5:中文显示成 □□□
**解** XeLaTeX 字体回退失败。检查 `fc-list :lang=zh` 是否有可用中文字体,或安装思源/Noto。

### Q6:listings 报 `Couldn't load language: json`
**解** 已在 main.tex 中自定义 `\lstdefinelanguage{json}`,如新增其他语言同理。

### Q7:tcolorbox / tikz 找不到
**解** `tlmgr install tcolorbox pgfplots tikz`(MacTeX/MiKTeX 需要 admin 权限)。

### Q8:emoji / 特殊符号显示为方框
**解** 已用 `newunicodechar` 把常用符号(✓ ✗ → ⚠ 等)映射到 `pifont` 等价字符。如缺失继续在 main.tex 中追加 `\newunicodechar{X}{...}`。

### Q9:PDF 太大
**解** 嵌入字体已优化。如仍超限:
- `gs -sDEVICE=pdfwrite -dPDFSETTINGS=/ebook -o main_compressed.pdf main.pdf`
- 或用 [Smallpdf 在线压缩](https://smallpdf.com/compress-pdf)

### Q10:Overleaf 上编译失败
**解** Overleaf Premium / Pro 才支持完整 LaTeX 包。免费账号通常够用,仅在缺包时升级。

---

## 7. 提交前检查清单

- [ ] 编译无 Error(Warning 可接受)
- [ ] 中文 / 英文 / 公式 / 代码 / 表格 / 图都正常
- [ ] 封面 `[选手姓名]` `[学校名称]` `Demo 链接` 已替换
- [ ] PDF 大小 ≤ 50MB
- [ ] PDF 页数符合预期(执行摘要 1-2 页 + 4 模块 + 附录,合计 20-50 页)
- [ ] PDF 元信息(标题/作者)正确(File → Properties)
- [ ] 在 Mac / Windows / Linux 至少 2 个平台预览验证字体显示

---

## 8. 命名规范

提交前重命名:

```
选手姓名_命题5_Ripple_Demo演示.pdf
```

例如:`张三_命题5_Ripple_Demo演示.pdf`

---

如有进一步问题,可参考 [docs/defense/QA.md](../defense/QA.md) 答辩话术或联系参赛人员。
