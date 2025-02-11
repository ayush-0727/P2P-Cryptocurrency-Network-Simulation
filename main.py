import argparse
import networkx as nx
import time
from simulation.network import Network
from simulation.simulator import Simulator

nodes = 50
low_cpu = 20
slow = 25
I = 600
max_time = 100000
Ttx = 5

def main():
    start_time = time.time()
    
    # parser = argparse.ArgumentParser()
    # parser.add_argument('--n', type=int, required=True, help='Number of peers')
    # parser.add_argument('--z0', type=float, required=True, help='Percentage of slow nodes')
    # parser.add_argument('--z1', type=float, required=True, help='Percentage of low CPU nodes')
    # parser.add_argument('--Ttx', type=float, required=True, help='Mean transaction interarrival time')
    # args = parser.parse_args()
    
    # network = Network(args.n, args.z0, args.z1)
    network = Network(nodes,slow , low_cpu, I)
    print(f"Network diameter: {nx.diameter(network.graph)}")
    print(f"Average degree: {sum(dict(network.graph.degree()).values())/100}")
    # simulator = Simulator(network, args.Ttx)
    simulator = Simulator(network, Ttx, I, max_time)
    simulator.initialize_events()
    simulator.run()
    
    end_time = time.time()
    execution_time = end_time - start_time
    print("Simulation Complete")
    print(f"Total Simulation Time: {execution_time:.2f} seconds")
    network.peers[0].export_included_transactions("peer0_transactions.txt")


if __name__ == "__main__":
    main()