import networkx as nx
import matplotlib.pyplot as plt

SHORT_ID_LENGTH = 6

def shorten_id(block_id):
    if block_id in ("None", "GENESIS"):
        return block_id
    return block_id[:SHORT_ID_LENGTH]

def visualize_blockchain_fork(file_path):
    """
    Reads a peer file containing lines of the form:
      child_id|parent_id|arrival_time
    Constructs a directed graph, then focuses on exactly four blocks
    around the first 'fork' found: the parent node, the forking node,
    and two of its children.
    """
    # -- 1. Build the full graph --
    G = nx.DiGraph()
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            child, parent, arrival_str = line.split('|')
            # We won't worry about arrival_time except to store it as an edge attribute
            arrival_time = float(arrival_str)

            G.add_node(parent)
            G.add_node(child)
            G.add_edge(parent, child, arrival=arrival_time)

    # -- 2. Find a node that "forks" = has more than 1 child --
    fork_node = None
    for node in G.nodes():
        # successors = children
        children = list(G.successors(node))
        if len(children) > 1:
            fork_node = node
            break

    if not fork_node:
        print("No fork found in this data!")
        return  # or just draw the entire graph, or handle differently

    # -- 3. Select exactly 4 blocks: the parent, the fork node, and two children --
    # Get the immediate parent(s)
    parent_list = list(G.predecessors(fork_node))  # Usually length 1 in a chain, ignoring GENESIS
    children_list = list(G.successors(fork_node))

    sub_nodes = []
    # Optionally include the single parent if it exists and is not "None"
    if parent_list:
        sub_nodes.append(parent_list[0])
    # The forking node itself
    sub_nodes.append(fork_node)
    # Pick two children (or one, if there's only one) 
    # If there's more than 2, we just slice to the first two:
    sub_nodes.extend(children_list[:2])

    # Make a subgraph containing those 4 nodes (and the edges among them)
    H = G.subgraph(sub_nodes).copy()

    # -- 4. Lay out the subgraph (in a small diagram) --
    pos = nx.spring_layout(H, seed=42)

    shortened_labels = {node: shorten_id(node) for node in H.nodes()}

    plt.figure(figsize=(6, 4))
    nx.draw_networkx_nodes(H, pos, node_size=1000, node_color="lightblue", edgecolors="black")
    nx.draw_networkx_edges(H, pos, arrowstyle="->", arrowsize=15, edge_color="gray")
    nx.draw_networkx_labels(H, pos, labels=shortened_labels, font_size=8, font_color="black")

    plt.title("Fork Subgraph (4 Blocks)")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig("fork_4blocks.png")

if __name__ == "__main__":
    visualize_blockchain_fork("peer_0.txt")
