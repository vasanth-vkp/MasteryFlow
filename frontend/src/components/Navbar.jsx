import React, { useState } from 'react';
import { 
  Network, 
  Sparkles, 
  GitCompare, 
  GraduationCap, 
  User, 
  Database,
  Compass,
  UserPlus,
  CheckCircle2,
  X
} from 'lucide-react';
import { createNewLearner } from '../api';

export default function Navbar({ 
  activeTab, 
  setActiveTab, 
  learners, 
  currentLearnerId, 
  setCurrentLearnerId,
  onLearnerCreated 
}) {
  const [showNewLearnerModal, setShowNewLearnerModal] = useState(false);
  const [newLearnerName, setNewLearnerName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleCreateLearner = async (e) => {
    e.preventDefault();
    if (!newLearnerName.trim()) return;
    setIsSubmitting(true);
    try {
      const created = await createNewLearner(newLearnerName.trim());
      setNewLearnerName('');
      setShowNewLearnerModal(false);
      if (onLearnerCreated) {
        await onLearnerCreated(created.id);
      }
    } catch (err) {
      alert('Error creating learner: ' + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-slate-800 bg-slate-950/95 backdrop-blur-md shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo & Brand */}
            <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('learner')}>
              <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-500 via-violet-600 to-pink-500 p-0.5 shadow-lg shadow-indigo-500/25">
                <div className="h-full w-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                  <Compass className="h-5 w-5 text-indigo-400" />
                </div>
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-xl font-extrabold tracking-tight text-white">
                    MasteryFlow
                  </span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    EduGenAI
                  </span>
                </div>
                <p className="text-xs text-slate-300 hidden sm:block font-medium">
                  Explainable Adaptive Learning & Intervention Engine
                </p>
              </div>
            </div>

            {/* Navigation Tabs */}
            <nav className="hidden md:flex items-center space-x-1.5">
              <button
                onClick={() => setActiveTab('learner')}
                className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
                  activeTab === 'learner'
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30 border border-indigo-400/40'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                }`}
              >
                <Network className="h-4 w-4" />
                <span>Learner Studio</span>
              </button>

              <button
                onClick={() => setActiveTab('diagnostic')}
                className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
                  activeTab === 'diagnostic'
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30 border border-indigo-400/40'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                }`}
              >
                <Sparkles className="h-4 w-4 text-amber-400" />
                <span>Cold-Start Diagnostic</span>
              </button>

              <button
                onClick={() => setActiveTab('compare')}
                className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
                  activeTab === 'compare'
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30 border border-indigo-400/40'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                }`}
              >
                <GitCompare className="h-4 w-4 text-emerald-400" />
                <span>Simulation & Compare</span>
              </button>

              <button
                onClick={() => setActiveTab('teacher')}
                className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
                  activeTab === 'teacher'
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30 border border-indigo-400/40'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                }`}
              >
                <GraduationCap className="h-4 w-4 text-pink-400" />
                <span>Teacher Dashboard</span>
              </button>
            </nav>

            {/* Learner Selector & Add Button */}
            <div className="flex items-center space-x-2.5">
              <div className="flex items-center space-x-2 bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-1.5 shadow-sm">
                <User className="h-4 w-4 text-indigo-400 flex-shrink-0" />
                <select
                  value={currentLearnerId || ''}
                  onChange={(e) => setCurrentLearnerId(e.target.value)}
                  className="bg-transparent text-slate-100 font-semibold focus:outline-none cursor-pointer text-xs"
                >
                  {learners.map((l) => (
                    <option key={l.id} value={l.id} className="bg-slate-900 text-white font-medium">
                      {l.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Add Dynamic Learner Button */}
              <button
                type="button"
                onClick={() => setShowNewLearnerModal(true)}
                className="p-2 rounded-xl bg-slate-800 hover:bg-indigo-600 text-slate-200 hover:text-white border border-slate-700 hover:border-indigo-500 transition-colors shadow-sm"
                title="Create New Dynamic Learner"
              >
                <UserPlus className="h-4 w-4" />
              </button>

              <div className="hidden lg:flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-xs font-bold text-emerald-400">
                <Database className="h-3.5 w-3.5" />
                <span>SQLite DB</span>
              </div>
            </div>
          </div>

          {/* Mobile Tab Row */}
          <div className="md:hidden flex items-center justify-around py-2.5 border-t border-slate-800 text-xs font-semibold">
            <button
              onClick={() => setActiveTab('learner')}
              className={`px-2 py-1 rounded-lg ${activeTab === 'learner' ? 'bg-indigo-600 text-white' : 'text-slate-300'}`}
            >
              Learner
            </button>
            <button
              onClick={() => setActiveTab('diagnostic')}
              className={`px-2 py-1 rounded-lg ${activeTab === 'diagnostic' ? 'bg-indigo-600 text-white' : 'text-slate-300'}`}
            >
              Diagnostic
            </button>
            <button
              onClick={() => setActiveTab('compare')}
              className={`px-2 py-1 rounded-lg ${activeTab === 'compare' ? 'bg-indigo-600 text-white' : 'text-slate-300'}`}
            >
              Compare
            </button>
            <button
              onClick={() => setActiveTab('teacher')}
              className={`px-2 py-1 rounded-lg ${activeTab === 'teacher' ? 'bg-indigo-600 text-white' : 'text-slate-300'}`}
            >
              Teacher
            </button>
          </div>
        </div>
      </header>

      {/* Dynamic Create Learner Modal */}
      {showNewLearnerModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <UserPlus className="h-5 w-5 text-indigo-400" />
                <h3 className="text-base font-bold text-white">Create New Dynamic Learner</h3>
              </div>
              <button
                onClick={() => setShowNewLearnerModal(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <p className="text-xs text-slate-300">
              Instantly create a new learner profile in the persistent SQLite database. All states and attempts will be dynamically tracked.
            </p>

            <form onSubmit={handleCreateLearner} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-200 block mb-1">
                  Learner Name:
                </label>
                <input
                  type="text"
                  placeholder="e.g. Maya Patel"
                  value={newLearnerName}
                  onChange={(e) => setNewLearnerName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500 font-medium"
                  required
                  autoFocus
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowNewLearnerModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white shadow-md shadow-indigo-600/30 flex items-center space-x-1.5"
                >
                  <span>{isSubmitting ? 'Creating...' : 'Create Learner'}</span>
                  <CheckCircle2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
