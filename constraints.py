# HELPERS

def _var(solver, key, negated=False):
    """
    Return the signed literal for `key`.
 
    The variable map stores positive integers starting at 1.  A negated
    literal is returned as the negative of the stored id.
    """
    if key not in solver.variable_map:
        solver.variable_map[key] = solver.counter
        solver.counter += 1
    lit = solver.variable_map[key]
    return -lit if negated else lit
 
 
def _ordering_literal(solver, i, j):
    """
    Return the literal for the ordering variable o_{i+1}.{j+1}.
 
    With the half-variable optimisation (Section 3), o_{p}.{q} is only
    introduced when p < q (0-indexed: i < j).  When i > j we return the
    negation of o_{j+1}.{i+1} instead, reflecting o_{j}.{i} ≡ ¬o_{i}.{j}.
    """
    if i < j:
        return _var(solver, f"o_{i+1}.{j+1}")
    else:
        return _var(solver, f"o_{j+1}.{i+1}", negated=True)

# SUCCESSOR CONSTRAINTS

def successor_constraint_1(solver):
    """Each node v_i has at least one successor among its neighbours."""
    return [
        [_var(solver, f"s_{i+1}.{j+1}") for j in neighbours]
        for i, neighbours in enumerate(solver.G)
    ]

def successor_constraint_2(solver):
    """Each node v_i has at most one successor (pairwise mutual exclusion)."""
    return [
        [_var(solver, f"s_{i+1}.{j+1}", negated=True),
         _var(solver, f"s_{i+1}.{k+1}", negated=True)]
        for i, neighbours in enumerate(solver.G)
        for j in neighbours
        for k in neighbours
        if j < k  
    ]

def successor_constraint_3(solver):
    """Each node v_i is the successor of at least one of its neighbours."""
    return [
        [_var(solver, f"s_{j+1}.{i+1}") for j in neighbours]
        for i, neighbours in enumerate(solver.G)
    ]

def successor_constraint_4(solver):
    """Each node v_i is the successor of at most one of its neighbours."""
    return [
        [_var(solver, f"s_{j+1}.{i+1}", negated=True),
         _var(solver, f"s_{k+1}.{i+1}", negated=True)]
        for i, neighbours in enumerate(solver.G)
        for j in neighbours
        for k in neighbours
        if j < k
    ]

def successor_mutual_exclusion_constraints(solver):
    """
    If v_j is the successor of v_i, then v_i cannot simultaneously be the
    successor of v_j  (¬s_{i}.{j} V ¬s_{j}.{i} for every edge).
    """
    return [
        [_var(solver, f"s_{i+1}.{j+1}", negated=True),
         _var(solver, f"s_{j+1}.{i+1}", negated=True)]
        for i, neighbours in enumerate(solver.G)
        for j in neighbours
    ]

# ORDERING CONSTRAINTS

def optimized_ordering_constraint_1(solver, n):
    """
    Transitivity constraints with the half-variable optimisation (Lemma 1).
 
    For every triple {v_i, v_j, v_k} with i < j < k, Lemma 1 gives exactly
    two clauses:
        (1)  ¬o_{ij} V ¬o_{jk} V  o_{ik}
        (2)   o_{ij} V  o_{jk} V ¬o_{ik}
 
    _ordering_literal handles the sign flip for any pair where the first
    index would be greater than the second.

    Because of this ordering constraint 2 is not needed.
    """
    clauses = []
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                o_ij = _ordering_literal(solver, i, j)
                o_jk = _ordering_literal(solver, j, k)
                o_ik = _ordering_literal(solver, i, k)
                # Clause 1: ¬o_ij V ¬o_jk V o_ik
                clauses.append([-o_ij, -o_jk, o_ik])
                # Clause 2:  o_ij V  o_jk V ¬o_ik
                clauses.append([o_ij, o_jk, -o_ik])
    return clauses

def ordering_constraint_3(solver, n, first_node: int = 0):
    """
    The chosen first node precedes all other nodes:
    o_{f}.{i} for all i ≠ f.
 
    first_node is the 0-based index selected by a Section 5 heuristic.
    """
    return [
        [_ordering_literal(solver, first_node, i)]
        for i in range(n)
        if i != first_node
    ]

def ordering_constraint_4(solver, n, first_node: int = 0):
    """
    The last node in the cycle (the neighbour of first_node selected as
    last via s_{l+1}.{f+1}) must precede all other non-first nodes:
        ¬s_{l+1}.{f+1} V o_{i}.{l}
    for every neighbour l of first_node, and every i ∉ {first_node, l}.
 
    first_node is the 0-based index selected by a Section 5 heuristic.
    """
    f = first_node
    return [
        [_var(solver, f"s_{l+1}.{f+1}", negated=True),
         _ordering_literal(solver, i, l)]
        for l in solver.G[f]
        for i in range(n)
        if i != f and i != l
    ]

# RELATIONSHIP CONSTRAINTS

def optimized_relationship_constraint(solver):
    """
    s_{ij} ⇒ o_{ij},  i.e.  ¬s_{ij} V o_{ij},  for every edge (i, j).

    """
    return [
        [_var(solver, f"s_{i+1}.{j+1}", negated=True),
         _ordering_literal(solver, i, j)]
        for i, neighbours in enumerate(solver.G)
        for j in neighbours
        if j != solver.first_node     # exclude closing-edge candidates
    ]

# INVERSE TRANSITIVITY CONSTRAINTS (Section 6 of paper)

def inverse_transitivity_constraints(solver):
    """
    For every directed edge (v_i → v_j) implied by s_{ij} and every third
    node v_k, two families of constraints prune the search space:
 
    Forward:  s_{ij} ∧ o_{ik} ⇒ o_{jk}
                         ¬s_{ij} V ¬o_{ik} V o_{jk}
 
    Backward:  s_{ij} ∧ o_{kj} ⇒ o_{ki}
                         ¬s_{ij} V ¬o_{kj} V o_{ki}
 
    These are generated for every edge (i, j) in the original graph and every
    node k that is different from both i and j.
    """
    n = len(solver.G)
    clauses = []
    for i, neighbours in enumerate(solver.G):
        for j in neighbours:
            s_ij = _var(solver, f"s_{i+1}.{j+1}", negated=True)
            for k in range(n):
                if k == i or k == j:
                    continue
                # Forward:  ¬s_ij V ¬o_ik V o_jk
                clauses.append([s_ij,
                                 -_ordering_literal(solver, i, k),
                                  _ordering_literal(solver, j, k)])
                # Backward: ¬s_ij V ¬o_kj V o_ki
                clauses.append([s_ij,
                                 -_ordering_literal(solver, k, j),
                                  _ordering_literal(solver, k, i)])
    return clauses
