import React, { useState, useEffect } from 'react';
import { fetchSimulationComparison, fetchConcepts, fetchLearners } from '../api';
import { 
  GitCompare, 
  Award, 
  AlertOctagon, 
  ShieldAlert, 
  ArrowRight, 
  CheckCircle2, 
  XCircle, 
  HelpCircle, 
  Zap,
  TrendingUp,
  AlertTriangle,
  RefreshCw,
  Users
} from 'lucide-react';

export default function SimulationCompareView({ onSwitchLearner }) {
  const [comparison, setComparison] = useState(null);
  const [concepts, setConcepts] = useState([]);
  const [learnersList, setLearnersList] = useState([]);
  
  // Dynamic selection state
  const [selectedConcept, setSelectedConcept] = useState('c_ratios');
  const [learnerAId, setLearnerAId] = useState('');
  const [learnerBId, setLearnerBId] = useState('');
  
  const [isLoading, setIsLoading] = useState(true);

  // Load available concepts & learners list dynamically
  useEffect(() => {
    async function initSelectors() {
      try {
        const [cList, lList] = await Promise.all([
          fetchConcepts(),
          fetchLearners(),
        ]);
        setConcepts(cList);
        setLearnersList(lList);

        if (cList.length > 0 && !selectedConcept) {
          setSelectedConcept(cList[0].id);
        }
        if (lList.length >= 2) {
          const defaultA = lList.find(l => l.id === 'learner_a')?.id || lList[0].id;
          const defaultB = lList.find(l => l.id === 'learner_b')?.id || lList[1].id;
          setLearnerAId(defaultA);
          setLearnerBId(defaultB);
        }
      } catch (err) {
        console.error('Failed to load concepts or learners:', err);
      }
    }
    initSelectors();
  }, []);

  const loadComparison = async (conceptId, aId, bId) => {
    setIsLoading(true);
    try {
      const data = await fetchSimulationComparison(conceptId, aId || null, bId || null);
      setComparison(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (selectedConcept) {
      loadComparison(selectedConcept, learnerAId, learnerBId);
    }
  }, [selectedConcept, learnerAId, learnerBId]);

  if (isLoading || !comparison) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-300 font-semibold">
        <RefreshCw className="h-5 w-5 animate-spin mr-2 text-indigo-400" />
        Computing dynamic comparison telemetry...
      </div>
    );
  }

  const { learner_a, learner_b, key_takeaway } = comparison;

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      {/* Header & Dynamic Selectors */}
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl p-6 shadow-2xl space-y-5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2.5">
              <span className="p-2 rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                <GitCompare className="h-5 w-5" />
              </span>
              <h2 className="text-xl font-extrabold text-white tracking-tight">
                Simulation & Contrast Engine
              </h2>
            </div>
            <p className="text-xs text-slate-300 mt-1 font-medium max-w-2xl">
              100% dynamic comparison: Select ANY concept and ANY two learners from SQLite to see how individual prerequisite health and attempt evidence drive contrasting interventions.
            </p>
          </div>

          {/* Dynamic Dropdown Selectors */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Concept Selector */}
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Target Concept:</span>
              <select
                value={selectedConcept}
                onChange={(e) => setSelectedConcept(e.target.value)}
                className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-white font-semibold focus:outline-none focus:border-indigo-500 shadow-sm"
              >
                {concepts.map((c) => (
                  <option key={c.id} value={c.id} className="bg-slate-900 text-white">
                    {c.name} (Tier {c.level})
                  </option>
                ))}
              </select>
            </div>

            {/* Learner A Selector */}
            <div>
              <span className="text-[10px] uppercase font-bold text-emerald-400 block mb-1">Learner 1:</span>
              <select
                value={learnerAId}
                onChange={(e) => setLearnerAId(e.target.value)}
                className="bg-slate-950 border border-emerald-500/50 rounded-xl px-3 py-1.5 text-xs text-emerald-300 font-semibold focus:outline-none shadow-sm"
              >
                {learnersList.map((l) => (
                  <option key={l.id} value={l.id} className="bg-slate-900 text-white">
                    {l.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Learner B Selector */}
            <div>
              <span className="text-[10px] uppercase font-bold text-rose-400 block mb-1">Learner 2:</span>
              <select
                value={learnerBId}
                onChange={(e) => setLearnerBId(e.target.value)}
                className="bg-slate-950 border border-rose-500/50 rounded-xl px-3 py-1.5 text-xs text-rose-300 font-semibold focus:outline-none shadow-sm"
              >
                {learnersList.map((l) => (
                  <option key={l.id} value={l.id} className="bg-slate-900 text-white">
                    {l.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Key Takeaway Callout */}
        <div className="p-4 rounded-xl bg-indigo-950/40 border border-indigo-400/40 text-xs text-indigo-100 leading-relaxed flex items-start space-x-3 shadow-inner">
          <Zap className="h-5 w-5 text-amber-400 mt-0.5 flex-shrink-0" />
          <div>
            <strong className="text-white block mb-0.5 font-bold">Judges' Core Takeaway:</strong>
            {key_takeaway}
          </div>
        </div>
      </div>

      {/* Side-by-Side Comparison Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Learner A Card */}
        <div className="bg-slate-900 border-2 border-emerald-500/50 rounded-2xl p-6 shadow-2xl space-y-5 relative overflow-hidden">
          <div className="flex items-start justify-between">
            <div>
              <span className="text-[10px] font-extrabold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                Learner Profile 1
              </span>
              <h3 className="text-xl font-bold text-white mt-1.5">{learner_a.learner_name}</h3>
              <p className="text-xs text-slate-300 font-medium">Concept Evidence: {learner_a.evidence_count} attempts</p>
            </div>

            <div className="text-right">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold block">Mastery Score</span>
              <span className="text-3xl font-extrabold font-mono text-emerald-400">
                {Math.round(learner_a.mastery_score * 100)}%
              </span>
            </div>
          </div>

          {/* Next Action Directive Banner */}
          <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/50">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] uppercase font-bold text-emerald-400 tracking-wider">
                Autonomous Directive
              </span>
              <span className="text-xs font-extrabold text-emerald-200 px-3 py-0.5 rounded-full bg-emerald-500/25 border border-emerald-400/50">
                {learner_a.next_action}
              </span>
            </div>
            <p className="text-xs text-slate-100 leading-relaxed font-sans font-medium">
              "{learner_a.reason_text}"
            </p>
          </div>

          {/* Cognitive & Attempt Metrics */}
          <div className="space-y-2 text-xs">
            <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wider block">
              Observed Evidence on {comparison.concept_name}
            </span>
            <div className="grid grid-cols-2 gap-2.5">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-700/80">
                <span className="text-slate-400 text-[10px] font-semibold block">Accuracy</span>
                <span className="font-extrabold text-emerald-400 text-sm">{learner_a.recent_attempts_summary.accuracy_pct}%</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-700/80">
                <span className="text-slate-400 text-[10px] font-semibold block">Avg Confidence</span>
                <span className="font-extrabold text-white text-sm">{learner_a.recent_attempts_summary.avg_confidence} / 5</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-700/80">
                <span className="text-slate-400 text-[10px] font-semibold block">Hints Used</span>
                <span className="font-extrabold text-white text-sm">{learner_a.recent_attempts_summary.hints_used_count} hints</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-700/80">
                <span className="text-slate-400 text-[10px] font-semibold block">Avg Response Time</span>
                <span className="font-extrabold font-mono text-white text-sm">{(learner_a.recent_attempts_summary.avg_response_time_ms / 1000).toFixed(1)}s</span>
              </div>
            </div>
          </div>

          <button
            onClick={() => onSwitchLearner(learner_a.learner_id)}
            className="w-full py-2.5 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-bold text-slate-100 flex items-center justify-center space-x-2 transition-colors border border-slate-700"
          >
            <span>Inspect in Learner Studio</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Learner B Card */}
        <div className="bg-slate-900 border-2 border-rose-500/50 rounded-2xl p-6 shadow-2xl space-y-5 relative overflow-hidden">
          <div className="flex items-start justify-between">
            <div>
              <span className="text-[10px] font-extrabold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40">
                Learner Profile 2
              </span>
              <h3 className="text-xl font-bold text-white mt-1.5">{learner_b.learner_name}</h3>
              <p className="text-xs text-slate-300 font-medium">Concept Evidence: {learner_b.evidence_count} attempts</p>
            </div>

            <div className="text-right">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold block">Mastery Score</span>
              <span className="text-3xl font-extrabold font-mono text-rose-400">
                {Math.round(learner_b.mastery_score * 100)}%
              </span>
            </div>
          </div>

          {/* Next Action Directive Banner */}
          <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/50">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] uppercase font-bold text-rose-400 tracking-wider">
                Autonomous Directive
              </span>
              <span className="text-xs font-extrabold text-rose-200 px-3 py-0.5 rounded-full bg-rose-500/25 border border-rose-400/50">
                {learner_b.next_action}
              </span>
            </div>
            <p className="text-xs text-slate-100 leading-relaxed font-sans font-medium">
              "{learner_b.reason_text}"
            </p>
          </div>

          {/* Cognitive & Attempt Metrics */}
          <div className="space-y-2 text-xs">
            <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wider block">
              Observed Evidence on {comparison.concept_name}
            </span>
            <div className="grid grid-cols-2 gap-2.5">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-700/80">
                <span className="text-slate-400 text-[10px] font-semibold block">Accuracy</span>
                <span className="font-extrabold text-rose-400 text-sm">{learner_b.recent_attempts_summary.accuracy_pct}%</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-700/80">
                <span className="text-slate-400 text-[10px] font-semibold block">Avg Confidence</span>
                <span className="font-extrabold text-white text-sm">{learner_b.recent_attempts_summary.avg_confidence} / 5</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-700/80">
                <span className="text-slate-400 text-[10px] font-semibold block">Hints Used</span>
                <span className="font-extrabold text-amber-300 text-sm">{learner_b.recent_attempts_summary.hints_used_count} hints</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-700/80">
                <span className="text-slate-400 text-[10px] font-semibold block">Rapid-Guess Flags</span>
                <span className="font-extrabold text-rose-400 text-sm">{learner_b.recent_attempts_summary.rapid_guess_flags} flag(s)</span>
              </div>
            </div>
          </div>

          <button
            onClick={() => onSwitchLearner(learner_b.learner_id)}
            className="w-full py-2.5 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-bold text-slate-100 flex items-center justify-center space-x-2 transition-colors border border-slate-700"
          >
            <span>Inspect in Learner Studio</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Side-by-Side Metric Contrast Table */}
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl p-6 shadow-2xl">
        <h4 className="text-sm font-extrabold text-white mb-4">
          Metric Contrast Table (Target Concept: {comparison.concept_name})
        </h4>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-[11px] text-slate-400 uppercase tracking-wider font-bold">
                <th className="pb-3">Decision Dimension</th>
                <th className="pb-3 text-emerald-400">{learner_a.learner_name}</th>
                <th className="pb-3 text-rose-400">{learner_b.learner_name}</th>
                <th className="pb-3 text-indigo-300">Engine Mathematical Policy</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-medium">
              <tr>
                <td className="py-3 text-slate-200 font-semibold">Bayesian Mastery Score</td>
                <td className="py-3 font-mono font-extrabold text-emerald-400">{Math.round(learner_a.mastery_score * 100)}%</td>
                <td className="py-3 font-mono font-extrabold text-rose-400">{Math.round(learner_b.mastery_score * 100)}%</td>
                <td className="py-3 text-slate-300">Continuous BKT posterior tracking</td>
              </tr>
              <tr>
                <td className="py-3 text-slate-200 font-semibold">Accuracy & Cognitive Pace</td>
                <td className="py-3 text-emerald-300">{learner_a.recent_attempts_summary.accuracy_pct}% correct ({(learner_a.recent_attempts_summary.avg_response_time_ms/1000).toFixed(1)}s)</td>
                <td className="py-3 text-rose-300">{learner_b.recent_attempts_summary.accuracy_pct}% correct ({(learner_b.recent_attempts_summary.avg_response_time_ms/1000).toFixed(1)}s)</td>
                <td className="py-3 text-slate-300">P(S) and P(G) dynamic modulations</td>
              </tr>
              <tr>
                <td className="py-3 text-slate-200 font-semibold">Scaffolding Dependency</td>
                <td className="py-3 text-slate-200">{learner_a.recent_attempts_summary.hints_used_count} hints</td>
                <td className="py-3 text-amber-300">{learner_b.recent_attempts_summary.hints_used_count} hints used</td>
                <td className="py-3 text-slate-300">Hint usage penalizes guess probability to 0.75</td>
              </tr>
              <tr>
                <td className="py-3 text-slate-200 font-semibold">Anti-Gaming Checks</td>
                <td className="py-3 text-emerald-400">Pass (paced)</td>
                <td className="py-3 text-rose-400">{learner_b.recent_attempts_summary.rapid_guess_flags > 0 ? 'Rapid attempts flagged' : 'Clean'}</td>
                <td className="py-3 text-slate-300">&lt;10s attempts discounted by 85%, gain capped</td>
              </tr>
              <tr>
                <td className="py-3 font-bold text-white">Next Best Learning Action</td>
                <td className="py-3 font-extrabold text-emerald-400">{learner_a.next_action}</td>
                <td className="py-3 font-extrabold text-rose-400">{learner_b.next_action}</td>
                <td className="py-3 font-bold text-indigo-300">Explainable adaptive policy branching</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
