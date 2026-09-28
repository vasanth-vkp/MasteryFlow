import React from 'react';
import { CheckCircle2, Lock, Clock, ArrowRight, BookOpen, AlertOctagon, Star } from 'lucide-react';

export default function ConceptGraphView({ 
  graphData, 
  selectedConceptId, 
  onSelectConcept,
  recommendedConceptId
}) {
  if (!graphData || !graphData.nodes) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-300 font-medium">
        Loading concept knowledge graph...
      </div>
    );
  }

  // Group nodes by DAG depth level
  const levels = {};
  graphData.nodes.forEach((node) => {
    if (!levels[node.level]) levels[node.level] = [];
    levels[node.level].push(node);
  });

  const sortedLevels = Object.keys(levels)
    .map(Number)
    .sort((a, b) => a - b);

  const getStatusBadge = (node) => {
    if (node.decay_applied) {
      return {
        bg: 'bg-amber-500/20 border-amber-500/50 text-amber-300 font-bold',
        icon: <Clock className="h-3.5 w-3.5 text-amber-400" />,
        text: 'Decay / Review',
      };
    }
    if (node.status === 'mastered') {
      return {
        bg: 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300 font-bold',
        icon: <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />,
        text: 'Mastered',
      };
    }
    if (node.status === 'in_progress') {
      return {
        bg: 'bg-sky-500/20 border-sky-500/50 text-sky-300 font-semibold',
        icon: <BookOpen className="h-3.5 w-3.5 text-sky-400" />,
        text: 'In Progress',
      };
    }
    if (node.status === 'ready') {
      return {
        bg: 'bg-indigo-500/20 border-indigo-500/50 text-indigo-300 font-semibold',
        icon: <ArrowRight className="h-3.5 w-3.5 text-indigo-400" />,
        text: 'Ready to Learn',
      };
    }
    return {
      bg: 'bg-slate-800 border-slate-700 text-slate-300 font-medium',
      icon: <Lock className="h-3.5 w-3.5 text-slate-400" />,
      text: 'Locked Prereqs',
    };
  };

  return (
    <div className="bg-slate-900 border border-slate-700/80 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
      {/* Header & Legend */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center space-x-2.5">
            <h2 className="text-lg font-bold text-white tracking-tight">
              Algebra Prerequisite DAG Graph
            </h2>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-bold">
              {graphData.nodes.length} Dynamic Concepts
            </span>
          </div>
          <p className="text-xs text-slate-300 mt-1 font-medium">
            Topological curriculum hierarchy. Select any concept node to inspect its live Bayesian parameters or launch practice.
          </p>
        </div>

        {/* High-Visibility Legend */}
        <div className="flex flex-wrap items-center gap-2 text-[11px] font-semibold">
          <span className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-emerald-500/15 text-emerald-300 border border-emerald-500/40">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400" />
            <span>Mastered (≥85%)</span>
          </span>
          <span className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-sky-500/15 text-sky-300 border border-sky-500/40">
            <span className="h-2.5 w-2.5 rounded-full bg-sky-400 shadow-sm shadow-sky-400" />
            <span>Developing (40-84%)</span>
          </span>
          <span className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-amber-500/15 text-amber-300 border border-amber-500/40">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-400 shadow-sm shadow-amber-400" />
            <span>Retention Decay</span>
          </span>
          <span className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 border border-slate-700">
            <span className="h-2.5 w-2.5 rounded-full bg-slate-400" />
            <span>Locked (&lt;50% Prereq)</span>
          </span>
        </div>
      </div>

      {/* DAG Multi-Tier Flow Columns */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 overflow-x-auto pb-3">
        {sortedLevels.map((lvl) => (
          <div key={lvl} className="flex flex-col space-y-3.5 min-w-[210px]">
            {/* Level Column Header */}
            <div className="text-center py-2 px-3 rounded-xl bg-slate-950 border border-slate-700/80 text-[11px] font-bold text-indigo-300 uppercase tracking-wider shadow-inner">
              {lvl === 1 ? 'Tier 1 • Roots' : lvl === 2 ? 'Tier 2 • Building' : lvl === 3 ? 'Tier 3 • Intermediate' : lvl === 4 ? 'Tier 4 • Equations' : 'Tier 5 • Advanced'}
            </div>

            {/* Nodes in this level */}
            <div className="space-y-3">
              {levels[lvl].map((node) => {
                const isSelected = selectedConceptId === node.id;
                const isRecommended = recommendedConceptId === node.id;
                const badge = getStatusBadge(node);
                const scorePct = Math.round(node.mastery_score * 100);

                return (
                  <div
                    key={node.id}
                    onClick={() => onSelectConcept(node.id)}
                    className={`group relative p-4 rounded-xl border transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-indigo-950/70 border-indigo-400 shadow-xl shadow-indigo-500/25 ring-2 ring-indigo-500/30 scale-[1.02]'
                        : isRecommended
                        ? 'bg-violet-950/50 border-violet-400 shadow-lg shadow-violet-500/20 hover:border-violet-300'
                        : 'bg-slate-950/70 border-slate-700/80 hover:border-slate-500 hover:bg-slate-900 shadow-sm'
                    }`}
                  >
                    {/* Recommended Star Badge */}
                    {isRecommended && (
                      <span className="absolute -top-2.5 -right-1.5 flex h-5 w-5">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violet-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-5 w-5 bg-gradient-to-tr from-violet-600 to-indigo-500 text-[10px] font-bold text-white items-center justify-center shadow-md">
                          ★
                        </span>
                      </span>
                    )}

                    {/* Concept Name */}
                    <div className="flex items-start justify-between gap-1 mb-2">
                      <h4 className="text-xs font-bold text-white group-hover:text-indigo-300 transition-colors leading-snug">
                        {node.name}
                      </h4>
                    </div>

                    {/* Status Badge & Mastery Score */}
                    <div className="flex items-center justify-between mb-3">
                      <span className={`inline-flex items-center space-x-1.5 text-[10px] px-2 py-0.5 rounded-md border ${badge.bg}`}>
                        {badge.icon}
                        <span>{badge.text}</span>
                      </span>

                      <span className={`text-sm font-mono font-extrabold ${
                        node.decay_applied ? 'text-amber-300' :
                        scorePct >= 85 ? 'text-emerald-300' :
                        scorePct >= 40 ? 'text-sky-300' : 'text-slate-300'
                      }`}>
                        {scorePct}%
                      </span>
                    </div>

                    {/* Progress Bar with glow */}
                    <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden p-0.5">
                      <div
                        className={`h-full transition-all duration-500 rounded-full ${
                          node.decay_applied
                            ? 'bg-amber-400 shadow-sm shadow-amber-400'
                            : scorePct >= 85
                            ? 'bg-emerald-400 shadow-sm shadow-emerald-400'
                            : scorePct >= 40
                            ? 'bg-sky-400 shadow-sm shadow-sky-400'
                            : 'bg-slate-500'
                        }`}
                        style={{ width: `${Math.min(100, Math.max(4, scorePct))}%` }}
                      />
                    </div>

                    {/* Evidence & Prerequisite Metadata */}
                    <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-300 font-medium">
                      <span>Prereqs: {node.prerequisites ? node.prerequisites.length : 0}</span>
                      <span className="font-mono text-slate-200">Evidence: {node.evidence_count}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
