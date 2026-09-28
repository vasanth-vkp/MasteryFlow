/**
 * MasteryFlow API Client
 */

const BASE_URL = '/api';

export async function fetchConceptGraph(learnerId = null) {
  const url = learnerId ? `${BASE_URL}/concepts/graph?learner_id=${encodeURIComponent(learnerId)}` : `${BASE_URL}/concepts/graph`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch concept graph');
  return res.json();
}

export async function fetchConcepts() {
  const res = await fetch(`${BASE_URL}/concepts`);
  if (!res.ok) throw new Error('Failed to fetch concepts');
  return res.json();
}

export async function fetchLearners() {
  const res = await fetch(`${BASE_URL}/learners`);
  if (!res.ok) throw new Error('Failed to fetch learners');
  return res.json();
}

export async function createNewLearner(name) {
  const res = await fetch(`${BASE_URL}/learners`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) throw new Error('Failed to create learner');
  return res.json();
}

export async function fetchLearnerDetail(learnerId) {
  const res = await fetch(`${BASE_URL}/learners/${encodeURIComponent(learnerId)}`);
  if (!res.ok) throw new Error('Failed to fetch learner details');
  return res.json();
}

export async function fetchNextAction(learnerId, conceptId = null) {
  const url = conceptId 
    ? `${BASE_URL}/next-action/${encodeURIComponent(learnerId)}?concept_id=${encodeURIComponent(conceptId)}`
    : `${BASE_URL}/next-action/${encodeURIComponent(learnerId)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch next action');
  return res.json();
}

export async function submitLearningAttempt(payload) {
  const res = await fetch(`${BASE_URL}/attempts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to submit attempt' }));
    throw new Error(err.detail || 'Failed to submit attempt');
  }
  return res.json();
}

export async function fetchDiagnosticQuestions() {
  const res = await fetch(`${BASE_URL}/diagnostic/questions`);
  if (!res.ok) throw new Error('Failed to fetch diagnostic questions');
  return res.json();
}

export async function submitDiagnostic(payload) {
  const res = await fetch(`${BASE_URL}/diagnostic/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to submit diagnostic');
  return res.json();
}

export async function fetchTeacherDashboard() {
  const res = await fetch(`${BASE_URL}/teacher/dashboard`);
  if (!res.ok) throw new Error('Failed to fetch teacher dashboard data');
  return res.json();
}

export async function submitTeacherOverride(payload) {
  const res = await fetch(`${BASE_URL}/teacher/override`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to submit teacher override');
  return res.json();
}

export async function fetchSimulationComparison(conceptId = 'c_ratios', learnerAId = null, learnerBId = null) {
  let url = `${BASE_URL}/simulation/compare?concept_id=${encodeURIComponent(conceptId)}`;
  if (learnerAId) url += `&learner_a_id=${encodeURIComponent(learnerAId)}`;
  if (learnerBId) url += `&learner_b_id=${encodeURIComponent(learnerBId)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch simulation comparison');
  return res.json();
}

export async function fetchPracticeQuestions(conceptId) {
  const res = await fetch(`${BASE_URL}/questions/concept/${encodeURIComponent(conceptId)}`);
  if (!res.ok) throw new Error('Failed to fetch practice questions');
  return res.json();
}
