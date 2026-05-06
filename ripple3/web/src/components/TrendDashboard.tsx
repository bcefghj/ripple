import { motion } from 'framer-motion'
import { X } from 'lucide-react'

interface Props {
  onClose: () => void
  onTopicSelect?: (prompt: string) => void
}

export default function TrendDashboard({ onClose, onTopicSelect }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="w-full max-w-2xl mx-4 rounded-2xl border border-slate-700/50 bg-slate-900 p-6 shadow-2xl"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-slate-200">热搜趋势</h2>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-slate-800 text-slate-400">
            <X className="w-4 h-4" />
          </button>
        </div>
        <p className="text-sm text-slate-500">实时热搜数据加载中...</p>
      </motion.div>
    </motion.div>
  )
}
