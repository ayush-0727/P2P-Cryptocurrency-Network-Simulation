import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict, deque

def read_blockchain_from_file(filename):
    """
    Reads lines of the form:
        block_id | parent_id | arrival_time
    and returns a list of edges (parent_id -> block_id).
    """
    edges = []
    with open(filename, 'r') as f:
        for line in f:
            parts = line.strip().split('|')
            if len(parts) == 3:
                block_id, parent_id, arrival_time = [p.strip() for p in parts]
                # If parent is "None", treat it as having no parent (genesis)
                if parent_id not in ("None", ""):
                    edges.append((parent_id, block_id))
    return edges

def build_block_digraph(edges):
    """
    Given a list of (parent, child) edges, build and return a directed graph.
    """
    G = nx.DiGraph()
    G.add_edges_from(edges)
    return G

def find_genesis_block(G):
    """
    Returns the block with no incoming edges (in-degree=0). 
    If multiple, returns one arbitrarily.
    """
    for node in G.nodes():
        if G.in_degree(node) == 0:
            return node
    return None  # Fallback if no node has in-degree=0

def layer_layout(G, root):
    """
    Compute a layout that places nodes in layers by their distance from 'root'.
    Uses BFS to determine layer (depth) for each node.
    Returns a dict: node -> (x_position, y_position).
    """
    layers = defaultdict(list)  # layer_index -> list of nodes
    visited = set()
    queue = deque([(root, 0)])  # (node, layer_index)

    while queue:
        node, layer_idx = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        layers[layer_idx].append(node)

        # Children go in the next layer
        for child in G.successors(node):
            if child not in visited:
                queue.append((child, layer_idx + 1))

    # Convert layer info to positions:
    pos = {}
    for layer_idx, nodes_in_layer in layers.items():
        n = len(nodes_in_layer)
        # Spread out nodes horizontally in this layer
        x_gap = 1.0 / (n + 1)
        for i, node in enumerate(nodes_in_layer):
            x = (i + 1) * x_gap
            y = -layer_idx  # deeper layers go downward
            pos[node] = (x, y)
    return pos

def visualize_blockchain(filename):
    """
    Reads the blockchain data from 'filename', builds a directed graph,
    finds the genesis block, computes a layered layout, and visualizes it.
    """
    # 1. Parse the file and build edges
    edges = read_blockchain_from_file(filename)

    # 2. Build the directed graph
    G = build_block_digraph(edges)

    # 3. Find the genesis block
    root = find_genesis_block(G)
    if root is None:
        print("No genesis block found (a node with in-degree=0).")
        return

    # 4. Compute the layout
    pos = layer_layout(G, root)

    # 5. Draw the graph
    plt.figure(figsize=(10, 6))
    nx.draw_networkx_nodes(G, pos, node_color='red', node_size=80)
    nx.draw_networkx_edges(G, pos, edge_color='black', arrows=True, arrowsize=12)

    plt.title("Blockchain Visualization from {}".format(filename))
    plt.axis('off')
    plt.tight_layout()
    plt.savefig("visualization_peer0.png")

# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    # Adjust the filename/path as needed:
    visualize_blockchain("peer_0.txt")
