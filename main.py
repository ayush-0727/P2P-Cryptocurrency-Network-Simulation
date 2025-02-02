import argparse
import networkx as nx
from simulation.network import Network
from simulation.simulator import Simulator

def main():
    # parser = argparse.ArgumentParser()
    # parser.add_argument('--n', type=int, required=True, help='Number of peers')
    # parser.add_argument('--z0', type=float, required=True, help='Percentage of slow nodes')
    # parser.add_argument('--z1', type=float, required=True, help='Percentage of low CPU nodes')
    # parser.add_argument('--Ttx', type=float, required=True, help='Mean transaction interarrival time')
    # args = parser.parse_args()
    
    # network = Network(args.n, args.z0, args.z1)
    network = Network(15, 30, 20)
    print(f"Network diameter: {nx.diameter(network.graph)}")
    print(f"Average degree: {sum(dict(network.graph.degree()).values())/100}")
    # simulator = Simulator(network, args.Ttx)
    simulator = Simulator(network, 5)
    simulator.initialize_events()
    simulator.run()

if __name__ == "__main__":
    main()