export const NAV_LINKS = [
  { label: 'Product', href: '#product' },
  { label: 'Intelligence', href: '#intelligence' },
  { label: 'Analytics', href: '#analytics' },
  { label: 'How It Works', href: '#how-it-works' },
  { label: 'Technology', href: '#technology' },
] as const;

export const PROOF_STRIP = [
  'Continuous Monitoring',
  'Predictive Risk',
  'Peer Intelligence',
  'Agentic Investigation',
  'Human-Gated Action',
  'Closed-Loop Outcomes',
] as const;

export const PROBLEM_STAGES = [
  {
    label: 'Normal',
    description: 'Project tracking within expected parameters',
    progress: 61,
    expenditure: 64,
    dphis: 54,
  },
  {
    label: 'Small Divergence',
    description: 'Minor deviations begin to accumulate',
    progress: 60,
    expenditure: 66,
    dphis: 58,
  },
  {
    label: 'Risk Acceleration',
    description: 'Divergence compounds across multiple dimensions',
    progress: 59,
    expenditure: 69,
    dphis: 66,
  },
  {
    label: 'Critical Exposure',
    description: 'Project enters high-risk territory',
    progress: 59,
    expenditure: 71,
    dphis: 72,
  },
] as const;

export const DIFFERENTIATORS = [
  {
    id: 'predict',
    title: 'Predict',
    description: 'Cost, schedule, and implementation risk estimated before they materialize.',
    items: ['Cost risk', 'Schedule risk', 'Implementation risk'],
  },
  {
    id: 'contextualize',
    title: 'Contextualize',
    description: 'Place every project against comparable peers and historical trajectory.',
    items: ['Peer cohort', 'Benchmarks', 'Trajectory'],
  },
  {
    id: 'investigate',
    title: 'Investigate',
    description: 'Evidence-driven stateful agent that examines possible explanations.',
    items: ['Evidence', 'Hypotheses', 'Stateful agent'],
  },
  {
    id: 'act',
    title: 'Act',
    description: 'Validated recommendations with human approval and automated follow-up.',
    items: ['Validated recommendation', 'Human approval', 'Automation'],
  },
] as const;

export const WHAT_CHANGED = {
  previous: {
    label: 'Previous Snapshot',
    progress: 61,
    expenditure: 64,
    dphis: 54,
  },
  current: {
    label: 'New Snapshot',
    progress: 59,
    expenditure: 71,
    dphis: 72,
  },
  detected: ['Cost / Progress Mismatch', 'Risk Accelerating'],
  peerContext: {
    peerMedianDphis: 46,
    targetDphis: 72,
    deviation: '+26',
  },
} as const;

export const INVESTIGATION_STEPS = [
  { label: 'Event', description: 'Risk signal detected' },
  { label: 'Evidence Needed', description: 'Identify relevant data sources' },
  { label: 'Tool Selected', description: 'Choose investigation approach' },
  { label: 'Observation', description: 'Gather project history, milestones, financial signals' },
  { label: 'Hypothesis Update', description: 'Revise explanation based on evidence' },
  { label: 'More Evidence?', description: 'Continue or conclude' },
  { label: 'Conclude', description: 'Present findings with confidence level' },
] as const;

export const PEER_COHORT = {
  target: { name: 'Target Project', dphis: 72 },
  peers: [
    { name: 'Peer A', dphis: 44 },
    { name: 'Peer B', dphis: 48 },
    { name: 'Peer C', dphis: 42 },
    { name: 'Peer D', dphis: 50 },
    { name: 'Peer E', dphis: 46 },
  ],
  median: 46,
  deviation: '+26',
} as const;

export const ANALYTICS_PREVIEW = [
  { title: 'Portfolio Risk Trend', type: 'line' },
  { title: 'Cost vs Schedule Risk', type: 'scatter' },
  { title: 'Event Heatmap', type: 'heatmap' },
  { title: 'Geographic Risk', type: 'map' },
  { title: 'Peer Deviation', type: 'bar' },
  { title: 'Intervention Outcomes', type: 'bar' },
] as const;

export const GOVERNANCE_PRINCIPLES = [
  {
    title: 'Evidence Lineage',
    description: 'Every prediction and recommendation traces back to observable project data.',
  },
  {
    title: 'Uncertainty',
    description: 'Confidence levels and evidence gaps are always visible, never hidden.',
  },
  {
    title: 'Human Approval',
    description: 'Consequential interventions require explicit authorization from decision-makers.',
  },
  {
    title: 'Audit Trail',
    description: 'Complete record of what was detected, investigated, recommended, and acted upon.',
  },
  {
    title: 'Durable Automation',
    description: 'Approved workflows execute reliably with full delivery tracking.',
  },
] as const;

export const WALKTHROUGH_STEPS = [
  {
    id: 'monitor',
    title: 'Monitor',
    description: 'Continuous observation of project state, data freshness, and milestones.',
  },
  {
    id: 'detect',
    title: 'Detect',
    description: 'Meaningful changes identified through snapshot comparison and event engine.',
  },
  {
    id: 'investigate',
    title: 'Investigate',
    description: 'Stateful agent gathers evidence, forms hypotheses, and examines causes.',
  },
  {
    id: 'decide',
    title: 'Decide',
    description: 'Evidence-backed recommendations presented for human review and approval.',
  },
  {
    id: 'learn',
    title: 'Learn',
    description: 'Outcomes measured, memory updated, peer context refined for next cycle.',
  },
] as const;

export const TECHNOLOGIES = [
  { name: 'React', role: 'Interface layer' },
  { name: 'TypeScript', role: 'Type safety' },
  { name: 'Python', role: 'Agent & ML runtime' },
  { name: 'FastAPI', role: 'Backend services' },
  { name: 'MongoDB', role: 'Document store' },
  { name: 'XGBoost', role: 'Predictive layer' },
  { name: 'SHAP', role: 'Explainability' },
  { name: 'Agent', role: 'Investigation' },
  { name: 'n8n', role: 'Automation' },
  { name: 'Langfuse', role: 'Observability' },
  { name: 'MCP', role: 'Tool protocol' },
] as const;

export const FOOTER_LINKS = {
  product: [
    { label: 'Product', href: '#product' },
    { label: 'Intelligence', href: '#intelligence' },
    { label: 'Analytics', href: '#analytics' },
  ],
  architecture: [
    { label: 'How It Works', href: '#how-it-works' },
    { label: 'Technology', href: '#technology' },
    { label: 'Governance', href: '#governance' },
  ],
  documentation: [
    { label: 'Documentation', href: '#' },
    { label: 'API Reference', href: '#' },
    { label: 'Architecture', href: '#' },
  ],
  contact: [
    { label: 'Contact', href: '#' },
    { label: 'Sign In', href: '#' },
    { label: 'Request Access', href: '#' },
  ],
  legal: [
    { label: 'Privacy', href: '#' },
    { label: 'Terms', href: '#' },
  ],
} as const;
