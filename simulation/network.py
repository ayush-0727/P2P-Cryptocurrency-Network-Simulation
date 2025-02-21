from .peer import Peer
import random
import networkx as nx
import matplotlib.pyplot as plt

class Network:
    def __init__(self, n, z0, z1,I):
        self.peers = []
        self.graph = nx.Graph()
        self.link_params = {}  # Stores (rho, c) for each edge
        
        all_ids = list(range(n))
        
        slow_ids = set(random.sample(all_ids, int(n * z0 / 100)))
        low_cpu_ids = set(random.sample(all_ids, int(n * z1 / 100)))
        
        for pid in all_ids:
            peer = Peer(
                peer_id=pid,
                is_slow=pid in slow_ids,
                is_low_cpu=pid in low_cpu_ids,
                link_params=self.link_params,
                I=I
            )
            self.peers.append(peer)

        self.set_hashing_powers()

        for p in self.peers:
            p.peers = self.peers

        all_peer_ids = [p.peer_id for p in self.peers]
        for peer in self.peers:
            peer.known_peer_ids = [pid for pid in all_peer_ids if pid != peer.peer_id]
       
        # Generate connected topology
        while True: 
            self.create_random_topology() 

            if nx.is_connected(self.graph): 
                self.save_graph_as_png()
                break
        
        self.set_neighbors()


    def set_hashing_powers(self):
        total = sum(10 if not p.is_low_cpu else 1 for p in self.peers)
        for p in self.peers:
            p.hashing_power = 10/total if not p.is_low_cpu else 1/total 
    
    def set_neighbors(self):
        for p in self.peers:
            p.neighbors = list(self.graph.neighbors(p.peer_id))
    
    def create_random_topology(self):
        self.graph.clear()
        self.graph.add_nodes_from(range(len(self.peers)))

        for peer in self.graph.nodes:

            # Degree of peer is randomly chosen between 3 and 6
            target_degree = random.randint(3, 6)
            current_degree = self.graph.degree(peer)

            while current_degree < target_degree:
                # Nodes with degree <= 6
                candidates = [n for n in self.graph.nodes if n != peer and not self.graph.has_edge(peer, n) and self.graph.degree(n) < 6]
                if not candidates: break

                neighbor = random.choice(candidates)
                self.graph.add_edge(peer, neighbor)
                current_degree = self.graph.degree(peer)

                # Initialize link parameters
                p1, p2 = self.peers[peer], self.peers[neighbor]
                cij = 100e6 if (not p1.is_slow and not p2.is_slow) else 5e6 
                rhoij = random.uniform(0.01, 0.5)
                self.link_params[(peer, neighbor)] = (rhoij, cij)
                self.link_params[(neighbor, peer)] = (rhoij, cij) 

    def save_graph_as_png(self):
        plt.figure(figsize=(8, 8))
        nx.draw(self.graph, with_labels=True, node_size=500, node_color="skyblue", font_size=15, font_weight="bold")
        plt.title("Network Topology")
        plt.savefig("topology_graph.png")
        plt.close()