import type { MaskResponse } from '../lib/api'

type DiffViewProps = {
  result: MaskResponse | null
}

export function DiffView({ result }: DiffViewProps) {
  return (
    <div className="grid md:grid-cols-2 gap-4">
      <div>
        <div className="text-xs text-slate-500 mb-1">原文</div>
        <div className="min-h-[120px] border border-slate-200 rounded p-3 whitespace-pre-wrap bg-white">
          {result ? result.original : 'original text'}
        </div>
      </div>
      <div>
        <div className="text-xs text-slate-500 mb-1">マスク後</div>
        <div className="min-h-[120px] border border-slate-200 rounded p-3 whitespace-pre-wrap bg-white">
          {result ? result.masked : 'masked text'}
        </div>
      </div>
    </div>
  )
}


