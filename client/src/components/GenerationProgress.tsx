import React, { useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { CheckCircle2, Circle, Loader2, AlertTriangle, Info, Zap, XCircle } from 'lucide-react';

export type PipelineStage =
  | 'idle'
  | 'RequirementCrew'
  | 'ArchitectureCrew'
  | 'SubsystemCrew'
  | 'ReviewCrew'
  | 'DocumentationCrew'
  | 'complete'
  | 'error';

export interface LogEvent {
  type: 'crew' | 'info' | 'warning' | 'error' | 'success';
  message: string;
  timestamp: Date;
  crew?: string;
}

interface GenerationProgressProps {
  currentStage: PipelineStage;
  message: string;
  eventLog: LogEvent[];
}

const STAGES = [
  { id: 'RequirementCrew', label: 'Requirement Analysis', icon: '📋', description: 'Analyzing business & technical requirements' },
  { id: 'ArchitectureCrew', label: 'Architecture Design', icon: '🏗️', description: 'Selecting technologies & drawing the high-level system' },
  { id: 'SubsystemCrew', label: 'Subsystem Design', icon: '⚙️', description: 'Defining APIs, schemas, and message queues' },
  // ReviewCrew disabled — uncomment to re-enable
  // { id: 'ReviewCrew', label: 'Design Review', icon: '🔍', description: 'Critiquing for security, scalability & reliability' },
  { id: 'DocumentationCrew', label: 'Documentation', icon: '📄', description: 'Compiling final Markdown & Mermaid diagrams' },
];

const LOG_ICONS = {
  crew: <Zap className="w-3.5 h-3.5 text-blue-400 shrink-0" />,
  info: <Info className="w-3.5 h-3.5 text-sky-400 shrink-0" />,
  warning: <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />,
  error: <XCircle className="w-3.5 h-3.5 text-red-400 shrink-0" />,
  success: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />,
};

const LOG_COLORS = {
  crew: 'text-slate-300',
  info: 'text-sky-300',
  warning: 'text-amber-300 font-medium',
  error: 'text-red-300 font-medium',
  success: 'text-emerald-300 font-medium',
};

const LOG_BG = {
  crew: '',
  info: '',
  warning: 'bg-amber-500/5 border-l-2 border-amber-500/50 pl-2',
  error: 'bg-red-500/5 border-l-2 border-red-500/50 pl-2',
  success: 'bg-emerald-500/5 border-l-2 border-emerald-500/50 pl-2',
};

export const GenerationProgress: React.FC<GenerationProgressProps> = ({ currentStage, message, eventLog }) => {
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [eventLog]);

  const getStageStatus = (stageId: string) => {
    if (currentStage === 'complete') return 'completed';
    if (currentStage === 'error') return 'error';
    if (currentStage === 'idle') return 'pending';
    const currentIndex = STAGES.findIndex(s => s.id === currentStage);
    const stageIndex = STAGES.findIndex(s => s.id === stageId);
    if (stageIndex < currentIndex) return 'completed';
    if (stageIndex === currentIndex) return 'active';
    return 'pending';
  };

  const getProgressPercentage = () => {
    if (currentStage === 'complete') return 100;
    if (currentStage === 'idle' || currentStage === 'error') return 0;
    const currentIndex = STAGES.findIndex(s => s.id === currentStage);
    return Math.max(8, ((currentIndex) / STAGES.length) * 100);
  };

  const hasWarning = message.includes('⚠️');
  const hasInfo = message.includes('⚡');

  return (
    <div className="w-full max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-5 gap-6">

      {/* Left: Pipeline stages */}
      <div className="lg:col-span-3">
        <Card className="shadow-xl border-slate-800 bg-slate-900/60 backdrop-blur-sm text-slate-100 h-full">
          <CardHeader className="pb-4">
            <CardTitle className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
              AI Pipeline Running
            </CardTitle>
            <div className="mt-3">
              <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
                <span>Overall Progress</span>
                <span>{Math.round(getProgressPercentage())}%</span>
              </div>
              <Progress value={getProgressPercentage()} className="h-1.5 bg-slate-800" />
            </div>

            {/* Current status message */}
            <div className={`mt-3 flex items-center gap-2 text-sm px-3 py-2 rounded-lg transition-all ${
              hasWarning ? 'bg-amber-500/10 border border-amber-500/20 text-amber-300' :
              hasInfo ? 'bg-blue-500/10 border border-blue-500/20 text-blue-300' :
              'bg-slate-800/50 border border-slate-700/50 text-slate-400'
            }`}>
              {hasWarning && <AlertTriangle className="w-4 h-4 shrink-0" />}
              {hasInfo && <Zap className="w-4 h-4 shrink-0" />}
              {!hasWarning && !hasInfo && <Loader2 className="w-4 h-4 shrink-0 animate-spin text-blue-400" />}
              <span className="truncate">{message || 'Initializing AI pipeline...'}</span>
            </div>
          </CardHeader>

          <CardContent className="space-y-3 pt-0">
            {STAGES.map((stage) => {
              const status = getStageStatus(stage.id);
              return (
                <div
                  key={stage.id}
                  className={`flex items-center gap-4 p-3 rounded-xl border transition-all duration-500 ${
                    status === 'active' ? 'bg-blue-600/10 border-blue-500/30 shadow-[0_0_20px_rgba(59,130,246,0.08)]' :
                    status === 'completed' ? 'bg-emerald-600/5 border-emerald-500/20' :
                    'bg-slate-800/20 border-slate-800/50'
                  }`}
                >
                  {/* Status icon */}
                  <div className={`flex items-center justify-center w-9 h-9 rounded-full border-2 shrink-0 transition-all ${
                    status === 'completed' ? 'bg-emerald-500 border-emerald-400' :
                    status === 'active' ? 'bg-blue-600 border-blue-400 shadow-[0_0_12px_rgba(59,130,246,0.5)]' :
                    'bg-slate-800 border-slate-700'
                  }`}>
                    {status === 'completed' && <CheckCircle2 className="w-4 h-4 text-white" />}
                    {status === 'active' && <Loader2 className="w-4 h-4 text-white animate-spin" />}
                    {status === 'pending' && <Circle className="w-4 h-4 text-slate-600" />}
                    {status === 'error' && <XCircle className="w-4 h-4 text-red-400" />}
                  </div>

                  {/* Stage info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-base">{stage.icon}</span>
                      <h4 className={`font-semibold text-sm ${
                        status === 'active' ? 'text-blue-300' :
                        status === 'completed' ? 'text-emerald-300' :
                        'text-slate-500'
                      }`}>
                        {stage.label}
                      </h4>
                    </div>
                    <p className={`text-xs mt-0.5 truncate ${
                      status === 'active' ? 'text-slate-400' : 'text-slate-600'
                    }`}>
                      {stage.description}
                    </p>
                  </div>

                  {/* Active badge */}
                  {status === 'active' && (
                    <span className="shrink-0 text-xs font-mono text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded-full border border-blue-500/20 animate-pulse">
                      running
                    </span>
                  )}
                  {status === 'completed' && (
                    <span className="shrink-0 text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                      done
                    </span>
                  )}
                </div>
              );
            })}
          </CardContent>
        </Card>
      </div>

      {/* Right: Live activity log */}
      <div className="lg:col-span-2">
        <Card className="shadow-xl border-slate-800 bg-slate-900/60 backdrop-blur-sm text-slate-100 h-full flex flex-col">
          <CardHeader className="pb-3 shrink-0">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-semibold text-slate-300 flex items-center gap-2">
                <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                Live Activity Log
              </CardTitle>
              <span className="text-xs text-slate-600 font-mono">{eventLog.length} events</span>
            </div>
            <p className="text-xs text-slate-600 mt-1">
              Real-time events from the AI pipeline. Rate limit events are displayed transparently here — this is an <span className="text-amber-400/80">API quota</span> constraint, not a server error.
            </p>
          </CardHeader>

          <CardContent className="flex-1 overflow-hidden pt-0 px-3">
            <div className="h-[340px] lg:h-full overflow-y-auto space-y-1.5 pr-1 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
              {eventLog.length === 0 && (
                <div className="flex items-center justify-center h-20 text-slate-600 text-xs">
                  Waiting for events...
                </div>
              )}
              {eventLog.map((event, i) => (
                <div
                  key={i}
                  className={`flex items-start gap-2 py-1.5 px-2 rounded-md transition-all animate-in fade-in slide-in-from-bottom-1 duration-200 ${LOG_BG[event.type]}`}
                >
                  <span className="mt-0.5">{LOG_ICONS[event.type]}</span>
                  <div className="flex-1 min-w-0">
                    <p className={`text-xs leading-relaxed ${LOG_COLORS[event.type]}`}>
                      {event.message}
                    </p>
                    <span className="text-[10px] text-slate-600 font-mono">
                      {event.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))}
              <div ref={logEndRef} />
            </div>
          </CardContent>
        </Card>
      </div>

    </div>
  );
};
