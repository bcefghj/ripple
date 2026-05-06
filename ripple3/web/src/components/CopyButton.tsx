import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Copy, Check, ChevronDown } from 'lucide-react'

interface Props {
  content: string
}

type Format = 'raw' | 'xiaohongshu' | 'shipinhao' | 'gongzhonghao'

const FORMAT_LABELS: Record<Format, { name: string; emoji: string; desc: string }> = {
  raw: { name: '原文', emoji: '📋', desc: '直接复制 Markdown 原文' },
  xiaohongshu: { name: '小红书', emoji: '🔴', desc: '自动 emoji + 分段 + #标签' },
  shipinhao: { name: '视频号', emoji: '🟢', desc: '开场 Hook + 主体 + CTA 脚本' },
  gongzhonghao: { name: '公众号', emoji: '📰', desc: '正文 + 引导关注' },
}

// 把通用 markdown 转成小红书风格
function toXiaohongshu(content: string): string {
  // 简化：取主标题 + 关键章节，加 emoji + 分段 + 标签
  const lines = content.split('\n')
  const out: string[] = []

  // 取第一个评分作为开头
  const scoreMatch = content.match(/(\d+(?:\.\d+)?)\s*\/\s*10/)
  if (scoreMatch) out.push(`✨ 这个赛道我打 ${scoreMatch[1]}/10 分！`)
  out.push('')

  let inSection = false
  let sectionCount = 0
  for (const line of lines) {
    if (sectionCount >= 3) break  // 小红书短一些
    if (line.startsWith('### ')) {
      inSection = true
      sectionCount++
      const title = line.replace(/^###\s*/, '')
      out.push('')
      out.push(`📍 ${title}`)
      continue
    }
    if (line.startsWith('##')) continue
    if (line.match(/^\s*\|/)) continue  // 跳过表格
    if (line.startsWith('---')) continue
    if (inSection && line.trim() && !line.startsWith('**')) {
      // 第一段拿来用
      out.push(line.replace(/\*\*/g, ''))
    }
    if (line.trim() === '') {
      out.push('')
    }
  }

  out.push('')
  out.push('🌟 你也想做 KOC 吗？评论区告诉我你的领域，下期帮你分析！')
  out.push('')
  out.push('#KOC增长 #内容创作 #小红书运营 #微信视频号 #大学生创业')

  return out.join('\n').slice(0, 1000)
}

function toShipinhao(content: string): string {
  const out: string[] = []
  out.push('【视频号脚本 · 60 秒版】')
  out.push('')

  // 开场 Hook（找 ### 或第一段加感叹）
  const sectionMatch = content.match(/###\s*(.+)/m)
  out.push('🎬 开场 Hook（前 3 秒）')
  if (sectionMatch) {
    out.push(`如果你也在思考「${sectionMatch[1].trim()}」，这条视频帮你少走 3 个月弯路。`)
  } else {
    out.push('注意看，这个内容方向其实是 2026 年最大的机会窗口。')
  }
  out.push('')

  // 主体（取 30 字以下的关键句）
  out.push('📖 主体（约 40 秒）')
  const bullets = content.match(/^[\-•·]\s*(.{10,50})/gm)?.slice(0, 4) || []
  for (const b of bullets) {
    out.push(b.replace(/^[\-•·]\s*/, '· '))
  }
  out.push('')

  // CTA
  out.push('🎯 结尾 CTA（最后 5 秒）')
  out.push('如果觉得有用，点个赞让我知道，下期讲 [具体话题]。')
  out.push('转发给你最想@的同学，一起做 KOC！')
  out.push('')
  out.push('💡 发布建议：周二/四/六 20:00 + 工作日 12:00 双发')
  out.push('🔑 核心关键词：[请根据内容嵌入 3-5 个]')

  return out.join('\n')
}

function toGongzhonghao(content: string): string {
  const out: string[] = []
  out.push('【公众号格式版】')
  out.push('')
  out.push(content)  // 公众号格式适合保留长内容
  out.push('')
  out.push('━━━━━━━━━━━━━━')
  out.push('📌 关注 Ripple，免费获取：')
  out.push('  · AI 增长方案（每周 1 篇）')
  out.push('  · KOC 起号工具包（PDF）')
  out.push('  · 微信生态运营技巧')
  out.push('━━━━━━━━━━━━━━')
  out.push('转发本文给同学，一起做 KOC ↗')

  return out.join('\n')
}

function transform(content: string, format: Format): string {
  switch (format) {
    case 'xiaohongshu': return toXiaohongshu(content)
    case 'shipinhao': return toShipinhao(content)
    case 'gongzhonghao': return toGongzhonghao(content)
    default: return content
  }
}

export default function CopyButton({ content }: Props) {
  const [open, setOpen] = useState(false)
  const [copied, setCopied] = useState<Format | null>(null)

  const handleCopy = async (format: Format) => {
    const text = transform(content, format)
    try {
      await navigator.clipboard.writeText(text)
      setCopied(format)
      setTimeout(() => setCopied(null), 2000)
      setOpen(false)
    } catch (e) {
      console.error('Copy failed:', e)
    }
  }

  return (
    <div className="relative inline-block">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-[11px] px-2.5 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-300 hover:border-violet-500/50 hover:text-violet-300 transition-all"
      >
        {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
        {copied ? `已复制 ${FORMAT_LABELS[copied].name}` : '复制为'}
        <ChevronDown className="w-3 h-3" />
      </button>
      <AnimatePresence>
        {open && (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="absolute right-0 top-full mt-1 z-20 w-60 rounded-xl bg-slate-900 border border-slate-700 shadow-2xl overflow-hidden"
            >
              {(Object.keys(FORMAT_LABELS) as Format[]).map(f => {
                const meta = FORMAT_LABELS[f]
                return (
                  <button
                    key={f}
                    onClick={() => handleCopy(f)}
                    className="w-full flex items-center gap-2 px-3 py-2.5 hover:bg-slate-800 transition-colors text-left border-b border-slate-800 last:border-0"
                  >
                    <span className="text-base">{meta.emoji}</span>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-medium text-slate-200">{meta.name}</div>
                      <div className="text-[10px] text-slate-500 line-clamp-1">{meta.desc}</div>
                    </div>
                  </button>
                )
              })}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}
