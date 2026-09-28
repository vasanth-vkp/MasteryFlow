import React, { useState, useEffect } from 'react';
import { fetchTeacherDashboard } from '../api';
import TeacherOverrideModal from './TeacherOverrideModal';
import { 
  GraduationCap, 
  AlertTriangle, 
  ShieldAlert, 
  ShieldCheck, 
  Clock, 
  RefreshCw, 
  Search, 
  SlidersHorizontal,
  ArrowUpRight,
  UserX,
  FileText
} from 'lucide-react';

export default function TeacherDashboardView({ onSelectLearner }) {
  const [dashboardData, setDashboardData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isOverrideModalOpen, setIsOverrideModalOpen] = useState(false);
  const [selectedLearnerForOverride, setSelectedLearnerForOverride] = useState('');
  const [selectedConceptForOverride, setSelectedConceptForOverride] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const loadData = async () => {
    setIsLoading(true);
    try {
      const data = await fetchTeacherDashboard();
      setDashboardData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (isLoading || !dashboardData) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-300 font-semibold">
        <RefreshCw className="h-5 w-5 animate-spin mr-2 text-indigo-400" />
        Loading educator telemetry & heatmap matrix...
      </div>
    );
  }

  const { learners, concepts, stuck_learner_ids, recent_actions } = dashboardData;

  // Filter learners by search
  const filteredLearners = learners.filter(l => 
    l.learner_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    l.learner_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalOverrides = recent_actions.filter(a => a.was_teacher_override).length;

  const handleOpenOverride = (learnerId = '', conceptId = '') => {
    setSelectedLearnerForOverride(learnerId);
    setSelectedConceptForOverride(conceptId);
    setIsOverrideModalOpen(true);
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header & KPI Summary */}
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl p-6 shadow-2xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2.5">
              <span className="p-2 rounded-xl bg-pink-500/20 text-pink-300 border border-pink-500/40">
                <GraduationCap className="h-5 w-5" />
              </span>
              <h2 className="text-xl font-extrabold text-white tracking-tight">
                Teacher Intervention & Mastery Dashboard
              </h2>
            </div>
            <p className="text-xs text-slate-300 mt-1 font-medium">
              Real-time classroom telemetry: Concept heatmap matrix, stuck-learner triage, and educator override controls.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => handleOpenOverride()}
              className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-pink-600 to-indigo-600 hover:from-pink-500 hover:to-indigo-500 text-white font-extrabold text-xs shadow-md shadow-pink-600/25 flex items-center space-x-1.5 transition-all"
            >
              <ShieldCheck className="h-4 w-4" />
              <span>Apply Teacher Override</span>
            </button>

            <button
              onClick={loadData}
              className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors shadow-sm"
              title="Refresh Dashboard"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* 4 KPI Metrics with high contrast */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-1">
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-700/80">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider font-bold block">Total Learners</span>
            <span className="text-2xl font-extrabold font-mono text-white">{learners.length}</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-700/80">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider font-bold block">Curriculum Concepts</span>
            <span className="text-2xl font-extrabold font-mono text-indigo-400">{concepts.length}</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-700/80">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider font-bold block">Stuck Learners</span>
            <span className="text-2xl font-extrabold font-mono text-rose-400">{stuck_learner_ids.length}</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-700/80">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider font-bold block">Teacher Overrides</span>
            <span className="text-2xl font-extrabold font-mono text-pink-400">{totalOverrides}</span>
          </div>
        </div>
      </div>

      {/* Stuck Learners Alert Bar */}
      {stuck_learner_ids.length > 0 && (
        <div className="bg-rose-950/40 border-2 border-rose-500/50 rounded-2xl p-5 shadow-2xl space-y-3.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-rose-300">
              <ShieldAlert className="h-5 w-5 text-rose-400" />
              <h3 className="text-sm font-extrabold tracking-tight">
                Attention Required: {stuck_learner_ids.length} Stuck Learner(s) Flagged by Algorithmic Engine
              </h3>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {learners.filter(l => stuck_learner_ids.includes(l.learner_id)).map((stuck) => (
              <div key={stuck.learner_id} className="p-4 rounded-xl bg-slate-950 border border-rose-500/40 flex items-start justify-between gap-3 shadow-md">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-bold text-white">{stuck.learner_name}</span>
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-rose-500/25 text-rose-200 border border-rose-500/40">
                      {stuck.current_action?.action || 'Stuck'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-200 mt-1.5 line-clamp-2 leading-relaxed font-medium">
                    {stuck.stuck_reason || stuck.current_action?.reason_text}
                  </p>
                </div>

                <button
                  onClick={() => handleOpenOverride(stuck.learner_id, stuck.current_action?.concept_id)}
                  className="px-3 py-1.5 rounded-lg bg-pink-600 hover:bg-pink-500 text-xs font-bold text-white flex-shrink-0 transition-colors shadow-sm"
                >
                  Intervene
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Mastery Heatmap Matrix */}
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl p-6 shadow-2xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-extrabold text-white">
              Learner × Concept Knowledge Heatmap Matrix
            </h3>
            <p className="text-xs text-slate-300 font-medium">
              Click any cell to inspect or forcefully override next action for that learner.
            </p>
          </div>

          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search learners..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-xl pl-9 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500 font-medium"
            />
          </div>
        </div>

        {/* Heatmap Table */}
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800">
                <th className="p-3 font-bold text-slate-300 bg-slate-950 sticky left-0 z-10 min-w-[160px]">
                  Learner Name
                </th>
                <th className="p-3 font-bold text-slate-300 text-center min-w-[70px]">
                  Avg
                </th>
                {concepts.map((c) => (
                  <th key={c.id} className="p-2 font-semibold text-slate-300 text-center min-w-[90px]">
                    <div className="text-[10px] font-bold text-slate-200 truncate max-w-[85px]" title={c.name}>
                      {c.name.split(' ')[0]}
                    </div>
                    <span className="text-[9px] text-indigo-400 font-mono font-bold">Tier {c.level}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {filteredLearners.map((lrn) => (
                <tr key={lrn.learner_id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="p-3 font-bold text-white bg-slate-950 sticky left-0 z-10 flex items-center justify-between">
                    <div>
                      <span className="block truncate max-w-[130px] font-semibold">{lrn.learner_name}</span>
                      <span className="text-[10px] font-mono text-slate-400">{lrn.learner_id}</span>
                    </div>
                    {lrn.is_stuck && (
                      <span className="h-2.5 w-2.5 rounded-full bg-rose-500 flex-shrink-0 animate-pulse" title="Intervention Needed" />
                    )}
                  </td>

                  <td className="p-3 text-center font-mono font-extrabold text-indigo-400 text-sm">
                    {Math.round(lrn.average_mastery * 100)}%
                  </td>

                  {lrn.mastery_cells.map((cell) => {
                    const pct = Math.round(cell.mastery_score * 100);
                    let cellBg = 'bg-slate-950 text-slate-500 border border-slate-800';

                    if (cell.decay_applied) {
                      cellBg = 'bg-amber-500/25 text-amber-200 border-2 border-amber-500/60 font-bold';
                    } else if (pct >= 85) {
                      cellBg = 'bg-emerald-500/25 text-emerald-200 border-2 border-emerald-500/60 font-extrabold';
                    } else if (pct >= 40) {
                      cellBg = 'bg-sky-500/25 text-sky-200 border border-sky-500/50 font-bold';
                    } else if (cell.evidence_count > 0) {
                      cellBg = 'bg-rose-500/25 text-rose-200 border border-rose-500/50 font-bold';
                    }

                    return (
                      <td key={cell.concept_id} className="p-1 text-center">
                        <div
                          onClick={() => handleOpenOverride(lrn.learner_id, cell.concept_id)}
                          className={`py-2 px-1 rounded-lg text-xs font-mono cursor-pointer transition-all hover:scale-105 shadow-sm ${cellBg}`}
                          title={`${cell.concept_name}: ${pct}% (${cell.evidence_count} evidence items)`}
                        >
                          {cell.evidence_count > 0 ? `${pct}%` : '—'}
                          {cell.decay_applied && <Clock className="inline h-3 w-3 ml-0.5 text-amber-400" />}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Action & Override Audit Trail */}
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl p-6 shadow-2xl space-y-4">
        <h3 className="text-base font-extrabold text-white flex items-center space-x-2">
          <FileText className="h-5 w-5 text-indigo-400" />
          <span>Action Log & Teacher Override Audit Trail</span>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700 font-bold">
            {recent_actions.length} Decisions Logged
          </span>
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-[11px] text-slate-400 uppercase tracking-wider font-bold">
                <th className="pb-3">Timestamp</th>
                <th className="pb-3">Learner</th>
                <th className="pb-3">Concept</th>
                <th className="pb-3">Action</th>
                <th className="pb-3">Explainable Rationale</th>
                <th className="pb-3 text-center">Source</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-medium">
              {recent_actions.map((act) => (
                <tr key={act.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 text-[11px] font-mono text-slate-400 whitespace-nowrap">
                    {new Date(act.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </td>
                  <td className="py-3 font-semibold text-white whitespace-nowrap">
                    {act.learner_id}
                  </td>
                  <td className="py-3 text-slate-200 font-semibold whitespace-nowrap">
                    {act.concept_name}
                  </td>
                  <td className="py-3 whitespace-nowrap">
                    <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                      act.action === 'Challenge' ? 'bg-purple-500/25 text-purple-200 border border-purple-400/50' :
                      act.action === 'Advance' ? 'bg-emerald-500/25 text-emerald-200 border border-emerald-400/50' :
                      act.action === 'Review' ? 'bg-amber-500/25 text-amber-200 border border-amber-400/50' :
                      act.action === 'RemediatePrerequisite' ? 'bg-rose-500/25 text-rose-200 border border-rose-400/50' :
                      act.action === 'TeacherIntervention' ? 'bg-red-500/35 text-red-100 border border-red-400/50' :
                      'bg-sky-500/25 text-sky-200 border border-sky-400/50'
                    }`}>
                      {act.action}
                    </span>
                  </td>
                  <td className="py-3 text-slate-200 max-w-md text-xs leading-relaxed font-sans">
                    {act.reason_text}
                  </td>
                  <td className="py-3 text-center whitespace-nowrap">
                    {act.was_teacher_override ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-pink-500/25 text-pink-200 border border-pink-500/40">
                        Teacher Override
                      </span>
                    ) : (
                      <span className="text-[10px] font-mono text-slate-400 font-semibold">
                        Engine Policy
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Teacher Override Modal */}
      <TeacherOverrideModal
        isOpen={isOverrideModalOpen}
        onClose={() => setIsOverrideModalOpen(false)}
        learners={learners.map(l => ({ id: l.learner_id, name: l.learner_name }))}
        concepts={concepts}
        onOverrideSuccess={loadData}
        defaultLearnerId={selectedLearnerForOverride}
        defaultConceptId={selectedConceptForOverride}
      />
    </div>
  );
}
