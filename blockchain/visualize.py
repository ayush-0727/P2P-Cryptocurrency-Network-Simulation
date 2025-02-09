# import networkx as nx
# import matplotlib.pyplot as plt

# SHORT_ID_LENGTH = 6

# def shorten_id(block_id):
#     if block_id in ("None", "GENESIS"):
#         return block_id
#     return block_id[:SHORT_ID_LENGTH]

# def linear_layout(G):
#     """
#     Computes a layout so that nodes are placed in a straight line
#     from left to right in a topological order.
#     """
#     # Ensure the graph is directed acyclic or at least treat as DAG
#     order = list(nx.topological_sort(G))
    
#     pos = {}
#     for i, node in enumerate(order):
#         pos[node] = (i, 0)   # x = i, y = 0 for a left-to-right line
    
#     return pos

# def visualize_blockchain(file_path):
#     """
#     Reads a peer file containing lines of the form:
#       child_id|parent_id|arrival_time
#     and constructs a directed graph for visualization in a straight line.
#     """
#     G = nx.DiGraph()

#     with open(file_path, 'r') as f:
#         for line in f:
#             line = line.strip()
#             if not line:
#                 continue
#             child, parent, arrival_str = line.split('|')
            
#             arrival_time = float(arrival_str)
            
#             # Add nodes
#             G.add_node(child)
#             G.add_node(parent)
            
#             # Add edge: parent -> child
#             # (Some people skip edges from "None" or "GENESIS",
#             #  but if you want a line for the entire chain, we can keep them.)
#             G.add_edge(parent, child, arrival=arrival_time)

#     # Use our custom linear layout
#     pos = linear_layout(G)

#     shortened_labels = {node: shorten_id(node) for node in G.nodes()}

#     plt.figure(figsize=(12, 2))   # shorter height for a line
#     nx.draw_networkx_nodes(G, pos, node_size=800, node_color="lightblue", edgecolors="black")
#     nx.draw_networkx_edges(G, pos, arrowstyle="->", arrowsize=15, edge_color="gray")
#     nx.draw_networkx_labels(G, pos, labels=shortened_labels, font_size=8, font_color="black")

#     plt.title(f"Block Graph: {file_path}")
#     plt.axis("off")
#     plt.tight_layout()
#     plt.savefig("peer0_linear.png")

# if __name__ == "__main__":
#     visualize_blockchain("peer_0.txt")


import networkx as nx
import matplotlib.pyplot as plt

SHORT_ID_LENGTH = 6

def shorten_id(block_id):
    if block_id in ("GENESIS", None):
        return block_id
    return block_id[:SHORT_ID_LENGTH]

def tree_layout(G, root="GENESIS"):
    """
    Computes a layout that arranges nodes in a tree structure.
    Parents are placed above their children.
    """
    levels = {}  # depth of each block
    pos = {}  # positions for plotting
    
    def assign_levels(node, depth=0, x=0):
        if node in levels:  # Avoid cycles
            return
        levels[node] = depth
        pos[node] = (x, -depth)  # Higher depth goes lower in the graph
        children = list(G.successors(node))
        for i, child in enumerate(children):
            assign_levels(child, depth + 1, x + i - len(children) / 2)  # Space out children

    assign_levels(root)  # Start from GENESIS
    return pos

def visualize_blockchain(file_path):
    """
    Reads a peer file containing lines of the form:
      child_id|parent_id|arrival_time
    Constructs a directed graph and visualizes it as a tree.
    """
    G = nx.DiGraph()

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            child, parent, arrival_str = line.split('|')
            if parent == "None":  # Skip invalid parent
                continue
            
            arrival_time = float(arrival_str)
            G.add_edge(parent, child, arrival=arrival_time)

    if "GENESIS" not in G:
        print("Warning: No GENESIS block found.")
        return

    # Compute tree layout
    pos = tree_layout(G, root="GENESIS")
    shortened_labels = {node: shorten_id(node) for node in G.nodes()}

    plt.figure(figsize=(10, 6))
    nx.draw_networkx_nodes(G, pos, node_size=800, node_color="lightblue", edgecolors="black")
    nx.draw_networkx_edges(G, pos, arrowstyle="->", arrowsize=15, edge_color="gray")
    nx.draw_networkx_labels(G, pos, labels=shortened_labels, font_size=8, font_color="black")

    plt.title(f"Blockchain Tree: {file_path}")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig("peer0_tree.png")

if __name__ == "__main__":
    visualize_blockchain("peer_0.txt")

