def add_to_map(solver, key, neg): 
    if key not in solver.variable_map:
        solver.variable_map[key] = solver.counter
        solver.counter += 1
    return solver.variable_map[key] * neg


def successor_constraint_1(solver):
    return [[add_to_map(solver, f"s_{i+1}.{j+1}", 1) for j in dom_var] for i, dom_var in enumerate(solver.G)]


def successor_constraint_2(solver):
    return [[add_to_map(solver, f"s_{i+1}.{j+1}", -1), add_to_map(solver, f"s_{i+1}.{k+1}", -1)] 
            for i, dom_var in enumerate(solver.G)
            for j in dom_var
            for k in dom_var if j != k]


def successor_constraint_3(solver):
    return [[add_to_map(solver, f"s_{j+1}.{i+1}", 1) for j in dom_var] for i, dom_var in enumerate(solver.G)]


def successor_constraint_4(solver):
    return [[add_to_map(solver, f"s_{j+1}.{i+1}", -1), add_to_map(solver, f"s_{k+1}.{i+1}", -1)] 
            for i, dom_var in enumerate(solver.G)
            for j in dom_var
            for k in dom_var if j != k]


def successor_mutual_exclusion_constraints(solver):
    return [[add_to_map(solver, f"s_{i+1}.{j+1}", -1), add_to_map(solver, f"s_{j+1}.{i+1}", -1)]
            for i, dom_var in enumerate(solver.G)
            for j in dom_var]


def optimized_ordering_constraint_1(solver, n): #using point 3
    return [
        [add_to_map(solver, f"o_{i+1}.{j+1}", -1), add_to_map(solver, f"o_{j+1}.{k+1}", -1), add_to_map(solver, f"o_{i+1}.{k+1}", 1)]
        for i in range(n)
        for j in range(i + 1, n)
        for k in range(j + 1, n)
    ] + [
        [add_to_map(solver, f"o_{i+1}.{j+1}", 1), add_to_map(solver, f"o_{j+1}.{k+1}", 1), add_to_map(solver, f"o_{i+1}.{k+1}", -1)]
        for i in range(n)
        for j in range(i + 1, n)
        for k in range(j + 1, n)
    ]

def ordering_constraint_1(solver, n):
    return [
        [add_to_map(solver, f"o_{i+1}.{j+1}", -1), add_to_map(solver, f"o_{j+1}.{k+1}", -1), add_to_map(solver, f"o_{i+1}.{k+1}", 1)]
        for i in range(n)
        for j in range(n)
        for k in range(n)
        if j != k and k != i and i != j
    ]


def ordering_constraint_2(solver, n):
    return [[add_to_map(solver, f"o_{i+1}.{j+1}", -1), add_to_map(solver, f"o_{j+1}.{i+1}", -1)]
            for i in range(n)
            for j in range(n)
            if j != i]

def ordering_constraint_3(solver, n):
    return [[add_to_map(solver, f"o_1.{i+1}", 1)]
            for i in range(1, n)]

def ordering_constraint_4(solver, n):
    return [
        [add_to_map(solver, f"s_{l+1}.1", -1), add_to_map(solver, f"o_{i+1}.{l+1}", 1)]
        for l in solver.G[0]
        for i in range(1, n)
        if i != l
    ]

def optimized_relationship_constraint(solver):
    return [
        # Original direction
        [add_to_map(solver, f"s_{i+1}.{j+1}", -1), add_to_map(solver, f"o_{i+1}.{j+1}", 1)]
        for i, dom_var in enumerate(solver.G)
        for j in dom_var
        if i < j
    ] + [
        # Inverted direction
        [add_to_map(solver, f"s_{j+1}.{i+1}", -1), add_to_map(solver, f"o_{j+1}.{i+1}", 1)]
        for i, dom_var in enumerate(solver.G)
        for j in dom_var
        if i < j and i != 0
    ]
