"""Project Dependency Graph Modeler & Critical Path Bottleneck Analyzer (DSI-13).

Models the directed execution dependency network linking statutory clearances,
land parcels, utility relocations, civil packages, and contractual milestones.
"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set

from .schemas import (
    ClearanceStatus,
    DependencyEdge,
    DependencyGraphReport,
    DependencyNode,
    DependencyNodeType,
    DependencyStatus,
    EnvironmentalClearanceAnalysis,
    LandAcquisitionAnalysis,
    UtilityShiftingAnalysis,
    UtilityStage,
)


class DependencyGraphBuilder:
    """Builds and analyzes directed operational dependency graphs."""

    def build_graph(
        self,
        project_code: str,
        land_analysis: Optional[LandAcquisitionAnalysis] = None,
        clearance_analysis: Optional[EnvironmentalClearanceAnalysis] = None,
        utility_analysis: Optional[UtilityShiftingAnalysis] = None,
        packages: Optional[List[Dict[str, Any]]] = None,
        milestones: Optional[List[Dict[str, Any]]] = None,
    ) -> DependencyGraphReport:
        nodes: List[DependencyNode] = []
        edges: List[DependencyEdge] = []
        node_map: Dict[str, DependencyNode] = {}

        # 1. Statutory Clearances
        if clearance_analysis and clearance_analysis.clearances:
            for idx, c in enumerate(clearance_analysis.clearances):
                nid = f"CLR_{idx+1}_{c.clearance_type.value}"
                status = DependencyStatus.SATISFIED if c.status == ClearanceStatus.FINAL_APPROVED else DependencyStatus.PENDING
                node = DependencyNode(
                    node_id=nid,
                    node_type=DependencyNodeType.CLEARANCE,
                    name=f"Clearance: {c.name}",
                    status=status,
                    critical_path=c.critical_path,
                    metadata={"clearance_type": c.clearance_type.value, "status": c.status.value},
                )
                nodes.append(node)
                node_map[nid] = node

        # 2. Land Acquisition Parcels / Stages
        land_node_id = f"LAND_{project_code}"
        if land_analysis and land_analysis.required_ha > 0:
            status = DependencyStatus.SATISFIED if land_analysis.handover_pct >= 95.0 else DependencyStatus.BLOCKED if land_analysis.handover_pct < 60.0 else DependencyStatus.PENDING
            land_node = DependencyNode(
                node_id=land_node_id,
                node_type=DependencyNodeType.LAND_PARCEL,
                name=f"RoW Land Handover ({land_analysis.handover_pct:.1f}%)",
                status=status,
                critical_path=True,
                metadata={"required_ha": land_analysis.required_ha, "handover_pct": land_analysis.handover_pct},
            )
            nodes.append(land_node)
            node_map[land_node_id] = land_node

            # Connect any forest clearances as prerequisite to forest land
            if clearance_analysis:
                for idx, c in enumerate(clearance_analysis.clearances):
                    if "FOREST" in c.clearance_type.value or "WILDLIFE" in c.clearance_type.value:
                        cid = f"CLR_{idx+1}_{c.clearance_type.value}"
                        if cid in node_map:
                            edges.append(DependencyEdge(source_id=cid, target_id=land_node_id, relation="PREREQUISITE_FOR"))

        # 3. Utilities
        if utility_analysis and utility_analysis.utilities:
            for idx, u in enumerate(utility_analysis.utilities):
                uid = f"UTL_{idx+1}_{u.utility_type.value}"
                u_status = DependencyStatus.SATISFIED if u.stage == UtilityStage.SHIFTING_COMPLETED else DependencyStatus.BLOCKED if u.blocks_workfront else DependencyStatus.PENDING
                u_node = DependencyNode(
                    node_id=uid,
                    node_type=DependencyNodeType.UTILITY,
                    name=f"Utility: {u.identifier}",
                    status=u_status,
                    critical_path=u.blocks_workfront,
                    metadata={"stage": u.stage.value, "blocks_workfront": u.blocks_workfront},
                )
                nodes.append(u_node)
                node_map[uid] = u_node

        # 4. Civil Packages / Structural Workfronts
        workfront_id = f"WF_{project_code}_MAIN"
        wf_node = DependencyNode(
            node_id=workfront_id,
            node_type=DependencyNodeType.STRUCTURAL_WORKFRONT,
            name="Main Civil Construction Alignment",
            status=DependencyStatus.IN_PROGRESS,
            critical_path=True,
        )
        nodes.append(wf_node)
        node_map[workfront_id] = wf_node

        # Connect land to main workfront
        if land_node_id in node_map:
            edges.append(DependencyEdge(source_id=land_node_id, target_id=workfront_id, relation="ENABLES_WORKFRONT", is_blocking=True))

        # Connect blocking utilities to main workfront
        if utility_analysis:
            for idx, u in enumerate(utility_analysis.utilities):
                if u.blocks_workfront:
                    uid = f"UTL_{idx+1}_{u.utility_type.value}"
                    if uid in node_map:
                        edges.append(DependencyEdge(source_id=uid, target_id=workfront_id, relation="BLOCKS_ALIGNMENT", is_blocking=True))

        # 5. Contractual Milestones & COD
        milestone_nodes: List[str] = []
        if milestones:
            for m in milestones:
                mid = str(m.get("id") or f"MS_{len(milestone_nodes)+1}")
                m_stat = DependencyStatus.SATISFIED if str(m.get("status", "")).upper() == "COMPLETED" else DependencyStatus.PENDING
                m_node = DependencyNode(
                    node_id=mid,
                    node_type=DependencyNodeType.MILESTONE,
                    name=str(m.get("name") or mid),
                    status=m_stat,
                    critical_path=True,
                    metadata=m,
                )
                nodes.append(m_node)
                node_map[mid] = m_node
                milestone_nodes.append(mid)
                edges.append(DependencyEdge(source_id=workfront_id, target_id=mid, relation="LEADS_TO"))
        else:
            # Default Milestone: Commercial Operation Date (COD)
            cod_id = f"MS_{project_code}_COD"
            cod_node = DependencyNode(
                node_id=cod_id,
                node_type=DependencyNodeType.MILESTONE,
                name="Project Commissioning (COD)",
                status=DependencyStatus.PENDING,
                critical_path=True,
            )
            nodes.append(cod_node)
            node_map[cod_id] = cod_node
            milestone_nodes.append(cod_id)
            edges.append(DependencyEdge(source_id=workfront_id, target_id=cod_id, relation="COMPLETION_GATE"))

        # Analyze Graph
        return self._analyze_graph(nodes, edges, milestone_nodes)

    def _analyze_graph(
        self,
        nodes: List[DependencyNode],
        edges: List[DependencyEdge],
        milestone_ids: List[str],
    ) -> DependencyGraphReport:
        # Build adjacency maps
        adj_out: Dict[str, List[DependencyEdge]] = defaultdict(list)
        adj_in: Dict[str, List[DependencyEdge]] = defaultdict(list)
        node_lookup = {n.node_id: n for n in nodes}

        for edge in edges:
            adj_out[edge.source_id].append(edge)
            adj_in[edge.target_id].append(edge)

        # Identify blocking nodes: unfulfilled nodes with outgoing edges
        blocking_nodes: List[str] = []
        for n in nodes:
            if n.status in (DependencyStatus.BLOCKED, DependencyStatus.PENDING, DependencyStatus.AT_RISK):
                out_edges = adj_out.get(n.node_id, [])
                if any(e.is_blocking for e in out_edges):
                    blocking_nodes.append(n.node_id)

        # Identify blocked milestones via BFS/DFS from blocking nodes
        blocked_milestones: Set[str] = set()
        for b_id in blocking_nodes:
            queue = deque([b_id])
            visited = {b_id}
            while queue:
                curr = queue.popleft()
                if curr in milestone_ids:
                    blocked_milestones.add(curr)
                for edge in adj_out.get(curr, []):
                    nxt = edge.target_id
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append(nxt)

        # Critical path nodes
        critical_path_nodes = [n.node_id for n in nodes if n.critical_path]

        total_nodes = len(nodes)
        total_edges = len(edges)

        complexity = "LOW"
        if total_nodes > 25 or total_edges > 30:
            complexity = "HIGH"
        elif total_nodes > 10 or total_edges > 12:
            complexity = "MEDIUM"

        if blocking_nodes:
            summary = (
                f"Dependency graph reveals {len(blocking_nodes)} active upstream blockage(s) "
                f"propagating delay into {len(blocked_milestones)} downstream milestone(s)."
            )
        else:
            summary = "No upstream clearance or utility dependencies currently blocking the execution sequence."

        return DependencyGraphReport(
            nodes=nodes,
            edges=edges,
            total_nodes=total_nodes,
            total_edges=total_edges,
            critical_path_nodes=critical_path_nodes,
            blocking_nodes=blocking_nodes,
            blocked_milestones=sorted(list(blocked_milestones)),
            bottleneck_summary=summary,
            graph_complexity=complexity,
        )
