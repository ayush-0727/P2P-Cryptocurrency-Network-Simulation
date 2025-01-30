import random
import networkx as nx
from .peer import Peer

class Network:
    def __init__(self, n, z0, z1):
        self.peers = []
        self.graph = nx.Graph()
        self.link_params = {}  # Stores (ρ, c) for each edge
        all_ids = list(range(n))
        
        # Create slow/fast peers
        slow_ids = set(random.sample(all_ids, int(n * z0 / 100)))
        low_cpu_ids = set(random.sample(all_ids, int(n * z1 / 100)))
        
        for pid in all_ids:
            peer = Peer(
                peer_id=pid,
                is_slow=pid in slow_ids,
                is_low_cpu=pid in low_cpu_ids
            )
            self.peers.append(peer)
        
        # Set known peers for each node
        all_peer_ids = [p.id for p in self.peers]
        for peer in self.peers:
            peer.known_peer_ids = [pid for pid in all_peer_ids if pid != peer.id]
        
        # Generate connected topology
        while True:
            self._create_random_topology()
            if nx.is_connected(self.graph):
                break
    
    def _create_random_topology(self):
        self.graph.clear()
        self.graph.add_nodes_from(range(len(self.peers)))
        
        for peer in self.graph.nodes:
            target_degree = random.randint(3,6)
            current_degree = self.graph.degree(peer)
            
            while current_degree < target_degree:
                candidates = [n for n in self.graph.nodes 
                            if n != peer and not self.graph.has_edge(peer, n)]
                if not candidates: break
                neighbor = random.choice(candidates)
                self.graph.add_edge(peer, neighbor)
                
                # Initialize link parameters
                p1, p2 = self.peers[peer], self.peers[neighbor]
                cij = 100e6 if (not p1.is_slow and not p2.is_slow) else 5e6  # 100/5 Mbps
                ρij = random.uniform(0.01, 0.5)  # 10-500ms in seconds
                self.link_params[(peer, neighbor)] = (ρij, cij)
                self.link_params[(neighbor, peer)] = (ρij, cij)  # Undirected