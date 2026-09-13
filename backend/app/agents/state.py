from typing import TypedDict, List, Dict, Any, Optional

class InvestigationState(TypedDict):
    project_id: str
    user_query: Optional[str]
    project_data: Dict[str, Any]
    historical_snapshots: List[Dict[str, Any]]
    engineered_features: Dict[str, float]
    predictions: Dict[str, Any]
    shap_factors: List[Dict[str, Any]]
    environmental_data: Dict[str, Any]
    peer_comparisons: List[Dict[str, Any]]
    findings: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    tools_executed: List[str]
    confidence_score: float
    final_summary: str
