const API_BASE = 'http://localhost:8000/api/v1';

export interface ProjectData {
  project_id: string;
  project_name: string;
  ministry: string;
  department: string;
  sector: string;
  state: string;
  location: {
    latitude: number;
    longitude: number;
    district: string;
    state: string;
  };
  cost: {
    original: number;
    revised: number;
    currency: string;
  };
  schedule: {
    original_start: string;
    original_end: string;
    revised_end: string;
  };
  dphis: number;
  risk_level: 'critical' | 'high' | 'moderate' | 'low';
  data_quality_score?: number;
}

export interface RiskData {
  project_id: string;
  dphis: number;
  level: string;
  components: {
    time: number;
    cost: number;
    progress: number;
    milestone: number;
    financial: number;
    implementation: number;
  };
  trend: {
    previous: number;
    current: number;
    change_pts: number;
    direction: string;
  };
}

export interface PredictionData {
  project_id: string;
  cost: {
    predicted_final_cost: number;
    predicted_overrun_pct: number;
    cost_risk_score: number;
  };
  delay: {
    predicted_completion_date: string;
    expected_delay_months: number;
    time_risk_score: number;
  };
  overall_risk_probability: number;
  top_shap_factors: Array<{
    feature: string;
    impact: number;
    direction: string;
    description: string;
  }>;
}

export interface InvestigationReport {
  investigation_id: string;
  project_id: string;
  trigger_reason: string;
  executive_summary: string;
  findings: Array<{
    title: string;
    summary: string;
    evidence: Array<{
      source: string;
      field: string;
      value: any;
      context?: string;
    }>;
    confidence: number;
  }>;
  recommendations: Array<{
    action: string;
    reason: string;
    priority: string;
    confidence: number;
    target_agency?: string;
  }>;
  tools_executed: string[];
  overall_confidence: number;
}

export interface AnalyticsOverview {
  total_projects: number;
  critical: number;
  high: number;
  moderate: number;
  low: number;
  average_dphis: number;
  total_original_cost_cr: number;
  total_revised_cost_cr: number;
  cost_overrun_pct: number;
}

export interface AlertItem {
  alert_id: string;
  project_id: string;
  project_name: string;
  severity: string;
  previous_severity?: string;
  trigger: string;
  dphis: number;
  message: string;
  status: string;
  created_at: string;
}

export async function fetchProjects(risk?: string, limit = 50): Promise<ProjectData[]> {
  try {
    const url = new URL(`${API_BASE}/projects`);
    if (risk) url.searchParams.set('risk', risk);
    url.searchParams.set('limit', String(limit));
    const res = await fetch(url.toString());
    if (!res.ok) throw new Error('Failed to fetch projects');
    return await res.json();
  } catch (err) {
    console.warn('Backend offline or failed, returning mock pins fallback', err);
    return [];
  }
}

export async function fetchProject(id: string): Promise<ProjectData | null> {
  try {
    const res = await fetch(`${API_BASE}/projects/${id}`);
    if (!res.ok) throw new Error('Project not found');
    return await res.json();
  } catch (err) {
    return null;
  }
}

export async function fetchProjectRisk(id: string): Promise<RiskData | null> {
  try {
    const res = await fetch(`${API_BASE}/projects/${id}/risk`);
    if (!res.ok) throw new Error('Risk data error');
    return await res.json();
  } catch (err) {
    return null;
  }
}

export async function fetchProjectPredictions(id: string): Promise<PredictionData | null> {
  try {
    const res = await fetch(`${API_BASE}/projects/${id}/predictions`);
    if (!res.ok) throw new Error('Predictions error');
    return await res.json();
  } catch (err) {
    return null;
  }
}

export async function triggerInvestigation(id: string): Promise<InvestigationReport | null> {
  try {
    const res = await fetch(`${API_BASE}/projects/${id}/investigate`, { method: 'POST' });
    if (!res.ok) throw new Error('Investigation error');
    return await res.json();
  } catch (err) {
    return null;
  }
}

export async function fetchAnalyticsOverview(): Promise<AnalyticsOverview | null> {
  try {
    const res = await fetch(`${API_BASE}/analytics/overview`);
    if (!res.ok) throw new Error('Analytics error');
    return await res.json();
  } catch (err) {
    return null;
  }
}

export async function fetchRiskTrend(): Promise<any[]> {
  try {
    const res = await fetch(`${API_BASE}/analytics/risk-trend`);
    if (!res.ok) throw new Error('Risk trend error');
    return await res.json();
  } catch (err) {
    return [];
  }
}

export async function fetchAlerts(): Promise<AlertItem[]> {
  try {
    const res = await fetch(`${API_BASE}/alerts`);
    if (!res.ok) throw new Error('Alerts error');
    return await res.json();
  } catch (err) {
    return [];
  }
}

export async function acknowledgeAlert(alertId: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/alerts/${alertId}/acknowledge`, { method: 'POST' });
    return res.ok;
  } catch (err) {
    return false;
  }
}

export async function sendChatMessage(message: string, projectId?: string): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, project_id: projectId }),
    });
    if (!res.ok) throw new Error('Chat API error');
    return await res.json();
  } catch (err) {
    return {
      reply: "Backend connection unavailable. Please ensure the PAIMANA FastAPI service is running at http://localhost:8000.",
      intent: "ERROR",
      grounded_evidence: [],
      suggested_actions: ["Check backend status", "Retry query"]
    };
  }
}
