import React, { useState, useEffect } from 'react';
import { 
  fetchConceptGraph, 
  fetchNextAction, 
  fetchPracticeQuestions, 
  submitLearningAttempt,
  fetchLearnerDetail
} from '../api';
import ConceptGraphView from './ConceptGraphView';
import { 
  Sparkles, 
  ArrowRight, 
  HelpCircle, 
  ShieldAlert, 
  Clock, 
  BrainCircuit, 
  CheckCircle, 
  XCircle, 
  Lightbulb, 
  Award, 
  Zap, 
  AlertOctagon,
  RefreshCw,
  ChevronRight,
  ChevronLeft
} from 'lucide-react';

export default function LearnerStudio({ currentLearnerId }) {
  const [graphData, setGraphData] = useState(null);
  const [learnerDetail, setLearnerDetail] = useState(null);
  const [nextAction, setNextAction] = useState(null);
  const [selectedConceptId, setSelectedConceptId] = useState(null);
  const [practiceQuestions, setPracticeQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  // Attempt Simulator Form State
  const [selectedOption, setSelectedOption] = useState('');
  const [confidence, setConfidence] = useState(4);
  const [responseTimeMs, setResponseTimeMs] = useState(14000);
  const [hintUsed, setHintUsed] = useState(false);
  const [showHintBox, setShowHintBox] = useState(false);
  const [difficulty, setDifficulty] = useState('medium');

  // Submission feedback state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lastAttemptResult, setLastAttemptResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  // Load Learner Studio Data dynamically from SQLite
  const loadData = async (learnerId, focusConceptId = null) => {
    try {
      setErrorMsg(null);
      const [gData, lDetail, nAction] = await Promise.all([
        fetchConceptGraph(learnerId),
        fetchLearnerDetail(learnerId),
        fetchNextAction(learnerId, focusConceptId),
      ]);

      setGraphData(gData);
      setLearnerDetail(lDetail);
      setNextAction(nAction);

      const targetConcept = focusConceptId || nAction.concept_id;
      setSelectedConceptId(targetConcept);

      // Load dynamic practice questions for target concept from DB
      const questions = await fetchPracticeQuestions(targetConcept);
      setPracticeQuestions(questions);
      setCurrentQuestionIndex(0);
      setSelectedOption('');
      setHintUsed(false);
      setShowHintBox(false);
    } catch (err) {
      console.error(err);
      setErrorMsg(err.message);
    }
  };

  useEffect(() => {
    if (currentLearnerId) {
      loadData(currentLearnerId);
    }
  }, [currentLearnerId]);

  // Handle switching concept from DAG
  const handleSelectConcept = async (conceptId) => {
    setSelectedConceptId(conceptId);
    try {
      const [nAction, questions] = await Promise.all([
        fetchNextAction(currentLearnerId, conceptId),
        fetchPracticeQuestions(conceptId),
      ]);
      setNextAction(nAction);
      setPracticeQuestions(questions);
      setCurrentQuestionIndex(0);
      setSelectedOption('');
      setHintUsed(false);
      setShowHintBox(false);
    } catch (err) {
      console.error(err);
    }
  };

  // Submit Simulated Practice Attempt to API
  const handleAttemptSubmit = async (e) => {
    e.preventDefault();
    if (!selectedOption) {
      alert('Please select an option before submitting.');
      return;
    }

    const currentQ = practiceQuestions[currentQuestionIndex];
    const isCorrect = currentQ ? selectedOption.trim() === currentQ.correct_answer.trim() : true;

    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const result = await submitLearningAttempt({
        learner_id: currentLearnerId,
        concept_id: selectedConceptId,
        correct: isCorrect,
        confidence: Number(confidence),
        response_time_ms: Number(responseTimeMs),
        hint_used: hintUsed,
        difficulty: difficulty,
      });

      setLastAttemptResult(result);
      // Reload graph and next action dynamically without page reload
      await loadData(currentLearnerId, selectedConceptId);
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Quick Preset Handlers for Judges Demo
  const applyPreset = (type) => {
    const currentQ = practiceQuestions[currentQuestionIndex];
    if (type === 'fast_confident') {
      setConfidence(5);
      setResponseTimeMs(11000);
      setHintUsed(false);
      setShowHintBox(false);
      if (currentQ) setSelectedOption(currentQ.correct_answer);
    } else if (type === 'rapid_gaming') {
      setConfidence(1);
      setResponseTimeMs(2200); // Triggers < 10s anti-gaming penalty
      setHintUsed(false);
      setShowHintBox(false);
      if (currentQ) setSelectedOption(currentQ.correct_answer);
    } else if (type === 'struggle_hints') {
      setConfidence(2);
      setResponseTimeMs(38000);
      setHintUsed(true);
      setShowHintBox(true);
      if (currentQ && currentQ.options) {
        const wrongOpt = currentQ.options.find(o => o !== currentQ.correct_answer) || currentQ.options[0];
        setSelectedOption(wrongOpt);
      }
    }
  };

  const currentQ = practiceQuestions[currentQuestionIndex];

  const getActionTheme = (action) => {
    switch (action) {
      case 'Challenge':
        return {
          border: 'border-purple-400',
          bg: 'bg-purple-950/40',
          badge: 'bg-purple-500/25 text-purple-200 border-purple-400/50',
          icon: <Award className="h-5 w-5 text-purple-300" />,
        };
      case 'Advance':
        return {
          border: 'border-emerald-400',
          bg: 'bg-emerald-950/40',
          badge: 'bg-emerald-500/25 text-emerald-200 border-emerald-400/50',
          icon: <ArrowRight className="h-5 w-5 text-emerald-300" />,
        };
      case 'Review':
        return {
          border: 'border-amber-400',
          bg: 'bg-amber-950/40',
          badge: 'bg-amber-500/25 text-amber-200 border-amber-400/50',
          icon: <Clock className="h-5 w-5 text-amber-300" />,
        };
      case 'RemediatePrerequisite':
        return {
          border: 'border-rose-400',
          bg: 'bg-rose-950/40',
          badge: 'bg-rose-500/25 text-rose-200 border-rose-400/50',
          icon: <AlertOctagon className="h-5 w-5 text-rose-300" />,
        };
      case 'TeacherIntervention':
        return {
          border: 'border-red-500',
          bg: 'bg-red-950/50',
          badge: 'bg-red-500/35 text-red-100 border-red-400 animate-pulse',
          icon: <ShieldAlert className="h-5 w-5 text-red-300" />,
        };
      default: // Practice
        return {
          border: 'border-sky-400',
          bg: 'bg-sky-950/40',
          badge: 'bg-sky-500/25 text-sky-200 border-sky-400/50',
          icon: <BrainCircuit className="h-5 w-5 text-sky-300" />,
        };
    }
  };

  const actionTheme = nextAction ? getActionTheme(nextAction.action) : getActionTheme('Practice');

  return (
    <div className="space-y-6 pb-12">
      {/* Learner Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-700/80 rounded-2xl p-6 shadow-xl">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-extrabold text-white tracking-tight">
              {learnerDetail ? learnerDetail.name : 'Learner Studio'}
            </h1>
            <span className="text-xs px-3 py-1 rounded-full bg-slate-800 text-indigo-300 border border-slate-600 font-mono font-bold">
              Profile: {currentLearnerId}
            </span>
          </div>
          <p className="text-xs text-slate-300 mt-1.5 font-medium">
            Active Bayesian student model: Dynamic evidence tracking, prerequisite DAG gatekeeping, and explainable next actions.
          </p>
        </div>

        <div className="flex items-center space-x-5">
          <div className="text-right">
            <span className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold block">Average Mastery</span>
            <span className="text-3xl font-extrabold font-mono text-indigo-400">
              {learnerDetail ? `${Math.round(learnerDetail.average_mastery * 100)}%` : '--'}
            </span>
          </div>
          <button
            onClick={() => loadData(currentLearnerId, selectedConceptId)}
            className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors shadow-sm"
            title="Refresh Knowledge State"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-500/15 border border-red-500/30 text-red-200 text-xs font-semibold flex items-center space-x-2">
          <ShieldAlert className="h-5 w-5 text-red-400 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* DAG Concept Graph Visualizer */}
      <ConceptGraphView
        graphData={graphData}
        selectedConceptId={selectedConceptId}
        onSelectConcept={handleSelectConcept}
        recommendedConceptId={nextAction ? nextAction.concept_id : null}
      />

      {/* Next Action & Interactive Simulator Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Why This Next? Explainability Card */}
        <div className="lg:col-span-5 space-y-6">
          <div className={`rounded-2xl border-2 p-6 shadow-2xl ${actionTheme.bg} ${actionTheme.border} transition-all`}>
            {/* Action Badge */}
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-1.5">
                <Sparkles className="h-4 w-4 text-indigo-300" />
                <span>Next Best Action</span>
              </span>

              {nextAction && (
                <span className={`inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-full text-xs font-extrabold border shadow-sm ${actionTheme.badge}`}>
                  {actionTheme.icon}
                  <span>{nextAction.action}</span>
                </span>
              )}
            </div>

            {/* Target Concept Name */}
            <h3 className="text-xl font-bold text-white mb-2">
              Focus: {nextAction ? nextAction.concept_name : 'Analyzing knowledge state...'}
            </h3>

            {/* Explainable Rationale Box */}
            <div className="p-4 rounded-xl bg-slate-950/90 border border-slate-700/80 mb-4 shadow-inner">
              <span className="text-[11px] font-bold text-indigo-300 uppercase tracking-wider block mb-1.5">
                Explainable Algorithmic Rationale
              </span>
              <p className="text-xs text-slate-100 leading-relaxed font-sans font-medium">
                {nextAction ? nextAction.reason_text : 'Evaluating state...'}
              </p>
            </div>

            {/* Decision Metrics Breakdown */}
            {nextAction && nextAction.metrics && (
              <div className="grid grid-cols-2 gap-2.5 text-xs font-medium">
                {nextAction.metrics.mastery_score !== undefined && (
                  <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-700/70">
                    <span className="text-slate-400 text-[10px] uppercase font-semibold block">Concept Mastery</span>
                    <span className="text-sm font-mono font-extrabold text-white">
                      {Math.round(nextAction.metrics.mastery_score * 100)}%
                    </span>
                  </div>
                )}

                {nextAction.metrics.consecutive_failures !== undefined && (
                  <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-700/70">
                    <span className="text-slate-400 text-[10px] uppercase font-semibold block">Failures / Hints</span>
                    <span className="text-sm font-mono font-extrabold text-red-400">
                      {nextAction.metrics.consecutive_failures} fails ({nextAction.metrics.hints_used || 0} hints)
                    </span>
                  </div>
                )}

                {nextAction.metrics.prerequisite_mastery !== undefined && (
                  <div className="p-3 rounded-xl bg-slate-950/80 border border-rose-500/40 col-span-2">
                    <span className="text-rose-300 text-[10px] uppercase font-semibold block">Blocking Prerequisite Barrier</span>
                    <span className="text-xs font-bold text-rose-200">
                      {nextAction.metrics.blocking_prerequisite_name}: {Math.round(nextAction.metrics.prerequisite_mastery * 100)}% (&lt; 50% barrier)
                    </span>
                  </div>
                )}

                {nextAction.metrics.decay_applied && (
                  <div className="p-3 rounded-xl bg-amber-500/20 border border-amber-500/40 col-span-2 text-amber-200 font-bold">
                    Retention Decay Active: Concept untouched &gt; 7 days.
                  </div>
                )}

                {nextAction.was_teacher_override && (
                  <div className="p-3 rounded-xl bg-violet-500/20 border border-violet-500/40 col-span-2 text-violet-200 font-bold">
                    Educator Override Directive in effect.
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Last Attempt Engine Feedback Telemetry */}
          {lastAttemptResult && (
            <div className="p-5 rounded-2xl bg-slate-900 border border-indigo-400/50 shadow-2xl space-y-3.5 animate-in fade-in duration-300">
              <div className="flex items-center justify-between">
                <span className="text-xs font-extrabold text-indigo-300 uppercase tracking-wider flex items-center space-x-1.5">
                  <Zap className="h-4 w-4 text-amber-400" />
                  <span>Bayesian Knowledge Tracing Telemetry</span>
                </span>
                <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold ${
                  lastAttemptResult.attempt.correct 
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' 
                    : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                }`}>
                  {lastAttemptResult.attempt.correct ? '✓ Correct Answer' : '✗ Incorrect'}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-700/80">
                  <span className="text-[10px] text-slate-400 font-semibold block">Updated Mastery</span>
                  <span className="font-mono font-extrabold text-indigo-300 text-sm">
                    {Math.round(lastAttemptResult.updated_mastery.mastery_score * 100)}%
                  </span>
                  <span className="text-[10px] text-slate-400 ml-1.5 font-semibold">
                    (Δ: {lastAttemptResult.updated_mastery.factor_breakdown ? (lastAttemptResult.updated_mastery.factor_breakdown.delta * 100).toFixed(1) : '0'}%)
                  </span>
                </div>

                <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-700/80">
                  <span className="text-[10px] text-slate-400 font-semibold block">Evidence Weight</span>
                  <span className="font-mono font-extrabold text-slate-100 text-sm">
                    {Math.round(lastAttemptResult.attempt.evidence_weight * 100)}%
                  </span>
                </div>
              </div>

              {lastAttemptResult.attempt.is_rapid_guess && (
                <div className="p-2.5 rounded-xl bg-rose-500/20 border border-rose-500/40 text-xs text-rose-200 font-bold flex items-center space-x-2">
                  <ShieldAlert className="h-4 w-4 text-rose-400 flex-shrink-0" />
                  <span>Anti-Gaming Enforced: Fast attempt (&lt;10s) penalized by 85%! Gain capped.</span>
                </div>
              )}

              <p className="text-xs text-slate-300 leading-relaxed font-medium">
                {lastAttemptResult.updated_mastery.factor_breakdown?.explanation}
              </p>
            </div>
          )}
        </div>

        {/* Right Column: Interactive Practice Simulator */}
        <div className="lg:col-span-7">
          <div className="bg-slate-900 border border-slate-700/80 rounded-2xl p-6 shadow-2xl space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
              <div>
                <h3 className="text-base font-extrabold text-white flex items-center space-x-2">
                  <span>Interactive Learning Simulator</span>
                  {currentQ && (
                    <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-slate-800 text-indigo-300 border border-slate-600">
                      {currentQ.difficulty.toUpperCase()}
                    </span>
                  )}
                </h3>
                <p className="text-xs text-slate-300 mt-0.5 font-medium">
                  Practice authentic algebra problems stored dynamically in the SQLite database.
                </p>
              </div>

              {/* Demo Presets for Quick Testing */}
              <div className="flex items-center space-x-1.5">
                <button
                  type="button"
                  onClick={() => applyPreset('fast_confident')}
                  className="px-2.5 py-1 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 text-[10px] font-bold transition-all"
                >
                  ✓ High-Mastery
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset('struggle_hints')}
                  className="px-2.5 py-1 rounded-lg bg-amber-500/15 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 text-[10px] font-bold transition-all"
                >
                  ⚠ Hint & Struggle
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset('rapid_gaming')}
                  className="px-2.5 py-1 rounded-lg bg-rose-500/15 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 text-[10px] font-bold transition-all"
                >
                  ⚡ Rapid-Gaming
                </button>
              </div>
            </div>

            {/* Question Selector Stepper if multiple questions exist */}
            {practiceQuestions.length > 1 && (
              <div className="flex items-center justify-between text-xs text-slate-300 border-b border-slate-800/80 pb-2.5">
                <span className="font-semibold">Question {currentQuestionIndex + 1} of {practiceQuestions.length}</span>
                <div className="flex items-center space-x-1">
                  <button
                    type="button"
                    disabled={currentQuestionIndex === 0}
                    onClick={() => {
                      setCurrentQuestionIndex(currentQuestionIndex - 1);
                      setSelectedOption('');
                      setShowHintBox(false);
                    }}
                    className="p-1 rounded bg-slate-800 text-slate-300 hover:text-white disabled:opacity-30"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    disabled={currentQuestionIndex === practiceQuestions.length - 1}
                    onClick={() => {
                      setCurrentQuestionIndex(currentQuestionIndex + 1);
                      setSelectedOption('');
                      setShowHintBox(false);
                    }}
                    className="p-1 rounded bg-slate-800 text-slate-300 hover:text-white disabled:opacity-30"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}

            {/* Question Prompt */}
            {currentQ ? (
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-700/80">
                <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider block mb-1">
                  Problem Prompt
                </span>
                <p className="text-sm font-semibold text-white leading-relaxed">
                  {currentQ.prompt}
                </p>
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-400">
                Loading question bank...
              </div>
            )}

            {/* Answer Options */}
            <form onSubmit={handleAttemptSubmit} className="space-y-5">
              <div className="space-y-2">
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
                  Select Answer:
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {currentQ && currentQ.options && currentQ.options.map((opt, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => setSelectedOption(opt)}
                      className={`p-3.5 rounded-xl border text-left text-xs font-semibold transition-all ${
                        selectedOption === opt
                          ? 'bg-indigo-600/30 border-indigo-400 text-white shadow-md shadow-indigo-600/20 ring-1 ring-indigo-400'
                          : 'bg-slate-950 border-slate-700/80 text-slate-200 hover:border-slate-500 hover:bg-slate-800/60'
                      }`}
                    >
                      <span className="font-mono text-indigo-400 mr-2">{String.fromCharCode(65 + i)}.</span>
                      <span>{opt}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Scaffolding Hint Toggle */}
              <div>
                <button
                  type="button"
                  onClick={() => {
                    setHintUsed(true);
                    setShowHintBox(!showHintBox);
                  }}
                  className="text-xs text-amber-400 hover:text-amber-300 font-bold flex items-center space-x-1.5 transition-colors"
                >
                  <Lightbulb className="h-4 w-4" />
                  <span>{showHintBox ? 'Hide Hint' : 'Request Hint (BKT Factor P(G) → 0.75)'}</span>
                </button>

                {showHintBox && currentQ && currentQ.hint_text && (
                  <div className="mt-2.5 p-3.5 rounded-xl bg-amber-500/15 border border-amber-500/30 text-xs text-amber-200 font-medium">
                    <span className="font-bold block mb-0.5 text-amber-300">Scaffold Hint:</span>
                    {currentQ.hint_text}
                  </div>
                )}
              </div>

              {/* Cognitive & Behavioral Modulators */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-slate-800">
                {/* Confidence Slider */}
                <div>
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <span className="text-slate-300 font-semibold">Confidence:</span>
                    <span className="font-bold font-mono text-indigo-300">{confidence} / 5</span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={confidence}
                    onChange={(e) => setConfidence(e.target.value)}
                    className="w-full accent-indigo-500 h-2 bg-slate-800 rounded-lg cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-400 font-medium mt-1">
                    <span>1 (Wild Guess)</span>
                    <span>5 (Certain)</span>
                  </div>
                </div>

                {/* Simulated Response Time */}
                <div>
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <span className="text-slate-300 font-semibold">Response Time:</span>
                    <span className={`font-mono font-bold ${responseTimeMs < 3500 ? 'text-rose-400' : 'text-slate-100'}`}>
                      {(responseTimeMs / 1000).toFixed(1)}s
                    </span>
                  </div>
                  <input
                    type="range"
                    min="1000"
                    max="60000"
                    step="500"
                    value={responseTimeMs}
                    onChange={(e) => setResponseTimeMs(e.target.value)}
                    className="w-full accent-indigo-500 h-2 bg-slate-800 rounded-lg cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-400 font-medium mt-1">
                    <span>1s (Rapid)</span>
                    <span>60s (Slow)</span>
                  </div>
                </div>

                {/* Difficulty */}
                <div>
                  <span className="text-xs text-slate-300 font-semibold block mb-1.5">Difficulty:</span>
                  <select
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-slate-100 font-medium focus:outline-none focus:border-indigo-500"
                  >
                    <option value="easy">Easy (P(T)=0.12)</option>
                    <option value="medium">Medium (P(T)=0.18)</option>
                    <option value="hard">Hard (P(T)=0.25)</option>
                  </select>
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold text-xs tracking-wide shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                {isSubmitting ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span>Processing Bayesian Evidence...</span>
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4 text-amber-300" />
                    <span>Submit Attempt & Update Mastery State</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
