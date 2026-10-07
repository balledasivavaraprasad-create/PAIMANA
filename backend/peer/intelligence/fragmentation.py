"""Cohort Fragmentation & Peer Graph Connectivity Engine (CI-06, CI-7).

Constructs a peer-to-peer similarity network to detect isolated peers,
disconnected graph components, and structural fragmentation across the cohort.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from ..schemas import SimilarityBreakdown
from .schemas import FragmentationReport


class FragmentationDetector:
    """Detects isolated peers and disconnected components via similarity graph analysis."""

    def analyze_fragmentation(
        self,
        peers: List[SimilarityBreakdown],
        pairwise_threshold: float = 0.55,
    ) -> FragmentationReport:
        """Constructs peer similarity graph and assesses component connectivity."""
        n = len(peers)
        if n <= 2:
            return FragmentationReport(
                fragmentation_detected=False,
                connected_components=1 if n > 0 else 0,
                isolated_peers=[],
                largest_component_ratio=1.0,
                density=1.0,
                recommended_action="ACCEPT_COHORT",
            )

        peer_codes = [p.peer_code for p in peers]
        adj: Dict[str, Set[str]] = {c: set() for c in peer_codes}
        edge_count = 0

        # Construct edges: simulate pairwise compatibility by comparing attribute overlap
        for i in range(n):
            for j in range(i + 1, n):
                p1, p2 = peers[i], peers[j]
                # Measure pairwise closeness from similarity to target and shared attributes
                sim_diff = abs(p1.overall_similarity - p2.overall_similarity)
                ag1 = str(p1.raw_attributes.get("implementing_agency", "")).lower()
                ag2 = str(p2.raw_attributes.get("implementing_agency", "")).lower()
                sec1 = str(p1.raw_attributes.get("sector", "")).lower()
                sec2 = str(p2.raw_attributes.get("sector", "")).lower()

                # Edge condition: consistent similarity level and common agency or sector
                if sim_diff <= 0.20 and (sec1 == sec2 or ag1 == ag2):
                    adj[p1.peer_code].add(p2.peer_code)
                    adj[p2.peer_code].add(p1.peer_code)
                    edge_count += 1

        # Find connected components via BFS
        visited: Set[str] = set()
        components: List[List[str]] = []

        for code in peer_codes:
            if code not in visited:
                comp: List[str] = []
                queue = [code]
                visited.add(code)
                while queue:
                    curr = queue.pop(0)
                    comp.append(curr)
                    for neighbor in adj[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                components.append(comp)

        isolated_peers = [code for code, neighbors in adj.items() if len(neighbors) == 0]
        largest_comp_size = max(len(c) for c in components) if components else 0
        largest_comp_ratio = largest_comp_size / n if n > 0 else 1.0

        max_edges = (n * (n - 1)) / 2
        density = (edge_count / max_edges) if max_edges > 0 else 1.0

        fragmentation_detected = len(components) > 1 or len(isolated_peers) > 0

        if len(isolated_peers) > 0:
            rec = f"REVIEW_ISOLATED_PEERS: {len(isolated_peers)} peer(s) structurally disconnected from cohort."
        elif len(components) > 1:
            rec = f"REVIEW_FRAGMENTATION: Cohort divided into {len(components)} weakly connected components."
        else:
            rec = "ACCEPT_COHORT: Single strongly connected component."

        return FragmentationReport(
            fragmentation_detected=fragmentation_detected,
            connected_components=len(components),
            isolated_peers=isolated_peers,
            largest_component_ratio=largest_comp_ratio,
            density=density,
            recommended_action=rec,
        )
