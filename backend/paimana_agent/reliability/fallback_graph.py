"""Source Fallback Graph and Substitution Semantics.

Builds structured fallback graphs between primary evidence tools and their
secondary substitutes, ensuring that authority discounts and shared lineage
are tracked so fallbacks never masquerade as independent corroboration.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class FallbackNode:
    """Metadata for a tool's place in the evidence substitution hierarchy."""
    tool_name: str
    fallback_tools: list[str] = field(default_factory=list)
    source_authority: float = 0.85
    underlying_source_id: str = "PRIMARY"
    equivalence_class: str = "EXACT"  # EXACT, APPROXIMATE, WEAKER_CORROBORATION


class FallbackGraph:
    """Directed graph of tool fallback and substitution paths."""

    DEFAULT_GRAPH = {
        "approval_timeline": FallbackNode(
            tool_name="approval_timeline",
            fallback_tools=["project_history", "milestone_audit"],
            source_authority=0.88,
            underlying_source_id="APPROVAL_REGISTRY",
            equivalence_class="APPROXIMATE",
        ),
        "gis_satellite_validation": FallbackNode(
            tool_name="gis_satellite_validation",
            fallback_tools=["field_muster_rolls", "milestone_audit"],
            source_authority=0.85,
            underlying_source_id="SATELLITE_GIS",
            equivalence_class="WEAKER_CORROBORATION",
        ),
        "financial_velocity": FallbackNode(
            tool_name="financial_velocity",
            fallback_tools=["milestone_audit", "project_history"],
            source_authority=0.92,
            underlying_source_id="CUF_FINANCE",
            equivalence_class="APPROXIMATE",
        ),
        "peer_intelligence": FallbackNode(
            tool_name="peer_intelligence",
            fallback_tools=["memory_retrieval"],
            source_authority=0.75,
            underlying_source_id="PEER_DATABASE",
            equivalence_class="APPROXIMATE",
        ),
        "field_muster_rolls": FallbackNode(
            tool_name="field_muster_rolls",
            fallback_tools=["milestone_audit"],
            source_authority=0.80,
            underlying_source_id="FIELD_PORTAL",
            equivalence_class="APPROXIMATE",
        ),
        "project_history": FallbackNode(
            tool_name="project_history",
            fallback_tools=["milestone_audit"],
            source_authority=0.85,
            underlying_source_id="PAIMANA_STORE",
            equivalence_class="APPROXIMATE",
        ),
        "milestone_audit": FallbackNode(
            tool_name="milestone_audit",
            fallback_tools=["project_history"],
            source_authority=0.90,
            underlying_source_id="CUF_MILESTONE",
            equivalence_class="APPROXIMATE",
        ),
    }

    def __init__(self, nodes: Optional[dict[str, FallbackNode]] = None):
        self.nodes = dict(self.DEFAULT_GRAPH)
        if nodes:
            self.nodes.update(nodes)

    def get_fallbacks(self, tool_name: str) -> list[str]:
        """Returns ordered list of fallback tools for a failing primary tool."""
        base = tool_name.replace("tool_", "").lower()
        node = self.nodes.get(base)
        if node:
            return list(node.fallback_tools)
        return []

    def get_substitution_metadata(
        self,
        primary_tool: str,
        fallback_tool: str,
        primary_group_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Generates substitution metadata accounting for authority loss and shared lineage."""
        p_base = primary_tool.replace("tool_", "").lower()
        f_base = fallback_tool.replace("tool_", "").lower()

        p_node = self.nodes.get(p_base)
        f_node = self.nodes.get(f_base)

        p_auth = p_node.source_authority if p_node else 0.85
        f_auth = f_node.source_authority if f_node else 0.70

        # Authority discount
        authority_ratio = min(1.0, f_auth / max(0.01, p_auth))

        # Check shared lineage
        same_lineage = False
        if p_node and f_node and p_node.underlying_source_id == f_node.underlying_source_id:
            same_lineage = True

        return {
            "primary_tool": primary_tool,
            "fallback_tool": fallback_tool,
            "primary_authority": p_auth,
            "fallback_authority": f_auth,
            "authority_discount": round(authority_ratio, 3),
            "equivalence_class": f_node.equivalence_class if f_node else "APPROXIMATE",
            "same_underlying_lineage": same_lineage,
            "is_independent_corroboration": not same_lineage,
        }
