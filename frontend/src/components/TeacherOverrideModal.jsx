import React, { useState } from 'react';
import { submitTeacherOverride } from '../api';
import { ShieldCheck, X, AlertTriangle, ArrowRight } from 'lucide-react';

export default function TeacherOverrideModal({ 
  isOpen, 
  onClose, 
  learners, 
  concepts, 
  onOverrideSuccess,
  defaultLearnerId = '',
  defaultConceptId = ''
}) {
  if (!isOpen) return null;

  const [learnerId, setLearnerId] = useState(defaultLearnerId || (learners[0]?.id || ''));
  const [conceptId, setConceptId] = useState(defaultConceptId || (concepts[0]?.id || ''));
  const [action, setAction] = useState('Review');
  const [teacherNotes, setTeacherNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      await submitTeacherOverride({
        learner_id: learnerId,
        concept_id: conceptId,
        action: action,
        teacher_notes: teacherNotes || 'Manual educator intervention',
      });

      onOverrideSuccess();
      onClose();
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <span className="p-1.5 rounded-lg bg-pink-500/10 text-pink-400 border border-pink-500/20">
              <ShieldCheck className="h-4 w-4" />
            </span>
            <h3 className="text-base font-bold text-white">
              Teacher Action Override Control
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <p className="text-xs text-slate-400">
          Forcefully mandate the learner's next pedagogical action. This is immutably logged with <code className="text-pink-400 bg-slate-950 px-1 py-0.5 rounded">was_teacher_override=True</code> in the audit trail without erasing history.
        </p>

        {errorMsg && (
          <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-red-300">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="text-slate-300 font-medium block mb-1">Select Learner:</label>
            <select
              value={learnerId}
              onChange={(e) => setLearnerId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              {learners.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.name} ({l.id})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-slate-300 font-medium block mb-1">Target Concept:</label>
            <select
              value={conceptId}
              onChange={(e) => setConceptId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              {concepts.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-slate-300 font-medium block mb-1">Forced Next Action:</label>
            <select
              value={action}
              onChange={(e) => setAction(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 font-semibold focus:outline-none focus:border-indigo-500"
            >
              <option value="Advance">Advance (Unlock Next Topic)</option>
              <option value="Practice">Practice (Strengthen Concept)</option>
              <option value="Review">Review (Address Retention Decay)</option>
              <option value="RemediatePrerequisite">RemediatePrerequisite (Step Back)</option>
              <option value="Challenge">Challenge (Stretch Problem)</option>
              <option value="TeacherIntervention">TeacherIntervention (1-on-1 Session)</option>
            </select>
          </div>

          <div>
            <label className="text-slate-300 font-medium block mb-1">Educator Justification / Notes:</label>
            <textarea
              rows={3}
              value={teacherNotes}
              onChange={(e) => setTeacherNotes(e.target.value)}
              placeholder="e.g. Conducted 1-on-1 tutoring on fraction common denominators; ready for review."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-slate-200 focus:outline-none focus:border-indigo-500"
              required
            />
          </div>

          <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2 rounded-xl bg-gradient-to-r from-pink-600 to-indigo-600 hover:from-pink-500 hover:to-indigo-500 text-white font-bold shadow-md shadow-pink-600/20 disabled:opacity-50 flex items-center space-x-1.5 transition-all"
            >
              <span>{isSubmitting ? 'Enforcing...' : 'Enforce Teacher Override'}</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
