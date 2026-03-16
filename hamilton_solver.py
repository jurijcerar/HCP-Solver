import constraints
import triangulation as tri
from pysat.solvers import Cadical103
 
 
class HamiltonSolver:
 
    def __init__(self):
        self.variable_map: dict[str, int] = {}
        self.counter: int = 1
        self.G: list[list[int]] = []   # adjacency list (0-indexed)
        self.clauses: list[list[int]] = []
 
    def read_file(self, filename: str) -> None:
        """Parse a .hcp file (TSPLIB / HCP format) into an adjacency list."""
        edges = []
        dimension = 0
        record_edges = False
 
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith("DIMENSION"):
                    dimension = int(line.split(":")[1].strip())
                elif line.startswith("EDGE_DATA_SECTION"):
                    record_edges = True
                elif line.startswith("-1"):
                    break
                elif record_edges:
                    u, v = map(int, line.split())
                    edges.append((u, v))
 
        self.G = [[] for _ in range(dimension)]
        for u, v in edges:
            self.G[u - 1].append(v - 1)
            self.G[v - 1].append(u - 1)

    
    def full_encoding(
        self,
        first_node_heuristic: str = "f1",
        triangulation_heuristic: str = "t9",
        use_inverse_transitivity: bool = True,
    ) -> None:
 
        n = len(self.G)
        first = tri.select_first_node(self.G, first_node_heuristic)
 
        self.clauses = [
            *constraints.successor_constraint_1(self),
            *constraints.successor_constraint_2(self),
            *constraints.successor_constraint_3(self),
            *constraints.successor_constraint_4(self),
            *constraints.successor_mutual_exclusion_constraints(self),
            *constraints.ordering_constraint_3(self, n, first_node=first),
            *constraints.ordering_constraint_4(self, n, first_node=first),
            *constraints.optimized_relationship_constraint(self),
            *tri.minimal_transitivity_constraints(self, first, triangulation_heuristic),
            *tri.minimal_inverse_transitivity_constraints(self, first, triangulation_heuristic),
        ]
    
    def solve_hamilton(self):
        with Cadical103(bootstrap_with=self.clauses) as solver:
            if not solver.solve():
                return "UNSAT"
 
            raw = solver.get_model()
            true_vars = self._decode_solution(raw)
            edges = _parse_successor_edges(true_vars)
            cycle = _extract_cycle(edges)
 
            print("Is valid Hamiltonian cycle?", _is_valid_hamiltonian(self.G, true_vars))
            return cycle
    
    # HELPERS
    def _decode_solution(self, model: list[int]) -> list[str]:
        """Return the names of all variables that are true in *model*."""
        reverse_map = {v: k for k, v in self.variable_map.items()}
        return [reverse_map[lit] for lit in model if lit > 0 and lit in reverse_map]
 
    def decode_encoding(self) -> list[list[str]]:
        """Return a human-readable representation of the current clause set."""
        reverse_map = {v: k for k, v in self.variable_map.items()}
        result = []
        for clause in self.clauses:
            decoded = []
            for lit in clause:
                name = reverse_map.get(abs(lit), f"UNKNOWN_{abs(lit)}")
                decoded.append(f"-{name}" if lit < 0 else name)
            result.append(decoded)
        return result

def _parse_successor_edges(true_vars: list[str]) -> list[tuple[int, int]]:
    """Extract (u, v) pairs from variables of the form 's_{u}.{v}'."""
    edges = []
    for var in true_vars:
        if var.startswith("s_"):
            u_str, v_str = var[2:].split(".")
            edges.append((int(u_str), int(v_str)))
    return edges
 
 
def _extract_cycle(edges: list[tuple[int, int]]) -> list[int]:
    """Follow the successor chain to produce an ordered cycle."""
    nxt = {u: v for u, v in edges}
    start = edges[0][0]
    cycle = [start]
    current = nxt[start]
    while current != start:
        cycle.append(current)
        current = nxt[current]
    cycle.append(start)   # close the cycle
    return cycle
 
 
def _is_valid_hamiltonian(graph: list[list[int]], true_vars: list[str]) -> bool:
    """
    Verify that the solution encoded in *true_vars* is a valid Hamiltonian
    cycle for *graph*.
    """
    edges = _parse_successor_edges(true_vars)
 
    # Every graph vertex must appear
    vertices = {u for u, _ in edges} | {v for _, v in edges}
    if len(vertices) != len(graph):
        return False
 
    # Every selected edge must exist in the graph (convert to 0-based)
    for u, v in edges:
        if v - 1 not in graph[u - 1]:
            return False
 
    # Must form a single cycle visiting all nodes
    nxt = {u: v for u, v in edges}
    start = edges[0][0]
    visited, current = set(), start
    while current not in visited:
        visited.add(current)
        current = nxt.get(current, start)
    return len(visited) == len(graph) and current == start