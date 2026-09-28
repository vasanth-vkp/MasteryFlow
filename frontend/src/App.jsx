import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import LearnerStudio from './components/LearnerStudio';
import DiagnosticView from './components/DiagnosticView';
import SimulationCompareView from './components/SimulationCompareView';
import TeacherDashboardView from './components/TeacherDashboardView';
import { fetchLearners } from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('learner');
  const [learners, setLearners] = useState([]);
  const [currentLearnerId, setCurrentLearnerId] = useState('learner_a');
  const [isLoading, setIsLoading] = useState(true);

  const loadLearnersList = async () => {
    try {
      const list = await fetchLearners();
      setLearners(list);
      if (list.length > 0 && !currentLearnerId) {
        setCurrentLearnerId(list[0].id);
      }
    } catch (err) {
      console.error('Failed to load learners:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadLearnersList();
  }, []);

  const handleDiagnosticComplete = async (newLearnerId) => {
    await loadLearnersList();
    setCurrentLearnerId(newLearnerId);
    setActiveTab('learner');
  };

  const handleSwitchLearner = (learnerId) => {
    setCurrentLearnerId(learnerId);
    setActiveTab('learner');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Navigation Bar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        learners={learners}
        currentLearnerId={currentLearnerId}
        setCurrentLearnerId={setCurrentLearnerId}
        onLearnerCreated={handleDiagnosticComplete}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        {activeTab === 'learner' && (
          <LearnerStudio currentLearnerId={currentLearnerId} />
        )}

        {activeTab === 'diagnostic' && (
          <DiagnosticView onDiagnosticComplete={handleDiagnosticComplete} />
        )}

        {activeTab === 'compare' && (
          <SimulationCompareView onSwitchLearner={handleSwitchLearner} />
        )}

        {activeTab === 'teacher' && (
          <TeacherDashboardView onSelectLearner={handleSwitchLearner} />
        )}
      </main>

      {/* Clean Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>MasteryFlow • YUVA Megathon 2026 EduGenAI Submission</span>
          <span className="font-mono text-[11px] text-slate-600">
            FastAPI + SQLAlchemy + React + Tailwind • 100% Inspectable Math
          </span>
        </div>
      </footer>
    </div>
  );
}
