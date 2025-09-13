import type { MaskTargets, MaskingOptions } from '../lib/api'

type LeftControlsProps = {
  text: string
  onTextChange: (v: string) => void
  targets: MaskTargets
  onToggleTarget: (key: keyof MaskTargets) => void
  masking: MaskingOptions
  onMaskingChange: (next: MaskingOptions) => void
  onSubmit: () => void
  loading: boolean
  error: string | null
}

export function LeftControls({
  text,
  onTextChange,
  targets,
  onToggleTarget,
  masking,
  onMaskingChange,
  onSubmit,
  loading,
  error,
}: LeftControlsProps) {
  const m = masking || { preserve_length: true, fixed_length: null }

  return (
    <section className="lg:col-span-1 space-y-4">
      <div className="border border-slate-200 rounded-xl bg-white p-4">
        <h2 className="text-sm font-medium mb-2">入力</h2>
        <div className="text-xs text-slate-500 mb-2">テキスト</div>
        <textarea
          className="w-full h-40 border rounded-md p-2"
          value={text}
          onChange={(e) => onTextChange(e.target.value)}
        />
      </div>

      <div className="border border-slate-200 rounded-xl bg-white p-4">
        <h3 className="text-sm font-medium mb-3">パラメータ（マスク対象）</h3>
        <div className="divide-y">
          {(
            [
              'PERSON',
              'EMAIL',
              'PHONE',
              'LOCATION',
              'ORGANIZATION',
              'URL',
            ] as (keyof MaskTargets)[]
          ).map((key) => (
            <label key={key} className="flex items-center justify-between py-2 text-sm">
              <span>{key}</span>
              <input
                type="checkbox"
                className="h-4 w-4"
                checked={!!targets[key]}
                onChange={() => onToggleTarget(key)}
              />
            </label>
          ))}
        </div>

        <div className="mt-4 space-y-2 text-sm">
          <label className="flex items-center justify-between gap-4">
            <span>replacement</span>
            <input
              className="border rounded px-2 py-1 w-32"
              value={m.replacement ?? ''}
              onChange={(e) => onMaskingChange({ ...m, replacement: e.target.value })}
            />
          </label>
          <label className="flex items-center justify-between gap-4">
            <span>preserve_length</span>
            <input
              type="checkbox"
              className="h-4 w-4"
              checked={m.preserve_length ?? true}
              onChange={(e) => onMaskingChange({ ...m, preserve_length: e.target.checked })}
            />
          </label>
          <label className="flex items-center justify-between gap-4">
            <span>fixed_length</span>
            <input
              className="border rounded px-2 py-1 w-24"
              placeholder="空で無効"
              value={m.fixed_length ?? ''}
              onChange={(e) => {
                const v = e.target.value.trim()
                onMaskingChange({ ...m, fixed_length: v === '' ? null : Number.parseInt(v, 10) })
              }}
            />
          </label>
        </div>

        <button
          className="mt-4 w-full h-10 rounded-lg bg-slate-900/80 text-white disabled:opacity-50"
          onClick={onSubmit}
          disabled={loading}
        >
          {loading ? 'マスク中…' : 'マスクを実行'}
        </button>

        {error && (
          <div className="mt-2 text-sm text-red-600">Error: {error}</div>
        )}
      </div>
    </section>
  )
}


