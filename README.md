# Hamiltonian Cycle SAT Solver

A Python implementation of a SAT-based Hamiltonian Cycle Problem (HCP) solver, based on the relative encoding described in:

> Velev, M.N. & Gao, P. (2009). *Efficient SAT Techniques for Relative Encoding of Permutations with Constraints, Applied to Hamiltonian Cycles*. AI 2009, LNAI 5866, pp. 517–527.

## What is the Hamiltonian Cycle Problem?

Given a graph, a **Hamiltonian cycle** is a route that visits every node exactly once and returns to the starting node. Finding one (or proving none exists) is NP-complete — meaning there's no known polynomial-time algorithm, and it becomes very hard very fast as graphs grow.

This solver encodes the problem as a **Boolean satisfiability (SAT)** formula and hands it to a modern SAT solver (CaDiCaL). SAT solvers have become extraordinarily fast through decades of engineering, so this approach scales much better than naive search.

## Installation

Requires Python 3.9+ and one dependency:

```bash
pip install python-sat
```

## Usage

```python
from hamilton_solver import HamiltonSolver

solver = HamiltonSolver()
solver.read_file("Examples/graph26.hcp")
solver.full_encoding()
solution = solver.solve_hamilton()

print("SOLUTION:", solution)
```

`solve_hamilton()` returns either:
- A list of 1-based node indices representing the cycle, with the first node repeated at the end — e.g. `[1, 4, 3, 6, 5, 2, 1]`
- The string `"UNSAT"` if no Hamiltonian cycle exists

## Input format

Graph files use the TSPLIB/HCP format:

```
NAME : my_graph
TYPE : HCP
DIMENSION : 6
EDGE_DATA_FORMAT : EDGE_LIST
EDGE_DATA_SECTION
1 2
1 4
2 3
3 4
-1
EOF
```

Nodes are 1-indexed in the file. The solver converts to 0-indexed internally.
For testing the [FHCP Challenge Set](https://sites.flinders.edu.au/flinders-hamiltonian-cycle-project/fhcp-challenge-set/) was used.

## Heuristics

`full_encoding()` accepts two heuristic parameters. The paper's best overall combination is the default: `f1` + `t9`.

```python
solver.full_encoding(
    first_node_heuristic="f1",      # default, best for random graphs
    triangulation_heuristic="t9",   # default, best for random graphs
)
```

For structured graphs (e.g. DIMACS coloring instances), `f4` + `t4` performs better.

### First-node heuristics (`f1`–`f11`)

Fix one node as the start of the cycle. All choices are equivalent for correctness — the heuristic only affects performance.

| Heuristic | Selection strategy |
|---|---|
| `f1` | First node in graph description (default) |
| `f2` | Maximum degree |
| `f3` | Minimum degree |
| `f4` | Degree closest to average |
| `f5` | Random |
| `f6` | Max degree, tie-break: lesser neighbour degree sum |
| `f7` | Max degree, tie-break: greater neighbour degree sum |
| `f8` | Average degree, tie-break: lesser neighbour degree sum |
| `f9` | Average degree, tie-break: greater neighbour degree sum |
| `f10` | Min degree, tie-break: lesser neighbour degree sum |
| `f11` | Min degree, tie-break: greater neighbour degree sum |

### Triangulation heuristics (`t1`–`t12`)

Controls how the base relational graph is triangulated into a chordal graph. All heuristics first select the node with the current minimum degree, then break ties as follows:

| Heuristic | Tie-breaking strategy |
|---|---|
| `t1` | Lesser sum of neighbours' degrees |
| `t2` | Greater sum of neighbours' degrees |
| `t3` | Lesser fill count (fewer edges added) |
| `t4` | Greater fill count |
| `t5` | Lesser original degree in R_B |
| `t6` | Greater original degree in R_B |
| `t7` | Fewer additional triangles created in R_T |
| `t8` | More additional triangles created in R_T |
| `t9` | Minimum fill, then smallest node index (deterministic, default) |
| `t10` | Minimum fill, then random (Kjaerulff's "minimum fill") |
| `t11` | Minimum additional triangles, then smallest node index |
| `t12` | Minimum additional triangles, then random |


## Performance

Results from the paper on random graphs (phase-transition region, 100 graphs per suite):

| Strategy | Avg speedup vs baseline |
|---|---|
| Half-variable elimination only | ~10× |
| + Minimal transitivity (t4, f4) | ~100× |
| + Inverse transitivity (t9, f1) | ~1000× |

Individual speedups reach up to 4 orders of magnitude on satisfiable structured graphs.
