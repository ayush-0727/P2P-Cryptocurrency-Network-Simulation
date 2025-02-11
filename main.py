import argparse
import networkx as nx
import time
from simulation.network import Network
from simulation.simulator import Simulator

n = 50
I = 600
max_time = 200000
z0 = 0
z1 = 0
Ttx = 100

def main():
    start_time = time.time()
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--n', type=int, default=50, help='Number of peers')
    parser.add_argument('--z0', type=float, default=z0, help='Percentage of slow nodes')
    parser.add_argument('--z1', type=float, default=z1, help='Percentage of low CPU nodes')
    parser.add_argument('--Ttx', type=float, default=Ttx, help='Mean transaction interarrival time')
    args = parser.parse_args()
    
    network = Network(args.n, args.z0, args.z1,I)
    print(f"Network diameter: {nx.diameter(network.graph)}")
    print(f"Average degree: {sum(dict(network.graph.degree()).values())/100}")
    simulator = Simulator(network, args.Ttx, I, max_time)
    simulator.initialize_events()
    simulator.run()
    
    end_time = time.time()
    execution_time = end_time - start_time
    print("Simulation Complete")
    print(f"Total Simulation Time: {execution_time:.2f} seconds")


if __name__ == "__main__":
    main()