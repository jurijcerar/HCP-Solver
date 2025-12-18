import constraints
#import pycosat
from pysat.solvers import Cadical103

class HamiltonSolver:

    def __init__(self):
        self.variable_map = {}
        self.counter = 1
        self.G = []
        self.clauses = []

    def read_file(self, filename):
        edges = []
        record_edges = False

        with open(filename, 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith("DIMENSION"):
                    dimension = int(line.split(":")[1].strip())
                elif line.startswith("EDGE_DATA_SECTION"):
                    record_edges = True
                elif line.startswith("-1"):
                    break
                elif record_edges:
                    edge = list(map(int, line.split()))
                    edges.append(edge)

        self.G = [[] for _ in range(dimension)]

        for edge in edges:
            u, v = edge[0] - 1, edge[1] - 1
            self.G[u].append(v)
            self.G[v].append(u)

    
    def full_encoding(self):
        n = len(self.G)
        
        self.clauses = [
            *constraints.successor_constraint_1(self),
            *constraints.successor_constraint_2(self),
            *constraints.successor_constraint_3(self),
            *constraints.successor_constraint_4(self),
            *constraints.successor_mutual_exclusion_constraints(self),
            *constraints.optimized_ordering_constraint_1(self, n),
            #*constraints.ordering_constraint_1(self, n),
            *constraints.ordering_constraint_2(self, n),
            *constraints.ordering_constraint_3(self, n),
            *constraints.ordering_constraint_4(self, n),
            *constraints.optimized_relationship_constraint(self)
        ]

        #unique_clauses = list(map(list, set(map(tuple, clauses))))

        # Remove duplicate clauses
        '''seen = set()
        unique_clauses = []

        for clause in clauses:
            sorted_clause = tuple(sorted(clause))
            
            if sorted_clause not in seen:
                seen.add(sorted_clause)
                unique_clauses.append(clause)
        
        self.clauses = unique_clauses'''

        #test = self.decode_encoding(self.clauses)
        #print(test)
    
    def decode_solution(self, solution):
        # Create a reverse map from value to key
        reverse_map = {v: k for k, v in self.variable_map.items()}
        
        # Collect all keys with positive values in the solution
        true_variables = [
            reverse_map[val] 
            for val in solution 
            if val > 0 and val in reverse_map
        ]
        
        return true_variables
    
    def decode_encoding(self, encoding):
        """
        Decodes the encoding (clauses) to a more human-readable form.
        It goes through each clause and each variable within the clause.
        """
        # Create a reverse map from value to key
        reverse_map = {v: k for k, v in self.variable_map.items()}

        decoded_encoding = []
        for clause in encoding:
            decoded_clause = []
            for val in clause:  
                var_name = reverse_map.get(abs(val), f"UNKNOWN_{abs(val)}")
                if val < 0:
                    decoded_clause.append(f"-{var_name}")
                else:
                    decoded_clause.append(var_name)
            decoded_encoding.append(decoded_clause)
        
        return decoded_encoding


    def solve_hamilton(self):

        '''solution = pycosat.solve(self.clauses)

        if solution == "UNSAT":
            return "No"'''
        
        with Cadical103(bootstrap_with=self.clauses) as l:

            if l.solve() == False:

                return "UNSAT"

            else:

                solution = l.get_model()
                # Decode the solution
                dec_solution = self.decode_solution(solution)

                edges = parse_solution(dec_solution)

                cycle = extract_cycle(edges)

                print("Is solution valid hamilton graph? ", is_valid_hamiltonian(self.G, dec_solution))

                return cycle

def is_valid_hamiltonian(graph, solution):

    edges = parse_solution(solution)

    # Ensure that all vertices are visited
    visited_vertices = set()
    for u, v in edges:
        visited_vertices.add(u)
        visited_vertices.add(v)
    
    # Ensure that all vertices in the graph are visited
    if len(visited_vertices) != len(graph):
        return False

    # Check if each edge in the solution exists in the graph
    for u, v in edges:
        if v-1 not in graph[u-1]:  # Adjust indexing (1-based to 0-based)
            return False

    # Check if it's a Hamiltonian circuit or path
    # The last edge must return to the starting vertex
    if edges[0][0] == edges[-1][1]:  # Circuit
        return True
    else:
        # Ensure no vertices are revisited (for a path, not a circuit)
        return len(edges) == len(graph)

def parse_solution(solution):
        edges = []
        for edge in solution:
            if edge.startswith('s_'):
                vertices = edge[2:].split('.')
                u = int(vertices[0]) 
                v = int(vertices[1])  
                edges.append((u, v))  
        return edges

    
def extract_cycle(edges):
    # Create a dictionary to map nodes to their connected neighbors
    graph = {}
    for u, v in edges:
        graph[u] = v

    # Start from node 1 (or any other node in the graph)
    start_node = edges[0][0]
    cycle = [start_node]

    # Traverse the graph until we come back to the starting node
    current_node = graph[start_node]
    while current_node != start_node:
        cycle.append(current_node)
        current_node = graph[current_node]

    # Finally, append the start_node to complete the cycle
    cycle.append(start_node)

    return cycle