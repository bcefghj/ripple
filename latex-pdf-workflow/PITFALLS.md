# LaTeX PDF 踩坑详细记录

> 来源：2026 年 4 月 LarkMentor 飞书AI校园挑战赛比赛材料制作过程中的真实报错。

---

## 坑 1：`\end{tcolorbox}\\[1.0cm]` 报错

**错误信息**
```
LaTeX Error: There's no line here to end.
```

**原因**  
`\\` 用于表格或 tabular 环境内的换行，在 `tcolorbox` 之后直接用会出错。

**修复**
```latex
% 错误
\end{tcolorbox}\\[1.0cm]

% 正确
\end{tcolorbox}
\vspace{1.0cm}
```

---

## 坑 2：Emoji 无法渲染

**错误信息**
```
warning: could not represent character "🤖" (0x1f916) in font "[lmroman10-regular]"
```

**原因**  
`ctexart` 默认字体不含 emoji 字符（需要 Noto Color Emoji 等专用字体）。

**修复**  
直接替换为文本：
```latex
% 错误
🤖 LarkMentor

% 正确
[AI] LarkMentor
% 或用 \textbf{★} 等符号代替
```

> 不要尝试 `\usepackage{emoji}` 或 `\setemojifont`，配置成本极高且不稳定。

---

## 坑 3：`\titleformat` 报 `Illegal parameter number`

**错误信息**
```
larkmentor_report_A.tex:63: Illegal parameter number in definition of \ttlf@section
```

**原因**  
`\titleformat` 的第 5 个参数（before-code）里才能用 `#1`（代表标题文本），放在其他参数位置会报错。

**错误写法**
```latex
\titleformat{\section}{\Large\bfseries}{\thesection}{1em}{#1\newline\rule...}
```

**正确写法**
```latex
\titleformat{\section}[block]
  {\Large\bfseries\color{primary}}
  {\thesection}{0.6em}{}
  [\vspace{-0.4em}{\color{primary}\rule{\linewidth}{1.2pt}}]
```

---

## 坑 4：TikZ 中 `Paragraph ended before \tikz@picture was complete`

**错误信息**
```
larkmentor_report_A.tex:396: Paragraph ended before \tikz@picture was complete
```

**原因**  
TikZ 样式定义中括号不匹配。常见于：
```latex
% 错误：最后是 ] 而不是 }
arrow/.style={-Latex, thick, color=primary],
%                                         ^-- 应该是 }
```

**修复**  
检查 `tikzpicture` 环境中所有 `[...]` 和 `{...}` 的配对，确保每个 `{` 有对应 `}`。

---

## 坑 5：TikZ `step` 样式名冲突

**错误信息**
```
Package pgfkeys Error: The key '/tikz/step' requires a value.
```

**原因**  
`step` 是 TikZ/pgf 的保留关键字（用于网格步长），不能作为自定义样式名。

**修复**  
重命名自定义样式：
```latex
% 错误
step/.style={draw, rounded corners, ...}
\node[step] (a) {...}

% 正确
proc/.style={draw, rounded corners, ...}
\node[proc] (a) {...}
```

**其他常见保留字**：`scale`, `shift`, `rotate`, `opacity`, `draw`, `fill`——避免用这些做自定义样式名。

---

## 坑 6：表格内容重叠/溢出

**现象**  
长路径或 URL 的 `\texttt{}` 文本延伸到相邻列的中文文字上面。

**根本原因**  
- 使用了 `l`/`c`/`r` 列格式，这些格式不限制列宽，内容会无限延伸
- `p{宽度}` 列中宽度设置太小

**系统性修复方法**

```latex
% 1. 把所有列改成 p{宽度} 格式
% 2. 长路径列加 >{\raggedright\arraybackslash} 允许换行
% 3. 整个表格用 {\small ...} 包裹
% 4. 手动在长路径中插入 \newline 换行

{\small
\begin{tabular}{
  p{0.5cm}                           % 编号列（很窄）
  p{3.0cm}                           % 名称列
  >{\raggedright\arraybackslash}p{5.8cm}  % 路径列（允许换行）
  p{4.8cm}                           % 说明列
}
\toprule
\textbf{\#} & \textbf{名称} & \textbf{模块路径} & \textbf{说明} \\
\midrule
1 & PermissionManager
  & \texttt{core/security/}\newline\texttt{permission\_manager.py}
  & 5 级权限 deny-by-default \\
\bottomrule
\end{tabular}
}
```

**列宽分配经验**（A4 纸，默认页边距，正文宽约 15cm）

| 列数 | 推荐分配 |
|------|---------|
| 4列 | 0.5 + 3.0 + 5.8 + 4.8 cm |
| 3列（等宽） | 4.5 + 4.5 + 5.0 cm |
| 2列 | 5.0 + 9.0 cm |

---

## 坑 7：logo 图片路径找不到

**错误信息**
```
! LaTeX Error: File `logo.png' not found.
```

**原因**  
图片路径相对于 `.tex` 文件位置，而不是执行 `tectonic` 命令的目录。

**修复**
```latex
% 如果 logo.png 在 .tex 文件同级目录
\includegraphics[width=4cm]{logo.png}

% 如果 logo.png 在上两级目录（如项目根目录）
\includegraphics[width=4cm]{../../logo.png}

% 或用 \graphicspath 统一设置
\graphicspath{{../../}}
```

---

## 坑 8：`tectonic` 命令位置

**现象**  
`tectonic` 安装成功但 `zsh: command not found: tectonic`

**原因**  
tectonic 可能安装到 `/tmp/tectonic`（临时安装）或 `~/.cargo/bin/`（cargo 安装），但未加入 PATH。

**解决方案**
```bash
# 直接用绝对路径调用
/tmp/tectonic -X compile file.tex

# 或加入 PATH（永久）
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

## 坑 9：`\\` 在 tcolorbox 外失效

类似坑 1，总结规律：

| 场景 | 换行方式 |
|------|---------|
| tabular 内 | `\\` |
| 正文段落间 | `\vspace{1cm}` 或空行 |
| 标题页竖向空白 | `\vfill` 或 `\vspace{2cm}` |
| minipage/tcolorbox 后 | `\vspace{1cm}`，不要 `\\` |

---

## 坑 10：`ctexart` 与英文字体混用

**现象**  
中英文混排时字体风格不统一，英文部分偶尔偏粗或偏细。

**推荐设置**
```latex
\usepackage{fontspec}    % XeLaTeX / LuaLaTeX 时使用
\setmainfont{Times New Roman}
% ctexart 会自动处理中文字体，不需要额外设置
```

> tectonic 默认使用 pdfLaTeX，`fontspec` 需要 XeLaTeX。如果用 tectonic 的默认引擎，中文字体交给 ctex 自动处理即可，不要额外引入 fontspec。

---

## 流程总结（最优路径）

```
1. ctexart 文档类 + tectonic 编译器
2. 封面：titlepage 环境 + \vfill 控制间距
3. 目录：\tableofcontents + \newpage
4. 章节：Part > section > subsection
5. 表格：p{} 列 + \small + \newline 手动断路径
6. 图表：tikzpicture，样式名避开保留字
7. 编译：/tmp/tectonic -X compile file.tex
8. 检查：无 emoji，无溢出，箭头正常
```
