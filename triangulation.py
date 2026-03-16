from __future__ import annotations

import random
from typing import Callable

# FIRST NODE SELECTION HEURISTICS (Section 5)
def select_first_node(G: list[list[int]], heuristic: str = "f1") -> int:
    """
    Return the 0-based index of the node to use as the fixed first node.
    """
    n = len(G)
    degrees = [len(G[i]) for i in range(n)]
    avg_deg = sum(degrees) / n

    def neighbour_deg_sum(i: int) -> int:
        return sum(degrees[j] for j in G[i])

    if heuristic == "f1":
        return 0

    if heuristic == "f2":
        return max(range(n), key=lambda i: degrees[i])

    if heuristic == "f3":
        return min(range(n), key=lambda i: degrees[i])

    if heuristic == "f4":
        return min(range(n), key=lambda i: abs(degrees[i] - avg_deg))

    if heuristic == "f5":
        return random.randrange(n)

    if heuristic == "f6":
        max_deg = max(degrees)
        candidates = [i for i in range(n) if degrees[i] == max_deg]
        return min(candidates, key=neighbour_deg_sum)

    if heuristic == "f7":
        max_deg = max(degrees)
        candidates = [i for i in range(n) if degrees[i] == max_deg]
        return max(candidates, key=neighbour_deg_sum)

    if heuristic == "f8":
        target = min(range(n), key=lambda i: abs(degrees[i] - avg_deg))
        avg_like = degrees[target]
        candidates = [i for i in range(n) if degrees[i] == avg_like]
        return min(candidates, key=neighbour_deg_sum)

    if heuristic == "f9":
        target = min(range(n), key=lambda i: abs(degrees[i] - avg_deg))
        avg_like = degrees[target]
        candidates = [i for i in range(n) if degrees[i] == avg_like]
        return max(candidates, key=neighbour_deg_sum)

    if heuristic == "f10":
        min_deg = min(degrees)
        candidates = [i for i in range(n) if degrees[i] == min_deg]
        return min(candidates, key=neighbour_deg_sum)

    if heuristic == "f11":
        min_deg = min(degrees)
        candidates = [i for i in range(n) if degrees[i] == min_deg]
        return max(candidates, key=neighbour_deg_sum)

    raise ValueError(f"Unknown first-node heuristic: {heuristic!r}")


# MINIMAL ENUMERATION (Section 4)

def build_base_relational_graph(
    G: list[list[int]],
    first_node: int,
) -> set[frozenset[int]]:
    """
    Build the undirected edge set of the base relational graph R_B.

    Three types of edges are required (Section 4):
      1. Every edge from the original graph G (needed for the successor-
        ordering relationship constraints).
      2. An edge between first_node and every other node (first node must
        precede all others in the permutation).
      3. An edge between every neighbour of first_node and every other node
        that is not first_node itself (the last-node constraint requires
        that whichever neighbour becomes the last node precedes all others).
    """
    n = len(G)
    edges: set[frozenset[int]] = set()

    # Type 1 — original graph edges
    for u, neighbours in enumerate(G):
        for v in neighbours:
            edges.add(frozenset((u, v)))

    # Type 2 — first_node to all others
    for i in range(n):
        if i != first_node:
            edges.add(frozenset((first_node, i)))

    # Type 3 — neighbours of first_node to all non-first-node nodes
    for neighbour in G[first_node]:
        for i in range(n):
            if i != first_node and i != neighbour:
                edges.add(frozenset((neighbour, i)))

    return edges


def _fill_edges(adj: dict[int, set[int]], node: int) -> set[frozenset[int]]:
    """Return the set of fill edges that would be added when eliminating node."""
    nbrs = list(adj[node])
    return {
        frozenset((nbrs[a], nbrs[b]))
        for a in range(len(nbrs))
        for b in range(a + 1, len(nbrs))
        if nbrs[b] not in adj[nbrs[a]]
    }


def _triangles_added(adj: dict[int, set[int]], node: int,
                     fill: set[frozenset[int]]) -> int:
    """
    Count triangles in R_T that would include *node* at this elimination step,
    using edges from adj plus the fill edges that will be added.
    """
    # Temporary adjacency with fill
    nbrs = adj[node] | {v for e in fill for v in e if v != node}
    nbrs.discard(node)
    count = 0
    nbr_list = list(nbrs)
    for a in range(len(nbr_list)):
        for b in range(a + 1, len(nbr_list)):
            u, v = nbr_list[a], nbr_list[b]
            if v in adj[u] or frozenset((u, v)) in fill:
                count += 1
    return count


def triangulate(
    edges: set[frozenset[int]],
    n: int,
    heuristic: str = "t9",
) -> set[frozenset[int]]:
    """
    Extend *edges* to a chordal graph via node-elimination triangulation.

    Returns the edge set of the triangulated relational graph R_T, which
    includes all original edges plus any fill edges added during elimination.
    """
    # Build working adjacency from the edge set
    nodes = set(range(n))
    adj: dict[int, set[int]] = {v: set() for v in nodes}
    for e in edges:
        u, v = tuple(e)
        adj[u].add(v)
        adj[v].add(u)

    original_degrees = {v: len(adj[v]) for v in nodes}
    rt_edges = set(edges)          # accumulate R_T edges here
    remaining = set(nodes)

    while remaining:
        # --- Primary key: current minimum degree ---
        min_deg = min(len(adj[v]) for v in remaining)
        candidates = [v for v in remaining if len(adj[v]) == min_deg]

        # --- Tie-breaking ---
        def nbr_deg_sum(v):
            return sum(len(adj[u]) for u in adj[v] if u in remaining)

        def fill_size(v):
            return len(_fill_edges(adj, v))

        if heuristic == "t1":
            node = min(candidates, key=nbr_deg_sum)
        elif heuristic == "t2":
            node = max(candidates, key=nbr_deg_sum)
        elif heuristic == "t3":
            node = min(candidates, key=fill_size)
        elif heuristic == "t4":
            node = max(candidates, key=fill_size)
        elif heuristic == "t5":
            node = min(candidates, key=lambda v: original_degrees[v])
        elif heuristic == "t6":
            node = max(candidates, key=lambda v: original_degrees[v])
        elif heuristic == "t7":
            node = min(candidates,
                       key=lambda v: _triangles_added(adj, v, _fill_edges(adj, v)))
        elif heuristic == "t8":
            node = max(candidates,
                       key=lambda v: _triangles_added(adj, v, _fill_edges(adj, v)))
        elif heuristic == "t9":
            # Min fill, tie-break: first in description (smallest index)
            node = min(candidates, key=lambda v: (fill_size(v), v))
        elif heuristic == "t10":
            # Min fill, tie-break: random  (Kjaerulff "minimum fill")
            min_fill = min(fill_size(v) for v in candidates)
            node = random.choice([v for v in candidates
                                   if fill_size(v) == min_fill])
        elif heuristic == "t11":
            node = min(candidates,
                       key=lambda v: (_triangles_added(adj, v, _fill_edges(adj, v)), v))
        elif heuristic == "t12":
            min_tri = min(_triangles_added(adj, v, _fill_edges(adj, v))
                          for v in candidates)
            node = random.choice([v for v in candidates
                                   if _triangles_added(adj, v,
                                                        _fill_edges(adj, v)) == min_tri])
        else:
            raise ValueError(f"Unknown triangulation heuristic: {heuristic!r}")

        # Add fill edges to R_T and update adjacency
        for e in _fill_edges(adj, node):
            u, v = tuple(e)
            rt_edges.add(e)
            adj[u].add(v)
            adj[v].add(u)

        # Eliminate node
        for nbr in list(adj[node]):
            adj[nbr].discard(node)
        del adj[node]
        remaining.remove(node)

    return rt_edges

def enumerate_triangles(
    rt_edges: set[frozenset[int]],
    n: int,
) -> list[tuple[int, int, int]]:
    """
    Return all triangles (i, j, k) with i < j < k in the chordal graph R_T.

    These are the triples for which transitivity constraints are emitted.
    """
    # Rebuild adjacency from R_T edge set
    adj: dict[int, set[int]] = {v: set() for v in range(n)}
    for e in rt_edges:
        u, v = tuple(e)
        adj[u].add(v)
        adj[v].add(u)

    triangles = []
    nodes = sorted(adj.keys())
    for idx, i in enumerate(nodes):
        for jdx in range(idx + 1, len(nodes)):
            j = nodes[jdx]
            if j not in adj[i]:
                continue
            for kdx in range(jdx + 1, len(nodes)):
                k = nodes[kdx]
                if k in adj[i] and k in adj[j]:
                    triangles.append((i, j, k))
    return triangles


# ---------------------------------------------------------------------------
# Public interface used by constraints.py
# ---------------------------------------------------------------------------

def minimal_transitivity_constraints(
    solver,
    first_node: int,
    triangulation_heuristic: str = "t9",
) -> list[list[int]]:
    """
    Build and return transitivity clauses using minimal enumeration (Section 4).

    Steps:
      1. Build R_B for the given first_node.
      2. Triangulate R_B → R_T using the chosen heuristic.
      3. For each triangle in R_T, emit the two Lemma-1 clauses.

    """
    from constraints import _ordering_literal   # avoid circular import at module level

    n = len(solver.G)
    rb = build_base_relational_graph(solver.G, first_node)
    rt = triangulate(rb, n, heuristic=triangulation_heuristic)
    triangles = enumerate_triangles(rt, n)

    clauses = []
    for i, j, k in triangles:
        # i < j < k guaranteed by enumerate_triangles
        o_ij = _ordering_literal(solver, i, j)
        o_jk = _ordering_literal(solver, j, k)
        o_ik = _ordering_literal(solver, i, k)
        # Lemma 1, clause 1: ¬o_ij ∨ ¬o_jk ∨ o_ik
        clauses.append([-o_ij, -o_jk,  o_ik])
        # Lemma 1, clause 2:  o_ij ∨  o_jk ∨ ¬o_ik
        clauses.append([ o_ij,  o_jk, -o_ik])

    return clauses


def minimal_inverse_transitivity_constraints(
    solver,
    first_node: int,
    triangulation_heuristic: str = "t9",
) -> list[list[int]]:
    """
    Inverse transitivity constraints (Section 6) restricted to ordering-variable
    pairs that actually appear as edges in R_T (the triangulated graph).

    """
    from constraints import _ordering_literal, _var

    n = len(solver.G)
    rb = build_base_relational_graph(solver.G, first_node)
    rt = triangulate(rb, n, heuristic=triangulation_heuristic)

    # Build adjacency of R_T for fast edge lookup
    rt_adj: dict[int, set[int]] = {v: set() for v in range(n)}
    for e in rt:
        u, v = tuple(e)
        rt_adj[u].add(v)
        rt_adj[v].add(u)

    clauses = []
    for i, neighbours in enumerate(solver.G):
        for j in neighbours:
            s_ij_neg = _var(solver, f"s_{i+1}.{j+1}", negated=True)
            for k in range(n):
                if k == i or k == j:
                    continue
                # Only emit if the required ordering variables exist in R_T
                ik_in_rt = k in rt_adj[i]
                jk_in_rt = k in rt_adj[j]
                kj_in_rt = j in rt_adj[k]  # same as jk due to undirected
                ki_in_rt = i in rt_adj[k]  # same as ik due to undirected

                # Forward:  ¬s_ij ∨ ¬o_ik ∨ o_jk  (needs o_ik and o_jk)
                if ik_in_rt and jk_in_rt:
                    clauses.append([
                        s_ij_neg,
                        -_ordering_literal(solver, i, k),
                         _ordering_literal(solver, j, k),
                    ])
                # Backward: ¬s_ij ∨ ¬o_kj ∨ o_ki  (needs o_kj and o_ki)
                if kj_in_rt and ki_in_rt:
                    clauses.append([
                        s_ij_neg,
                        -_ordering_literal(solver, k, j),
                         _ordering_literal(solver, k, i),
                    ])

    return clauses
