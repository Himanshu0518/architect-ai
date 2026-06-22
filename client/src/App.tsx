import { useState, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Hexagon, Sparkles } from 'lucide-react'
import { GenerationProgress } from './components/GenerationProgress'
import type { PipelineStage, LogEvent } from './components/GenerationProgress'
import { MarkdownRenderer } from './components/MarkdownRenderer'

function App() {
  const [companyName, setCompanyName] = useState('')
  const [requirements, setRequirements] = useState('')

  const [status, setStatus] = useState<'idle' | 'generating' | 'complete' | 'error'>('idle')
  const [currentStage, setCurrentStage] = useState<PipelineStage>('idle')
  const [progressMessage, setProgressMessage] = useState('')
  const [finalDocument, setFinalDocument] = useState('')
  const [eventLog, setEventLog] = useState<LogEvent[]>([])
  const startTimeRef = useRef<number>(0)

  const addEvent = (event: LogEvent) => {
    setEventLog(prev => [...prev, event])
  }

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!companyName) return

    setStatus('generating')
    setCurrentStage('RequirementCrew')
    setProgressMessage('Initializing pipeline...')
    setFinalDocument('')
    setEventLog([])
    startTimeRef.current = Date.now()

    addEvent({ type: 'info', message: `Starting ArchitectFlow for "${companyName}"`, timestamp: new Date() })

    try {
      const response = await fetch('http://localhost:8000/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company_name: companyName, user_requirements: requirements || 'none' })
      })

      if (!response.body) throw new Error('No readable stream available')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.replace('data: ', '').trim()
            if (!dataStr) continue

            try {
              const data = JSON.parse(dataStr)

              if (data.status === 'complete') {
                setStatus('complete')
                setCurrentStage('complete')
                setFinalDocument(data.document)
                const elapsed = Math.round((Date.now() - startTimeRef.current) / 1000)
                addEvent({ type: 'success', message: `Pipeline complete! Total time: ${elapsed}s`, timestamp: new Date() })
                return
              }

              if (data.status === 'error') {
                setStatus('error')
                setCurrentStage('error')
                setProgressMessage(data.message)
                addEvent({ type: 'error', message: data.message, timestamp: new Date() })
                return
              }

              if (data.status === 'warning') {
                setProgressMessage(`⚠️ ${data.message}`)
                addEvent({ type: 'warning', message: data.message, timestamp: new Date() })
                continue
              }

              if (data.status === 'info') {
                setProgressMessage(`⚡ ${data.message}`)
                addEvent({ type: 'info', message: data.message, timestamp: new Date() })
                continue
              }

              // Standard crew progress event
              setCurrentStage(data.crew as PipelineStage)
              setProgressMessage(data.message)
              addEvent({ type: 'crew', message: `[${data.crew}] ${data.message}`, crew: data.crew, timestamp: new Date() })

            } catch (err) {
              console.error("Failed to parse SSE event", err)
            }
          }
        }
      }
    } catch (error: unknown) {
      const msg = error instanceof Error ? error.message : 'An error occurred during generation.'
      console.error(error)
      setStatus('error')
      setCurrentStage('error')
      setProgressMessage(msg)
      addEvent({ type: 'error', message: msg, timestamp: new Date() })
    }
  }

  const resetForm = () => {
    setStatus('idle')
    setCompanyName('')
    setRequirements('')
    setCurrentStage('idle')
    setFinalDocument('')
    setEventLog([])
  }

  return (
    <div className="min-h-screen bg-[#020617] bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(120,119,198,0.3),rgba(255,255,255,0))] selection:bg-blue-500/30 flex flex-col font-sans">

      <header className="border-b border-slate-800/60 bg-slate-900/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 cursor-pointer" onClick={resetForm}>
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-emerald-400 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <Hexagon className="w-5 h-5 text-white fill-white/20" />
            </div>
            <span className="font-bold text-xl tracking-tight text-slate-100">Architect<span className="text-blue-400">Flow</span></span>
          </div>
          {status === 'complete' && (
            <Button variant="outline" size="sm" onClick={resetForm} className="border-slate-700 hover:bg-slate-800 text-slate-300">
              Start New Design
            </Button>
          )}
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center p-6 w-full max-w-7xl mx-auto py-12">

        {status === 'idle' && (
          <div className="w-full max-w-xl mx-auto animate-in fade-in slide-in-from-bottom-8 duration-700">
            <div className="text-center mb-10">
              <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white mb-4">
                Design <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">Scalable Systems</span>
              </h1>
              <p className="text-lg text-slate-400">
                Enter a company or product name, and our AI engineering team will architect a production-ready system.
              </p>
            </div>

            <Card className="border-slate-800 bg-slate-900/50 backdrop-blur shadow-2xl overflow-hidden">
              <div className="h-1 bg-gradient-to-r from-blue-500 via-teal-400 to-emerald-500 w-full"></div>
              <CardHeader>
                <CardTitle className="text-slate-200">System Parameters</CardTitle>
                <CardDescription className="text-slate-500">Provide the basics to kick off the design process.</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleGenerate} className="space-y-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">Company / Product Name *</label>
                    <Input
                      placeholder="e.g., Airbnb, Uber, Stripe..."
                      value={companyName}
                      onChange={(e) => setCompanyName(e.target.value)}
                      className="bg-slate-950/50 border-slate-700 text-slate-200 placeholder:text-slate-600 focus-visible:ring-blue-500 h-12"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">Specific Requirements (Optional)</label>
                    <Input
                      placeholder="e.g., Handle 50k RPS, Use microservices..."
                      value={requirements}
                      onChange={(e) => setRequirements(e.target.value)}
                      className="bg-slate-950/50 border-slate-700 text-slate-200 placeholder:text-slate-600 focus-visible:ring-blue-500 h-12"
                    />
                  </div>
                  <Button
                    type="submit"
                    className="w-full h-12 bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-500 hover:to-emerald-500 text-white font-medium shadow-lg shadow-blue-500/25 transition-all active:scale-[0.98]"
                    disabled={!companyName}
                  >
                    <Sparkles className="w-5 h-5 mr-2" />
                    Generate Architecture
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>
        )}

        {(status === 'generating' || status === 'error') && (
          <div className="w-full animate-in fade-in zoom-in-95 duration-500">
            <GenerationProgress currentStage={currentStage} message={progressMessage} eventLog={eventLog} />
            {status === 'error' && (
              <div className="mt-6 text-center">
                <Button variant="outline" onClick={resetForm} className="border-slate-700 text-slate-300">
                  Try Again
                </Button>
              </div>
            )}
          </div>
        )}

        {status === 'complete' && (
          <div className="w-full animate-in fade-in slide-in-from-bottom-12 duration-700 pb-16">
            <MarkdownRenderer content={finalDocument} />
          </div>
        )}

      </main>
    </div>
  )
}

export default App
