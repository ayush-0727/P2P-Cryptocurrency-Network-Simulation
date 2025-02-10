import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch
from matplotlib.collections import LineCollection

SHORT_ID_LENGTH = 6

def shorten_id(block_id):
    if block_id in ("GENESIS", None):
        return block_id
    return block_id[:SHORT_ID_LENGTH]

def curved_edges(G, pos, ax, color="black"):
    """Draws curved edges to better visualize blockchain branching."""
    for u, v in G.edges():
        start, end = pos[u], pos[v]
        mid = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2 + 0.2]  # Offset for curvature
        curve = np.array([start, mid, end])
        ax.add_collection(LineCollection([curve], color=color, linewidths=1))

def visualize_blockchain(file_path):
    """
    Reads a peer file containing lines of the form:
      child_id|parent_id|arrival_time
    Constructs a directed graph and visualizes it.
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

    # Use Kamada-Kawai layout for a structured look
    pos = nx.kamada_kawai_layout(G)
    shortened_labels = {node: shorten_id(node) for node in G.nodes()}

    fig, ax = plt.subplots(figsize=(12, 7))
    curved_edges(G, pos, ax)  # Draw smooth edges

    nx.draw_networkx_nodes(G, pos, node_size=100, node_color="red", edgecolors="black", alpha=0.9, ax=ax)
    nx.draw_networkx_labels(G, pos, labels=shortened_labels, font_size=2, font_color="black", ax=ax)

    plt.title("Blockchain Tree Representation")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig("blockchain_tree.png", dpi=300)

if __name__ == "__main__":
    visualize_blockchain("peer_3.txt")
