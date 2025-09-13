import { useMemo, useState } from 'react'
import {
  postMask,
  type MaskResponse,
  type MaskTargets,
  type MaskingOptions,
} from './lib/api'
import { Header } from './components/Header'
import { LeftControls } from './components/LeftControls'
import { Tabs } from './components/Tabs'
import { ResultView } from './components/ResultView'
import { DetectedTable } from './components/DetectedTable'
import { DiffView } from './components/DiffView'

function App() {
  const [text, setText] = useState('太郎のメールは taro@example.com です。')
  const [targets, setTargets] = useState<MaskTargets>({
    PERSON: true,
    EMAIL: true,
    PHONE: true,
    LOCATION: true,
    ORGANIZATION: true,
    URL: true,
  })
  const [maskingReplacement, setMaskingReplacement] = useState('＊')
  const [maskingPreserve, setMaskingPreserve] = useState(true)
  const [maskingFixedLen, setMaskingFixedLen] = useState<string>('')

  const [activeTab, setActiveTab] = useState<'result' | 'diff'>('result')
  const [result, setResult] = useState<MaskResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const masking: MaskingOptions = useMemo(() => {
    const fixed = maskingFixedLen.trim() === '' ? null : Number.parseInt(maskingFixedLen, 10)
    return {
      replacement: maskingReplacement || undefined,
      preserve_length: maskingPreserve,
      fixed_length: Number.isNaN(fixed as number) ? null : fixed,
    }
  }, [maskingReplacement, maskingPreserve, maskingFixedLen])

  const handleToggleTarget = (key: keyof MaskTargets) => {
    setTargets((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  const handleMask = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const targetArray = Object.entries(targets)
        .filter(([, v]) => !!v)
        .map(([k]) => k)
      const res = await postMask({ text, targets: targetArray, masking })
      setResult(res)
      setActiveTab('result')
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }

  const highlightedMasked = useMemo(() => {
    if (!result) return null
    if (!result.detected?.length) return <pre className="whitespace-pre-wrap">{result.masked}</pre>
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
    return <pre className="whitespace-pre-wrap">{parts}</pre>
  }, [result])

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 font-sans">
      <Header title="PersonalMasker — Playground" subtitle="開発用（Vite）" />

      <main className="mx-auto max-w-6xl px-4 py-6 grid grid-cols-1 lg:grid-cols-3 gap-4">
        <LeftControls
          text={text}
          onTextChange={setText}
          targets={targets}
          onToggleTarget={handleToggleTarget}
          masking={masking}
          onMaskingChange={(next) => {
            setMaskingReplacement(next?.replacement ?? maskingReplacement)
            setMaskingPreserve(next?.preserve_length ?? maskingPreserve)
            setMaskingFixedLen(
              next?.fixed_length === null || next?.fixed_length === undefined
                ? ''
                : String(next?.fixed_length),
            )
          }}
          onSubmit={handleMask}
          loading={loading}
          error={error}
        />

        {/* Right: 結果 / 差分 タブ */}
        <section className="lg:col-span-2 space-y-4">
          <div className="border border-slate-200 rounded-xl bg-white">
            <Tabs active={activeTab} onChange={setActiveTab} />

            {activeTab === 'result' && (
              <div className="p-4 space-y-4">
                <div>
                  <div className="text-sm text-slate-500 mb-1">マスクした結果</div>
                  <ResultView result={result} />
                </div>

                <div>
                  <div className="text-sm text-slate-500 mb-1">検出スパン一覧</div>
                  <DetectedTable result={result} />
                </div>
              </div>
            )}

            {activeTab === 'diff' && (
              <div className="p-4 space-y-4">
                <DiffView result={result} />
                <div>
                  <div className="text-xs text-slate-500 mb-1">差分（簡易）</div>
                  <div className="min-h-[80px] border rounded p-3 text-sm space-y-1">
                    {result?.detected?.length ? (
                      result.detected.map((d, i) => (
                        <div key={i} className="flex gap-2 items-center">
                          <span className="text-slate-500">[{d.label}]</span>
                          <span className="line-through">{d.text}</span>
                          <span>→</span>
                          <span className="font-mono">
                            {result.masked.slice(d.masked_start, d.masked_end)}
                          </span>
                        </div>
                      ))
                    ) : (
                      <div className="text-slate-400">差分はありません</div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="text-xs text-slate-500">状態: {loading ? 'Loading' : error ? 'Error' : result ? 'Success' : 'Empty'}</div>
        </section>
      </main>
    </div>
  )
}

export default App
