type TabsProps = {
  active: 'result' | 'diff'
  onChange: (t: 'result' | 'diff') => void
}

export function Tabs({ active, onChange }: TabsProps) {
  return (
    <div className="border-b border-slate-200 flex items-center justify-between">
      <div className="flex text-sm" role="tablist" aria-label="結果/差分">
        <button
          role="tab"
          aria-selected={active === 'result'}
          className={
            'px-4 py-2 border-b-2 ' +
            (active === 'result' ? 'border-slate-900' : 'text-slate-500')
          }
          onClick={() => onChange('result')}
        >
          結果
        </button>
        <button
          role="tab"
          aria-selected={active === 'diff'}
          className={
            'px-4 py-2 border-b-2 ' +
            (active === 'diff' ? 'border-slate-900' : 'text-slate-500')
          }
          onClick={() => onChange('diff')}
        >
          差分
        </button>
      </div>
    </div>
  )
}


