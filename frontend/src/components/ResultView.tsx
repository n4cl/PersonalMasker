import type { MaskResponse } from '../lib/api'

type ResultViewProps = {
  result: MaskResponse | null
}

export function ResultView({ result }: ResultViewProps) {
  if (!result) {
    return (
      <div className="min-h-[120px] border border-slate-200 rounded p-3 text-slate-400 bg-white">masked text preview</div>
    )
  }

  const spans = [...result.detected].sort((a, b) => a.masked_start - b.masked_start)
  const parts: JSX.Element[] = []
  let cursor = 0
  spans.forEach((s, idx) => {
    if (cursor < s.masked_start) {
      parts.push(
        <span key={`t-${idx}`}>{result.masked.slice(cursor, s.masked_start)}</span>,
      )
    }
    parts.push(
      <mark key={`m-${idx}`} className="bg-amber-200 px-0.5">
        {result.masked.slice(s.masked_start, s.masked_end)}
      </mark>,
    )
    cursor = s.masked_end
  })
  if (cursor < result.masked.length) {
    parts.push(<span key="tail">{result.masked.slice(cursor)}</span>)
  }

  return <div className="min-h-[120px] border border-slate-200 rounded p-3 whitespace-pre-wrap bg-white">{parts}</div>
}


