import type { MaskResponse } from '../lib/api'

type DetectedTableProps = {
  result: MaskResponse | null
}

export function DetectedTable({ result }: DetectedTableProps) {
  return (
    <div className="border border-slate-200 rounded overflow-hidden bg-white">
      <div className="grid grid-cols-4 gap-0 bg-slate-50 text-xs font-medium">
        <div className="p-2">Label</div>
        <div className="p-2">Text</div>
        <div className="p-2">[start,end]</div>
        <div className="p-2">[masked_start, masked_end]</div>
      </div>
      {result?.detected?.map((d, i) => (
        <div key={i} className="grid grid-cols-4 gap-0 text-sm border-t">
          <div className="p-2">{d.label}</div>
          <div className="p-2 truncate" title={d.text}>{d.text}</div>
          <div className="p-2">{d.start_char}–{d.end_char}</div>
          <div className="p-2">{d.masked_start}–{d.masked_end}</div>
        </div>
      ))}
      {!result && (
        <div className="p-2 text-sm text-slate-400 border-t">No data</div>
      )}
    </div>
  )
}


