import React, { useState, useEffect } from 'react';
import { fetchDiagnosticQuestions, submitDiagnostic } from '../api';
import { 
  Sparkles, 
  CheckCircle2, 
  HelpCircle, 
  ArrowRight, 
  UserCheck, 
  BrainCircuit, 
  RefreshCw,
  Lightbulb,
  Award
} from 'lucide-react';

export default function DiagnosticView({ onDiagnosticComplete }) {
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [learnerName, setLearnerName] = useState('Elena Rostova');
  const [answers, setAnswers] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [showHint, setShowHint] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  useEffect(() => {
    async function loadQuestions() {
      try {
        const qList = await fetchDiagnosticQuestions();
        setQuestions(qList);
      } catch (err) {
        console.error(err);
        setErrorMsg('Failed to load diagnostic questions.');
      }
    }
    loadQuestions();
  }, []);

  const currentQ = questions[currentIndex];

  const handleSelectOption = (opt) => {
    setAnswers({
      ...answers,
      [currentQ.id]: {
        ...(answers[currentQ.id] || { confidence: 3, response_time_ms: 15000, hint_used: false }),
        selected_option: opt,
      }
    });
  };

  const handleConfidenceChange = (val) => {
    setAnswers({
      ...answers,
      [currentQ.id]: {
        ...(answers[currentQ.id] || { selected_option: '', response_time_ms: 15000, hint_used: false }),
        confidence: Number(val),
      }
    });
  };

  const handleHintToggle = () => {
    setShowHint(true);
    setAnswers({
      ...answers,
      [currentQ.id]: {
        ...(answers[currentQ.id] || { selected_option: '', confidence: 3, response_time_ms: 15000 }),
        hint_used: true,
      }
    });
  };

  const handleSubmitDiagnostic = async () => {
    // Validate that all questions are answered
    for (const q of questions) {
      if (!answers[q.id] || !answers[q.id].selected_option) {
        alert(`Please complete question ${questions.indexOf(q) + 1} before submitting.`);
        setCurrentIndex(questions.indexOf(q));
        return;
      }
    }

    setIsSubmitting(true);
    setErrorMsg(null);

    const payload = {
      learner_name: learnerName,
      responses: questions.map(q => ({
        question_id: q.id,
        selected_option: answers[q.id].selected_option,
        confidence: answers[q.id].confidence || 3,
        response_time_ms: answers[q.id].response_time_ms || 15000,
        hint_used: answers[q.id].hint_used || false,
      }))
    };

    try {
      const res = await submitDiagnostic(payload);
      setResult(res);
    } catch (err) {
      console.error(err);
      setErrorMsg(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (result) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 pb-12">
        <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-8 shadow-2xl space-y-6">
          <div className="flex items-center space-x-3 text-emerald-400">
            <CheckCircle2 className="h-8 w-8" />
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight">
                Cold-Start Diagnostic Complete!
              </h2>
              <p className="text-xs text-slate-400">
                Initial Bayesian prior states derived from empirical evidence.
              </p>
            </div>
          </div>

          {/* Diagnostic Metrics Scorecard */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Learner</span>
              <span className="text-base font-bold text-white">{result.learner_name}</span>
            </div>
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Diagnostic Score</span>
              <span className="text-2xl font-bold font-mono text-indigo-400">
                {result.diagnostic_score}% ({result.correct_count}/{result.total_questions})
              </span>
            </div>
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
              <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Starting Pathway</span>
              <span className="text-sm font-semibold text-emerald-300">
                {result.recommended_start_concept}
              </span>
            </div>
          </div>

          {/* Derived Priors Matrix */}
          <div>
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
              Derived Concept Mastery Priors (P(L₀))
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
              {result.initial_mastery_states.map((st) => (
                <div key={st.concept_id} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-center">
                  <span className="text-[11px] font-medium text-slate-300 block truncate">
                    {st.concept_name}
                  </span>
                  <span className="text-sm font-bold font-mono text-indigo-400">
                    {Math.round(st.mastery_score * 100)}%
                  </span>
                  <span className="text-[9px] text-slate-500 block">
                    {st.evidence_count > 0 ? `${st.evidence_count} direct item` : 'DAG Prior'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Action Recommendation */}
          <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-500/30">
            <span className="text-xs font-bold text-indigo-300 uppercase tracking-wider block mb-1">
              Initial Engine Directive: {result.recommended_action.action}
            </span>
            <p className="text-xs text-slate-200">
              {result.recommended_action.reason_text}
            </p>
          </div>

          {/* Launch CTA */}
          <button
            onClick={() => onDiagnosticComplete(result.learner_id)}
            className="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold text-xs tracking-wide shadow-lg shadow-indigo-600/30 flex items-center justify-center space-x-2 transition-all"
          >
            <span>Launch Personalized Pathway in Learner Studio</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    );
  }

  if (questions.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <RefreshCw className="h-5 w-5 animate-spin mr-2" />
        Loading diagnostic assessment bank...
      </div>
    );
  }

  const currentAnswer = answers[currentQ?.id] || { confidence: 3, selected_option: '', hint_used: false };

  return (
    <div className="max-w-3xl mx-auto space-y-6 pb-12">
      {/* Intro Header */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-lg">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <Sparkles className="h-4 w-4 text-amber-400" />
              <span>Cold-Start Diagnostic Assessment</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              6-question mixed assessment establishing genuine prior knowledge. Mastery is calibrated rather than assuming 0%.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-400">Learner Name:</span>
            <input
              type="text"
              value={learnerName}
              onChange={(e) => setLearnerName(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-white focus:outline-none focus:border-indigo-500 w-36 font-medium"
            />
          </div>
        </div>

        {/* Stepper Progress */}
        <div className="mt-6 flex items-center justify-between gap-2">
          {questions.map((q, idx) => (
            <button
              key={q.id}
              onClick={() => {
                setCurrentIndex(idx);
                setShowHint(false);
              }}
              className={`flex-1 h-2 rounded-full transition-all ${
                currentIndex === idx
                  ? 'bg-indigo-500 shadow-md shadow-indigo-500/50'
                  : answers[q.id]?.selected_option
                  ? 'bg-emerald-500'
                  : 'bg-slate-800'
              }`}
              title={`Question ${idx + 1}`}
            />
          ))}
        </div>
        <div className="flex justify-between text-[11px] text-slate-400 mt-2 font-mono">
          <span>Question {currentIndex + 1} of {questions.length}</span>
          <span>Target Concept: {currentQ.concept_name}</span>
        </div>
      </div>

      {/* Active Question Card */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
        <div>
          <span className="text-[11px] font-semibold text-indigo-400 uppercase tracking-wider">
            Diagnostic Item #{currentIndex + 1} • {currentQ.difficulty.toUpperCase()}
          </span>
          <h3 className="text-base font-semibold text-white mt-1 leading-relaxed">
            {currentQ.prompt}
          </h3>
        </div>

        {/* Options */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {currentQ.options.map((opt, i) => (
            <button
              key={i}
              type="button"
              onClick={() => handleSelectOption(opt)}
              className={`p-3.5 rounded-xl border text-left text-xs font-medium transition-all ${
                currentAnswer.selected_option === opt
                  ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-md shadow-indigo-500/10'
                  : 'bg-slate-950/40 border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-900/60'
              }`}
            >
              <span className="font-mono text-slate-400 mr-2">{String.fromCharCode(65 + i)}.</span>
              <span>{opt}</span>
            </button>
          ))}
        </div>

        {/* Confidence & Hint Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-slate-800">
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">Confidence Rating:</span>
              <span className="font-bold text-indigo-400">{currentAnswer.confidence} / 5</span>
            </div>
            <input
              type="range"
              min="1"
              max="5"
              value={currentAnswer.confidence}
              onChange={(e) => handleConfidenceChange(e.target.value)}
              className="w-full accent-indigo-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
            />
          </div>

          <div className="flex items-center sm:justify-end">
            <button
              type="button"
              onClick={handleHintToggle}
              className="text-xs text-amber-400 hover:text-amber-300 font-medium flex items-center space-x-1.5"
            >
              <Lightbulb className="h-3.5 w-3.5" />
              <span>{showHint ? 'Hint Revealed' : 'Peek Hint (Modulates Guess Prior)'}</span>
            </button>
          </div>
        </div>

        {showHint && currentQ.hint_text && (
          <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-200">
            {currentQ.hint_text}
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between pt-4 border-t border-slate-800">
          <button
            type="button"
            disabled={currentIndex === 0}
            onClick={() => {
              setCurrentIndex(currentIndex - 1);
              setShowHint(false);
            }}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 disabled:opacity-30"
          >
            Previous
          </button>

          {currentIndex < questions.length - 1 ? (
            <button
              type="button"
              onClick={() => {
                setCurrentIndex(currentIndex + 1);
                setShowHint(false);
              }}
              className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-md"
            >
              Next Question
            </button>
          ) : (
            <button
              type="button"
              disabled={isSubmitting}
              onClick={handleSubmitDiagnostic}
              className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-xs font-bold text-white shadow-lg shadow-emerald-600/30 flex items-center space-x-2"
            >
              {isSubmitting ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>Evaluating Priors...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="h-4 w-4" />
                  <span>Submit Diagnostic & Generate Pathway</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
