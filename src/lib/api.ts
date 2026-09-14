export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1';

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

export interface PublicProjectRiskSummary {
  project_name: string;
  sector: string;
  state: string;
  risk_level: 'critical' | 'high' | 'moderate' | 'low';
  dphis: number;
  cost_revised_cr: number;
  schedule_slippage_months: number;
}

export interface PublicRiskOverview {
  total_projects: number;
  total_capex_lakh_cr: number;
  at_risk_count: number;
  critical_count: number;
  ministries_count: number;
  sectors_count: number;
  top_sectors: string[];
  risk_watchlist: PublicProjectRiskSummary[];
  governance_mode?: string;
  timestamp?: string;
}

export async function fetchPublicRiskOverview(): Promise<PublicRiskOverview> {
  try {
    const res = await fetch(`${API_BASE}/projects/public-risk-overview`);
    if (!res.ok) throw new Error('Failed to fetch public risk overview');
    return await res.json();
  } catch (err) {
    console.warn('Backend offline, returning fallback public overview:', err);
    return {
      total_projects: 3394,
      total_capex_lakh_cr: 74.5,
      at_risk_count: 223,
      critical_count: 18,
      ministries_count: 17,
      sectors_count: 22,
      top_sectors: [
        'Road Transport & Highways',
        'Railways & Freight',
        'Urban Transit & Metro',
        'Power & Grid',
        'Coal & Mining'
      ],
      risk_watchlist: [
        {
          project_name: 'Araria-Supaul Railway Corridor (92 km)',
          sector: 'Railways',
          state: 'Bihar',
          risk_level: 'high',
          dphis: 77.9,
          cost_revised_cr: 2621.05,
          schedule_slippage_months: 34.0
        },
        {
          project_name: 'Punpun Barrage Irrigation Project',
          sector: 'Water Resources',
          state: 'Bihar',
          risk_level: 'high',
          dphis: 77.2,
          cost_revised_cr: 658.12,
          schedule_slippage_months: 75.0
        },
        {
          project_name: 'Chhota Udepur-Dhar Broad Gauge (157 km)',
          sector: 'Railways',
          state: 'Gujarat / MP',
          risk_level: 'high',
          dphis: 77.1,
          cost_revised_cr: 1993.65,
          schedule_slippage_months: 0.0
        }
      ],
      governance_mode: 'RESTRICTED_PUBLIC_PREVIEW'
    };
  }
}

export async function fetchMyProjects(username?: string, limit = 50): Promise<ProjectData[]> {
  try {
    const url = new URL(`${API_BASE}/projects/my-projects`);
    if (username) url.searchParams.set('username', username);
    url.searchParams.set('limit', String(limit));
    const res = await fetch(url.toString());
    if (!res.ok) throw new Error('Failed to fetch user-specific projects');
    return await res.json();
  } catch (err) {
    console.warn('Backend offline or failed to fetch user-associated projects', err);
    return [];
  }
}

export interface NormalAssetIngestRequest {
  page?: number;
  s_no?: number;
  project_id: string;
  project_name: string;
  original_cost_crores: number;
  revised_cost_crores: number;
  expenditure_crores: number;
  physical_progress_percent: number;
  ministry?: string;
  sector?: string;
  state?: string;
  username?: string;
}

export async function ingestNormalAsset(payload: NormalAssetIngestRequest): Promise<ProjectData> {
  const res = await fetch(`${API_BASE}/projects/ingest-normal-asset`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'Failed to ingest project via Gemini pipeline');
  }
  return data;
}

export async function fetchProjects(risk?: string, limit = 50, ministry?: string, search?: string, username?: string): Promise<ProjectData[]> {
  try {
    const url = new URL(`${API_BASE}/projects`);
    if (risk) url.searchParams.set('risk', risk);
    if (ministry && ministry.trim()) url.searchParams.set('ministry', ministry.trim());
    if (search && search.trim()) url.searchParams.set('search', search.trim());
    if (username && username.trim()) url.searchParams.set('username', username.trim());
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
    return {
      project_id: id,
      dphis: 76.0,
      level: 'high',
      components: {
        time: 0.345,
        cost: 0.983,
        progress: 0.772,
        milestone: 0.584,
        financial: 0.723,
        implementation: 0.990
      },
      trend: {
        previous: 73.8,
        current: 76.0,
        change_pts: 2.2,
        direction: 'WORSENING'
      }
    };
  }
}

export async function fetchProjectPredictions(id: string): Promise<PredictionData | null> {
  try {
    const res = await fetch(`${API_BASE}/projects/${id}/predictions`);
    if (!res.ok) throw new Error('Predictions error');
    return await res.json();
  } catch (err) {
    return {
      project_id: id,
      cost: {
        predicted_final_cost: 2034.94,
        predicted_overrun_pct: 7.34,
        cost_risk_score: 0.983
      },
      delay: {
        predicted_completion_date: '2027-10-28',
        expected_delay_months: 21.0,
        time_risk_score: 0.345
      },
      overall_risk_probability: 0.983,
      top_shap_factors: [
        { feature: 'Critical Path Schedule Deviation', impact: 31.5, direction: 'increase', description: 'Critical path schedule deviation: slippage = 21.0 mos' },
        { feature: 'CapEx Disbursement–Execution Disparity', impact: 18.2, direction: 'increase', description: 'Disbursement velocity exceeds certified physical completion by 24 pts' },
        { feature: 'Monthly Progress Velocity Gap', impact: 12.0, direction: 'increase', description: 'Required monthly progress velocity exceeds actual burn rate' },
        { feature: 'Cost Escalation Budget Expansion', impact: 6.6, direction: 'increase', description: 'Projected capital outlay expansion variance: 7.3%' }
      ]
    };
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

export async function triggerN8nRiskEvent(params: {
  projectId: string;
  dphis: number;
  threshold?: number;
  recipientEmail?: string;
  recipientName?: string;
}): Promise<{
  success: boolean;
  threshold_exceeded: boolean;
  message?: string;
  status_code?: number;
  target_url?: string;
  recipient_email?: string;
  n8n_response?: string;
}> {
  try {
    const url = new URL(`${API_BASE}/alerts/trigger-n8n-event`);
    url.searchParams.set('project_id', params.projectId);
    url.searchParams.set('dphis', String(params.dphis));
    if (params.threshold !== undefined) url.searchParams.set('threshold', String(params.threshold));
    if (params.recipientEmail) url.searchParams.set('recipient_email', params.recipientEmail);
    if (params.recipientName) url.searchParams.set('recipient_name', params.recipientName);

    const res = await fetch(url.toString(), { method: 'POST' });
    return await res.json();
  } catch (err: any) {
    return {
      success: false,
      threshold_exceeded: false,
      message: err.message || 'Network error triggering n8n workflow'
    };
  }
}

// ============================================================
// Authentication & User Identity Management
// ============================================================

export interface UserProfile {
  username: string;
  role: string;
  email: string;
  full_name: string;
  ministry?: string;
  designation?: string;
  dphis_alert_threshold?: number;
  alert_email?: string;
  notify_via_email?: boolean;
  assigned_projects?: string[];
}

export interface MinistryItem {
  id: number;
  name: string;
  sector: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  role: string;
  username: string;
  email?: string;
  full_name?: string;
  ministry?: string;
  assigned_projects?: string[];
}

export function getAuthToken(): string | null {
  return localStorage.getItem('paimana_token');
}

export function setAuthToken(token: string): void {
  localStorage.setItem('paimana_token', token);
}

export function clearAuthToken(): void {
  localStorage.removeItem('paimana_token');
}

export async function fetchMinistries(): Promise<MinistryItem[]> {
  try {
    const res = await fetch(`${API_BASE}/ministries`);
    if (!res.ok) throw new Error('Failed to load ministries');
    return await res.json();
  } catch (err) {
    // Fallback list
    return [
      { id: 1, name: "Road Transport & Highways", sector: "Transport & Logistics" },
      { id: 2, name: "Railways", sector: "Railways & Freight" },
      { id: 3, name: "Housing & Urban Affairs", sector: "Urban Transit & Metro" },
      { id: 4, name: "Power", sector: "Energy & Power" },
      { id: 5, name: "Jal Shakti", sector: "Water Resources & Sanitation" },
      { id: 6, name: "Coal", sector: "Coal & Mining" },
      { id: 7, name: "Steel", sector: "Steel & Metallurgical" },
      { id: 8, name: "Petroleum & Natural Gas", sector: "Petrochemical & Gas" },
      { id: 9, name: "Ports, Shipping & Waterways", sector: "Ports & Shipping" },
    ];
  }
}

export async function loginUser(credentials: { email: string; password: string }): Promise<AuthResponse> {
  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || data.error || 'Authentication failed.');
    }
    if (data.access_token) {
      setAuthToken(data.access_token);
    }
    return data;
  } catch (err: any) {
    if (err.message && err.message !== 'Failed to fetch' && !err.message.includes('NetworkError')) {
      throw err;
    }
    // Remote / Offline demo fallback
    const em = credentials.email.trim().toLowerCase();
    if (em === 'admin' && credentials.password === 'paimana2026') {
      const demo: AuthResponse = {
        access_token: 'demo-token-admin',
        token_type: 'bearer',
        role: 'ADMIN',
        username: 'admin',
        email: 'admin@paimana.gov.in',
        full_name: 'Dr. Amitabh Verma',
        ministry: 'Central Infrastructure',
        designation: 'MoSPI Lead Director'
      };
      setAuthToken(demo.access_token);
      return demo;
    } else if (em === 'analyst' && credentials.password === 'analyst2026') {
      const demo: AuthResponse = {
        access_token: 'demo-token-analyst',
        token_type: 'bearer',
        role: 'ANALYST',
        username: 'analyst',
        email: 'analyst@paimana.gov.in',
        full_name: 'Priyanka Sen',
        ministry: 'Ministry of Statistics & Programme Implementation',
        designation: 'Lead Infrastructure Risk Analyst'
      };
      setAuthToken(demo.access_token);
      return demo;
    } else if (em === 'ramesh.kumar@morth.gov.in' && credentials.password === 'Password1234!') {
      const demo: AuthResponse = {
        access_token: 'demo-token-morth',
        token_type: 'bearer',
        role: 'PROJECT_OFFICER',
        username: 'ramesh.kumar',
        email: 'ramesh.kumar@morth.gov.in',
        full_name: 'Dr. Ramesh Kumar',
        ministry: 'Ministry of Road Transport & Highways',
        designation: 'Chief Engineer & Project Director'
      };
      setAuthToken(demo.access_token);
      return demo;
    }
    throw new Error('Invalid credentials or backend unreachable.');
  }
}

export async function registerUser(payload: {
  fullName: string;
  email: string;
  ministryId?: number;
  ministry?: string;
  designation?: string;
  password: string;
  termsAccepted: boolean;
  aiAckAccepted: boolean;
}): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'Registration failed.');
  }
  return data;
}

export async function verifyOtp(payload: { email: string; otp: string }): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/auth/verify-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'OTP verification failed.');
  }
  return data;
}

export async function resendOtp(payload: { email: string; purpose?: string }): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/auth/resend-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: payload.email, purpose: payload.purpose || 'signup' })
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.error || 'Could not resend verification code.');
  }
  return data;
}

export async function fetchCurrentUser(): Promise<UserProfile | null> {
  const token = getAuthToken();
  if (!token) return null;
  try {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) {
      clearAuthToken();
      return null;
    }
    return await res.json();
  } catch (err) {
    if (token.startsWith('demo-token-')) {
      if (token.includes('admin')) {
        return {
          username: 'admin',
          email: 'admin@paimana.gov.in',
          role: 'ADMIN',
          full_name: 'Dr. Amitabh Verma',
          ministry: 'Central Infrastructure',
          designation: 'MoSPI Lead Director',
          dphis_alert_threshold: 75.0,
          alert_email: 'admin@paimana.gov.in',
          notify_via_email: true
        };
      } else if (token.includes('morth')) {
        return {
          username: 'ramesh.kumar',
          email: 'ramesh.kumar@morth.gov.in',
          role: 'PROJECT_OFFICER',
          full_name: 'Dr. Ramesh Kumar',
          ministry: 'Ministry of Road Transport & Highways',
          designation: 'Chief Engineer & Project Director',
          dphis_alert_threshold: 75.0,
          alert_email: 'ramesh.kumar@morth.gov.in',
          notify_via_email: true
        };
      } else {
        return {
          username: 'analyst',
          email: 'analyst@paimana.gov.in',
          role: 'ANALYST',
          full_name: 'Priyanka Sen',
          ministry: 'Ministry of Statistics & Programme Implementation',
          designation: 'Lead Infrastructure Risk Analyst',
          dphis_alert_threshold: 70.0,
          alert_email: 'analyst@paimana.gov.in',
          notify_via_email: true
        };
      }
    }
    return null;
  }
}


