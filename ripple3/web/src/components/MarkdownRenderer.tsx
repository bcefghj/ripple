import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Props {
  content: string
  isStreaming?: boolean
}

export default function MarkdownRenderer({ content, isStreaming }: Props) {
  return (
    <div className={`prose prose-sm max-w-none dark:prose-invert ${isStreaming ? 'cursor-blink' : ''}`}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {content}
      </ReactMarkdown>
    </div>
  )
}
